import FSM


def react_to_input_start(arguments):
    print(f"input: {arguments['input']}")
    if arguments["input"] == "a":
        return "state2"
    if arguments["input"] == "b":
        return "state3"
    return "failed"


def react_to_input_state2(arguments):
    print(f"input: {arguments['input']}")
    if arguments["input"] == "x":
        return "start"
    if arguments["input"] == "b":
        return "state3"
    return "failed"


def react_to_input_state3(arguments):
    print(f"input: {arguments['input']}")
    if arguments["input"] == "x":
        return "start"
    if arguments["input"] == "a":
        return "state2"
    return "failed"


fsm = FSM.FiniteStateMachine()

start_state = FSM.State()
start_state.on_enter = lambda: print("Entered start state")
start_state.on_exit = lambda: print("Exited start state")
start_state.add_handler("input", react_to_input_start)
fsm.add_start_state(start_state, "start")

state2 = FSM.State()
state2.on_enter = lambda: print("Entered state2 state")
state2.on_exit = lambda: print("Exited state2 state")
state2.add_handler("input", react_to_input_state2)
fsm.add_state(state2, "state2")

state3 = FSM.State()
state3.on_enter = lambda: print("Entered state3 state")
state3.on_exit = lambda: print("Exited state3 state")
state3.add_handler("input", react_to_input_state3)
fsm.add_state(state3, "state3")

failed_state = FSM.State()
failed_state.on_enter = lambda: print("Entered failed state")
fsm.add_state(failed_state, "failed")


def run_fsm_with_string(state_machine, input_str: str):
    # restart fsm
    state_machine.run()
    print("Starting FSM")
    for i in input_str:
        fsm.send_event("input", {"input": i})
    print("Run complete")
    return fsm.current_state != "failed"


accepted_string = "abaxaxax"
print(f"run with string {accepted_string} : {run_fsm_with_string(fsm, accepted_string)}")

failed_string = "axaxaaaaaa"
print(f"run with string {failed_string} : {run_fsm_with_string(fsm, failed_string)}")
