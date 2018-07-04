import numpy as np
from configparser import ConfigParser
from novatech409b import driver
try:
    import nidaqmx
    from nidaqmx.constants import (LineGrouping, AcquisitionType)
except ImportError:
    pass
#import PySpin
#from andor2 import Andor

class settings:

    def __init__(self, simulation=False):

        # read configuration
        config = ConfigParser()
        config.read('config.ini')

        # NI DAQmx
        self.clock = float(config['nidaqmx']['clock']) # Hz
        self.interval = 1/self.clock # sec

        # Novatech DDS
        self.nova_serial = config['novatech']['nova_serial']

        # main coil voltage to current ratio
        self.VtoA = float(config['const']['VtoA'])

        # Point Grey
        #pgcam = PySpin.System.GetInstance()

        # Andor EMCCD
        #cam = Andor()

        # analog output channels
        self.ao_ch = {i: int(j) for i, j in config._sections['ao_ch'].items()}

        # digital output channels
        self.do_ch = {i: int(j) for i, j in config._sections['do_ch'].items()}

       # dds channels
        self.dds_ch = {int(i): j for i, j in config._sections['dds_ch'].items()}

        # PLL

        self.cooling_freq_div = int(config['const']['cooling_freq_div'])
        self.cooling_beatnote = float(config['const']['cooling_beatnote'])
        self.repump_freq_div = int(config['const']['repump_freq_div'])
        self.repump_beatnote = float(config['const']['repump_beatnote'])

        # constant Numpy arrays

        self.daq_data = np.zeros(int(self.clock*100), dtype=np.uint32, order='C') # preallocate data array
        self.runtime = 100e-6 # dummy time for configurting mot and Novatech trigger
        self.dds_data = np.zeros((32768, 4), dtype=np.float) # preallocate Novatech array
        self.nova_index = 0 # Novatech index number
        self.nova_set = np.uint32(np.ceil(100e-6*self.clock)) # Novatech minimum trigger width

        self.strob_int = np.uint32(2147483648) # write data int
        self.trig_int = np.uint32(1073741824) # output data int
        self.nova_trig = np.uint32(268435456) # Novatech trigger int
        self.ao_brd_list = np.array([9437184, 1048576, 14680064, 6291456], dtype=np.uint32) # PCB board jumper setting

#### Calculation ####

    def update(self, t, ao_channels, do_channels, dds_channels):
        c = int((self.runtime)*self.clock) # current step
        d = 0 if len(do_channels) is 0 else 6 # if any digital channel changes
        k = 0 # iterator

        assert int(t*self.clock) > 0, print('too short!') # check any update is >= 1 step
        assert not np.any(self.daq_data[(c-len(ao_channels)*2-d):c]), print('update collision!') # data update collision

        if d is not 0: # update digital data
            self.daq_data[c-6:c] = self.do_update({self.do_ch[i]: j for i, j in do_channels.items()})

        for i,j in ao_channels.items(): # update analog data
            self.daq_data[c-d-k-2:c-d-k] = self.ao_update(self.ao_ch[i], j)
            k += 2

        self.daq_data[c] = self.trig_int # update trigger
        self.runtime += t # update runtime

        if len(dds_channels) is not 0: # if any analog channel changes

            assert not np.any(np.bitwise_and(268435456, self.daq_data[c-self.nova_set-1:c])), print('nova trig collision!') # Novatech trigger collision

            dds_temp = np.zeros((1, 4)) # temp data table for dds
            for _ in range(4): # Novatech table
                if self.dds_ch[_] in dds_channels:
                    dds_temp[0, _] = dds_channels[self.dds_ch[_]]
                else:
                    dds_temp[0, _] = self.dds_data[self.nova_index-1, _]

            self.dds_data[self.nova_index:self.nova_index+1, :] = dds_temp
            self.nova_index +=1

            for _ in range(c-self.nova_set, c): # update Novatech trigger
                self.daq_data[_] += self.nova_trig

        return

    def ao_update(self, channel=0, voltage=0):
        # data format: 16 bits voltage + 3 bits channel address + 4 bits board address + strob bit
        data_int = np.uint32((voltage+10.0)*65535/20) + self.ao_brd_list[channel//8] + np.uint32(65536*(channel%8))
        return np.array([data_int + self.strob_int, data_int], dtype=np.uint32)

    def do_update(self, channels={0:0}):
        brd_2_int = np.uint32(65536) # right board
        brd_1_int = np.uint32(131072) # middle board
        brd_0_int = np.uint32(196608) # left board

        for i, j in channels.items():
            brd_num = i//16

            if brd_num == 0:
                brd_0_int += np.uint32( 2**(i%16) * bool(j) )

            elif brd_num == 1:
                brd_1_int += np.uint32( 2**(i%16) * bool(j) )

            elif brd_num == 2:
                brd_2_int += np.uint32( 2**(i%16) * bool(j) )

            else:
                pass

        return np.array([brd_0_int + self.strob_int, brd_0_int, brd_1_int + self.strob_int, brd_1_int, brd_2_int + self.strob_int, brd_2_int], dtype=np.uint32)

    def run(self):
        if self.simulation:
            #for _ in self.daq_data[0:int(self.runtime*self.clock)]:
            #    print('{0:032b}'.format(_))
            print(self.daq_data[0:int(self.runtime*self.clock)].shape)
            print(self.dds_data[0:self.nova_index, :])
            del self.daq_data, self.dds_data
        else:
            if self.nova_serial is not '':
                dds = driver.Novatech409B(self.nova_serial)
                try:
                    dds.setup()
                    dds._ser_send('m 0', get_response=False)
                    for i in range(self.nova_index):
                        dds._ser_send('t0 %04x %08x,%04x,%04x,ff'%(i, int(self.dds_data[i, 0]*1e7), 0, 1023), get_response=False)
                        dds._ser_send('t1 %04x %08x,%04x,%04x,ff'%(i, int(self.dds_data[i, 1]*1e7), 0, 1023), get_response=False)
                    #dds._ser_send('t0 %04x %08x,%04x,%04x,00'%(i, int(self.dds_data[-1, 0]*1e7), 0, 1023), get_response=False)
                    #dds._ser_send('t1 %04x %08x,%04x,%04x,00'%(i, int(self.dds_data[-1, 1]*1e7), 0, 1023), get_response=False)
                    dds._ser_send('m t', get_response=False)
                except:
                    print('Novatech error!')
                finally:
                    dds.close()
                    del self.dds_data

            with nidaqmx.Task() as task: # create NI-DAQmx task
                task.do_channels.add_do_chan('Dev1/port0/line0:7,Dev1/port1/line0:7,Dev1/port2/line0:7,Dev1/port3/line0:7', line_grouping=LineGrouping.CHAN_FOR_ALL_LINES) # group all lines
                task.timing.cfg_samp_clk_timing(self.clock, sample_mode=AcquisitionType.FINITE, samps_per_chan=int(np.ceil(self.runtime)*self.clock)) # set NI-DAQmx clock and samples

                try:
                    print(task.write(self.daq_data[0:int(np.ceil(self.runtime)*self.clock)], auto_start=False)) # write data
                    task.start()
                    task.wait_until_done(timeout=(np.ceil(self.runtime)+0.1))
                    task.stop()
                except nidaqmx.DaqError as e:
                    print(e)
                finally:
                    del self.daq_data

        return

    # Point Grey

    # Andor

if __name__ == "__main__":
    test = settings(simulation=True)
    print(test)
