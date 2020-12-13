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
    "--allow-open/--disallow-open",
    default=True,
    show_default=True,
    help="Flag to choose if open strings should be allowed, i.e., "
         "if the min-fret value "
         "should be considered fingerless (open string) or fingered.",
)
@click.option(
    "--reverse/--no-reverse", "-r",
    default=False,
    show_default=True,
    help="Flag to choose if the guitar tuning order should be used "
         "for trial-and-error by the fret finder algorithm, "
         "or if it should be reversed.",
)
@click.option(
    "--window-size", "-w",
    default=7,
    show_default=True,
    help="Size of history to be considered by the algorithm.",
)
@click.option(
    "--distinct-only/--no-distinct-removal", "-d",
    default=False,
    show_default=True,
    help="Choose if consecutive repeated fret numbers in history "
         "should be seen as just one history entry by the algorithm.",
)
@click.argument("staff", type=Staff)
def main(*, tuning, min_fret, max_fret, allow_open, reverse,
         window_size, distinct_only, staff):
    result = find_strings(
        staff=staff,
        guitar=Guitar(tuning, min_fret=min_fret, max_fret=max_fret),
        allow_open=allow_open,
        reverse=reverse,
        window_size=window_size,
        distinct_only=distinct_only,
    )
    print(result)


if __name__ == "__main__":
    main()
