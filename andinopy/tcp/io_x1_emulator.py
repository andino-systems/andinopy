#       _              _ _
#      / \   _ __   __| (_)_ __   ___  _ __  _   _
#     / _ \ | '_ \ / _` | | '_ \ / _ \| '_ \| | | |
#    / ___ \| | | | (_| | | | | | (_) | |_) | |_| |
#   /_/   \_\_| |_|\__,_|_|_| |_|\___/| .__/ \__, |
#                                     |_|    |___/
# by Jakob Groß
import math
import threading
import time
from typing import List

import andinopy.interfaces.andino_hardware_interface
from andinopy import base_config, save_base_config
from andinopy.base_devices.andinoio import andinoio


class x1_emulator(andinopy.interfaces.andino_hardware_interface.andino_hardware_interface):

    def __init__(self, broad_cast_function: callable(str)):
        super().__init__(broad_cast_function)
        self.handle_x1_message: callable(str) = None

        # Properties
        self._send_broadcast = None
        self._send_rel = None
        self._send_on_change = None
        self._change_pattern = None
        self._polling = None
        self._debouncing = None
        self._skip = None
        self._send_interval = None
        self._send_counter = None

        # andino
        input_functions = [lambda x=i: self._on_input_hex(x) for i in range(len(andinoio.input_pins))]
        change_functions = [lambda x=i: self._on_input_change(x) for i in range(len(andinoio.input_pins))]
        self.io = andinoio(on_input_functions=input_functions,
                           on_change_functions=change_functions)

        # Reinstated on start

        self._hex_counter = [0 for _ in range(len(self.io.input_pins))]

        self._read_size = None
        self._serial_port = None
        self._receive_thread = None

        self._running = False
        self._send_thread = threading.Thread(target=self._t_status_thread_code, args=[self])

    # region start_stop

    def start(self):
        self._running = True
        self.reset()
        self.io.start()
        self._send_thread.start()

    def stop(self):
        self._running = False
        self._send_thread.join()
        self.io.stop()

    # endregion

    # region input functions
    def _on_input_hex(self, i):
        self._hex_counter[i] = (self._hex_counter[i] + 1) % 0xFFFF

    def _on_input_change(self, i):
        if self.send_on_change and self.change_pattern[i] == True:
            self.broad_cast_function(self.generate_broadcast_string())

    # endregion

    # region properties

    # region send_broadcast
    @property
    def send_broadcast(self) -> bool:
        if self._send_broadcast is None:
            self._send_broadcast = base_config["io_x1_emulator"]["send_broadcast"]
        return self._send_broadcast

    @send_broadcast.setter
    def send_broadcast(self, value: bool):
        self._send_broadcast = value
        base_config["io_x1_emulator"]["send_broadcast"] = str(value)
        save_base_config()

    # endregion

    #region send_counter
    @property
    def send_counter(self) -> bool:
        if self._send_counter is None:
            self._send_counter = base_config["io_x1_emulator"]["send_counter"]=="True"
        return self._send_counter

    @send_counter.setter
    def send_counter(self,value:bool):
        self._send_counter = value
        base_config["io_x1_emulator"]["send_counter"] = str(value)
        save_base_config()
    #endregion

    # region send_rel
    @property
    def send_rel(self) -> bool:
        if self._send_rel is None:
            self._send_rel = base_config["io_x1_emulator"]["send_rel"]
        return self._send_rel

    @send_rel.setter
    def send_rel(self, value: bool):
        self._send_rel = value
        base_config["io_x1_emulator"]["send_rel"] = str(value)
        save_base_config()

    # endregion

    # region send_on_change
    @property
    def send_on_change(self) -> bool:
        if self._send_on_change is None:
            self._send_on_change = base_config["io_x1_emulator"]["send_on_change"] == True
        return self._send_on_change

    @send_on_change.setter
    def send_on_change(self, value: bool):
        self._send_on_change = value
        base_config["io_x1_emulator"]["send_on_change"] = str(value)
        save_base_config()

    # endregion

    # region change_pattern
    @property
    def change_pattern(self) -> List[bool]:
        if self._change_pattern is None:
            self._change_pattern = [bool(int(i)) for i in base_config["io_x1_emulator"]["change_pattern"].split(",")]
        return self._change_pattern

    @change_pattern.setter
    def change_pattern(self, values: List[bool]):
        self._change_pattern = values
        base_config["io_x1_emulator"]["change_pattern"] = ",".join([str(int(i)) for i in values])
        save_base_config()

    # endregion

    # region polling
    @property
    def polling(self) -> float:
        if self._polling is None:
            self._polling = float(base_config["io_x1_emulator"]["polling"])
        return self._polling

    @polling.setter
    def polling(self, value: float):
        self._polling = value
        base_config["io_x1_emulator"]["polling"] = str(value)
        self.io.polling = [self._polling for _ in range(len(self.io.Inputs))]
        save_base_config()

    # endregion

    # region debouncing
    @property
    def debouncing(self) -> float:
        if self._debouncing is None:
            self._debouncing = float(base_config["io_x1_emulator"]["debounce"])
        return self._debouncing

    @debouncing.setter
    def debouncing(self, value: float):
        self._debouncing = value
        base_config["io_x1_emulator"]["debounce"] = str(value)
        print(base_config["io_x1_emulator"]["debounce"])
        self.io.inputs_debounce_time = [self._debouncing for _ in range(len(self.io.Inputs))]
        save_base_config()

    # endregion

    # region skip
    @property
    def skip(self) -> int:
        if self._skip is None:
            self._skip = int(base_config["io_x1_emulator"]["skip"])
        return self._skip

    @skip.setter
    def skip(self, value: int):
        self._skip = value
        base_config["io_x1_emulator"]["skip"] = str(value)
        self.io.skip = [self._skip for _ in range(len(self.io.skip))]
        save_base_config()

    # endregion

    # region send_interval
    @property
    def send_interval(self) -> int:
        if self._send_interval is None:
            self._send_interval = int(base_config["io_x1_emulator"]["send_interval"])
        return self._send_interval

    @send_interval.setter
    def send_interval(self, value: int):
        self._send_interval = value
        base_config["io_x1_emulator"]["send_interval"] = str(value)
        save_base_config()

    # endregion

    # endregion

    @staticmethod
    def _t_status_thread_code(parent_object: 'x1_emulator'):

        while parent_object._running:
            time.sleep(parent_object.send_interval / 1000)

            if parent_object.send_broadcast and parent_object._running:
                parent_object.broad_cast_function(parent_object.generate_broadcast_string())

    def generate_broadcast_string(self) -> str:
        status = ""
        try:
            if self.send_counter:
                status += f"{{{','.join([format(i, 'x') for i in self._hex_counter])}}}"
            status += f"{{{','.join([str(int(i)) for i in self.io.get_input_statuses()])}}}"
            if self.send_rel:
                status += f"{{{','.join([str(i.value) for i in self.io.outRel])}}}"
        except Exception:
            return "ERROR GENERATING BROADCAST"
        return status

    def reset(self) -> str:
        self._hex_counter = [0 for _ in range(len(self.io.input_pins))]
        return "RESET"

    def info(self) -> str:
        return "ANDINO IO"

    def hardware(self, mode: int) -> str:
        if mode == 1:
            return "HARD 1"
        return "ERROR"

    def set_polling(self, polling_time: int) -> str:
        self.polling = polling_time
        return f"POLL {polling_time}"

    def set_skip(self, skip_count: int) -> str:
        self.skip = skip_count
        return f"SKIP{skip_count}"

    def set_edge_detection(self, value: bool) -> str:
        self.io.input_pull_up = [value for _ in range(len(self.io.Inputs))]
        return f"EDGE {int(value)}"

    def set_send_time(self, send_time: int) -> str:
        if send_time == 0:
            self.set_send_broadcast_timer(False)
        else:
            self.set_send_broadcast_timer(True)
            self.send_interval = send_time
        return f"SEND {send_time}"

    def set_debounce(self, debouncing: int) -> str:
        self.debouncing = debouncing
        return f"DEBO {int(debouncing)}"

    def set_power(self, value: int) -> str:
        return "ERROR"

    def set_send_relays_status(self, value: bool) -> str:
        self.send_rel = value
        return f"REL? {int(value)}"

    def set_relay(self, relay_num: int, value: int) -> str:
        self.io.set_relay(relay_num - 1, value)
        return f"REL{relay_num} {value}"

    def pulse_relay(self, relay_num: int, value: int) -> str:
        self.io.pulse_relays(relay_num - 1, value)
        return f"RPU{relay_num} {value}"

    def set_broadcast_on_change(self, value: bool) -> str:
        self.send_on_change = value
        return f"CHNG {int(value)}"

    def set_change_pattern(self, values: List[int]) -> str:
        if len(values) != len(self.io.Inputs):
            return "ERROR"
        for i in values:
            if not (i == 0 or i == 1):
                return "ERROR"
        self.change_pattern = [bool(i) for i in values]
        return f"CHNP {''.join([str(i) for i in values])}"

    def set_send_broadcast_timer(self, value: bool) -> str:
        self.send_broadcast = value
        return f"CNTR {int(value)}"

    def get_counters(self, mode: int) -> str:
        value = f"{{{','.join([format(i, 'x') for i in self._hex_counter])}}}"
        if mode > 0:
            value += f"{{{','.join([str(int(i)) for i in self.io.get_input_statuses()])}}}"
        if mode > 1:
            value += f"{{{','.join([str(i.value) for i in self.io.outRel])}}}"
        return value
