import re

from audiolazy import str2midi


class Staff:
    """Model of a musical score staff.

    The input structure is a string of whitespace-separated note names
    to be interpreted as a melody, where a chord is expressed
    as notes grouped by parentheses, like
    ``"(C3 G3 E4) (D4 F4) R E4 F4 G4 (Db3 B3 F4) (C3 G3 E4)"``.
    Where the name "R" is reserved for a rest.

    The data is splitten as two lists of lists of simultaneous notes,
    one with the note name strings in the ``simnotes_names`` attribute,
    and one with the MIDI numberings in the ``simnotes`` attribute.
    """

    def __init__(self, raw_str):
        self.raw_str = raw_str
        matches = re.finditer(r"(?<=\()[^\)]+(?=\))|(?=R)|[^R ()]+", raw_str)
        self.simnotes_names = [match.group().split() for match in matches]
        self.simnotes = [[str2midi(note_name) for note_name in note_names]
                         for note_names in self.simnotes_names]
