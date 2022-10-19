#       _              _ _
#      / \   _ __   __| (_)_ __   ___  _ __  _   _
#     / _ \ | '_ \ / _` | | '_ \ / _ \| '_ \| | | |
#    / ___ \| | | | (_| | | | | | (_) | |_) | |_| |
#   /_/   \_\_| |_|\__,_|_|_| |_|\___/| .__/ \__, |
#                                     |_|    |___/
# by Jakob Groß
import subprocess
from typing import List
from andinopy import base_config, save_base_config
from andinopy import andinopy_logger
from andinopy.gpio_zero_devices.gpio_relay import gpio_relay
from andinopy.gpio_zero_devices.gpio_input import gpio_input


class andinoio:
    """
        Create an andinoio instance.
        Be Sure to set custom configurations before starting
    """

    # region initialize

    def __init__(self, relays_start_config: bool = None,
                 relays_active_high=None,
                 input_pull_up: List[bool] = None,
                 inputs_polling_time: List[float] = None,
                 inputs_debounce_time: List[float] = None,
                 on_input_functions: List[callable] = None,
                 on_change_functions: List[callable] = None
                 ):
        """
        Initialize a new AndinoIo Instance
        :param relays_start_config:
        :param input_pull_up:
        :param inputs_polling_time:
        :param inputs_debounce_time:
        :param on_input_functions:
        """
        self.input_pins: List[int] = [int(i) for i in base_config["andino_io"]["input_pins"].split(",")]
        self.relay_pins: List[int] = [int(i) for i in base_config["andino_io"]["relay_pins"].split(",")]
        self.pin_power_fail: int = int(base_config["andino_io"]["pin_power_fail"])

        # Handlers
        self.outRel: List[gpio_relay] = []  # direct access to gpiozero
        self.Inputs: List[gpio_input] = []  # direct access to gpiozero
        self.power_button = None  # direct access to gpiozero

        # Custom Configuration
        self._shutdown_after_seconds = None
        self._input_pull_up = input_pull_up
        self._inputs_polling_time = inputs_polling_time
        self._inputs_debounce_time = inputs_debounce_time
        self._on_input_functions = on_input_functions
        self._on_change_functions = on_change_functions
        self._relays_start_config = relays_start_config
        self._relays_active_high = relays_active_high
        andinopy_logger.info("AndinoIo initialized")

    # endregion

    # region properties
    # region input_pull_up
    @property
    def input_pull_up(self) -> List[bool]:
        if self._input_pull_up is None:
            self._input_pull_up = [i == "True" for i in base_config["andino_io"]["input_pull_up"].split(",")]
        return self._input_pull_up

    @input_pull_up.setter
    def input_pull_up(self, values: List[bool]):
        self._input_pull_up = values
        for inp, value in zip(self.Inputs, values):
            inp.pull_up = value
        base_config["andino_io"]["input_pull_up"] = ",".join([str(i) for i in values])
        save_base_config()

    # endregion

    # region inputs_polling_time
    @property
    def inputs_polling_time(self) -> List[float]:
        if self._inputs_polling_time is None:
            self._inputs_polling_time = [float(i) for i in base_config["andino_io"]["inputs_polling_time"].split(",")]
        return self._inputs_polling_time

    @inputs_polling_time.setter
    def inputs_polling_time(self, values: List[float]):
        self._inputs_polling_time = values
        for inp, value in zip(self.Inputs, values):
            inp.hold_time = value
        base_config["andino_io"]["inputs_polling_time"] = ",".join([str(i) for i in values])
        save_base_config()

    # endregion

    # region inputs_debounce_time
    @property
    def inputs_debounce_time(self) -> List[float]:
        if self._inputs_debounce_time is None:
            self._inputs_debounce_time = [float(i) for i in base_config["andino_io"]["inputs_debounce_time"].split(",")]
        return self._inputs_debounce_time

    @inputs_debounce_time.setter
    def inputs_debounce_time(self, values: List[float]):
        self._inputs_debounce_time = values
        for inp, value in zip(self.Inputs, values):
            inp.bounce_time = value
        base_config["andino_io"]["inputs_debounce_time"] = ",".join([str(i) for i in values])
        save_base_config()

    # endregion

    # region on_input_functions
    @property
    def on_input_functions(self) -> List[callable]:
        if self._on_input_functions is None:
            self._on_input_functions = [None for _ in range(len(self.input_pins))]
        return self._on_input_functions

    @on_input_functions.setter
    def on_input_functions(self, values: List[callable]):
        self._on_input_functions = values
        for inp, value in zip(self.Inputs, values):
            inp.on_input = value

    # endregion

    # region on_change_functions
    @property
    def on_change_functions(self) -> List[callable]:
        if self._on_change_functions is None:
            self._on_change_functions = [None for _ in range(len(self.input_pins))]
        return self._on_change_functions

    @on_change_functions.setter
    def on_change_functions(self, values: List[callable]):
        self._on_change_functions = values
        for inp, value in zip(self.Inputs, values):
            inp.on_change = value

    # endregion

    # region relays_start_config
    @property
    def relays_start_config(self) -> List[bool]:
        if self._relays_start_config is None:
            self._relays_start_config = [i == "True" for i in
                                         base_config["andino_io"]["relays_start_config"].split(",")]
        return self._relays_start_config

    @relays_start_config.setter
    def relays_start_config(self, values: List[bool]):
        self._relays_start_config = values
        andinopy_logger.info("Relays start config saved for next start")
        base_config["andino_io"]["relays_start_config"] = ",".join([str(i) for i in values])
        save_base_config()

    # endregion

    # region relays_active_high
    @property
    def relays_active_high(self) -> List[bool]:
        if self._relays_active_high is None:
            self._relays_active_high = [i == "True" for i in base_config["andino_io"]["relays_active_high"].split(",")]
        return self._relays_active_high

    @relays_active_high.setter
    def relays_active_high(self, values: List[bool]):
        self._relays_active_high = values
        andinopy_logger.info("Relays active high config saved for next start")
        base_config["andino_io"]["relays_active_high"] = ",".join([str(i) for i in values])
        save_base_config()

    # endregion

    # region shutdown_after_seconds
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

    # endregion

    # endregion

    # region start_stop
    def start(self):
        """
        Be sure to assign Custom fields before calling
        :return: None
        """
        for i in range(len(self.input_pins)):
            tmp_input = gpio_input(self.input_pins[i],
                                   pull_up=self.input_pull_up[i],
                                   on_input=self.on_input_functions[i],
                                   on_change=self.on_change_functions[i],
                                   debounce=self.inputs_debounce_time[i],
                                   hold_time=self.inputs_polling_time[i])

            tmp_input.start()
            self.Inputs.append(tmp_input)
            self.reset_all_counters()

        for i in range(len(self.relay_pins)):
            self.outRel.append(gpio_relay(self.relay_pins[i],
                                          self.relays_start_config[i],
                                          self.relays_active_high[i]))

        self.power_button = gpio_input(hold_time=self.shutdown_after_seconds,
                                       pin=self.pin_power_fail,
                                       on_input=self.shutdown)
        andinopy_logger.info("AndinoIo started")

    def stop(self):
        self.power_button.stop()
        self.reset_all_counters()
        for btn in self.Inputs:
            btn.stop()
        self.Inputs = []
        for rel in self.outRel:
            rel.close()
        self.outRel = []
        andinopy_logger.info("AndinoIo stopped")

    # endregion

    # region inputs
    def reset_counter(self, input_nr: int):
        self.Inputs[input_nr].reset()

    def reset_all_counters(self):
        for i in self.Inputs:
            i.reset()
        andinopy_logger.info("AndinoIo reset all counters")

    def shutdown(self):
        andinopy_logger.info(f"Shutdown-Pin({self.pin_power_fail} held for longer than f{self.shutdown_after_seconds}")
        subprocess.run(base_config["andino_tcp"]["shutdown_script"], shell=True, check=True, text=True)

    def get_input_statuses(self):
        return [int(i.is_pressed) for i in self.Inputs]

    # endregion

    # region relays
    def set_relay(self, relays_nr: int, state: int):
        """
        :param relays_nr: goal relays
        :param state: goal state
        :return: None
        """
        andinopy_logger.debug(f"AndinoIo set relays {relays_nr}:{state}")
        if bool(state):
            self.outRel[relays_nr].on()
        else:
            self.outRel[relays_nr].off()

    def pulse_relays(self, relays_nr: int, duration: int):
        """
        opens/closes relays for duration ms
        :param relays_nr: goal relays
        :param duration: duration in ms
        :return: None
        """
        self.outRel[relays_nr].pulse(duration)
    # endregion
