from collections import namedtuple
import json
import logging


logger = logging.getLogger("adaptive")

StateHandlerResult = namedtuple(
    "StateHandlerResult",
    [
        "output",
        "adaptive_action",
        "adaptive_action_args",
        "direction",
        "next_state",
        "next_state_args",
    ],
    defaults=[None, None, tuple(), None, "reject", tuple()],
)
StateHandlerResult.to_json = lambda self, **kwargs: json.dumps({
    k: v
    for k, v in {
        **kwargs,
        "out": None if self.output is None else self.output,
        "adap":
            None if self.adaptive_action is None else
            f"{self.adaptive_action}" +
            (str(list(self.adaptive_action_args))
             if self.adaptive_action_args else ""),
        "move":
            None if self.direction is None else self.direction[3].upper(),
        "next":
            f"{self.next_state}" +
            (str(list(self.next_state_args)) if self.next_state_args else ""),
    }.items()
    if v is not None
})


class AdaptiveAlgorithm:
    """Abstract adaptive algorithm implementation.

    The initial state should be a string in the "state" attribute
    of either the concrete class or the automaton/algorithm instance.
    States are "parametrized" in order to allow a family of states
    to be grouped together in a more compact way,
    the state parameters, if any,
    should be in the ``states_args`` attribute.

    The "accept" and "reject" states are implicitly implemented,
    the other valid initial states must be implemented
    in the concrete class or in an instance.
    State handlers should be pure functions (methods)
    receiving ``self`` and the ``states_arg`` as positional parameters.
    All handlers must always return a ``StateHandlerResult`` instance.
    The initial state handlers of every instance
    should be defined in the concrete class
    as a method with a ``@AAStateHandler`` decorator.

    Any changes to the "automaton" (any storage attribute in ``self``)
    should be performed only by some adaptive action.
    One can register/remove/include/modify state handlers
    while an instance is running
    by changing the concrete class' ``state_handlers`` dictionary.
    Likewise, adaptive actions are functions (methods)
    registered in the ``adaptive_actions`` dictionary,
    which can also be changed,
    and the initial ones should be implemented in the concrete class
    by using the ``@AdaptiveAction`` decorator.
    """
    state = "reject"
    state_args = tuple()

    def __init__(self, cursor):
        self.cursor = cursor
        self.state_handlers = self.state_handlers.copy()
        self.adaptive_actions = self.adaptive_actions.copy()
        logger.info(StateHandlerResult(
            next_state=self.state,
            next_state_args=self.state_args,
        ).to_json(initial=True))

    def run(self):
        while self.state not in ["accept", "reject"]:
            self.step()
        return self.state == "accept"

    def step(self):
        state_handler = self.state_handlers[self.state]
        result = state_handler(self, *self.state_args)
        logger.info(result.to_json())
        if result.output is not None:
            self.cursor.current_output = result.output
        if result.adaptive_action is not None:
            adaptive_action = self.adaptive_actions[result.adaptive_action]
            adaptive_action(self, *result.adaptive_action_args)
        if result.direction is not None:
            getattr(self.cursor, result.direction)()
        self.state = result.next_state
        self.state_args = result.next_state_args


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
