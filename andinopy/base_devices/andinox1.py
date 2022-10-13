#       _              _ _
#      / \   _ __   __| (_)_ __   ___  _ __  _   _
#     / _ \ | '_ \ / _` | | '_ \ / _ \| '_ \| | | |
#    / ___ \| | | | (_| | | | | | (_) | |_) | |_| |
#   /_/   \_\_| |_|\__,_|_|_| |_|\___/| .__/ \__, |
#                                     |_|    |___/
# by Jakob Groß
import subprocess
import time
from threading import Thread, Timer

import serial

from andinopy import base_config, save_base_config, andinopy_logger
from andinopy.interfaces.andino_hardware_interface import andino_hardware_interface
from andinopy.interfaces.andino_temp_interface import andino_temp_interface


class andino_x1(andino_hardware_interface, andino_temp_interface):
    def get_counters(self, mode: int) -> str:
        raise NotImplementedError()

    def __init__(self, broad_cast_function: callable(str), port: str = "/dev/ttyAMA0", baud: int = 38400, timeout=1,
                 write_timeout: int = None, byte_size: int = serial.EIGHTBITS, parity=serial.PARITY_NONE,
                 read_size: int = 1024, encoding: str = 'ascii'):
        """
        Generate the serial Port for communication with the x1
        :param port: ie. /dev/tty/AMA0
        :param baud: standart Baud Rates
        :param timeout: send timeout
        :param write_timeout: write timeout
        :param byte_size: size of a byte ie 4,7,8
        :param parity: bit parity
        :param read_size: size in byte to read at once (max)
        :param encoding: ie ascii or utf-8
        """
        super().__init__(broad_cast_function)
        self.running = False
        self._encoding = encoding
        self._read_size = read_size
        self._serial_port = serial.Serial(port, baud, byte_size, parity, writeTimeout=write_timeout,
                                          timeout=timeout)
        self.received = []
        self.timeout = 1  # 1second
        self._shutdown_index = None
        self._shutdown_after_seconds = None
        self._shutdown_start = False
        self._do_shutdown = False

        def receive_thread_code(serial_port: serial.Serial, x1instance: 'andino_x1', ):
            buffer = ""

            while x1instance.running:
                data = serial_port.read(1024).decode()
                buffer += data
                buffer = buffer.replace("\r", "")
                index = buffer.find("\n")
                while index > 0:
                    word = buffer[:index]
                    buffer = buffer[index + 1:]
                    x1instance.handle_receive(word)
                    index = buffer.find("\n")

        self._receive_thread = Thread(target=receive_thread_code, args=[self._serial_port, self])

    @property
    def shutdown_index(self):
        if self._shutdown_index is None:
            self._shutdown_index = int(base_config["andino_x1"]["shutdown_input_index"])
        return self._shutdown_index

    @shutdown_index.setter
    def shutdown_index(self, value: int):
        self._shutdown_index = value
        base_config["andino_x1"]["shutdown_input_index"] = value
        save_base_config()

    @property
    def shutdown_after_seconds(self) -> float:
        if self._shutdown_after_seconds is None:
            self._shutdown_after_seconds = float(base_config["andino_tcp"]["shutdown_duration"])
        return self._shutdown_after_seconds

    @shutdown_after_seconds.setter
    def shutdown_after_seconds(self, value: float):
        self._shutdown_after_seconds = value
        base_config["andino_tcp"]["shutdown_duration"] = str(value)
        save_base_config()

    def shutdown(self):
        andinopy_logger.debug(f"Shutdown-Input incoming for longer than f{self.shutdown_after_seconds}")
        print(f"Shutdown-Input incoming for longer than f{self.shutdown_after_seconds}")
        subprocess.run(base_config["andino_tcp"]["shutdown_script"], shell=True, check=True, text=True)

    def start(self):
        """
        Start the x1 device after configuration
        :return:
        """
        self.running = True
        if not self._serial_port.is_open:
            self._serial_port.open()
            print("Serial Port Opened")
        self._receive_thread.start()

    def stop(self):
        """
        Stop the x1 device and close all ports
        :return:
        """
        self.running = False
        if self._serial_port.is_open:
            self._serial_port.close()
        self._receive_thread.join(1)

    def _send_to_x1(self, message):
        self._serial_port.write((message + "\r\n").encode())

    def reset(self) -> str:
        return self.send_with_confirm("RESET")

    def info(self) -> str:
        return self.send_with_confirm("INFO")

    def hardware(self, mode: int) -> str:
        return self.send_with_confirm(f"HARD {mode}")

    def set_polling(self, polling_time: int) -> str:
        return self.send_with_confirm(f"POLL {polling_time}")

    def set_skip(self, skip_count: int) -> str:
        return self.send_with_confirm("SKIP")

    def set_edge_detection(self, value: bool) -> str:
        return self.send_with_confirm(f"EGDE {int(value)}")

    def set_send_time(self, send_time: int) -> str:
        return self.send_with_confirm(f"SEND {send_time}")

    def set_send_broadcast_timer(self, value: bool) -> str:
        return self.send_with_confirm(f"CNTR {int(value)}")

    def set_debounce(self, debouncing: int) -> str:
        return self.send_with_confirm(f"DEBO {debouncing}")

    def set_power(self, value: int) -> str:
        return self.send_with_confirm(f"POWR {value}")

    def set_send_relays_status(self, value: bool) -> str:
        return self.send_with_confirm(f"REL? {int(value)}")

    def set_relay(self, relay_num: int, value: int) -> str:
        return self.send_with_confirm(f"REL{relay_num} {value}")

    def pulse_relay(self, relay_num: int, value: int) -> str:
        return self.send_with_confirm(f"RPU{relay_num} {int(value)}")

    def set_broadcast_on_change(self, value: bool) -> str:
        return self.send_with_confirm(f"CHNG {int(value)}")

    def set_temp_broadcast_timer(self, value: int) -> str:
        return self.send_with_confirm(f"SENDT {value}")

    def get_temp(self) -> str:
        return self.send_with_confirm(f"TEMP")

    def set_bus(self, count: int) -> str:
        return self.send_with_confirm(f"TBUS {count}")

    def get_addresses(self) -> str:
        return self.send_with_confirm(f"ADDRT")

    def handle_receive(self, from_x1):
        recv: str = from_x1
        if recv is None:
            return
        if recv.startswith(":"):
            stati = recv.split("{")[2].replace("}", "").split(",")
            if self.shutdown_index is not None and self._shutdown_index:
                self._do_shutdown = int(stati[self._shutdown_index]) == 1

                if self._do_shutdown and not self._shutdown_start:
                    print("shutdown signal")

                    def timed_shutdown(reference: andino_x1):
                        print("shutting down now")
                        if reference._do_shutdown:
                            reference.shutdown()
                        else:
                            reference._shutdown_start = False

                    self._shutdown_start = True
                    t = Timer(interval=self.shutdown_after_seconds, function=lambda: timed_shutdown(self))
                    t.start()

            self.broadcast(recv)
        else:

            self.received.append(recv)

    def send_with_confirm(self, message):
        check_interval = 0.01  # check all 10 ms
        self._send_to_x1(message)
        for i in range(int(self.timeout / check_interval)):
            if len(self.received) != 0:
                answer = self.received.pop()
                return answer
            time.sleep(check_interval)
        raise BufferError(f"Confirmation for {message} not received")

    def broadcast(self, received: str):
        self.broad_cast_function(received[5:])
