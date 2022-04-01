#       _              _ _
#      / \   _ __   __| (_)_ __   ___  _ __  _   _
#     / _ \ | '_ \ / _` | | '_ \ / _ \| '_ \| | | |
#    / ___ \| | | | (_| | | | | | (_) | |_) | |_| |
#   /_/   \_\_| |_|\__,_|_|_| |_|\___/| .__/ \__, |
#                                     |_|    |___/
# by Jakob Groß
import sys
from typing import Dict, List
import traceback

import andinopy
from andinopy import base_config

import logging
from andinopy.interfaces.andino_hardware_interface import andino_hardware_interface
from andinopy.interfaces.andino_temp_interface import andino_temp_interface
from andinopy.tcp import simpletcp

log = logging.getLogger("andinopy")


class andino_tcp:

    def __init__(self, hardware: str = None, port: int = None, oled: bool = None, temp: bool = None,
                 key_rfid: bool = None, display: bool = None, tcp_encoding=None, display_encoding=None):
        """
        create a new instance of the andino_tcp server
        :param hardware: "x1" or "io"
        :param port: The tcp Port the server will serve on
        :param oled: oled Display enabled
        :param temp: temperature measure enabled? (only on x1)
        :param key_rfid: keyboard and rfid controller enabled?
        :param display: display enabled?
        """

        self._message_counter = 0
        self.temperature_enabled = base_config["andino_tcp"]["temp"] == "True" if temp is None else temp
        self.display_enabled = base_config["andino_tcp"]["display"] == "True" if display is None else display
        self.key_rfid_enabled = base_config["andino_tcp"]["key_rfid"] == "True" if key_rfid is None else key_rfid
        self.oled_enabled = base_config["andino_tcp"]["oled"] == "True" if oled is None else oled
        self.port = int(base_config["andino_tcp"]["port"]) if port is None else port
        self.hardware = base_config["andino_tcp"]["hardware"] if hardware is None else hardware
        self.display_encoding = base_config["andino_tcp"][
            "display_encoding"] if display_encoding is None else display_encoding
        self.tcp_encoding = base_config["andino_tcp"]["tcp_encoding"] if tcp_encoding is None else tcp_encoding

        self.tcpserver = simpletcp.tcp_server(port=self.port,
                                              on_message=self._i_handle_tcp_input,
                                              encoding=self.tcp_encoding)

        self.display_instance = None

        if self.hardware == "io":
            import andinopy.tcp.io_x1_emulator
            from andinopy.tcp.io_x1_emulator import x1_emulator
            self.x1_instance: andino_hardware_interface = x1_emulator(self._o_broadcast)
        elif self.hardware == "x1":
            from andinopy.base_devices.andinox1 import andino_x1
            self.x1_instance: andino_hardware_interface = andino_x1(self._o_broadcast)
        else:
            raise AttributeError("hardware must be 'x1' or 'io")
        if temp and isinstance(self.x1_instance, andino_temp_interface):
            self.temperature_enabled = True
            self.temperature_handle: andino_temp_interface = self.x1_instance
        if self.key_rfid_enabled:
            self._init_key_rfid()
        if self.display_enabled:
            import andinopy.base_devices.nextion_display
            self.display_instance = andinopy.base_devices.nextion_display.display(encoding=self.display_encoding)
            self.display_instance.on_display_touch = self._o_on_display_touch
            self.display_instance.on_display_string = self._o_on_display_string
        if self.oled_enabled:
            self._init_oled()

        self.assign: Dict[str, callable([str, List[str], simpletcp.tcp_server.client_handle])] = {
            'RESET': lambda x: self._i_reset("", ""),
            'PING': self._i_ping,
            'INFO': self._i_handle_andino_hardware_message,
            'HARD': self._i_handle_andino_hardware_message,
            'POLL': self._i_handle_andino_hardware_message,
            'SKIP': self._i_handle_andino_hardware_message,
            'EDGE': self._i_handle_andino_hardware_message,
            'SEND': self._i_handle_andino_hardware_message,
            'CHNG': self._i_handle_andino_hardware_message,
            'CHNP': self._i_handle_andino_hardware_message,
            'CNTR': self._i_handle_andino_hardware_message,
            'DEBO': self._i_handle_andino_hardware_message,
            'POWR': self._i_handle_andino_hardware_message,
            'REL?': self._i_handle_andino_hardware_message,
            'REL1': self._i_handle_andino_hardware_message,
            'REL2': self._i_handle_andino_hardware_message,
            'REL3': self._i_handle_andino_hardware_message,
            'REL4': self._i_handle_andino_hardware_message,
            'REL5': self._i_handle_andino_hardware_message,
            'REL6': self._i_handle_andino_hardware_message,
            'REL7': self._i_handle_andino_hardware_message,
            'REL8': self._i_handle_andino_hardware_message,
            'RPU1': self._i_handle_andino_hardware_message,
            'RPU2': self._i_handle_andino_hardware_message,
            'RPU3': self._i_handle_andino_hardware_message,
            'RPU4': self._i_handle_andino_hardware_message,
            'RPU5': self._i_handle_andino_hardware_message,
            'RPU6': self._i_handle_andino_hardware_message,
            'RPU7': self._i_handle_andino_hardware_message,
            'RPU8': self._i_handle_andino_hardware_message,
            'TBUS': self._i_handle_temp_message,
            'ADDRT': self._i_handle_temp_message,
            'SENDT': self._i_handle_temp_message,
            'TEMP': self._i_handle_temp_message,
            'BUZZ': self._i_buzz_message,
            'DISP': self._i_handle_nextion_display_message,
            'OLED': self._i_handle_oled_message,
            'SYS': self._i_handle_sys_message
        }

    def start(self):
        self.x1_instance.start()
        if self.display_enabled:
            self.display_instance.start()
        if self.key_rfid_enabled:
            self.key_rfid_instance.start()
        self.tcpserver.start()

    def stop(self):
        self.x1_instance.stop()
        if self.display_enabled:
            self.display_instance.stop()
        if self.key_rfid_enabled:
            self.key_rfid_instance.stop()
        self.tcpserver.stop()

    # region custom initializers

    def _init_oled(self):
        from andinopy.base_devices import andino_io_oled
        self.oled_instance = andino_io_oled.andino_io_oled()

    def _init_key_rfid(self):
        if sys.platform.startswith("win"):
            import andinopy.base_devices
            import andinopy.base_devices.rfid_keyboard.rfid_keyboard_serial
            self.key_rfid_instance = andinopy.base_devices.rfid_keyboard.rfid_keyboard_serial.rfid_keyboard_serial()
        else:
            import andinopy.base_devices.rfid_keyboard.rfid_keyboard_i2c
            self.key_rfid_instance = andinopy.base_devices.rfid_keyboard.rfid_keyboard_i2c.rfid_keyboard_i2c()

        self.key_rfid_instance.on_rfid_string = self._o_on_rfid
        self.key_rfid_instance.on_function_button = self._o_on_function_button
        self.key_rfid_instance.on_keyboard_button = self._o_on_number_button

    # endregion

    # region incoming functions
    def _i_handle_tcp_input(self, tcp_in: str, client_handle: simpletcp.tcp_server.client_handle):
        message = tcp_in.split(" ")
        func = message[0].upper().rstrip()
        # print(f"IN:{tcp_in}")
        args = message[1:]
        if func == '':
            self.tcpserver.send_line_to_all('')
            return
        if func not in self.assign.keys():
            log.error(f"Syntax Error in message: {tcp_in}")
            return
        try:

            self.assign[func](func, args, client_handle)

        except BufferError as usrWarn:
            log.error(client_handle.address)
            log.error(usrWarn)
            log.error(traceback.format_exc())
            self.tcpserver.send_line_to_all("ERROR")

        except ValueError as val_error:
            log.error(client_handle.address)
            log.error(val_error)
            log.error(traceback.format_exc())
            self.tcpserver.send_line_to_all("ERROR")
        except Exception as ex:
            log.error(client_handle.address)
            log.error(ex)
            log.error(traceback.format_exc())
            self.tcpserver.send_line_to_all(f"ERROR")
        except BaseException as ex:
            log.error(client_handle.address)
            log.error(ex)
            log.error(traceback.format_exc())
            self.tcpserver.send_line_to_all(f"ERROR CRITICAL SERVICE CLOSED")
            self.stop()

    def _i_ping(self, _, _2, _3):
        self.tcpserver.send_line_to_all("PING")

    def _i_handle_sys_message(self, arguments: List[str], client_handle: simpletcp.tcp_server.client_handle):
        pass

    def _i_reset(self, _, _2):
        self._message_counter = 0
        self.x1_instance.reset()

    def _i_buzz_message(self, _, arguments: List[str], _2):
        try:
            self.key_rfid_instance.buzz_display(int(arguments[0]))
            self.tcpserver.send_line_to_all("BUZZ " + str(arguments[0]))
        except ValueError:
            self.tcpserver.send_line_to_all("ERROR in buzz - no int")

    def _i_handle_nextion_display_message(self, _, arguments: List[str],
                                          _2):
        # DISP PAGE <page> -> Display page setzen
        # DISP TXT <obj> -> Text setzen
        # DISP ATTR <obj> <attribute> <value> -> Object Atribut setzen
        # DISP RAW <bytes in hex> -> send raw bytes to the display
        if not self.display_enabled:
            self.tcpserver.send_line_to_all("ERROR DISPLAY DISABLED")
            return
        display_call = arguments[0].upper()
        if display_call == "PAGE":
            self.display_instance.set_page(arguments[1])
        elif display_call == "TXT":
            self.display_instance.set_text(arguments[1], " ".join(arguments[2:]))
        elif display_call == "ATTR":
            self.display_instance.set_attr(arguments[1], arguments[2], arguments[3])
        elif display_call == "RAW":
            self.display_instance.send_raw("".join(arguments[1:]))
        else:
            self.tcpserver.send_line_to_all("ERROR")
            return
        self.tcpserver.send_line_to_all("DISP " + " ".join(arguments))

    def _i_handle_temp_message(self, func, arguments: List[str], _):
        # SENDT [0| ms > 1000] -> Temperatur Meldezyklus
        # ADDRT [1|2] -> Temepraturmesser Adressen
        # TBUS [1|2] -> Bus anzahl setzen
        # TEMP        -> poll temperature once
        if not self.temperature_enabled:
            self.tcpserver.send_line_to_all("ERROR")
            return
        else:
            if func == "SENDT":
                self.tcpserver.send_line_to_all(self.temperature_handle.set_temp_broadcast_timer(int(arguments[0])))
            elif func == "ADDRT":
                # TODO.md unterschied ADDRT und TBUS
                self.tcpserver.send_line_to_all(self.temperature_handle.set_bus(int(arguments[0])))
            elif func == "TBUS":
                self.tcpserver.send_line_to_all(self.temperature_handle.set_bus(int(arguments[0])))
            elif func == "TEMP":
                self.tcpserver.send_line_to_all(self.temperature_handle.get_temp())
            # self.tcpserver.send_line_to_all(func + " " + " ".join(arguments))

    def _i_handle_oled_message(self, func, arguments: List[str], _):
        # TODO.md send respone to client
        if arguments[0].upper() == "MODE":
            if len(arguments) == 3:
                self.oled_instance.set_mode(arguments[1], arguments[2])
            else:
                self.oled_instance.set_mode(arguments[1])
        else:
            text = [j.replace("{", "").split("}")[:-1] for j in
                    [i.replace("<", "") for i in " ".join(arguments).split(">")[:-1]]]
            if len(text) == 2:
                self.oled_instance.set_text([text[0], text[1]])
            else:
                self.oled_instance.set_text(text[0])
        self.tcpserver.send_line_to_all(func + " " + " ".join(arguments))

    def _i_handle_andino_hardware_message(self, func, arguments: List[str],
                                          _):
        if func == "INFO":
            self.tcpserver.send_line_to_all(self.x1_instance.info())
            return
        elif func == "HARD":
            self.tcpserver.send_line_to_all(self.x1_instance.hardware(int(arguments[0])))
        elif func == "POLL":
            self.tcpserver.send_line_to_all(self.x1_instance.set_polling(int(arguments[0])))
        elif func == "SKIP":
            self.tcpserver.send_line_to_all(self.x1_instance.set_skip(int(arguments[0])))
        elif func == "EDGE":
            self.tcpserver.send_line_to_all(self.x1_instance.set_edge_detection(bool(int(arguments[0]))))
        elif func == "SEND":
            self.tcpserver.send_line_to_all(self.x1_instance.set_send_time(int(arguments[0])))
        elif func == "CHNG":
            self.tcpserver.send_line_to_all(self.x1_instance.set_broadcast_on_change(bool(int(arguments[0]))))
        elif func == "CHNP":
            if isinstance(self.x1_instance, andinopy.tcp.io_x1_emulator.x1_emulator):
                self.tcpserver.send_line_to_all(
                    self.x1_instance.set_change_pattern([int(i) for i in str(arguments[0])]))
        elif func == "CNTR":
            # TODO.md CNTR	Send Counter - Send counter+states(1) or only states(0)
            #  (default 1)
            self.tcpserver.send_line_to_all(self.x1_instance.get_counters(int(arguments[0])))
        elif func == "DEBO":
            self.tcpserver.send_line_to_all(self.x1_instance.set_debounce(int(arguments[0])))
        elif func == "POWR":
            self.tcpserver.send_line_to_all(self.x1_instance.set_power(int(arguments[0])))
        elif func == "REL?":
            self.tcpserver.send_line_to_all(self.x1_instance.set_send_relays_status(bool(int(arguments[0]))))
        elif func.startswith("REL"):
            i = int(func[3:])
            self.tcpserver.send_line_to_all(self.x1_instance.set_relay(i, int(arguments[0])))
        elif func.startswith("RPU"):
            i = func[3]
            self.tcpserver.send_line_to_all(self.x1_instance.pulse_relay(int(i), int(arguments[0])))

    # endregion

    # region outgoing functions
    def _o_on_rfid(self, message: str):
        self.tcpserver.send_line_to_all(
            f":{self._get_and_increase_send_ctr()}@R{{{message}}}"
        )

    def _o_on_function_button(self, message: str):
        self.tcpserver.send_line_to_all(
            f":{self._get_and_increase_send_ctr()}@F{{{message}}}"
        )

    def _o_on_number_button(self, message: str):
        self.tcpserver.send_line_to_all(
            f":{self._get_and_increase_send_ctr()}@N{{{message}}}"
        )

    def _o_on_display_touch(self, message: bytes):
        self.tcpserver.send_line_to_all(
            f":{self._get_and_increase_send_ctr()}@D{{{message}}}"
        )

    def _o_on_display_string(self, message: str):
        self.tcpserver.send_line_to_all(
            f":{self._get_and_increase_send_ctr()}@D{{{message}}}"
        )

    def _o_broadcast(self, message: str):
        self.tcpserver.send_line_to_all(f":{self._get_and_increase_send_ctr()}{message}")

    # endregion
    def _get_and_increase_send_ctr(self):
        ctr = self._message_counter
        self._message_counter = (self._message_counter + 1) % 0xFFFF
        return f'{ctr:04x}'.upper()


if __name__ == "__main__":
    """
    hardware: "x1" or "io"
    port: The tcp Port the server will serve on
    oled: oled Display enabled
    temp: temperature measure enabled? (only on x1)
    key_rfid: keyboard and rfid controller enabled?
    display: display enabled?
    """
    server = andino_tcp(hardware="io", port=9999, oled=True, temp=False, key_rfid=False, display=False)
    try:
        print("andino server started on port 9999")
        server.start()
        input()
        input()
    finally:
        server.stop()
