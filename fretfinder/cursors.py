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
