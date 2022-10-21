import time

import andinopy

# !!! REPLACE WITH YOUR CFG !!!
andinopy.initialize_cfg("/home/pi/andinopy/andinopy_cfg/generated.cfg")

import andinopy.base_devices.andinoio as andinoio

import andinopy.finite_state_machine.FSM as fsm

from threading import Timer, Thread


# Betriebsdatenerfassung
class BDE:
    def __init__(self):
        self.input_1 = 0
        self.input_2 = 0

        self.running = False
        self.status_thread = None

        self.timer = None

        self.IO = andinoio.andinoio()
        self.IO.on_change_functions = [lambda x=i: self.send_on_change(x) for i in range(len(self.IO.input_pins))]

        self.FSM = fsm.FiniteStateMachine()

        running_state = fsm.State()
        running_state.add_handler("andinoio pin change", self.input_handler_active)
        running_state.add_handler("downtime", self.down_event_handler)
        running_state.on_enter = self.turn_on_green_lamp

        downtime_state = fsm.State()
        downtime_state.add_handler("andinoio pin change", self.input_handler_down)
        downtime_state.on_enter = self.turn_on_red_lamp

        self.FSM.add_state(running_state, "active")
        self.FSM.add_start_state(downtime_state, "down")

    def start(self):
        self.IO.start()
        self.FSM.run()
        self.running = True

        def send_status(handle):
            while handle.running:
                print(f"Input1: {handle.input_1}, Input2: {handle.input_2}")
                time.sleep(3)

        self.status_thread = Thread(target=send_status, args=[self])
        self.status_thread.start()

    def stop(self):
        self.running = False
        self.status_thread.join()
        if isinstance(self.timer, Timer):
            self.timer.cancel()
        self.IO.stop()

    def send_on_change(self, input_nr):
        self.FSM.send_event("andinoio pin change", {"input": (input_nr, self.IO.get_input_statuses()[input_nr])})

    def input_handler_active(self, arguments):
        # print(f"input handler active: {arguments}")
        input_nr, status = arguments["input"]
        if input_nr == 0 and status == 1:
            self.input_1 += 1
            if isinstance(self.timer, Timer):
                self.timer.cancel()
            self.timer = Timer(10.0, lambda: self.FSM.send_event("downtime", {}))
            self.timer.start()
        if input_nr == 1 and status == 1:
            self.input_2 += 1

    def input_handler_down(self, arguments):
        # print(f"input handler down: {arguments}")
        input_nr, status = arguments["input"]
        if input_nr == 0 and status == 1:
            self.input_1 += 1
            if isinstance(self.timer, Timer):
                self.timer.cancel()
            self.timer = Timer(10.0, lambda: self.FSM.send_event("downtime", {}))
            self.timer.start()
            return "active"
        if input_nr == 1 and status == 1:
            self.input_2 += 1

    def down_event_handler(self, _):
        return "down"

    def turn_on_green_lamp(self):
        print("Green Lamp On")
        self.IO.set_relay(0, 1)
        self.IO.set_relay(1, 0)
        self.IO.set_relay(2, 0)

    def turn_on_red_lamp(self):
        print("Red Lamp On")
        self.IO.set_relay(0, 0)
        self.IO.set_relay(1, 0)
        self.IO.set_relay(2, 1)


if __name__ == "__main__":
    bde = BDE()
    bde.start()

    print("FSM and IO running, press Enter to quit")
    input()
    input()
