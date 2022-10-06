from typing import Dict, Optional, Callable, Any


class State:
    def __init__(self):
        self.handlers = {}
        self.on_enter = None
        self.on_exit = None

    def add_handler(self, name : str, function: Callable[[Dict], Optional[str]]):
        self.handlers[name] = function


class FiniteStateMachine:

    def __init__(self):
        self.states: Dict[str, State] = {}
        self.global_handlers: Dict[str, Callable[[Dict], Optional[str]]]= {}
        self.start_state: Optional[str] = None
        self.running: Optional[bool] = False
        self.current_state: Optional[str] = None

    def add_state(self, state: State, name: str):
        self.states[name] = state

    def add_start_state(self, state: State, name: str):
        self.add_state(state, name)
        self.start_state = name

    def run(self):
        self.current_state = self.start_state
        self.running = True
        if self.states[self.start_state].on_enter is not None:
            self.states[self.start_state].on_enter()

    def send_event(self, event_name: str, arguments: Dict):
        if not self.running:
            raise Exception("StateMachine has not been started")

        # First check if the event is handled in the state itself
        next_state = None
        if event_name in self.states[self.current_state].handlers.keys():
            next_state = self.states[self.current_state].handlers[event_name](arguments)

        # Then check if the event is handled in the global context
        elif event_name in self.global_handlers.keys():
            next_state = self.global_handlers[event_name](arguments)

        # If a new state is returned check for its existence and then call the exit and enter functions
        if next_state is not None:
            if next_state not in self.states.keys():
                raise Exception(f"Next state returned from EventHandler of State {self.current_state} is invalid")
            if self.states[self.current_state].on_exit is not None:
                self.states[self.current_state].on_exit()
            self.current_state = next_state
            if self.states[self.current_state].on_enter is not None:
                self.states[self.current_state].on_enter()

