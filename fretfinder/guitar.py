from audiolazy import str2midi


DEFAULT_TUNINGS = {
    "Guitar6": "E5 B4 G4 D4 A3 E3",
    "Bass4": "G3 D3 A2 E2",
}


class Guitar:
    """Model for some attributes of an acoustic/electric guitar.

    Parameters
    ----------
    tuning_name : str
        A whitespace-separed note name in the American format
        for the guitar strings in the "bottom-up" order,
        or a registered tuning name in the DEFAULT_TUNINGS dictionary.
    min_fret : int
        The tune clamp (capo) number, or zero for a free string.
    max_fret : int
        The number of frets of the guitar.
    """

    def __init__(self, tuning_name, *, min_fret=0, max_fret=24):
        self.tuning_name = tuning_name
        self.tuning = DEFAULT_TUNINGS.get(tuning_name, tuning_name)
        self.strings = tuple(self.tuning.split())
        self.midi = tuple(str2midi(s) for s in self.strings)
        self.num_strings = len(self.strings)
        self.min_fret = min_fret
        self.max_fret = max_fret

    def midi2frets(self, midi):
        return [midi - ref for ref in self.midi]
