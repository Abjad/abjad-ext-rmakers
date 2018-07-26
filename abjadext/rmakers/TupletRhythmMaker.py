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

            >>> abjad.f(lilypond_file[abjad.Staff])
            \new RhythmicStaff
            {
                {   % measure
                    \time 1/2
                    \times 4/5 {
                        c'4.
                        c'4
                    }
                }   % measure
                {   % measure
                    \time 3/8
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4.
                        c'4
                    }
                }   % measure
                {   % measure
                    \time 5/16
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8
                        ]
                    }
                }   % measure
                {   % measure
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8
                        ]
                    }
                }   % measure
            }

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
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

            >>> abjad.f(lilypond_file[abjad.Staff])
            \new RhythmicStaff
            {
                {   % measure
                    \time 1/2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'4
                        r4
                    }
                }   % measure
                {   % measure
                    \time 3/8
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'4.
                        c'8
                    }
                }   % measure
                {   % measure
                    \time 5/16
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6 {
                        c'8.
                        r8.
                    }
                }   % measure
                {   % measure
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4 {
                        c'8.
                        [
                        c'16
                        ]
                    }
                }   % measure
            }

    Object model of a partially evaluated function that accepts a (possibly
    empty) list of divisions as input and returns a list of selections as
    output. Output structured one selection per division with each selection
    wrapping a single tuplet.

    Usage follows the two-step configure-once / call-repeatedly pattern shown
    here.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Rhythm-makers'

    __slots__ = (
        '_denominator',
        '_tuplet_ratios',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        beam_specifier: BeamSpecifier = None,
        denominator: int = None,
        division_masks: typings.MaskKeyword = None,
        duration_specifier: DurationSpecifier = None,
        tie_specifier: TieSpecifier = None,
        tuplet_ratios: typing.Sequence[typing.Tuple[int, ...]] = None,
        tuplet_specifier: TupletSpecifier = None,
        ) -> None:
        RhythmMaker.__init__(
            self,
            beam_specifier=beam_specifier,
            duration_specifier=duration_specifier,
            division_masks=division_masks,
            tie_specifier=tie_specifier,
            tuplet_specifier=tuplet_specifier,
            )
        if denominator is not None:
            if isinstance(denominator, tuple):
                denominator = abjad.Duration(denominator)
            prototype = (abjad.Duration, int)
            assert (denominator == 'divisions' or
                isinstance(denominator, prototype))
        self._denominator = denominator
        tuple_ratios_ = None
        if tuplet_ratios is not None:
            tuplet_ratios_ = tuple([abjad.Ratio(_) for _ in tuplet_ratios])
        self._tuplet_ratios = tuplet_ratios_

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.List[typing.Tuple[int, int]],
        previous_state: abjad.OrderedDict = None,
        ) -> typing.List[abjad.Selection]:
        r"""
        Calls tuplet rhythm-maker on ``divisions``.

        ..  container:: example

            Calls tuplet rhythm-maker with one ratio:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 1/2
                        \times 4/5 {
                            c'4.
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 5/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Calls tuplet rhythm-maker on two ratios:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 1/2
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            r4
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'4.
                            c'8
                        }
                    }   % measure
                    {   % measure
                        \time 5/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            c'8.
                            r8.
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'8.
                            [
                            c'16
                            ]
                        }
                    }   % measure
                }

        Returns list of selections structured one selection per division.
        Each selection wraps a single tuplet.
        """
        return RhythmMaker.__call__(
            self,
            divisions,
            previous_state=previous_state,
            )

    def __format__(self, format_specification='') -> str:
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
        return super(TupletRhythmMaker, self).__format__(
            format_specification=format_specification,
            )

    ### PRIVATE METHODS ###

    def _make_music(self, divisions):
        tuplets = []
        prototype = abjad.NonreducedFraction
        assert all(isinstance(_, prototype) for _ in divisions)
        rotation = self.state.get('rotation', 0)
        tuplet_ratios = abjad.CyclicTuple(
            abjad.sequence(self.tuplet_ratios).rotate(n=rotation)
            )
        for duration_index, division in enumerate(divisions):
            ratio = tuplet_ratios[duration_index]
            duration = abjad.Duration(division)
            tuplet = abjad.Tuplet.from_duration_and_ratio(duration, ratio)
            tuplets.append(tuplet)
        selections = [abjad.select(_) for _ in tuplets]
        beam_specifier = self._get_beam_specifier()
        beam_specifier(selections)
        selections = self._apply_division_masks(selections)
        return selections

    ### PUBLIC PROPERTIES ###

    @property
    def beam_specifier(self) -> typing.Optional[BeamSpecifier]:
        r"""
        Gets beam specifier.

        ..  container:: example

            Beams each division:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 1, 2, 1, 1), (3, 1, 1)],
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file)  # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 5/8
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
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 6/8
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
                    }   % measure
                    {   % measure
                        \time 4/8
                        \times 4/5 {
                            c'4.
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Beams divisions together:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 1, 2, 1, 1), (3, 1, 1)],
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=True,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file)  # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 5/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/9 {
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 1
                            c'8.
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8.
                            ]
                            c'4.
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8.
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8.
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8
                        }
                    }   % measure
                    {   % measure
                        \time 6/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8
                            ]
                            c'4
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/8
                        \times 4/5 {
                            c'4.
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 1
                            c'8
                            [
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 0
                            c'8
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Beams nothing:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 1, 2, 1, 1), (3, 1, 1)],
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=False,
            ...         beam_each_division=False,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file)  # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 5/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/9 {
                            c'8.
                            c'8.
                            c'4.
                            c'8.
                            c'8.
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            c'8
                            c'8
                        }
                    }   % measure
                    {   % measure
                        \time 6/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            c'8
                            c'4
                            c'8
                            c'8
                        }
                    }   % measure
                    {   % measure
                        \time 4/8
                        \times 4/5 {
                            c'4.
                            c'8
                            c'8
                        }
                    }   % measure
                }

        Ignores ``beam_each_division`` when ``beam_division_together`` is true.
        """
        return super(TupletRhythmMaker, self).beam_specifier

    @property
    def denominator(self) -> typing.Optional[
        typing.Union[str, abjad.Duration, int]
        ]:
        r"""
        Gets preferred denominator.

        ..  container:: example

            Tuplet numerators and denominators are reduced to numbers that are
            relatively prime when ``denominator`` is set to none. This
            means that ratios like ``6:4`` and ``10:8`` do not arise:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=None,
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 4/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            The preferred denominator of each tuplet is set to the numerator of
            the division that generates the tuplet when ``denominator``
            is set to the string ``'divisions'``. This means that the tuplet
            numerator and denominator are not necessarily relatively prime.
            This also means that ratios like ``6:4`` and ``10:8`` may arise:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator='divisions',
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 4/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            The preferred denominator of each tuplet is set in terms of a unit
            duration when ``denominator`` is set to a duration. The
            setting does not affect the first tuplet:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 16),
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 4/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            Sets the preferred denominator of each tuplet in terms 32nd notes.
            The setting affects all tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 32),
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 8/10 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 16/20 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            Sets the preferred denominator each tuplet in terms 64th notes. The
            setting affects all tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 64),
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/16
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 16/20 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 24/20 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 32/40 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            The preferred denominator of each tuplet is set directly when
            ``denominator`` is set to a positive integer. This example
            sets the preferred denominator of each tuplet to ``8``. Setting
            does not affect the third tuplet:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=8,
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/16
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 8/10 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``12``. Setting
            affects all tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=12,
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/16
                        \times 12/15 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 12/15 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 12/15 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``13``. Setting
            does not affect any tuplet:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=13,
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 4/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        Set to ``'divisions'``, duration, positive integer or none.
        """
        return self._denominator

    @property
    def division_masks(self) -> typing.Optional[abjad.PatternTuple]:
        r"""
        Gets division masks.

        ..  container:: example

            No division masks:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(4, 1)],
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=False,
            ...         beam_each_division=False,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 3/8
                        \times 4/5 {
                            c'4.
                            c'16.
                        }
                    }   % measure
                    {   % measure
                        \time 4/8
                        \times 4/5 {
                            c'2
                            c'8
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \times 4/5 {
                            c'4.
                            c'16.
                        }
                    }   % measure
                    {   % measure
                        \time 4/8
                        \times 4/5 {
                            c'2
                            c'8
                        }
                    }   % measure
                }

        ..  container:: example

            Masks every other output division:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(4, 1)],
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=False,
            ...         beam_each_division=False,
            ...         ),
            ...     division_masks=[
            ...         abjadext.rmakers.silence([1], 2),
            ...         ],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 3/8
                        \times 4/5 {
                            c'4.
                            c'16.
                        }
                    }   % measure
                    {   % measure
                        \time 4/8
                        r2
                    }   % measure
                    {   % measure
                        \time 3/8
                        \times 4/5 {
                            c'4.
                            c'16.
                        }
                    }   % measure
                    {   % measure
                        \time 4/8
                        r2
                    }   % measure
                }

        """
        return super(TupletRhythmMaker, self).division_masks

    @property
    def tie_specifier(self) -> typing.Optional[TieSpecifier]:
        r"""
        Gets tie specifier.

        ..  container:: example

            Ties nothing:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(2, 3), (1, -2, 1)],
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=False,
            ...         ),
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 1/2
                        \times 4/5 {
                            c'4
                            c'4.
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16.
                            r8.
                            c'16.
                        }
                    }   % measure
                    {   % measure
                        \time 5/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8.
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Ties across all divisions:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(2, 3), (1, -2, 1)],
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 1/2
                        \times 4/5 {
                            c'4
                            c'4.
                            ~
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16.
                            r8.
                            c'16.
                            ~
                        }
                    }   % measure
                    {   % measure
                        \time 5/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8.
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Ties across every other division:

            >>> pattern = abjad.Pattern(
            ...     indices=[0],
            ...     period=2,
            ...     )
            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(2, 3), (1, -2, 1)],
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=pattern,
            ...         ),
            ...     )

            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 1/2
                        \times 4/5 {
                            c'4
                            c'4.
                            ~
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16.
                            r8.
                            c'16.
                        }
                    }   % measure
                    {   % measure
                        \time 5/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8.
                            ~
                            ]
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            c'16.
                            r8.
                            c'16.
                        }
                    }   % measure
                }

        """
        return super(TupletRhythmMaker, self).tie_specifier

    @property
    def tuplet_ratios(self) -> typing.Optional[typing.List[abjad.Ratio]]:
        r"""
        Gets tuplet ratios.

        ..  container:: example

            Makes tuplets with ``3:2`` ratios:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 1/2
                        \times 4/5 {
                            c'4.
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 5/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 1/2
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            r4
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'4.
                            c'8
                        }
                    }   % measure
                    {   % measure
                        \time 5/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            c'8.
                            r8.
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'8.
                            [
                            c'16
                            ]
                        }
                    }   % measure
                }

        """
        if self._tuplet_ratios:
            return list(self._tuplet_ratios)
        else:
            return None

    @property
    def tuplet_specifier(self) -> typing.Optional[TupletSpecifier]:
        r"""
        Gets tuplet specifier.

        ..  container:: example

            Makes diminished tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(2, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         diminution=True,
            ...         ),
            ...     )

            >>> divisions = [(2, 8), (2, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/8
                        \times 2/3 {
                            c'4
                            c'8
                        }
                    }   % measure
                    {   % measure
                        \times 2/3 {
                            c'4
                            c'8
                        }
                    }   % measure
                    {   % measure
                        \time 4/8
                        \times 2/3 {
                            c'2
                            c'4
                        }
                    }   % measure
                }

        ..  container:: example

            Makes augmented tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(2, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         diminution=False,
            ...         ),
            ...     )

            >>> divisions = [(2, 8), (2, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'8
                            [
                            c'16
                            ]
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'8
                            [
                            c'16
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'4
                            c'8
                        }
                    }   % measure
                }

        ..  container:: example

            Makes diminished tuplets and does not rewrite dots:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=False,
            ...         diminution=True,
            ...         ),
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 7/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8..
                            [
                            c'8..
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Makes diminished tuplets and rewrites dots:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         diminution=True,
            ...         ),
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'4
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 7/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 7/8 {
                            c'4
                            c'4
                        }
                    }   % measure
                }

        ..  container:: example

            Makes augmented tuplets and does not rewrite dots:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=False,
            ...         diminution=False,
            ...         ),
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 7/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8..
                            [
                            c'8..
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Makes augmented tuplets and rewrites dots:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         diminution=False,
            ...         ),
            ...     )

            >>> divisions = [(2, 8), (3, 8), (7, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 7/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 7/4 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Leaves trivializable tuplets as-is when ``trivialize`` is false:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(3, -2), (1,), (-2, 3), (1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         trivialize=False,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            r4
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            r4
                            c'4.
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Rewrites trivializable tuplets when ``trivialize`` is true.
            Measures 2 and 4 contain trivial tuplets with 1:1 ratios. To remove
            these trivial tuplets, set ``extract_trivial`` as shown in the next
            example:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(3, -2), (1,), (-2, 3), (1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         trivialize=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            r4
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4.
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            r4
                            c'4.
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                    }   % measure
                }

            REGRESSION: Ignores ``trivialize`` and respects ``rewrite_dots`` when
            both are true. Measures 2 and 4 are first rewritten as trivial but
            then supplied again with nontrivial prolation when removing dots.
            The result is that measures 2 and 4 carry nontrivial prolation with
            no dots:
            
            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(3, -2), (1,), (-2, 3), (1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         trivialize=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            r4
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            r4
                            c'4.
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/2 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Leaves trivial tuplets as-is when ``extract_trivial`` is
            false:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     tuplet_ratios=[(2, 3), (1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=False,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            c'4.
                            ~
                        }
                    }   % measure
                    {   % measure
                        \time 2/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ~
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            c'4.
                            ~
                        }
                    }   % measure
                    {   % measure
                        \time 2/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }   % measure
                }

        ..  container:: example

            Extracts trivial tuplets when ``extract_trivial`` is true.
            Measures 2 and 4 in the example below now contain only a flat list
            of notes:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     tuplet_ratios=[(2, 3), (1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            c'4.
                            ~
                        }
                    }   % measure
                    {   % measure
                        \time 2/8
                        c'8
                        [
                        c'8
                        ~
                        ]
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            c'4.
                            ~
                        }
                    }   % measure
                    {   % measure
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }   % measure
                }

            .. note:: Flattening trivial tuplets makes it possible
                subsequently to rewrite the meter of the untupletted notes.

        ..  container:: example

            REGRESSION: Very long ties are preserved when ``extract_trivial``
            is true:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         tie_consecutive_notes=True,
            ...         ),
            ...     tuplet_ratios=[(2, 3), (1, 1)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            ~
                            c'4.
                            ~
                        }
                    }   % measure
                    {   % measure
                        \time 2/8
                        c'8
                        ~
                        [
                        c'8
                        ~
                        ]
                    }   % measure
                    {   % measure
                        \time 3/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            ~
                            c'4.
                            ~
                        }
                    }   % measure
                    {   % measure
                        \time 2/8
                        c'8
                        ~
                        [
                        c'8
                        ]
                    }   % measure
                }

        """
        return super(TupletRhythmMaker, self).tuplet_specifier
