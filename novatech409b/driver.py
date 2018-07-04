# https://github.com/m-labs/artiq/tree/master/artiq/devices/novatech409b
# Written by Joe Britton, 2015
# Revised by C.A., 2018

import math
import logging
import time

import serial


logger = logging.getLogger(__name__)


class UnexpectedResponse(Exception):
    pass


class Novatech409B:
    """Driver for Novatech 409B 4-channel DDS.

    All output channels are in range [0, 1, 2, 3].
    All frequencies are in Hz.
    All phases are in turns.
    All amplitudes are in volts.
    """

    error_codes = {
        "?0": "Unrecognized Command",
        "?1": "Bad Frequency",
        "?2": "Bad AM Command",
        "?3": "Input line too long",
        "?4": "Bad Phase",
        "?5": "Bad Time",
        "?6": "Bad Mode",
        "?7": "Bad Amp",
        "?8": "Bad Constant",
        "?f": "Bad Byte"
    }

    def __init__(self, serial_dev):
        if serial_dev is None:
            self.simulation = True
        else:
            self.simulation = False
            self.port = serial.serial_for_url(
                serial_dev,
                baudrate=19200,
                bytesize=8,
                parity="N",
                stopbits=1,
                xonxoff=0)

    def close(self):
        """Close the serial port."""
        if not self.simulation:
            self.port.close()

    def _ser_readline(self):
        c = self.port.read(1)
        r = c
        while c != b"\n":
            c = self.port.read(1)
            r += c
        return r

    def _ser_send(self, cmd, get_response=True):
        """Send a string to the serial port."""

        # Low-level routine for sending serial commands to device. It sends
        # strings and listens for a response terminated by a carriage return.
        # example:
        # ser_send("F0 1.0") # sets the freq of channel 0 to 1.0 MHz

        if self.simulation:
            logger.info("simulation _ser_send(\"%s\")", cmd)
        else:
            logger.debug("_ser_send(\"%s\")", cmd)
            self.port.reset_input_buffer()
            self.port.write((cmd + "\r\n").encode())
            if get_response:
                result = (self._ser_readline()).rstrip().decode()
                logger.debug("got response from device: %s", result)
                if result != "OK":
                    errstr = self.error_codes.get(result, "Unrecognized reply")
                    s = "Erroneous reply from device: {ec}, {ecs}".format(
                        ec=result, ecs=errstr)
                    raise ValueError(s)
            else:
                pass

    def reset(self):
        """Hardware reset of 409B."""
        self._ser_send("R", get_response=False)
        time.sleep(1)
        self.setup()

    def setup(self):
        """Initial setup of 409B."""

        # Setup the Novatech 409B with the following defaults:
        # * command echo off ("E d")
        # * external clock ("") 10 MHz sinusoid -1 to +7 dBm

        self._ser_send("E d", get_response=False)
        self.set_phase_continuous(True)
        self.set_simultaneous_update(False)

    def save_state_to_eeprom(self):
        """Save current state to EEPROM."""
        self._ser_send("S")

    def set_phase_continuous(self, is_continuous):
        """Toggle phase continuous mode.

        Sends the "M n" command. This turns off the automatic
        clearing of the phase register. In this mode, the phase
        register is left intact when a command is performed.
        Use this mode if you want frequency changes to remain
        phase synchronous, with no phase discontinuities.

        :param is_continuous: True or False
        """
        if is_continuous:
            self._ser_send("M n")
        else:
            self._ser_send("M a")

    def set_simultaneous_update(self, simultaneous):
        """Set simultaneous update mode.

        Sends the "I m" command. In this mode an update
        pulse will not be sent to the DDS chip until
        an "I p" command is sent. This is useful when it is
        important to change all the outputs to new values
        simultaneously.
        """
        if simultaneous:
            self._ser_send("I m")
        else:
            self._ser_send("I a")

    def do_simultaneous_update(self):
        """Apply update in simultaneous update mode."""
        self._ser_send("I p")

    def set_freq(self, ch_no, freq):
        """Set frequency of one channel."""
        # Novatech expects MHz
        self._ser_send("F{:d} {:f}".format(ch_no, freq/1e6))

    def set_phase(self, ch_no, phase):
        """Set phase of one channel."""
        # phase word is required by device
        # N is an integer from 0 to 16383. Phase is set to
        # N*360/16384 deg; in ARTIQ represent phase in cycles [0, 1]
        phase_word = round(phase*16383)
        cmd = "P{:d} {:d}".format(ch_no, phase_word)
        self._ser_send(cmd)

    def set_gain(self, ch_no, volts):
        """Set amplitude of one channel."""

        # due to error in Novatech it doesn't generate an error for
        # dac_value>1024, so need to trap.
        dac_value = int(math.floor(volts/0.51*1024))
        if dac_value < 0 or dac_value > 1023:
            s = "Amplitude out of range {v}".format(v=volts)
            raise ValueError(s)

        s = "V{:d} {:d}".format(ch_no, dac_value)
        self._ser_send(s)

    def get_status(self):
        if self.simulation:
            return ["00989680 2000 01F5 0000 00000000 00000000 000301",
                    "00989680 2000 01F5 0000 00000000 00000000 000301",
                    "00989680 2000 01F5 0000 00000000 00000000 000301",
                    "00989680 2000 01F5 0000 00000000 00000000 000301",
                    "80 BC0000 0000 0102 21"]
        else:
            self.port.reset_input_buffer()
            result = []
            self.port.write(("QUE" + "\r\n").encode())
            for i in range(6):
                m = (self._ser_readline()).rstrip().decode()
                result.append(m)
            logger.debug("got device status: %s", result)
            return result

    def ping(self):
        try:
            stat = self.get_status()
        except:
            return False
        # check that version number matches is "21"
        if stat[5][20:] == "21":
            logger.debug("ping successful")
            return True
        else:
            return False
