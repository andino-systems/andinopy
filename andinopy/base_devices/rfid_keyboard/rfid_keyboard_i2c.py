#       _              _ _
#      / \   _ __   __| (_)_ __   ___  _ __  _   _
#     / _ \ | '_ \ / _` | | '_ \ / _ \| '_ \| | | |
#    / ___ \| | | | (_| | | | | | (_) | |_) | |_| |
#   /_/   \_\_| |_|\__,_|_|_| |_|\___/| .__/ \__, |
#                                     |_|    |___/
# by Jakob Groß
import sys
import time
from threading import Thread
from typing import Optional

import smbus2
from gpiozero import Button

from andinopy import andinopy_logger
from andinopy.interfaces.rfid_keyboard_interface import rfid_keyboard_interface


class rfid_keyboard_i2c(rfid_keyboard_interface):

    def __init__(self, on_rfid: callable(str) = None, on_function: callable(str) = None,
                 on_keyboard: callable(str) = None):
        """
        Initialize the Keyboard and RFID
        :param on_rfid: function
        :param on_function: function
        :param on_keyboard: function
        """
        self._interruptPin = 23
        self._slaveAddress = 0x4
        self._i2c = smbus2.SMBus(1)
        self._interrupt: Optional[Button] = None
        self.interrupted = False
        self._thread = None
        self.running = True

        super().__init__()
        self.on_rfid_string = on_rfid
        self.on_function_button = on_function
        self.on_keyboard_button = on_keyboard
        andinopy_logger.info("RFID and Keyboard initialized")

    def start(self):
        """
        start the Keyboard - be sure to set custom configuration first
        :return:
        """
        self._i2c.open(1)
        self._interrupt = Button(self._interruptPin, hold_time=0.01, hold_repeat=True, pull_up=False)

        # Ping I2C with timeout if no input has been received.
        #  Restart i2c connection if no answer is received after timeout.
        #  If it cant be restarted kill whole andinopy
        def _ping_read(handle):
            while handle.running:
                if not handle.interrupted:
                    andinopy_logger.info("Ping Reading")
                    handle.read_i2c()
                    time.sleep(5)

        self._thread = Thread(target=_ping_read, args=[self])
        self._thread.start()

        try:
            counter = 0
            while self._interrupt.active_time > 0:
                self._i2c.read_byte(self._slaveAddress)
                time.sleep(0.01)
                counter += 1
                if counter >= 128:
                    raise Exception("More than 128 Inputs buffered -> Firmware Corrupted")
        except TypeError:
            pass
        self._interrupt.when_held = self.read_i2c
        andinopy_logger.info("RFID and Keyboard started")

    def stop(self):
        self._interrupt.close()
        self._i2c.close()
        andinopy_logger.info("RFID and Keyboard stopped")
        self.running = False
        self._thread.join()

    def buzz_display(self, ms: int):
        """
        Make a Buzz sound for ms
        :param ms: duration in ms
        :return: None
        """
        self._send_to_controller(f"buz {ms}")

    def _send_to_controller(self, input_string):
        self._i2c.write_block_data(self._slaveAddress, 0, input_string.encode("utf-8"))

    def read_i2c(self):
        self.interrupted = True
        try:
            char_received = chr(self._i2c.read_byte(self._slaveAddress))
            self._on_char_received(char_received)
        except IOError as ioe:
            andinopy_logger.error(f"IOError while reading I2C - {ioe}")
            self._i2c.close()
            self._i2c = smbus2.SMBus(1)
            self._i2c.open(1)
        self.interrupted = False
