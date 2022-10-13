import andinopy

andinopy.initialize_cfg("../../andinopy/default.cfg")

import andinopy.base_devices.andinoio as andinoio

import andinopy.finite_state_machine.FSM as fsm

from threading import Timer

FSM = fsm.FiniteStateMachine()
IO = andinoio.andinoio()

input_1 = 0  # Input for IO items
input_2 = 0  # Input for non-IO items
t = None


def newTimer():
    global t
    t = Timer(10.0, FSM.send_event("downtime", {}))


# IO will send Input Changes to FSM
def send_on_change(input_nr):
    FSM.send_event("andinoio pin change", {input_nr: IO.get_input_statuses()[input_nr]})


def input_event_handler_active(arguments):
    if arguments.keys()[0] == 0:
        if arguments[0] == 1:
            global input_1
            input_1 += 1
            global t
            if isinstance(t, Timer):
                t.cancel()
                newTimer()
                t.start()
    if arguments.keys()[0] == 1:
        if arguments[1] == 1:
            global input_2
            input_2 += 1


def input_event_handler_down(arguments):
    if arguments.keys()[0] == 0:
        if arguments[0] == 1:
            global input_1
            input_1 += 1
            if isinstance(t, Timer):
                t.cancel()
                newTimer()
                t.start()
                return "active"
    if arguments.keys()[0] == 1:
        if arguments[1] == 1:
            global input_2
            input_2 += 1


def down_event_handler(_):
    return "down"


def turn_on_green_lamp():
    print("Green Lamp On")
    IO.set_relay(1, 1)
    IO.set_relay(2, 0)
    IO.set_relay(3, 0)


def turn_on_red_lamp():
    print("Red Lamp On")
    IO.set_relay(1, 0)
    IO.set_relay(2, 0)
    IO.set_relay(3, 1)


IO.on_change_functions = [lambda x=i: send_on_change(x) for i in range(len(IO.input_pins))]

running_state = fsm.State()
running_state.add_handler("andinoio pin change", input_event_handler_active)
running_state.add_handler("downtime", down_event_handler)
running_state.on_enter = turn_on_green_lamp

downtime_state = fsm.State()
downtime_state.add_handler("andinoio pin change", input_event_handler_down)
downtime_state.on_enter = turn_on_red_lamp

FSM.add_state(running_state, "active")
FSM.add_start_state(downtime_state, "down")

IO.start()
FSM.run()

print("FSM and IO running, press Enter to quit")
input()
input()

