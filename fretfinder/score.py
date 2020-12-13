import re

from audiolazy import str2midi

from .algorithm import find_strings


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


class Tablature:

    def __init__(self, *, staff, guitar, **kwargs):
        self.staff = staff
        self.guitar = guitar
        self.strings = find_strings(staff=staff, guitar=guitar, **kwargs)

    def string_fret_pairs_lists(self):
        for strings, simnotes in zip(self.strings, self.staff.simnotes):
            yield [(string_index, midi - self.guitar.midi[string_index])
                   for string_index, midi in zip(strings, simnotes)]

    def ascii_tab(self, width=79):
        # Gets the leading columns with the tuning
        tuning_length = max(map(len, self.guitar.strings)) + 2
        tuning_column = [f"{name + '|-': >{tuning_length}}"
                         for name in self.guitar.strings]
        available_width = width - tuning_length

        # Create tablature columns (list of strings for each row)
        # and "lines" (blocks with the given width)
        tab_columns = []
        line_slices = []
        line_length = line_start = 0
        for idx, pairs in enumerate(self.string_fret_pairs_lists()):
            column = ["-"] * len(tuning_column)
            suffix = "-"
            for string_index, fret in pairs:
                if string_index < 0:
                    suffix = "?-"
                column[string_index] = str(fret)
            length = max(map(len, column)) + len(suffix)
            if line_length + length > available_width - 2:
                filler = "-" * (available_width - line_length)
                tab_columns[-1][:] = [el + filler for el in tab_columns[-1]]
                line_length = 0
                line_slices.append(slice(line_start, idx))
                line_start = idx
            line_length += length
            column[:] = [f"{el + suffix:-<{length}}" for el in column]
            tab_columns.append(column)
        tab_columns.append(["||"] * len(tuning_column))
        line_slices.append(slice(line_start, idx + 2))

        # Join the string rows into "lines" and "lines" into the output
        return "\n\n".join(
            "\n".join(
                "".join(el)
                for el in zip(*([tuning_column] + tab_columns[line_range]))
            ) for line_range in line_slices
        )
