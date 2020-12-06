from collections import namedtuple


StateHandlerResult = namedtuple(
    "StateHandlerResult",
    [
        "output",
        "adaptive_action",
        "adaptive_action_args",
        "direction",
        "next_state",
    ],
    defaults=[None, None, tuple(), None, "reject"],
)


class AdaptiveAlgorithm:
    state = "reject"

    def __init__(self, tape):
        self.tape = tape
        self.state_handlers = self.state_handlers.copy()
        self.adaptive_actions = self.adaptive_actions.copy()

    def run(self):
        while self.state not in ["accept", "reject"]:
            self.step()
        return self.state == "accept"

    def step(self):
        state_handler = self.state_handlers[self.state]
        result = state_handler(self)
        if result.output is not None:
            self.tape.current_output = result.output
        if result.adaptive_action is not None:
            adaptive_action = self.adaptive_actions[result.adaptive_action]
            adaptive_action(self, *result.adaptive_action_args)
        if result.direction is not None:
            getattr(self.tape, result.direction)()
        self.state = result.next_state


class AADecorator:
    def __init__(self, func):
        self.func = func

    def __set_name__(self, owner, name):
        if not hasattr(owner, self.storage_name):
            setattr(owner, self.storage_name, {})
        getattr(owner, self.storage_name)[name] = self.func


class AAStateHandler(AADecorator):
    storage_name = "state_handlers"


class AdaptiveAction(AADecorator):
    storage_name = "adaptive_actions"
