class FrozenError(Exception):
    """Attempt to store an output on a frozen cursor position."""


class StaffCursor:
    """Tape-like cursor for a fretfinder.score.Staff instance.

    The only methods that changes its internal state
    are ``to_left`` and ``to_right``.
    """

    def __init__(self, staff):
        self.staff = staff
        self._pos = 0

    def to_left(self):
        self._pos -= 1
        return self

    def to_right(self):
        self._pos += 1
        return self

    def at_start(self):
        return self._pos == 0

    def at_end(self):
        return self._pos == len(self.staff.simnotes) - 1

    def after_end(self):
        return self._pos >= len(self.staff.simnotes)

    def get_simnotes(self):
        return self.staff.simnotes[self._pos]

    def at_rest(self):
        return not self.after_end() and not self.get_simnotes()

    def at_note(self):
        return not self.after_end() and len(self.get_simnotes()) == 1

    def at_chord(self):
        return not self.after_end() and len(self.get_simnotes()) >= 2


class ReadOnlyTabCursor(StaffCursor):
    """StaffCursor that access the staff contents as guitar frets
    found from using a fretfinder.guitar.Guitar instance.
    """

    def __init__(self, staff, guitar):
        super().__init__(staff)
        self.guitar = guitar

    def get_frets(self, index=0):
        """List of fret numbers for the note in the given index."""
        return self.guitar.midi2frets(self.get_simnotes()[index])

    def get_all_frets(self):
        """List of fret numbers for all notes of the given chord."""
        return [self.guitar.midi2frets(note) for note in self.get_simnotes()]

    def has_impossible_note(self):
        """Checks if all notes of the current position
        can be played by some string (perhaps not all at once).
        """
        return not all(any(self.guitar.min_fret <= fret <= self.guitar.max_fret
                           for fret in note_frets)
                       for note_frets in self.get_all_frets())

    def at_possible_note(self):
        return self.at_note() and not self.has_impossible_note()


class IOCursor(ReadOnlyTabCursor):
    """ReadOnlyTabCursor with an extra output tape of string numbers.

    The output is a list of lists of integers
    whose shape is the same of the staff.simnotes
    (i.e., one output for each input note),
    and the default/starting value for all entries is ``-1''.
    """

    def __init__(self, staff, guitar):
        super().__init__(staff, guitar)
        self._output_tape = {}
        self._frozen_until = -1

    def freeze_left(self):
        self._frozen_until = max(self._pos - 1, self._frozen_until)

    @property
    def current_output(self):
        return self._output_tape.get(self._pos,
                                     [-1] * len(self.get_simnotes()))

    @current_output.setter
    def current_output(self, value):
        if self._pos <= self._frozen_until:
            raise FrozenError
        self._output_tape[self._pos] = value

    @property
    def output_tape(self):
        return [self._output_tape.get(idx, [-1] * len(simnotes))
                for idx, simnotes in enumerate(self.staff.simnotes)]
