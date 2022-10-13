#       _              _ _
#      / \   _ __   __| (_)_ __   ___  _ __  _   _
#     / _ \ | '_ \ / _` | | '_ \ / _ \| '_ \| | | |
#    / ___ \| | | | (_| | | | | | (_) | |_) | |_| |
#   /_/   \_\_| |_|\__,_|_|_| |_|\___/| .__/ \__, |
#                                     |_|    |___/
# by Jakob Groß
from typing import Optional

import gpiozero

import andinopy


class gpio_input:
    def __init__(self, pin: int,
                 hold_time: float = 0.01,
                 debounce: float = None,
                 on_input: callable = None,
                 on_change: callable = None,
                 pull_up: bool = False):
        self._pin: int = pin
        self._pull_up: bool = pull_up
        self._hold_time: float = hold_time
        self._bounce_time: float = debounce
        self._on_input: callable = on_input
        self._on_change: callable = on_change
        self._button: Optional[gpiozero.Button] = None
        self._counter: int = 0
        self._running: bool = False
        andinopy.andinopy_logger.debug(f"gpio_input created on pin {self.pin}")

    # region start_stop
    def start(self):
        self._rebuild_button()
        self._running = True
        andinopy.andinopy_logger.debug(f"gpio_input started on pin {self.pin}")

    def stop(self):
        self._running = False
        if self._button:
            self._button.close()
            self._button = None

    # endregion

    # region properties
    # region pin
    @property
    def pin(self) -> int:
        return self._pin

    @pin.setter
    def pin(self, value: int):
        rebuild = self._pin != value
        self._pin = value
        if self._running and rebuild:
            self._rebuild_button()

    # endregion

    # region on_input
    @property
    def on_input(self) -> callable:
        return self._on_input

    @on_input.setter
    def on_input(self, value: callable):
        self._on_input = value
        andinopy.andinopy_logger.debug(f"pin{self.pin} on-input changed {self._on_input}")
    #endregion

    #region on_change
    @property
    def on_change(self):
        return self._on_change
    @on_change.setter
    def on_change(self,value: callable):
        self._on_change = value
        andinopy.andinopy_logger.debug(f"pin{self.pin} on-change changed {self._on_change}")
    #endregion

    # region pull_up
    @property
    def pull_up(self) -> bool:
        return self._pull_up

    @pull_up.setter
    def pull_up(self, value: bool):
        self._pull_up = value
        if self._running:
            self._rebuild_button()

    # endregion

    # region hold_time
    @property
    def hold_time(self) -> float:
        return self._hold_time

    @hold_time.setter
    def hold_time(self, value: float):
        self._hold_time = value
        if self._running:
            self._button.hold_time = value

    # endregion

    # region bounce_time
    @property
    def bounce_time(self) -> float:
        return self._hold_time

    @bounce_time.setter
    def bounce_time(self, value: float):
        self._bounce_time = value
        if self._running:
            self._rebuild_button()

    # endregion

    # region counter
    @property
    def counter(self):
        return self._counter
    # endregion

    # region is_pressed
    @property
    def is_pressed(self):
        if self._running:
            return self._button.is_active
        return False

    # endregion
    # endregion

    #region events
    def _input(self):
        self._counter += 1
        andinopy.andinopy_logger.info(f"input: {self.pin} input")
        if self._on_input is not None:
            self._on_input()

    def _change(self):
        andinopy.andinopy_logger.info(f"input: {self.pin} changed")
        if self._on_change is not None:
            self._on_change()
    #endregion

    def reset(self):
        self._counter = 0

    def flank(self, change):
        print(f"pin {self.pin} changed to {change}")

    def _rebuild_button(self):
        if self._button is not None:
            self._button.close()
        self._button = gpiozero.Button(pin=self._pin, hold_time=self._hold_time)
        self._button.when_held = self._input
        self._button.when_activated = self._change
        self._button.when_deactivated = self._change
        self._button.hold_repeat = False
        andinopy.andinopy_logger.debug(f"Pin {self.pin} rebuilt")
