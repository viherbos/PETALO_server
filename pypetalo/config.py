import json
import socket as sk



class JSON_config(object):

    def __init__(self, filename, data=None):
        self.data = data
        self.filename = filename

    def config_write(self):
        writeName = self.filename
        try:
            with open(writeName,'w') as outfile:
                json.dump(self.data, outfile)
        except IOError as e:
            print(e)

    def config_read(self):
        readName = self.filename
        try:
            with open(readName,'r') as infile:
                dict_values = json.load(infile)
                return (dict_values)
        except IOError as e:
            print(e)
            return('None')


class DATA(JSON_config):
    # Only filenames are read. The rest is taken from json file
    def __init__(self,read=True):
        self.config_filename = "daqd_config.json"
        self.local_host = sk.gethostbyname(sk.gethostname())

        if (read):

            super(DATA, self).__init__(filename=self.config_filename)
            self.daqd_cfg = super(DATA,self).config_read()
            self.daqd_cfg['localhost']=self.local_host
            super(DATA, self).config_write()

        else:
            # These are default values.
            # WARNING this data can change, see config file
            # For remote application same port can be used in both ends
            # For remote application use local_host_name and true ext_ip
            self.daqd_cfg= {'server_port':5005,
                            'client_port':5006,
                            'buffer_size':1024,
                            'localhost':self.local_host,
                            'ext_ip':'localhost',
                            'path_name' :"./sw_daq_tofpet2/",
                            'socket'    :"/tmp/d.sock",
                            'daq_type'  :"GBE",
                            'daq_sharem':"/dev/shm/daqd_shm",
                            'run':0
                            }
