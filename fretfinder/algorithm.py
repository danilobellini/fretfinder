from itertools import count
import json
import logging

from .adaptive import (AAStateHandler, AdaptiveAction, AdaptiveAlgorithm,
                       StateHandlerResult)
from .cursors import IOCursor


logger = logging.getLogger("algorithm")


def find_strings(staff, guitar, *, allow_open=True, reverse=False,
                 window_size=7, distinct_only=False):
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
    reverse : bool
        Choose if it should try to fit the notes in frets
        first on the leading guitar strings of the tuning (bottom-up),
        or on the trailing guitar strings (top-down, or reversed).
        The guitar tuning is usually described
        from its highest pitched note (also called the "first string")
        to its lowest pitched note.
    window_size : int
        Number of notes of history (previous notes output)
        to define the valid fret range for selecting the string/fret
        of the following note.
    distinct_only : bool
        Switch to enable/disable a filter
        to remove consecutive repeated fret numbers
        from the window history.

    Returns
    -------
    A list of lists with the number of the strings for each input note.

    See Also
    --------
    fretfinder.score.Tablature :
        An alternative way to call this algorithm.
    """
    cursor = IOCursor(staff=staff, guitar=guitar)
    while not cursor.after_end():
        if cursor.at_chord():
            cursor.current_output = find_multi_fingering(
                frets_matrix=cursor.get_all_frets(),
                guitar=guitar,
            )
            logger.info(json.dumps({
                "found": "chord",
                "out": cursor.current_output,
                "move": "R",
            }))
            cursor.to_right()
        elif cursor.at_possible_note():
            logger.info(json.dumps({"found": "melody"}))
            for dist_range in count(3):
                logger.info(json.dumps({
                    "processing": "melody",
                    "dist_range": dist_range,
                }))
                if AdaptiveFretFinderMelody(
                    cursor=cursor,
                    guitar=guitar,
                    dist_range=dist_range,
                    allow_open=allow_open,
                    reverse=reverse,
                    window_size=window_size,
                    distinct_only=distinct_only,
                ).run():
                    logger.info(json.dumps({
                        "processed": "melody",
                        "dist_range": dist_range,
                    }))
                    break  # Finished in an "accept" state
        else:  # A rest or an impossible note
            logger.info(json.dumps({
                "found": "rest" if cursor.at_rest() else "unknown",
                "move": "R",
            }))
            cursor.to_right()
        cursor.freeze_left()  # "Store" the new result
    return cursor.output_tape


class AdaptiveFretFinderMelody(AdaptiveAlgorithm):
    state = "transition"  # Initial state

    def __init__(self, cursor, *, guitar, dist_range,
                 allow_open=True, reverse=False,
                 window_size=7, distinct_only=False):
        super().__init__(cursor)
        self.guitar = guitar
        self.dist_range = dist_range
        self.allow_open = allow_open
        self.reverse = reverse
        self.window_size = window_size
        self.distinct_only = distinct_only
        self.fret_history = []
        self.min_x, self.max_x = self.get_valid_range()

    def get_transition_string_range(self):
        last_string = self.cursor.current_output[0]
        num_strings = self.guitar.num_strings
        if not self.reverse:
            return range(last_string + 1, num_strings)
        if last_string == -1:
            return range(num_strings - 1, -1, -1)
        return range(last_string - 1, -1, -1)

    @AAStateHandler
    def transition(self):
        for string_index in self.get_transition_string_range():
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
        if not self.cursor.at_possible_note():
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
        fret_number = self.cursor.get_frets()[string]
        return (
            (self.min_x <= fret_number <= self.max_x) or
            (self.allow_open and fret_number == self.guitar.min_fret)
        )

    @AdaptiveAction
    def update_x(self, string):
        """This is the "Ux" adaptive action from the paper."""
        fret_number = self.cursor.get_frets()[string]
        self.fret_history.append(fret_number)
        self.min_x, self.max_x = self.get_valid_range()
        logger.debug(json.dumps({
            "min_x": self.min_x,
            "max_x": self.max_x,
            "fret_number": fret_number,
        }))

    @AdaptiveAction
    def backup_x(self):
        """This is the "Bx" adaptive action from the paper."""
        self.fret_history.pop()
        self.min_x, self.max_x = self.get_valid_range()
        logger.debug(json.dumps({
            "min_x": self.min_x,
            "max_x": self.max_x,
        }))

    def get_valid_range(self):
        return get_valid_fret_range(
            history=get_clean_history(
                frets=self.fret_history,
                window_size=self.window_size,
                guitar=self.guitar,
                allow_open=self.allow_open,
                distinct_only=self.distinct_only,
            ),
            dist_range=self.dist_range,
            guitar=self.guitar,
        )


def get_clean_history(frets, *, window_size, guitar,
                      allow_open=True, distinct_only=False):
    """Create a list with the last ``window_size`` frets
    that match the given constraints.
    The ``frets`` should have the unfiltered history of output frets.
    See the ``find_strings`` documentation
    for more information about the remaining parameters.
    """
    previous = None
    result = []
    for fret in reversed(frets):
        if distinct_only and fret == previous:
            continue
        if allow_open and fret == guitar.min_fret:
            window_size -= 1
        else:
            previous = fret
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
