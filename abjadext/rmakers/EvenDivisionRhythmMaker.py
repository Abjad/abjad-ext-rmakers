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
        extra_counts_per_division: typing.Sequence[int] = None,
        spelling: _specifiers.Spelling = None,
        tag: str = None,
    ) -> None:
        RhythmMaker.__init__(
            self, *commands, divisions=divisions, spelling=spelling, tag=tag
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

            Forces tuplet diminution:

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

            Forces tuplet augmentation:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     rmakers.force_augmentation(),
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

            Ties nonlast tuplets:

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

            (Equivalent to earlier tie-across-divisions pattern.)

        ..  container:: example

            Forces rest at every third logical tie:

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

            Forces rest at every fourth logical tie:

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

            (Forcing rests at the fourth logical tie produces two rests.
            Forcing rests at the eighth logical tie produces only one rest.)

            Forces rest at leaf 0 of every tuplet:

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

        ..  container:: example

            Forces rest and rewrites every other tuplet:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.force_rest(
            ...         abjad.select().tuplets().get([0], 2),
            ...     ),
            ...     rmakers.rewrite_rest_filled(),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     extra_counts_per_division=[1],
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
                        \times 3/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        r2
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

            (Equivalent to ealier silence pattern.)

        ..  container:: example

            Ties and rewrites every other tuplet:

            >>> tuplets = abjad.select().tuplets().get([0], 2)
            >>> nonlast_notes = abjad.select().notes()[:-1]
            >>> selector = tuplets.map(nonlast_notes)
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.tie(selector),
            ...     rmakers.rewrite_sustained(),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     extra_counts_per_division=[1],
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
                        \times 3/4 {
                            c'8
                            [
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'2
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

            (Equivalent to earlier sustain pattern.)

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

            Fills tuplets with 16th notes and 8th notes, alternately:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
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
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        c'8
                        [
                        c'8
                        c'8
                        ]
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
                >>

        ..  container:: example

            Fills tuplets with 8th notes:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
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
                        c'8.
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        c'8
                        c'8
                        ]
                    }
                >>

            (Fills tuplets less than twice the duration of an eighth note with
            a single attack.)

            Fills tuplets with quarter notes:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
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
                        c'8.
                        c'4.
                        c'4
                        c'4
                        c'4
                    }
                >>

            (Fills tuplets less than twice the duration of a quarter note with
            a single attack.)

            Fills tuplets with half notes:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
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
                        c'8.
                        c'4.
                        c'2.
                    }
                >>

            (Fills tuplets less than twice the duration of a half note with a
            single attack.)

        """
        if self._denominators:
            return list(self._denominators)
        return None

    @property
    def extra_counts_per_division(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets extra counts per division.

        ..  container:: example

            Adds extra counts to tuplets according to a pattern of three
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

        Treats overly large and overly small values of
        ``extra_counts_per_division`` modularly. Denote by
        ``unprolated_note_count`` the number of unprolated notes included in
        any tuplet (as though ``extra_counts_per_division`` were set to zero).
        Then the number of extra counts included per tuplet is given by two
        formulas:

        * The number of extra counts per tuplet equals
          ``extra_counts_per_division % unprolated_note_count``
          when ``extra_counts_per_division`` is positive.

        ..  container:: example

            **Handling of overly small negative values.** Denote by
            ``unprolated_note_count`` the number counts included in a tuplet
            when ``extra_counts_per_division`` is set to zero. Then the number
            of extra counts per tuplet equals ``extra_counts_per_division %
            ceiling(unprolated_note_count / 2)`` when
            ``extra_counts_per_division`` is negative.

            The modulus of transformation of a tuplet with six notes is three:

            >>> import math
            >>> unprolated_note_count = 6
            >>> modulus = math.ceil(unprolated_note_count / 2)
            >>> modulus
            3

            Which produces the following pattern for negative values:

            >>> extra_counts_per_division = [0, -1, -2, -3, -4, -5, -6, -7, -8]
            >>> modular_counts = []
            >>> labels = []
            >>> for count in extra_counts_per_division:
            ...     modular_count = -(abs(count) % modulus)
            ...     modular_counts.append(modular_count)
            ...     label = f"{count:3} becomes {modular_count:2}"
            ...     labels.append(label)
            ...     print(label)
             0 becomes  0
            -1 becomes -1
            -2 becomes -2
            -3 becomes  0
            -4 becomes -1
            -5 becomes -2
            -6 becomes  0
            -7 becomes -1
            -8 becomes -2

            Which notate like this:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     denominators=[16],
            ...     extra_counts_per_division=[
            ...         0, -1, -2, -3, -4, -5, -6, -7, -8,
            ...     ]
            ... )

            >>> divisions = 9 * [(6, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )

            >>> staff = lilypond_file[abjad.Staff]
            >>> abjad.override(staff).text_script.staff_padding = 8
            >>> groups = abjad.select(staff).leaves().group_by_measure()
            >>> for group, label in zip(groups, labels):
            ...     markup = abjad.Markup(label, direction=abjad.Up)
            ...     abjad.attach(markup, group[0])
            ...

            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    \with
                    {
                        \override TextScript.staff-padding = #8
                    }
                    {
                        c'16
                        ^ \markup { "0 becomes 0" }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            ^ \markup { "-1 becomes -1" }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/4 {
                            c'16
                            ^ \markup { "-2 becomes -2" }
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        ^ \markup { "-3 becomes 0" }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            ^ \markup { "-4 becomes -1" }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/4 {
                            c'16
                            ^ \markup { "-5 becomes -2" }
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        ^ \markup { "-6 becomes 0" }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            ^ \markup { "-7 becomes -1" }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/4 {
                            c'16
                            ^ \markup { "-8 becomes -2" }
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

          This modular formula ensures that the values given as the
          rhythm-maker's ``denominators`` are always respected. A very large
          value of ``extra_counts_per_division``, for example, never causes a
          ``16``-denominated tuplet to result in 32nd or 64th note rhythms;
          ``16``-denominated tuplets always produce 16th note rhythms.

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
