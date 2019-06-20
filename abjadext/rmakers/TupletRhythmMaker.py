import abjad
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier
from .DurationSpecifier import DurationSpecifier
from .RhythmMaker import RhythmMaker
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier


class TupletRhythmMaker(RhythmMaker):
    r"""
    Tuplet rhythm-maker.

    ..  container:: example

        Makes tuplets with ``3:2`` ratios:

        >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
        ...     abjadext.rmakers.BeamSpecifier(
        ...         beam_each_division=True,
        ...     ),
        ...     tuplet_ratios=[(3, 2)],
        ...     )

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selections = rhythm_maker(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ...     )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/2
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
        ...     abjadext.rmakers.BeamSpecifier(
        ...         beam_each_division=True,
        ...     ),
        ...     tuplet_ratios=[(1, -1), (3, 1)],
        ...     )

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selections = rhythm_maker(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ...     )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/2
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'4
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'4.
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6 {
                        c'8.
                        r8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4 {
                        c'8.
                        [
                        c'16
                        ]
                    }
                }
            >>

    Object model of a partially evaluated function that accepts a (possibly
    empty) list of divisions as input and returns a list of selections as
    output. Output structured one selection per division with each selection
    wrapping a single tuplet.

    Usage follows the two-step configure-once / call-repeatedly pattern shown
    here.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_denominator", "_tuplet_ratios")

    ### INITIALIZER ###

    def __init__(
        self,
        *specifiers: typings.SpecifierTyping,
        denominator: typing.Union[int, abjad.DurationTyping] = None,
        division_masks: typings.MasksTyping = None,
        duration_specifier: DurationSpecifier = None,
        tag: str = None,
        tuplet_ratios: abjad.RatioSequenceTyping = None,
    ) -> None:
        RhythmMaker.__init__(
            self,
            *specifiers,
            duration_specifier=duration_specifier,
            division_masks=division_masks,
            tag=tag,
        )
        if denominator is not None:
            if isinstance(denominator, tuple):
                denominator = abjad.Duration(denominator)
            prototype = (abjad.Duration, int)
            assert denominator == "divisions" or isinstance(
                denominator, prototype
            )
        self._denominator = denominator
        tuple_ratios_ = None
        if tuplet_ratios is not None:
            tuplet_ratios_ = tuple([abjad.Ratio(_) for _ in tuplet_ratios])
        self._tuplet_ratios = tuplet_ratios_

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.Sequence[abjad.IntegerPair],
        previous_state: abjad.OrderedDict = None,
    ) -> typing.List[abjad.Selection]:
        r"""
        Calls tuplet rhythm-maker on ``divisions``.

        ..  container:: example

            Calls tuplet rhythm-maker with one ratio:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     tuplet_ratios=[(3, 2)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/2
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Calls tuplet rhythm-maker on two ratios:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     tuplet_ratios=[(1, -1), (3, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/2
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'4.
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            c'8.
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'8.
                            [
                            c'16
                            ]
                        }
                    }
                >>

        Stuctures selections one selection per division.
        
        Each selection wraps a single tuplet.
        """
        return RhythmMaker.__call__(
            self, divisions, previous_state=previous_state
        )

    def __format__(self, format_specification="") -> str:
        r"""
        Formats tuplet rhythm-maker.

        ..  container:: example

            Formats tuplet rhythm-maker with one ratio:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(3, 2)],
            ...     )

            >>> abjad.f(rhythm_maker)
            abjadext.rmakers.TupletRhythmMaker(
                tuplet_ratios=[
                    abjad.Ratio((3, 2)),
                    ],
                )

        ..  container:: example

            Formats tuplet rhythm-maker with two ratios:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, -1), (3, 1)],
            ...     )

            >>> abjad.f(rhythm_maker)
            abjadext.rmakers.TupletRhythmMaker(
                tuplet_ratios=[
                    abjad.Ratio((1, -1)),
                    abjad.Ratio((3, 1)),
                    ],
                )

        """
        return super().__format__(format_specification=format_specification)

    ### PRIVATE METHODS ###

    def _make_music(self, divisions):
        tuplets = []
        prototype = abjad.NonreducedFraction
        assert all(isinstance(_, prototype) for _ in divisions)
        tuplet_ratios = abjad.CyclicTuple(self.tuplet_ratios)
        for duration_index, division in enumerate(divisions):
            ratio = tuplet_ratios[duration_index]
            duration = abjad.Duration(division)
            tuplet = abjad.Tuplet.from_duration_and_ratio(
                duration, ratio, tag=self.tag
            )
            tuplets.append(tuplet)
        selections = [abjad.select(_) for _ in tuplets]
        return selections

    ### PUBLIC PROPERTIES ###

    @property
    def denominator(
        self
    ) -> typing.Optional[typing.Union[str, abjad.Duration, int]]:
        r"""
        Gets preferred denominator.

        ..  container:: example

            Tuplet numerators and denominators are reduced to numbers that are
            relatively prime when ``denominator`` is set to none. This
            means that ratios like ``6:4`` and ``10:8`` do not arise:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=None,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            The preferred denominator of each tuplet is set to the numerator of
            the division that generates the tuplet when ``denominator``
            is set to the string ``'divisions'``. This means that the tuplet
            numerator and denominator are not necessarily relatively prime.
            This also means that ratios like ``6:4`` and ``10:8`` may arise:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator='divisions',
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            The preferred denominator of each tuplet is set in terms of a unit
            duration when ``denominator`` is set to a duration. The
            setting does not affect the first tuplet:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 16),
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator of each tuplet in terms 32nd notes.
            The setting affects all tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 32),
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 8/10 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                        \times 16/20 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator each tuplet in terms 64th notes. The
            setting affects all tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 64),
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 16/20 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 24/20 {
                            c'16
                            c'4
                        }
                        \times 32/40 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            The preferred denominator of each tuplet is set directly when
            ``denominator`` is set to a positive integer. This example
            sets the preferred denominator of each tuplet to ``8``. Setting
            does not affect the third tuplet:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=8,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 8/10 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``12``. Setting
            affects all tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=12,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 12/15 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 12/15 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                        \times 12/15 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``13``. Setting
            does not affect any tuplet:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=13,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }
                >>

        Set to ``'divisions'``, duration, positive integer or none.
        """
        return self._denominator

    @property
    def specifiers(self) -> typing.List[typings.SpecifierTyping]:
        r"""
        Gets specifiers.

        ..  container:: example

            Beams each division:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 1, 2, 1, 1), (3, 1, 1)],
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file)  # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 3/8
                        s1 * 3/8
                        \time 6/8
                        s1 * 3/4
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/9 {
                            c'8.
                            [
                            c'8.
                            ]
                            c'4.
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                            c'4
                            c'8
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'4.
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Beams divisions together:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         beam_divisions_together=True,
            ...         ),
            ...     tuplet_ratios=[(1, 1, 2, 1, 1), (3, 1, 1)],
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file)  # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 3/8
                        s1 * 3/8
                        \time 6/8
                        s1 * 3/4
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/9 {
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8.
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8.
                            ]
                            c'4.
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8.
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                            c'4
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'4.
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Beams nothing:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=False,
            ...         beam_each_division=False,
            ...         ),
            ...     tuplet_ratios=[(1, 1, 2, 1, 1), (3, 1, 1)],
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file)  # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 3/8
                        s1 * 3/8
                        \time 6/8
                        s1 * 3/4
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/9 {
                            c'8.
                            c'8.
                            c'4.
                            c'8.
                            c'8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            c'8
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            c'8
                            c'4
                            c'8
                            c'8
                        }
                        \times 4/5 {
                            c'4.
                            c'8
                            c'8
                        }
                    }
                >>

        Ignores ``beam_each_division`` when ``beam_division_together`` is true.

        ..  container:: example

            Ties nothing:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(2, 3), (1, -2, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/2
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16.
                            r8.
                            c'16.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8.
                            ]
                        }
                    }
                >>

        ..  container:: example

            Ties across all divisions:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(2, 3), (1, -2, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/2
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16.
                            r8.
                            c'16.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8.
                            ]
                        }
                    }
                >>

        ..  container:: example

            Ties across every other division:

            >>> pattern = abjad.Pattern(
            ...     indices=[0],
            ...     period=2,
            ...     )
            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=pattern,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(2, 3), (1, -2, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/2
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16.
                            r8.
                            c'16.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            c'16.
                            r8.
                            c'16.
                        }
                    }
                >>

        ..  container:: example

            Makes diminished tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         diminution=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(2, 1)],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'4
                            c'8
                        }
                        \times 2/3 {
                            c'4
                            c'8
                        }
                        \times 2/3 {
                            c'2
                            c'4
                        }
                    }
                >>

        ..  container:: example

            Makes augmented tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         diminution=False,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(2, 1)],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'8
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'8
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'4
                            c'8
                        }
                    }
                >>

        ..  container:: example

            Makes diminished tuplets and does not rewrite dots:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=False,
            ...         diminution=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 1)],
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \time 3/8
                        s1 * 3/8
                        \time 7/16
                        s1 * 7/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8..
                            [
                            c'8..
                            ]
                        }
                    }
                >>

        ..  container:: example

            Makes diminished tuplets and rewrites dots:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         diminution=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 1)],
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \time 3/8
                        s1 * 3/8
                        \time 7/16
                        s1 * 7/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 7/8 {
                            c'4
                            c'4
                        }
                    }
                >>

        ..  container:: example

            Makes augmented tuplets and does not rewrite dots:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=False,
            ...         diminution=False,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 1)],
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \time 3/8
                        s1 * 3/8
                        \time 7/16
                        s1 * 7/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8..
                            [
                            c'8..
                            ]
                        }
                    }
                >>

        ..  container:: example

            Makes augmented tuplets and rewrites dots:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         diminution=False,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, 1)],
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \time 3/8
                        s1 * 3/8
                        \time 7/16
                        s1 * 7/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 7/4 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Leaves trivializable tuplets as-is when ``trivialize`` is false:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         trivialize=False,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(3, -2), (1,), (-2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            r4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Rewrites trivializable tuplets when ``trivialize`` is true.
            Measures 2 and 4 contain trivial tuplets with 1:1 ratios. To remove
            these trivial tuplets, set ``extract_trivial`` as shown in the next
            example:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         trivialize=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(3, -2), (1,), (-2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            r4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                    }
                >>

            REGRESSION: Ignores ``trivialize`` and respects ``rewrite_dots`` when
            both are true. Measures 2 and 4 are first rewritten as trivial but
            then supplied again with nontrivial prolation when removing dots.
            The result is that measures 2 and 4 carry nontrivial prolation with
            no dots:
            
            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         trivialize=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(3, -2), (1,), (-2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            r4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Leaves trivial tuplets as-is when ``extract_trivial`` is
            false:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=False,
            ...         ),
            ...     abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \time 2/8
                        s1 * 1/4
                        \time 3/8
                        s1 * 3/8
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Extracts trivial tuplets when ``extract_trivial`` is true.
            Measures 2 and 4 in the example below now contain only a flat list
            of notes:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \time 2/8
                        s1 * 1/4
                        \time 3/8
                        s1 * 3/8
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            c'4.
                            ~
                        }
                        c'8
                        [
                        c'8
                        ~
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            c'4.
                            ~
                        }
                        c'8
                        [
                        c'8
                        ]
                    }
                >>

            .. note:: Flattening trivial tuplets makes it possible
                subsequently to rewrite the meter of the untupletted notes.

        ..  container:: example

            REGRESSION: Very long ties are preserved when ``extract_trivial``
            is true:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         tie_consecutive_notes=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \time 2/8
                        s1 * 1/4
                        \time 3/8
                        s1 * 3/8
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            ~
                            c'4.
                            ~
                        }
                        c'8
                        ~
                        [
                        c'8
                        ~
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            ~
                            c'4.
                            ~
                        }
                        c'8
                        ~
                        [
                        c'8
                        ]
                    }
                >>

        ..  container:: example

            No division masks:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=False,
            ...         ),
            ...     tuplet_ratios=[(4, 1)],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \times 4/5 {
                            c'4.
                            c'16.
                        }
                        \times 4/5 {
                            c'2
                            c'8
                        }
                        \times 4/5 {
                            c'4.
                            c'16.
                        }
                        \times 4/5 {
                            c'2
                            c'8
                        }
                    }
                >>

        ..  container:: example

            Masks every other output division:

            >>> pattern = abjad.Pattern([1], period=2)
            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.SilenceMask(
            ...         selector=abjad.select().tuplets()[pattern],
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_rest_filled=True,
            ...         selector=abjad.select().tuplets()[pattern],
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     tuplet_ratios=[(4, 1)],
            ... )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
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
                        \times 4/5 {
                            c'4.
                            c'16.
                        }
                        r2
                        \times 4/5 {
                            c'4.
                            c'16.
                        }
                        r2
                    }
                >>

        """
        return super().specifiers

    @property
    def tag(self) -> typing.Optional[str]:
        r"""
        Gets tag.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tag='TUPLET_RHYTHM_MAKER',
            ...     tuplet_ratios=[(3, 2)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> abjad.f(lilypond_file[abjad.Score], strict=30)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/2
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \times 4/5 {          %! TUPLET_RHYTHM_MAKER
                        c'4.              %! TUPLET_RHYTHM_MAKER
                        c'4               %! TUPLET_RHYTHM_MAKER
                    }                     %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! TUPLET_RHYTHM_MAKER
                    \times 3/5 {          %! TUPLET_RHYTHM_MAKER
                        c'4.              %! TUPLET_RHYTHM_MAKER
                        c'4               %! TUPLET_RHYTHM_MAKER
                    }                     %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! TUPLET_RHYTHM_MAKER
                    \times 1/1 {          %! TUPLET_RHYTHM_MAKER
                        c'8.              %! TUPLET_RHYTHM_MAKER
                        [                 %! TUPLET_RHYTHM_MAKER
                        c'8               %! TUPLET_RHYTHM_MAKER
                        ]                 %! TUPLET_RHYTHM_MAKER
                    }                     %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! TUPLET_RHYTHM_MAKER
                    \times 1/1 {          %! TUPLET_RHYTHM_MAKER
                        c'8.              %! TUPLET_RHYTHM_MAKER
                        [                 %! TUPLET_RHYTHM_MAKER
                        c'8               %! TUPLET_RHYTHM_MAKER
                        ]                 %! TUPLET_RHYTHM_MAKER
                    }                     %! TUPLET_RHYTHM_MAKER
                }
            >>

        """
        return super().tag

    @property
    def tuplet_ratios(self) -> typing.Optional[typing.List[abjad.Ratio]]:
        r"""
        Gets tuplet ratios.

        ..  container:: example

            Makes tuplets with ``3:2`` ratios:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(3, 2)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/2
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     tuplet_ratios=[(1, -1), (3, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/2
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'4.
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            c'8.
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'8.
                            [
                            c'16
                            ]
                        }
                    }
                >>

        """
        if self._tuplet_ratios:
            return list(self._tuplet_ratios)
        else:
            return None
