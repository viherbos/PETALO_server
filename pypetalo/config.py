import json
import socket as sk


class DATA(object):
    # Only filenames are read. The rest is taken from json file
    def __init__(self,read=True):
        self.filename = "daqd_config.json"
        self.local_host = sk.gethostbyname(sk.gethostname())
        self.data=[]

        if (read==True):
            self.config_read()
            self.data['localhost']=self.local_host
        else:
            # These are default values.
            # WARNING this data can change, see config file
            # For remote application same port can be used in both ends
            # For remote application use local_host_name and true ext_ip
            self.data= {'server_port'    :5005,
                        'client_port'    :5006,
                        'buffer_size'    :1024,
                        'localhost'      :self.local_host,
                        'ext_ip'         :'',
                        'daqd_path_name' :"../sw_daq_tofpet2/",
                        'data_path'      :"/data/",
                        'socket'         :"/tmp/d.sock",
                        'daq_type'       :"GBE",
                        'daq_sharem'     :"/dev/shm/daqd_shm",
                        'run'            :0
                        }
        self.config_write()

    def config_write(self):
        try:
            with open(self.filename,'w') as outfile:
                json.dump(self.data, outfile, indent=4, sort_keys=False)
        except IOError as e:
            print(e)

    def config_read(self):
        try:
            with open(self.filename,'r') as infile:
                self.data = json.load(infile)
        except IOError as e:
            print(e)
