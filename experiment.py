import numpy as np
from hardware import settings
from functions import *

class procedure(settings, atom):

    def __init__(self, simulation=False):

        self.simulation = simulation
        super().__init__(self.simulation)

#### Procedures ####

    def test(self, t=5e-8, ao=10., do=1):

        ao_channels = {
            "test_ao": ao
        }

        do_channels = {
            "test_do": do
        }

        dds_channels = {
            "cooling_freq": (0 + self.cooling_beatnote)/self.cooling_freq_div ,
            "repump_freq": (0 + self.repump_beatnote)/self.repump_freq_div
        }

        self.update(t, ao_channels, do_channels, dds_channels)

        return

    def mot(self, t=2, detune=10e6, mot_cooling=5, mot_repump_seed=5, current=5):

        ao_channels = {
            "mot_cooling": mot_cooling,
            "mot_repump_seed": mot_repump_seed,
            "coil_sum": current/self.VtoA,
            "coil_diff": 0
        }

        do_channels = {
            "mot_cooling_shutter": 1,
            "mot_repump_seed_shutter": 1,
            "slower_coil": 1,
            "coil_top_dir": 1,
            "coil_bottom_dir": 1
        }

        dds_channels = {
            "cooling_freq": (detune + self.cooling_beatnote)/self.cooling_freq_div ,
            "repump_freq": (0 + self.repump_beatnote)/self.repump_freq_div
        }

        self.update(t, ao_channels, do_channels, dds_channels)

        return

    def cmot(self, t=20e-3, detune=30e6, mot_cooling=1, mot_repump_seed=1, current=10):

        do_channels = {"slower_coil": 0}
        self.update(1e-3, {}, do_channels, {})

        self.mot(t=t-1e-3, detune=detune, mot_cooling=mot_cooling, mot_repump_seed=mot_repump_seed, current=current)

        return

    def pgc(self, t=20e-3, detune=120e6, mot_cooling=0.2, mot_repump_seed=0.1):

        self.mot(t=t, detune=detune, mot_cooling=mot_cooling, mot_repump_seed=mot_repump_seed, current=-10)

        return

    def drsc(self, t=10e-3, detune=251e6, drsc=5, optpump=1, current=-10, bias_x=1, bias_y=1, bias_z=0):

        # Degenerate Raman sideband cooling procedure

        return

    def odt(self, t=2, odt_x_ao=10, odt_y_ao=10, odt_sheet_ao=10, current=0):

        ao_channels = {
            "drsc": 0,
            "optpump": 0,
            "coil_sum": current/4,
            "coil_diff": 0,

            "odt_x_ao": odt_x_ao,
            "odt_y_ao": odt_y_ao,
            "odt_sheet_ao": odt_sheet_ao
        }

        do_channels = {
            "drsc_shutter": 0,
            "optpump_shutter": 0,
            "coil_top_dir": 1,

            "odt_x_do": 1,
            "odt_y_do": 1,
            "odt_sheet_do": 1
        }

        self.update(t, ao_channels, do_channels, {})

        return

    def evap(self, t=4, odt_x_ao=10, odt_y_ao=10, odt_sheet_ao=10, tau=2):

        step = 10000
        for i in np.linspace(1e-4, t, num=step):

            ao_channels = {
                "odt_x_ao": odt_x_ao * np.exp(-1*i/tau),
                "odt_y_ao": odt_y_ao * np.exp(-1*i/tau)
            }
            do_channels = {
                "test_do": 1
            }
            self.update((t-2)/step, ao_channels, do_channels, {})

        return

    def tof(self, t=20e-3, detune=0):

        ao_channels = {
            "odt_x_ao": 0,
            "odt_y_ao": 0,
            "odt_sheet_ao": 0
        }

        do_channels = {
            "himg_shutter": 1,

            "odt_x_do": 1,
            "odt_y_do": 1,
            "odt_sheet_do": 1
        }

        dds_channels = {
            "cooling_freq": (detune + self.cooling_beatnote)/self.cooling_freq_div ,
            "repump_freq": (0 + self.repump_beatnote)/self.repump_freq_div
        }

        self.update(t, ao_channels, do_channels, dds_channels)

        return

    def insitu(self, detune=0, img=2):

        self.tof(t=100e-6, detune=detune, img=img)

        return

    def abs_img(self, img=2):

        if self.simulation:
            self.raw_img = np.ones((2, 1024, 1280))
        else:
            self.update(100e-6, {"img": img}, {"img_trig": 1}, {})
            self.update(100e-6, {"img": 0}, {"img_trig": 0}, {})
            self.update(20e-3, {"img": img}, {"img_trig": 1}, {})
            self.update(20.1e-3, {"img": 0}, {"img_trig": 0}, {})

            self.raw_img = np.ones((2, 1024, 1280)) # dummy

        return

    def end(self, t=0.1):

        self.mot(t=t)

        return

if __name__ == "__main__":
    import timeit

    def main():
        exp = procedure(simulation=True)
#        exp.test()
        exp.mot()
        exp.cmot()
        exp.pgc()
        exp.drsc()
        exp.odt()
        exp.evap()
        exp.tof()
        exp.abs_img()
        exp.run()

        return

    begin = timeit.default_timer()
    main()

    print('Time:', timeit.default_timer() - begin, 'sec')
