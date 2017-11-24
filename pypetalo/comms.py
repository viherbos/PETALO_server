from threading import Thread, Event
from Queue import Queue
from Queue import Empty
import sys
import os
import json
import socket as sk

BYE_MSG={'command':"BYE",'arg1':"",'arg2':""}



class SCK_server(Thread):

    def __init__(self,upper_class,queue,stopper):
        self.uc = upper_class
        super(SCK_server,self).__init__()
        self.queue = queue
        self.stopper = stopper
        self.s = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        try:
            self.s.bind((self.uc.daqd_cfg['localhost'],
                        self.uc.daqd_cfg['server_port']))
            self.s.listen(5)
        except sk.error as e:
            print ("Server couldn't be opened: %s" % e)
            os._exit(1)


    def run(self):
        while not self.stopper.is_set():
            try:
                self.s.settimeout(5.0)
                self.conn, self.addr = self.s.accept()
            except sk.timeout:
                pass
            else:
                #print ("Connection Host/Address: %s  %s" % (self.uc.daqd_cfg['localhost'],
                #                                        self.addr))
                try:
                    self.s.settimeout(5.0)
                    # Ten seconds to receive the data
                    self.data = self.conn.recv(int(self.uc.daqd_cfg['buffer_size']))
                except:
                    print ("Data not received by server")
                    pass
                else:
                    self.queue.put(self.data)
                    self.conn.send(json.dumps(BYE_MSG))
                    # Handshake Message
                    self.conn.close()
        self.s.close()
        print ("SERVER SOCKET IS DEAD")


class SCK_client(Thread):

    def __init__(self,upper_class,queue,stopper):
        self.uc = upper_class
        super(SCK_client,self).__init__()
        self.queue = queue
        self.stopper = stopper

    def run(self):
      while not self.stopper.is_set():
            try:
                self.item = self.queue.get(True,timeout=5)
                # Timeout should decrease computational load
            except Empty:
                pass
                # Wait for another timeout
            else:
                self.s = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
                try:
                    #print self.uc.daqd_cfg['ext_ip']
                    self.s.connect((self.uc.daqd_cfg['ext_ip'],
                                    int(self.uc.daqd_cfg['client_port'])))
                    self.s.send(self.item)
                    # print ("Data Sent: %s" % self.item)
                    # Insert handshake
                    try:
                        # ADD TIMEOUT Mechanism !!!!
                        self.s.settimeout(5.0)
                        data_r = json.loads(self.s.recv(int(self.uc.daqd_cfg['buffer_size'])))
                        if (data_r['command']!='BYE'):
                            print ('Communication Error handshake failure (1)')
                            # A JSON stream has been received but it isn't correct
                    except:
                        print ('Communication Error handshake failure (2)')
                        # No JSON stream has been received
                        break
                    self.queue.task_done()
                    self.s.close()
                except sk.error as e:
                    print ("Client couldn't open socket: %s" % e)
                    #os._exit(1)
                    break
