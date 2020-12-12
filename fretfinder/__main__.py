from .algorithm import find_frets
from .guitar import Guitar, DEFAULT_TUNINGS
from .score import Staff

import click


@click.command()
@click.option(
    "--tuning", "-t",
    default="Guitar6",
    show_default=True,
    help="Guitar tuning name or whitespace-separated note names. "
         "Possible tuning names: " +
         ", ".join(f"{k} ({v})" for k, v in DEFAULT_TUNINGS.items()) +
         ".",
)
@click.option(
    "--min-fret", "-m",
    default=0,
    show_default=True,
    help="Smallest fret number for the output, "
         "it's tipically zero for free strings, "
         "or the fret number of the tune clamp (capo) position.",
)
@click.option(
    "--max-fret", "-M",
    default=24,
    show_default=True,
    help="Biggest fret number available for the guitar.",
)
@click.option(
    "--window-size", "-w",
    default=7,
    show_default=True,
    help="Size of history to be considered by the algorithm.",
)
@click.argument("staff", type=Staff)
def main(*, tuning, min_fret, max_fret, window_size, staff):
    result = find_frets(
        staff=staff,
        guitar=Guitar(tuning, min_fret=min_fret, max_fret=max_fret),
        window_size=window_size,
    )
    print(result)


if __name__ == "__main__":
    main()
