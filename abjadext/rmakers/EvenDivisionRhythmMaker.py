import abjad
import math
import typing
from . import commands as _commands
from . import specifiers as _specifiers
from .RhythmMaker import RhythmMaker


class EvenDivisionRhythmMaker(RhythmMaker):
    """
    Even division rhythm-maker.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_denominator", "_denominators", "_extra_counts_per_division")

    ### INITIALIZER ###

    def __init__(
        self,
        *commands: _commands.Command,
        denominator: typing.Union[str, int] = "from_counts",
        denominators: typing.Sequence[int] = [8],
        divisions: abjad.Expression = None,
        duration_specifier: _specifiers.Duration = None,
        extra_counts_per_division: typing.Sequence[int] = None,
        tag: str = None,
    ) -> None:
        RhythmMaker.__init__(
            self,
            *commands,
            divisions=divisions,
            duration_specifier=duration_specifier,
            tag=tag,
        )
        assert abjad.mathtools.all_are_nonnegative_integer_powers_of_two(
            denominators
        ), repr(denominators)
        denominators = tuple(denominators)
        self._denominators: typing.Tuple[int, ...] = denominators
        if extra_counts_per_division is not None:
            assert abjad.mathtools.all_are_integer_equivalent(
                extra_counts_per_division
            ), repr(extra_counts_per_division)
            extra_counts_per_division = [
                int(_) for _ in extra_counts_per_division
            ]
            extra_counts_per_division = tuple(extra_counts_per_division)
        self._extra_counts_per_division = extra_counts_per_division
        extra_counts_per_division = extra_counts_per_division or (0,)
        self._denominator = denominator

    ### PRIVATE METHODS ###

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        tuplets = []
        divisions_consumed = self.previous_state.get("divisions_consumed", 0)
        divisions = [abjad.NonreducedFraction(_) for _ in divisions]
        denominators = abjad.sequence(self.denominators)
        denominators = denominators.rotate(-divisions_consumed)
        denominators = abjad.CyclicTuple(denominators)
        extra_counts_per_division_ = self.extra_counts_per_division or [0]
        extra_counts_per_division = abjad.sequence(extra_counts_per_division_)
        extra_counts_per_division = extra_counts_per_division.rotate(
            -divisions_consumed
        )
        extra_counts_per_division = abjad.CyclicTuple(
            extra_counts_per_division
        )
        for i, division in enumerate(divisions):
            if not abjad.mathtools.is_positive_integer_power_of_two(
                division.denominator
            ):
                message = "non-power-of-two divisions not implemented:"
                message += f" {division}."
                raise Exception(message)
            denominator_ = denominators[i]
            extra_count = extra_counts_per_division[i]
            basic_duration = abjad.Duration(1, denominator_)
            unprolated_note_count = None
            maker = abjad.NoteMaker(tag=self.tag)
            if division < 2 * basic_duration:
                notes = maker([0], [division])
            else:
                unprolated_note_count = division / basic_duration
                unprolated_note_count = int(unprolated_note_count)
                unprolated_note_count = unprolated_note_count or 1
                if 0 < extra_count:
                    modulus = unprolated_note_count
                    extra_count = extra_count % modulus
                elif extra_count < 0:
                    modulus = int(math.ceil(unprolated_note_count / 2.0))
                    extra_count = abs(extra_count) % modulus
                    extra_count *= -1
                note_count = unprolated_note_count + extra_count
                durations = note_count * [basic_duration]
                notes = maker([0], durations)
                assert all(
                    _.written_duration.denominator == denominator_
                    for _ in notes
                )
            tuplet_duration = abjad.Duration(division)
            tuplet = abjad.Tuplet.from_duration(
                tuplet_duration, notes, tag=self.tag
            )
            if (
                self.denominator == "from_counts"
                and unprolated_note_count is not None
            ):
                denominator = unprolated_note_count
                tuplet.denominator = denominator
            elif isinstance(self.denominator, int):
                tuplet.denominator = self.denominator
            tuplets.append(tuplet)
        assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
        return tuplets

    ### PUBLIC PROPERTIES ###

    @property
    def commands(self) -> typing.List[_commands.Command]:
        r"""
        Gets commands.

        ..  container:: example

            No rest commands:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Silences every third logical tie:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([0], 3),
            ...     ),
            ...     rmakers.beam(),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            r8
                            c'8
                            [
                            c'8
                            ]
                            r8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            ]
                            r8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            ]
                            r8
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            r8
                            c'8
                        }
                    }
                >>

        ..  container:: example

            Silences every logical tie except the first two and last two:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.force_rest(abjad.select().logical_ties()[2:-2]),
            ...     rmakers.beam(),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            ]
                            r8
                            r8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            r8
                            r8
                            r8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            r8
                            r8
                            r8
                            r8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            r8
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            TIE-ACROSS-DIVISIONS RECIPE:

            >>> last_leaf = abjad.select().leaf(-1)
            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

            Silences every fourth logical tie:

            >>> last_leaf = abjad.select().leaf(-1)
            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([3], 4),
            ...     ),
            ...     rmakers.beam(),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            r8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            r8
                            c'8
                            [
                            c'8
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            ]
                            r8
                            c'8
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

            Silencing the fourth logical tie produces two rests. Silencing the
            eighth logical tie produces only one rest.

        ..  container:: example

            No tuplet specifier:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[8],
            ...     extra_counts_per_division=[0, 0, 1],
            ...     )

            >>> divisions = [(5, 16), (6, 16), (6, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/16
                        s1 * 5/16
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Extracts trivial tuplets:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     denominators=[8],
            ...     extra_counts_per_division=[0, 0, 1],
            ...     )

            >>> divisions = [(5, 16), (6, 16), (6, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/16
                        s1 * 5/16
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'8
                            [
                            c'8
                            ]
                        }
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Extracts trivial tuplets and spells tuplets as diminutions:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.force_diminution(),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     denominators=[8],
            ...     extra_counts_per_division=[0, 0, 1],
            ...     )

            >>> divisions = [(5, 16), (6, 16), (6, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/16
                        s1 * 5/16
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/8 {
                            c'4
                            c'4
                        }
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

            Extracts trivial tuplets and spells tuplets as augmentations:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.force_augmentation(),
            ...     rmakers.extract_trivial(),
            ...     denominators=[8],
            ...     extra_counts_per_division=[0, 0, 1],
            ...     )

            >>> divisions = [(5, 16), (6, 16), (6, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/16
                        s1 * 5/16
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'8
                            [
                            c'8
                            ]
                        }
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            No rest commands:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...  )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Silences every other tuplet:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.force_rest(
            ...         abjad.select().tuplets().get([0], 2),
            ...     ),
            ...     rmakers.rewrite_rest_filled(
            ...         abjad.select().tuplets().get([0], 2)
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(
            ...         abjad.select().tuplets().get([0], 2),
            ...     ),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        r2
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Sustains every other tuplet:

            >>> selector = abjad.select().tuplets().get([0], 2)
            >>> nonlast_notes = abjad.select().notes()[:-1]
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.tie(selector.map(nonlast_notes)),
            ...     rmakers.rewrite_sustained(selector),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(selector),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        c'2
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Silences every output tuplet:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.force_rest(abjad.select().leaves()),
            ...     rmakers.rewrite_rest_filled(),
            ...     rmakers.extract_trivial(),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r4.
                        r2
                        r4.
                    }
                >>

        ..  container:: example

            Forces the first leaf and the last two leaves to be rests:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.force_rest(abjad.select().leaf(0)),
            ...     rmakers.force_rest(abjad.select().leaves()[-2:]),
            ...     rmakers.beam(),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            r8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'8
                            [
                            c'8
                            ]
                            r8
                            r8
                        }
                    }
                >>

            Forced rests also work when given a single tuplet:

            >>> divisions = [(7, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 7/8
                        s1 * 7/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 7/7 {
                            r8
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                            r8
                            r8
                        }
                    }
                >>

        ..  container:: example

            Forces the first leaf of every tuplet to be a rest:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.force_rest(
            ...         abjad.select().tuplets().map(abjad.select().leaf(0))
            ...     ),
            ...     rmakers.beam(),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            r8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            r8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            r8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            r8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        """
        return super().commands

    @property
    def denominator(self) -> typing.Union[str, int]:
        r"""
        Gets preferred denominator.

        ..  container:: example

            No preferred denominator:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominator=None,
            ...     denominators=[16],
            ...     extra_counts_per_division=[4],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 2/3 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            Expresses tuplet ratios in the usual way with numerator and
            denominator relatively prime.

        ..  container:: example

            Preferred denominator equal to 4:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominator=4,
            ...     denominators=[16],
            ...     extra_counts_per_division=[4],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \times 4/6 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 4/6 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            Preferred denominator equal to 8:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominator=8,
            ...     denominators=[16],
            ...     extra_counts_per_division=[4],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \times 8/12 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 8/12 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            Preferred denominator equal to 16:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominator=16,
            ...     denominators=[16],
            ...     extra_counts_per_division=[4],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \times 16/24 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 16/24 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Preferred denominator taken from count of elements in tuplet:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominator='from_counts',
            ...     denominators=[16],
            ...     extra_counts_per_division=[4],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \times 8/12 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/10 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 8/12 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/10 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        """
        return self._denominator

    @property
    def denominators(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets denominators.

        ..  container:: example

            Fills divisions with alternating 16th / 8th notes:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16, 8],
            ...     )

            >>> divisions = [(3, 16), (3, 8), (3, 4)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/16
                        s1 * 3/16
                        \time 3/8
                        s1 * 3/8
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/12 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Fills divisions with 8th notes:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[8],
            ...     )

            >>> divisions = [(3, 16), (3, 8), (3, 4)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/16
                        s1 * 3/16
                        \time 3/8
                        s1 * 3/8
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/6 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

            Fills divisions less than twice the duration of an eighth note with
            a single attack.

        ..  container:: example

            Fills divisions with quarter notes:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[4],
            ...     )

            >>> divisions = [(3, 16), (3, 8), (3, 4)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/16
                        s1 * 3/16
                        \time 3/8
                        s1 * 3/8
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'4
                            c'4
                            c'4
                        }
                    }
                >>

            Divisions less than twice the duration of a quarter note are filled
            with a single attack.

        ..  container:: example

            Fills divisions with half notes:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[2],
            ...     )

            >>> divisions = [(3, 16), (3, 8), (3, 4)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/16
                        s1 * 3/16
                        \time 3/8
                        s1 * 3/8
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'2.
                        }
                    }
                >>

            Fills divisions less than twice the duration of a half note with a
            single attack.

        """
        if self._denominators:
            return list(self._denominators)
        return None

    @property
    def extra_counts_per_division(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets extra counts per division.

        Treats overly large and overly small values of
        ``extra_counts_per_division`` modularly. Denote by
        ``unprolated_note_count`` the number of unprolated notes included in
        any division (as though ``extra_counts_per_division`` were set to
        zero). Then the actual number of extra counts included per division is
        given by two formulas:

        * The actual number of extra counts included per division is given by
          ``extra_counts_per_division % unprolated_note_count`` when
          ``extra_counts_per_division`` is positive.

        * The actual number of extra counts included per division is given by
          the formula
          ``extra_counts_per_division % ceiling(unprolated_note_count / 2)``
          when ``extra_counts_per_division`` is negative.

        These formulas ensure that:

        * even very large and very small values of
          ``extra_counts_per_division`` produce valid output, and that

        * the values given as the rhythm-maker's ``denominators`` are always
          respected. A very large value of ``extra_counts_per_division``, for
          example, never causes a `16`-denominated division to result 32nd or
          64th note rhythms; `16`-denominated divisions always produce 16th
          note rhythms.

        ..  container:: example

            Four missing counts per division:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[-4],
            ...     )

            >>> divisions = [(1, 16), (2, 16), (3, 16), (4, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/16
                        s1 * 1/16
                        \time 2/16
                        s1 * 1/8
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'16
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Three missing counts per division:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[-3],
            ...     )

            >>> divisions = [(1, 16), (2, 16), (3, 16), (4, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/16
                        s1 * 1/16
                        \time 2/16
                        s1 * 1/8
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'16
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'16
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Two missing counts per division:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[-2],
            ...     )

            >>> divisions = [(1, 16), (2, 16), (3, 16), (4, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/16
                        s1 * 1/16
                        \time 2/16
                        s1 * 1/8
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'16
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            One missing count per division:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[-1],
            ...     )

            >>> divisions = [(1, 16), (2, 16), (3, 16), (4, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/16
                        s1 * 1/16
                        \time 2/16
                        s1 * 1/8
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'16
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'16
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Neither missing nor extra counts per division:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=None,
            ...     )

            >>> divisions = [(1, 16), (2, 16), (3, 16), (4, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/16
                        s1 * 1/16
                        \time 2/16
                        s1 * 1/8
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'16
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            One extra count per division:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(1, 16), (2, 16), (3, 16), (4, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/16
                        s1 * 1/16
                        \time 2/16
                        s1 * 1/8
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \times 2/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 4/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Two extra counts per division:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[2],
            ...     )

            >>> divisions = [(1, 16), (2, 16), (3, 16), (4, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/16
                        s1 * 1/16
                        \time 2/16
                        s1 * 1/8
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'16
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 4/6 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/7 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Three extra counts per division:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[3],
            ...     )

            >>> divisions = [(1, 16), (2, 16), (3, 16), (4, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/16
                        s1 * 1/16
                        \time 2/16
                        s1 * 1/8
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \times 2/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \times 4/7 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/8 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>


        ..  container:: example

            Four extra counts per division:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[4],
            ...     )

            >>> divisions = [(1, 16), (2, 16), (3, 16), (4, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/16
                        s1 * 1/16
                        \time 2/16
                        s1 * 1/8
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'16
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/9 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Adds extra counts per division according to a pattern of three
            elements:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[0, 1, 2],
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/6 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/8 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/6 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        """
        if self._extra_counts_per_division:
            return list(self._extra_counts_per_division)
        return None

    @property
    def state(self) -> abjad.OrderedDict:
        r"""
        Gets state dictionary.

        ..  container:: example

            Fills divisions with 16th, 8th, quarter notes. Consumes 5:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     denominators=[16, 8, 4],
            ...     extra_counts_per_division=[0, 1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                        }
                        \times 4/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 5),
                    ('logical_ties_produced', 15),
                    ]
                )

            Advances 5 divisions; then consumes another 5 divisions:

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
            >>> selection = rhythm_maker(divisions, previous_state=state)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/4 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                        }
                        \times 4/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 10),
                    ('logical_ties_produced', 29),
                    ]
                )

        """
        return super().state
