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

    def __getitem__(self, index):
        return self.get_simnotes()[index]

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
        return self.guitar.midi2frets(self[index])

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
