from threading import Thread, Event
from Queue import Queue, Empty
import subprocess as sbp
import sys
import os
import json
import time
import socket as sk
# from config import DATA
# from comms import SCK_server, SCK_client
from pypetalo.config import DATA as DATA
from pypetalo.comms import SCK_server as SCK_server
from pypetalo.comms import SCK_client as SCK_client
import fcntl



class DAQ(Thread):

    def __init__(self, upper_class, stopper, q_client):
        self.uc = upper_class
        super(DAQ,self).__init__()
        self.stopper = stopper
        self.q_client = q_client

    def stop(self):
        self.daq_child.terminate()



    def run(self):
        # Starts background process for DAQD communications
        try:
            self.daqlogfile = open(self.uc.out_log,'w')

            #try:
            if os.access(self.uc.daqd_cfg['socket'], os.R_OK):
                os.remove(self.uc.daqd_cfg['socket'])
            if os.access(self.uc.daqd_cfg['daq_sharem'], os.R_OK):
                os.remove(self.uc.daqd_cfg['daq_sharem'])
            #Remove Trash from daqd failures

            self.daqd_call = self.uc.daqd_cfg['path_name'] + "daqd"
            self.daqd_args1 = "--socket-name="+self.uc.daqd_cfg['socket']
            self.daqd_args2 = "--daq-type="+self.uc.daqd_cfg['daq_type']

            chain = self.daqd_call+' '+self.daqd_args1+' '+self.daqd_args2+' '

            self.daq_child = sbp.Popen( chain,
                                        shell=True,
                                        stdout=sbp.PIPE,
                                        stderr=sbp.STDOUT
                                        )
            #
            while self.daq_child.poll() == None:
                 pass

            print "DAQ THREAD IS DEAD"
            self.q_client.put("\n \n DAQ is not working \n \n")
            self.daqlogfile.write(self.daq_child.stdout.read())
            self.daqlogfile.close()

            #except:
            #    print "DAQ Initialization Failure!!"

        except IOError as e:
            print(e)



class MSG_executer(Thread):

    def __init__(self,upper_class,queue,stopper, q_client):
        self.uc = upper_class
        super(MSG_executer,self).__init__()
        self.queue = queue
        self.stopper = stopper
        self.q_client = q_client



    def logger(self):
        while True:
            line = self.cfg_child.stdout.readline()
            sys.stdout.write(line)
            self.q_client.put(line)
            if line == '' and self.cfg_child.poll() != None:
                break

    def run(self):
        while not self.stopper.is_set():
            try:
                self.qrx = self.queue.get(True,timeout=0.5)
                # Timeout should decrease computational load
            except Empty:
                pass
                # Wait for another timeout
            else:
                self.item = json.loads(self.qrx)
                print ("Data Received: %s" % self.item)
                self.queue.task_done()

                # Insert an input flag to avoid execution !!!!

                if (self.item['command']=="CONFIG"):
                    # Basic configuration: FEBD + SiPM
                    # Use checkout from subprocess
                    print ("Configuration Operation: QDC+TDC Calibration")
                    os.chdir("/home/viherbos/TOFPET2/sw_daq_tofpet2")
                    self.config_call = "sh " + "configuration.template.sh"
                    chain = self.config_call

                    self.cfg_child = sbp.Popen( chain,
                                                shell=True)


                elif (self.item['command']=="TEMP"):
                    print ("Read TOFPET Temperatures")
                    os.chdir("/home/viherbos/TOFPET2/sw_daq_tofpet2")
                    self.config_call = "./read_temperature_sensors"
                    chain = self.config_call

                    self.cfg_child = sbp.Popen( chain,
                                                shell=True
                                                #stdout=sbp.PIPE
                                                )

                elif (self.item['command']=="ACQUIRE"):
                    # Data acquisition
                    print ("Acquiring Data!!")
                    os.chdir("/home/viherbos/TOFPET2/sw_daq_tofpet2")
                    self.config_call = "./acquire_sipm_data " + \
                                    "--config config.ini " + \
                                    "-o " + self.item['arg2']+' ' \
                                    "--time "+ self.item['arg1']+' '\
                                    "--mode qdc"
                    chain = self.config_call

                    self.cfg_child = sbp.Popen( chain,
                                                shell=True,
                                                stdout=sbp.PIPE,
                                                stderr=sbp.STDOUT
                                                )
                    self.logger()


                elif (self.item['command']=="C_FILTER"):
                    # Coincidence Filter
                    os.chdir("/home/viherbos/TOFPET2/sw_daq_tofpet2")
                    # ./convert_raw_to_coincidence --config config.ini -i data/my_data -o data/my_data_coincidence --writeBinary
                    print ("Applying coarse coincidence filter")
                    self.config_call = "./convert_raw_to_coincidence " + \
                                    "--config config.ini " + \
                                    "-i "+ self.item['arg1']+' '\
                                    "-o "+ self.item['arg2']+' '\
                                    "--writeBinary"
                    chain = self.config_call

                    self.cfg_child = sbp.Popen( chain,
                                                shell=True
                                                #stdout=sbp.PIPE,
                                                #stderr=sbp.PIPE
                                                )


                elif (self.item['command']=='STOP'):
                    print ("Quit Control")
                    self.stopper.set()
                    try:
                        self.cfg_child.terminate()
                    except:
                        pass

                else:
                    sys.stdout.write("Command Sequence not recognized")

        print ("EXECUTER THREAD IS DEAD")



if __name__ == "__main__":

    sh_data = DATA(read=True)
    srv_queue = Queue()
    log_queue = Queue()
    clt_queue = Queue()
    q_client  = Queue()
    q_client2  = Queue()

    stopper = Event()

    # Start DAQD utility
    thread_daq    = DAQ(sh_data,stopper,q_client2)
    thread_SERVER = SCK_server(sh_data,srv_queue,stopper)
    thread_LOGGER = SCK_client(sh_data,q_client,stopper)
    thread_LOGGER2 = SCK_client(sh_data,q_client2,stopper)
    thread_EXEC   = MSG_executer(sh_data,srv_queue,stopper,q_client)


    # Start
    thread_daq.start()
    thread_logger.start()
    thread_SERVER.start()
    thread_LOGGER.start()
    thread_LOGGER2.start()
    thread_EXEC.start()


    while not stopper.is_set():
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            print ("KeyBoard Interrupt")
            break

    stopper.set()
    thread_daq.stop()


    thread_SERVER.join()
    thread_LOGGER.join()
    thread_LOGGER2.join()
    thread_EXEC.join()
    thread_daq.join()


    # First time Jason writing
    # json_utils = JSON_config(sh_data.config_filename,
    #                          sh_data.daqd_cfg_init)
    # json_utils.config_write()
