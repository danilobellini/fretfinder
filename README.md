# Guitar fret finder implementation in Python

This repository has a re-implementation of the algorithm proposed in
the following research article (written in Brazilian Portuguese),
available at <http://www.lta.poli.usp.br/lta/publicacoes/artigos/2008>:

> Bellini, D.J.S.; Tavella, A.C.B.;
> *Conversão de partituras para tablaturas*
> *usando algoritmo baseado em autômato adaptativo*.
> In: Segundo Workshop de Tecnologia Adaptativa - WTA 2008.
> EPUSP, pages 39-42, 2008.

The algorithm can be regarded as a depth-first search
implemented through an "adaptive Turing Machine" model
(a custom alternative to the adaptive automatons
proposed by João José Neto)
with synchronized input/output "tapes" that can go back and forth.
One of the tapes has the data input
(musical score/staff as a list of fret numbers for each string,
one list for each note)
while the other has the output
(the string index where one should play the notes from the input).


## Example

It's possible to run the Greensleaves excerpt example from the paper
with the following terminal command:

```bash
python -m fretfinder -rt Bass4 -M14 'A3 C4 D4 E4 F4 E4 D4'
```

Or, from Python:

```python
>>> from fretfinder import Tablature, Guitar, Staff
>>> tab = Tablature(
...     staff=Staff("A3 C4 D4 E4 F4 E4 D4"),
...     guitar=Guitar("Bass4", max_fret=14),
...     reverse=True,
... )
>>> tab.strings  # Result of fretfinder.find_strings(...)
[[2], [1], [1], [0], [0], [0], [1]]
>>> print(tab.ascii_tab())
G3|----------9-10-9----||
D3|----10-12--------12-||
A2|-12-----------------||
E2|--------------------||

```

The guitar tuning is configured using the same syntax of a melody.
For more complex staves, use "`R`" for rests
and parentheses to group simultaneous notes.
For more details, use:

```bash
python -m fretfinder --help
```


## Differences between the paper and this implementation

Most of the content in this repository
tried to emphasize the way the algorithm was proposed
in the cited research article,
but there are a few differences between this implementation
and the original specification, as follows:

1. Most configuration defaults are the same of the paper, but one:
   use `--disallow-open` explicitly
   to get the original algorithm behavior.

2. The following names were internally modified:

  - `MinX` and `MaxX` were renamed to `min_x` and `max_x`,
    not a big issue, that's just to follow the PEP8 convention;
  - The `X(i)` function was renamed to the `is_valid_range` method;
  - The `Ux` and `Bx` adaptive actions
    were implemented as `update_x` and `backup_x`,
    which are also their descriptive names in the paper;
  - `fretStack` was renamed to `fret_history`,
    it really behaves as a stack for most of the time,
    but the new name is more descriptive for what it really stores,
    and it's easier to access its contents
    without requiring to pop-and-push its contents back and forth
    just to update the `min_x` and `max_x`.

3. The `Ux` (`update_x`) adaptive action
   wasn't explicitly seen as a parametrized function
   in the original article, unlike the "string" states
   and the `X(i)` (`is_valid_range`) function.
   In some sense, that's not really a difference,
   but an implementation detail,
   as the behavior is the same as the one described in the article.
   That parameter is required in order to get the fret number
   regarding the next string state the "automaton" is going to be in,
   something that can be interpreted as a distinct `Ux`
   for each possible target string (a parametrized implementation),
   or a single `Ux` that "knows" the target state
   (the article description).
   One can store the fret number
   when it's required to evaluate `X(i)`,
   that's what the article assumes that had been done
   since it's an optimization
   to avoid calculating the same fret number twice.
   Here the fret number is calculated twice
   because of a strict "software engineering" constraint:
   neither the state handlers nor `X(i)`
   should have any collateral effect
   as they're neither adaptive actions nor state transitions,
   and the adaptive actions in this implementation
   doesn't "know" the next target state,
   hence `Ux` becomes a parametrized "`Ux(i)`".

4. The `--reverse` option (the `reverse` keyword argument)
   was created to let the evaluation
   begin from the last string to the first
   to solve the indeterminacy
   when more than one string state is a possible next state.
   The article proposes that the string order
   should be from the first string (the highest pitched one)
   to the last string (the lowest pitched one),
   and that's the default behavior of this implementation.
   On the other hand, the example from the article
   results from applying the algorithm in the reverse direction
   for an output whose last fret is 14
   (e.g. to play on an acoustic guitar),
   that's why this option had been included.

5. The original paper tells us that the output tape storing action
   was linked with the tape transitions to left/right.
   The same happens in this implementation,
   but the code doesn't enforce any link between the tape transition
   and the output tape storing action.

6. There's no "open string" for the algorithm proposed in the paper.
   Here it's implemented as the `--allow-open/--disallow-open` options
   (the `allow_open` keyword argument in Python),
   which makes the notes bypass the valid fret range.
   These open string notes are also filtered out
   from the fret history window,
   but they count as part of the window size.

7. The `--distinct-only` option (the `distinct_only` argument)
   has nothing to do with the paper, it's another way
   to avoid the issue regarding the tremolo picking,
   which was the reason underlying the choice
   of the default window size of 7.
