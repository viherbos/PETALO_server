import os
import struct
import pandas as pd
import numpy as np

def coincidence_to_hdf5(ldat_dir  = ".",
                        ldat_name = "my_data_coincidence.ldat",
                        hdf5_name = "my_data_coincidence.hdf",
                        env_name  = "env.txt"):

    struct_event  = 'HHqfiHHqfi'
    # Coincidence struct
    struct_len    = struct.calcsize(struct_event)

    os.chdir(ldat_dir)
    i=0; j=0
    data_array=[]
    env_array=[]

    with open(ldat_name, "rb") as f:
        while True:
            data = f.read(struct_len)
            if not data: break
            i=i+1
            s = struct.unpack(struct_event,data)
            data_array.append(s)
        print ("Number of Events %d" % i)

    with open(env_name, "rb") as f:
        while True:
            data = f.readline()
            if data=="": break
            j=j+1
            env_array.append(float(data))
        print ("Number of TEMP SENSORS %d" % j)

    with pd.HDFStore( hdf5_name,
                      complevel=9, complib='bzip2') as store:
        panel_array = pd.DataFrame( data=data_array,
                                    columns=['mh_n1',
                                             'mh_j1',
                                             'timestamp1',
                                             'Q1',
                                             'id1',
                                             'mh_n2',
                                             'mh_j2',
                                             'timestamp2',
                                             'Q2',
                                             'id2'])
        env_array = pd.DataFrame( data=env_array,
                                  columns=['temp'])

        store.put('data',panel_array)
        store.put('env',env_array)
        store.close()
