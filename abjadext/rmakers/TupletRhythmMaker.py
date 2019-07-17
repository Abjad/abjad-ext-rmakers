import abjad
import typing
from . import commands
from .DurationSpecifier import DurationSpecifier
from .RhythmMaker import RhythmMaker


class TupletRhythmMaker(RhythmMaker):
    r"""
    Tuplet rhythm-maker.

    ..  container:: example

        Makes tuplets with ``3:2`` ratios:

        >>> rhythm_maker = rmakers.TupletRhythmMaker(
        ...     rmakers.beam(),
        ...     tuplet_ratios=[(3, 2)],
        ...     )

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
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

        >>> rhythm_maker = rmakers.TupletRhythmMaker(
        ...     rmakers.beam(),
        ...     tuplet_ratios=[(1, -1), (3, 1)],
        ...     )

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
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
        *specifiers: commands.Command,
        denominator: typing.Union[int, abjad.DurationTyping] = None,
        divisions: abjad.Expression = None,
        duration_specifier: DurationSpecifier = None,
        tag: str = None,
        tuplet_ratios: abjad.RatioSequenceTyping = None,
    ) -> None:
        RhythmMaker.__init__(
            self,
            *specifiers,
            duration_specifier=duration_specifier,
            divisions=divisions,
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
    ) -> abjad.Selection:
        r"""
        Calls tuplet rhythm-maker on ``divisions``.

        ..  container:: example

            Calls tuplet rhythm-maker with one ratio:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(3, 2)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(1, -1), (3, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
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

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        tuplets = []
        tuplet_ratios = abjad.CyclicTuple(self.tuplet_ratios)
        for i, division in enumerate(divisions):
            ratio = tuplet_ratios[i]
            tuplet = abjad.Tuplet.from_duration_and_ratio(
                division, ratio, tag=self.tag
            )
            tuplets.append(tuplet)
        return tuplets

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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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

            The preferred denominator of each tuplet is set in terms of a unit
            duration when ``denominator`` is set to a duration. The
            setting does not affect the first tuplet:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator((1, 16)),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator((1, 32)),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator((1, 64)),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator(8),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator(12),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator(13),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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

        Set to duration, positive integer or none.
        """
        return self._denominator

    @property
    def specifiers(self) -> typing.List[commands.Command]:
        r"""
        Gets specifiers.

        ..  container:: example

            Beams each division:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(1, 1, 1, 1)],
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
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
                        \times 5/6 {
                            c'8.
                            [
                            c'8.
                            c'8.
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16.
                            [
                            c'16.
                            c'16.
                            c'16.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            c'8.
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
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

            Beams each division:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(1, 1, 1, 1)],
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
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
                        \times 5/6 {
                            c'8.
                            [
                            c'8.
                            c'8.
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16.
                            [
                            c'16.
                            c'16.
                            c'16.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            c'8.
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
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

            Beams tuplets together:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam_groups(abjad.select().tuplets()),
            ...     tuplet_ratios=[(1, 1, 2, 1, 1), (3, 1, 1)],
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 1, 2, 1, 1), (3, 1, 1)],
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
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

        ..  container:: example

            Ties nothing:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(2, 3), (1, -2, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16)]
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

            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(2, 3), (1, -2, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16)]
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

            >>> tuplets = abjad.select().tuplets().get([0], 2)
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.tie(tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(2, 3), (1, -2, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.force_diminution(),
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(2, 1)],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (4, 8)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.force_augmentation(),
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(2, 1)],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (4, 8)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.force_diminution(),
            ...     tuplet_ratios=[(1, 1)],
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.rewrite_dots(),
            ...     rmakers.force_diminution(),
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(1, 1)],
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.force_augmentation(),
            ...     tuplet_ratios=[(1, 1)],
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.force_augmentation(),
            ...     tuplet_ratios=[(1, 1)],
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     tuplet_ratios=[(3, -2), (1,), (-2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.trivialize(),
            ...     tuplet_ratios=[(3, -2), (1,), (-2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
            
            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.trivialize(),
            ...     rmakers.rewrite_dots(),
            ...     tuplet_ratios=[(3, -2), (1,), (-2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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

            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
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

            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     tuplet_ratios=[(2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     rmakers.tie(abjad.select().notes()[:-1]),
            ...     tuplet_ratios=[(2, 3), (1, 1)],
            ...     )

            >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
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
                        [
                        ~
                        c'8
                        ]
                        ~
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            ~
                            c'4.
                            ~
                        }
                        c'8
                        [
                        ~
                        c'8
                        ]
                    }
                >>

        ..  container:: example

            No rest commands:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(4, 1)],
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.rest(
            ...         abjad.select().tuplets().get([1], 2),
            ...     ),
            ...     rmakers.rewrite_rest_filled(
            ...         abjad.select().tuplets().get([1], 2),
            ...     ),
            ...     rmakers.extract_trivial(),
            ...     tuplet_ratios=[(4, 1)],
            ... )

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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     tag='TUPLET_RHYTHM_MAKER',
            ...     tuplet_ratios=[(3, 2)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(3, 2)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
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

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.beam(),
            ...     tuplet_ratios=[(1, -1), (3, 1)],
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
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
