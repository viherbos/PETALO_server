import json
import socket as sk


class CONF_SWEEP(object):
    # Only filenames are read. The rest is taken from json file
    def __init__(self,read=True):
        self.filename = "sweep_config.json"
        self.data=[]

        if (read==True):
            self.sweep_read()
        else:
            # These are default values.

            self.data= {'QDC_GAIN'  :{"v_att_diff_bias_ig":56,
                                      "att"               :6,
                                      "integ_source_sw"   :3},
                        'DISC_LSB'  :{"disc_lsb_e"        :40},
                        'NOISE'     :{"fe_ib1"            :40,    # TOP 62
                                      "fe_ib2"            :1},    # TOP 62 - DEFAULT 48
                        'BASELINES' :{"baseline_t"        :25,    # TOP 62 - DEFAULT 61
                                      "baseline_e"        :60},   # TOP 62 - DEFAULT 60
                        'INTEG'     :{"max_intg_time"     :127,   # TOP 127
                                      "min_intg_time"     :16},   # TOP 127
                        'THRESHOLDS':{"vth_t1"            :24,    # TOP 62 - DEFAULT 25
                                      "vth_t2"            :24,    # TOP 62 - DEFAULT 24
                                      "vth_e"             :60}    # TOP 62 - DEFAULT 29
                        }
        self.sweep_write()

    def sweep_write(self):
        try:
            with open(self.filename,'w') as outfile:
                json.dump(self.data, outfile, indent=4, sort_keys=False)
        except IOError as e:
            print(e)

    def sweep_read(self):
        try:
            with open(self.filename,'r') as infile:
                self.data = json.load(infile)
        except IOError as e:
            print(e)


if __name__ == "__main__":
    config_test_w = CONF_SWEEP(read=False)
    config_test_r = CONF_SWEEP(read=True)
    print config_test_r.data['QDC_GAIN']["att"]
