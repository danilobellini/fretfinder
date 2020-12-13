import pytest

from fretfinder.adaptive import (AAStateHandler, AdaptiveAction,
                                 AdaptiveAlgorithm, StateHandlerResult)
from fretfinder.cursors import IOCursor


class ParenthesesMatcher(AdaptiveAlgorithm):
    state = "start"  # Initial state

    @AAStateHandler
    def start(self):
        if self.cursor.after_end():
            return StateHandlerResult(next_state="accept")
        char = self.cursor.get_simnotes()
        if char == "(":
            new_state_name = object()
            return StateHandlerResult(
                output=1,
                adaptive_action="add_state",
                adaptive_action_args=("start", new_state_name,),
                direction="to_right",
                next_state=new_state_name,
            )
        if char == ")":
            return StateHandlerResult(next_state="reject")
        return StateHandlerResult(
            output=0,
            direction="to_right",
            next_state="start",
        )

    @AdaptiveAction
    def add_state(self, origin_state, new_state_name):
        def new_handler(this):
            if self.cursor.after_end():
                return StateHandlerResult(next_state="reject")
            char = self.cursor.get_simnotes()
            if char == "(":
                another_state_name = object()
                return StateHandlerResult(
                    output=1,
                    adaptive_action="add_state",
                    adaptive_action_args=(new_state_name, another_state_name,),
                    direction="to_right",
                    next_state=another_state_name,
                )
            if char == ")":
                return StateHandlerResult(
                    output=2,
                    adaptive_action="remove_state",
                    adaptive_action_args=(new_state_name,),
                    direction="to_right",
                    next_state=origin_state,
                )
            return StateHandlerResult(
                output=0,
                direction="to_right",
                next_state=new_state_name,
            )
        self.state_handlers[new_state_name] = new_handler

    @AdaptiveAction
    def remove_state(self, origin_state):
        del self.state_handlers[origin_state]


class StringPseudoStaff:
    """Mocked Staff to use IOCursor on a string."""

    def __init__(self, raw_str):
        self.simnotes = raw_str


@pytest.mark.parametrize("input_string, expected_result, expected_output", [
    ("((aa))", True, [1, 1, 0, 0, 2, 2]),
    ("a((aa)b(cc))()", True, [0, 1, 1, 0, 0, 2, 0, 1, 0, 0, 2, 2, 1, 2]),
    ("((())))", False, [1, 1, 1, 2, 2, 2, [-1]]),
])
def test_parentheses_match(input_string, expected_result, expected_output):
    staff = StringPseudoStaff(input_string)
    cursor = IOCursor(staff=staff, guitar=None)
    result = ParenthesesMatcher(cursor).run()
    assert result is expected_result
    assert cursor.output_tape == expected_output
