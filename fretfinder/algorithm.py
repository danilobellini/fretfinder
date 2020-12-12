from itertools import count

from .adaptive import (AAStateHandler, AdaptiveAction, AdaptiveAlgorithm,
                       StateHandlerResult)
from .cursors import IOCursor


def find_frets(staff, guitar, *, allow_open=True, window_size=7):
    """Automated guitar fingerings "fret finder"
    based on an adaptive algorithm.

    Parameters
    ----------
    guitar : fretfinder.guitar.Guitar
        The guitar model to be used.
    staff : fretfinder.score.Staff
        The musical staff in which the algorithm should be applied.
    allow_open : bool
        Flag to choose if the open string (clamped by a capo or not)
        should be considered a fingerless note by the algorithm,
        hence it won't need to be part of the window range.
    window_size : int
        Number of notes of history (previous notes output)
        to define the valid fret range for selecting the string/fret
        of the following note.
    """
    tape = IOCursor(staff=staff, guitar=guitar)
    while not tape.after_end():
        if tape.at_chord():
            tape.current_output = find_multi_fingering(
                frets_matrix=tape.get_all_frets(),
                guitar=guitar,
            )
            tape.to_right()
        elif tape.at_possible_note():
            for dist_range in count(3):
                if AdaptiveFretFinderMelody(
                    tape=tape,
                    guitar=guitar,
                    dist_range=dist_range,
                    allow_open=allow_open,
                    window_size=window_size,
                ).run():
                    break  # Finished in an "accept" state
        else:  # A rest or an impossible note
            tape.to_right()
        tape.freeze_left()  # "Store" the new result
    return tape.output_tape


class AdaptiveFretFinderMelody(AdaptiveAlgorithm):
    state = "transition"  # Initial state

    def __init__(self, tape, *, guitar, dist_range,
                 allow_open=True, window_size=7):
        super().__init__(tape)
        self.guitar = guitar
        self.dist_range = dist_range
        self.allow_open = allow_open
        self.window_size = window_size
        self.fret_history = []
        self.min_x, self.max_x = self.get_valid_range()

    @AAStateHandler
    def transition(self):
        for string_index in range(self.tape.current_output[0] + 1,
                                  self.guitar.num_strings):
            if self.in_valid_range(string_index):
                return StateHandlerResult(
                    output=[string_index],
                    adaptive_action="update_x",
                    adaptive_action_args=(string_index,),
                    direction="to_right",
                    next_state="string",
                    next_state_args=(string_index,),
                )
        if self.fret_history:  # If it can go left...
            return StateHandlerResult(
                output=[-1],
                adaptive_action="backup_x",
                direction="to_left",
                next_state="transition",
            )
        return StateHandlerResult(output=[-1], next_state="reject")

    @AAStateHandler
    def string(self, current_string):
        if not self.tape.at_possible_note():
            return StateHandlerResult(next_state="accept")
        if self.in_valid_range(current_string):
            return StateHandlerResult(
                output=[current_string],
                adaptive_action="update_x",
                adaptive_action_args=(current_string,),
                direction="to_right",
                next_state="string",
                next_state_args=(current_string,),
            )
        return StateHandlerResult(next_state="transition")

    def in_valid_range(self, string):
        """This is the "X(i)" function from the paper."""
        fret_number = self.tape.get_frets()[string]
        return (
            (self.min_x <= fret_number <= self.max_x) or
            (self.allow_open and fret_number == self.guitar.min_fret)
        )

    @AdaptiveAction
    def update_x(self, string):
        """This is the "Ux" adaptive action from the paper."""
        fret_number = self.tape.get_frets()[string]
        self.fret_history.append(fret_number)
        self.min_x, self.max_x = self.get_valid_range()

    @AdaptiveAction
    def backup_x(self):
        """This is the "Bx" adaptive action from the paper."""
        self.fret_history.pop()
        self.min_x, self.max_x = self.get_valid_range()

    def get_valid_range(self):
        return get_valid_fret_range(
            history=get_clean_history(
                frets=self.fret_history,
                window_size=self.window_size,
                guitar=self.guitar,
                allow_open=self.allow_open,
            ),
            dist_range=self.dist_range,
            guitar=self.guitar,
        )


def get_clean_history(frets, *, window_size, guitar, allow_open=True):
    """Create a list with the last ``window_size`` frets
    that match the given constraints.
    The ``frets`` should have the unfiltered history of output frets.
    See the ``find_frets`` documentation
    for more information about the remaining parameters.
    """
    result = []
    for fret in reversed(frets):
        if allow_open and fret == guitar.min_fret:
            window_size -= 1
        else:
            result.append(fret)
        if len(result) == window_size:
            break
    return result


def get_valid_fret_range(history, *, dist_range, guitar):
    """Find the ``(min_x, max_x)`` fret range for allowed fingerings
    from a given history (i.e., list) of fret numbers.
    """
    min_w = guitar.max_fret
    max_w = guitar.min_fret
    for fret in history:
        min_w = min(min_w, fret)
        max_w = max(max_w, fret)
    min_x = max(max_w - dist_range, guitar.min_fret)
    max_x = min(min_w + dist_range, guitar.max_fret)
    return min_x, max_x


def find_multi_fingering(frets_matrix, *, guitar):
    """Get the fingering of a single isolated chord.

    That's not a good way of finding the fingering of a chord,
    it was written to fill a gap in the original algorithm,
    which was intended to be used only on melodies.
    The original algorithm was implemented as a part of a score editor,
    so it was required to somehow handle cases like this,
    although it wasn't the purpose of the algorithm.
    """
    midi_tuning = guitar.midi
    tuning_order = sorted(range(len(midi_tuning)), reverse=True,
                          key=lambda idx: midi_tuning[idx])
    notes_order = sorted(range(len(frets_matrix)), reverse=True,
                         key=lambda idx: frets_matrix[idx])
    result = [-1 for unused in notes_order]
    for nidx in notes_order:
        note_frets = frets_matrix[nidx]
        for tidx, sidx in enumerate(tuning_order):
            if tuning_order[tidx] != -1:
                fret = note_frets[sidx]
                if guitar.min_fret <= fret <= guitar.max_fret:
                    result[nidx] = tuning_order[tidx]
                    tuning_order[tidx] = -1
                    break
    return result
