from .cursors import IOCursor


def find_frets(staff, guitar):
    tape = IOCursor(staff=staff, guitar=guitar)
    while not tape.after_end():
        tape.current_output = find_multi_fingering(
            frets_matrix=tape.get_all_frets(),
            guitar=guitar,
        )
        tape.to_right()
    return tape.output_tape


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
