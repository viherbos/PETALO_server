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

    def __init__(self, upper_class, stopper):
        self.uc = upper_class
        super(DAQ,self).__init__()
        self.stopper = stopper

    def stop(self):
        self.daq_child.terminate()

    # https://gist.github.com/sebclaeys/1232088
    # Non blocking version of read stdout
    # Doesn't work with daq (no idea)
    def non_block_read(self, daq_child):
        fd = daq_child.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        try:
            return daq_child.read()
        except:
            return ""


    def run(self):
        # # Starts background process for DAQD communications
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

            #print self.daqd_call + self.daqd_args1 + self.daqd_args2
            chain = self.daqd_call+' '+self.daqd_args1+' '+self.daqd_args2+' '

            self.daq_child = sbp.Popen( chain,
                                        #[self.daqd_call,self.daqd_args1,self.daqd_args2],
                                        shell=True
                                        #stdout=sbp.PIPE
                                        #stderr=sbp.STDOUT
                                        )

            while not self.stopper.is_set():

                # nextline = self.non_block_read(self.daq_child.stdout)
                # print nextline.decode()
                # time.sleep(0.5)
                # if nextline != '':
                    # sys.stdout.write(nextline)
                    # self.daqlogfile.write(nextline)
                    # sys.stdout.flush()
                pass

            self.daq_child.terminate()
            # out_txt_daq = self.daq_child.stdout.read()
            # self.daqlogfile.write(out_txt_daq)
            # sys.stdout.write(out_txt_daq)
            # self.daqlogfile.close()
            print "DAQ THREAD IS DEAD"


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
            #stdout.append(line)
            print line
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
                    # while True:
                    #     inline = self.cfg_child.stdout.readline()
                    #     if not inline:
                    #         break
                    #     sys.stdout.write(inline)
                    #     sys.stdout.flush()
                    #sbp.check_output(chain,shell=True)

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
                    #logger(self.cfg_child)
                    #thread_logger.join()

                    #sbp.check_output(chain,shell=True)
                    # for line in self.cfg_child.stdout:
                    #     sys.stdout.write(line)
                    #     self.sklog.send(line)
                    #     sys.stdout.flush()
                    #     self.cfg_child.stdout.flush()

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
                    # while True:
                    #     inline = self.cfg_child.stdout.readline()
                    #     if not inline:
                    #         break
                    #     sys.stdout.write(inline)
                    #     sys.stdout.flush()

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

    # main_thread = runner()
    # main_thread.runner()

    sh_data = DATA(read=True)
    srv_queue = Queue()
    clt_queue = Queue()
    q_client  = Queue()

    stopper = Event()

    # Start DAQD utility
    thread_daq    = DAQ(sh_data,stopper)
    thread_SERVER = SCK_server(sh_data,srv_queue,stopper)
    thread_CLIENT = SCK_client(sh_data,q_client,stopper)
    thread_EXEC   = MSG_executer(sh_data,srv_queue,stopper,q_client)


    # Start
    thread_daq.start()
    thread_SERVER.start()
    thread_CLIENT.start()
    thread_EXEC.start()

    # aux_log = logger()
    # sys.stdout = aux_log #open('log.text', 'w')

    while not stopper.is_set():
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            print ("KeyBoard Interrupt")
            break

    stopper.set()
    thread_daq.stop()

    thread_SERVER.join()
    thread_CLIENT.join()
    thread_EXEC.join()
    thread_daq.join()


    # First time Jason writing
    # json_utils = JSON_config(sh_data.config_filename,
    #                          sh_data.daqd_cfg_init)
    # json_utils.config_write()
