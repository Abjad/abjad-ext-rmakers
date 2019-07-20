import abjad
import math
import typing
from . import commands as _commands
from . import specifiers as _specifiers
from .RhythmMaker import RhythmMaker


class AccelerandoRhythmMaker(RhythmMaker):
    r"""
    Accelerando rhythm-maker.

    ..  container:: example

        Makes accelerandi:

        >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ...     interpolations=rmakers.interpolate((1, 8), (1, 20), (1, 16)),
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
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'2
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'4.
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'2
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'4.
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                }
            >>

    ..  container:: example

        Makes ritardandi:

        >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ...     interpolations=rmakers.interpolate((1, 20), (1, 8), (1, 16)),
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
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'2
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #left
                        c'16 * 3/4
                        [
                        c'16 * 25/32
                        c'16 * 7/8
                        c'16 * 65/64
                        c'16 * 79/64
                        c'16 * 49/32
                        c'16 * 29/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'4.
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #left
                        c'16 * 5/8
                        [
                        c'16 * 43/64
                        c'16 * 51/64
                        c'16 * 65/64
                        c'16 * 85/64
                        c'16 * 25/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'2
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #left
                        c'16 * 3/4
                        [
                        c'16 * 25/32
                        c'16 * 7/8
                        c'16 * 65/64
                        c'16 * 79/64
                        c'16 * 49/32
                        c'16 * 29/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'4.
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #left
                        c'16 * 5/8
                        [
                        c'16 * 43/64
                        c'16 * 51/64
                        c'16 * 65/64
                        c'16 * 85/64
                        c'16 * 25/16
                        ]
                    }
                    \revert TupletNumber.text
                }
            >>

    ..  container:: example

        REGRESSION. ``abjad.new()`` preserves commands:

        >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
        ...     rmakers.force_fraction()
        ... )

        >>> abjad.new(rhythm_maker).commands
        [ForceFractionCommand()]

    Set interpolations' ``written_duration`` to ``1/16`` or less for multiple
    beams.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_exponent", "_interpolations")

    ### INITIALIZER ###

    def __init__(
        self,
        *commands: _commands.Command,
        interpolations: typing.Union[
            _specifiers.Interpolation,
            typing.Sequence[_specifiers.Interpolation],
        ] = None,
        preprocessor: abjad.Expression = None,
        spelling: _specifiers.Spelling = None,
        tag: str = None,
    ) -> None:
        RhythmMaker.__init__(
            self,
            *commands,
            preprocessor=preprocessor,
            spelling=spelling,
            tag=tag,
        )
        if isinstance(interpolations, _specifiers.Interpolation):
            interpolations = (interpolations,)
        if interpolations is not None:
            for interpolation in interpolations:
                if not isinstance(interpolation, _specifiers.Interpolation):
                    raise TypeError(interpolation)
            interpolations = tuple(interpolations)
        self._interpolations = interpolations

    ### PRIVATE METHODS ###

    @staticmethod
    def _fix_rounding_error(selection, total_duration, interpolation):
        selection_duration = abjad.inspect(selection).duration()
        if not selection_duration == total_duration:
            needed_duration = (
                total_duration - abjad.inspect(selection[:-1]).duration()
            )
            multiplier = needed_duration / interpolation.written_duration
            selection[-1].multiplier = multiplier

    def _get_interpolations(self):
        specifiers_ = self.interpolations
        if specifiers_ is None:
            specifiers_ = abjad.CyclicTuple([Interpolation()])
        elif isinstance(specifiers_, _specifiers.Interpolation):
            specifiers_ = abjad.CyclicTuple([specifiers_])
        else:
            specifiers_ = abjad.CyclicTuple(specifiers_)
        string = "divisions_consumed"
        divisions_consumed = self.previous_state.get(string, 0)
        specifiers_ = abjad.sequence(specifiers_).rotate(n=-divisions_consumed)
        specifiers_ = abjad.CyclicTuple(specifiers_)
        return specifiers_

    @staticmethod
    def _interpolate_cosine(y1, y2, mu) -> float:
        """
        Performs cosine interpolation of ``y1`` and ``y2`` with ``mu``
        ``[0, 1]`` normalized.

        ..  container:: example
        
            >>> rmakers.AccelerandoRhythmMaker._interpolate_cosine(
            ...     y1=0,
            ...     y2=1,
            ...     mu=0.5,
            ...     )
            0.49999999999999994

        """
        mu2 = (1 - math.cos(mu * math.pi)) / 2
        return y1 * (1 - mu2) + y2 * mu2

    @staticmethod
    def _interpolate_divide(
        total_duration, start_duration, stop_duration, exponent="cosine"
    ) -> typing.Union[str, typing.List[float]]:
        """
        Divides ``total_duration`` into durations computed from interpolating
        between ``start_duration`` and ``stop_duration``.

        ..  container:: example

            >>> rmakers.AccelerandoRhythmMaker._interpolate_divide(
            ...     total_duration=10,
            ...     start_duration=1,
            ...     stop_duration=1,
            ...     exponent=1,
            ...     )
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
            >>> sum(_)
            10.0

            >>> rmakers.AccelerandoRhythmMaker._interpolate_divide(
            ...     total_duration=10,
            ...     start_duration=5,
            ...     stop_duration=1,
            ...     )
            [4.798..., 2.879..., 1.326..., 0.995...]
            >>> sum(_)
            10.0

        Set ``exponent`` to ``'cosine'`` for cosine interpolation.

        Set ``exponent`` to a numeric value for exponential interpolation with
        ``exponent`` as the exponent.

        Scales resulting durations so that their sum equals ``total_duration``
        exactly.
        """
        if total_duration <= 0:
            message = "Total duration must be positive."
            raise ValueError(message)
        if start_duration <= 0 or stop_duration <= 0:
            message = "Both 'start_duration' and 'stop_duration'"
            message += " must be positive."
            raise ValueError(message)
        if total_duration < (stop_duration + start_duration):
            return "too small"
        durations = []
        total_duration = float(total_duration)
        partial_sum = 0.0
        while partial_sum < total_duration:
            if exponent == "cosine":
                duration = AccelerandoRhythmMaker._interpolate_cosine(
                    start_duration, stop_duration, partial_sum / total_duration
                )
            else:
                duration = AccelerandoRhythmMaker._interpolate_exponential(
                    start_duration,
                    stop_duration,
                    partial_sum / total_duration,
                    exponent,
                )
            durations.append(duration)
            partial_sum += duration
        # scale result to fit total exaclty
        durations = [_ * total_duration / sum(durations) for _ in durations]
        return durations

    @staticmethod
    def _interpolate_divide_multiple(
        total_durations, reference_durations, exponent="cosine"
    ) -> typing.List[float]:
        """
        Interpolates ``reference_durations`` such that the sum of the
        resulting interpolated values equals the given ``total_durations``.

        ..  container:: example

            >>> class_ = rmakers.AccelerandoRhythmMaker
            >>> durations = class_._interpolate_divide_multiple(
            ...     total_durations=[100, 50],
            ...     reference_durations=[20, 10, 20],
            ...     )
            >>> for duration in durations:
            ...     duration
            19.448...
            18.520...
            16.227...
            13.715...
            11.748...
            10.487...
            9.8515...
            9.5130...
            10.421...
            13.073...
            16.991...

        The operation is the same as the interpolate_divide() method
        implemented on this class. But this function takes multiple
        total durations and multiple reference durations at one time.

        Precondition: ``len(totals_durations) == len(reference_durations)-1``.

        Set ``exponent`` to ``cosine`` for cosine interpolation. Set
        ``exponent`` to a number for exponential interpolation.
        """
        assert len(total_durations) == len(reference_durations) - 1
        durations = []
        for i in range(len(total_durations)):
            durations_ = AccelerandoRhythmMaker._interpolate_divide(
                total_durations[i],
                reference_durations[i],
                reference_durations[i + 1],
                exponent,
            )
            for duration_ in durations_:
                assert isinstance(duration_, float)
                durations.append(duration_)
        return durations

    @staticmethod
    def _interpolate_exponential(y1, y2, mu, exponent=1) -> float:
        """
        Interpolates between ``y1`` and ``y2`` at position ``mu``.

        ..  container:: example

            Exponents equal to 1 leave durations unscaled:

            >>> class_ = rmakers.AccelerandoRhythmMaker
            >>> for mu in (0, 0.25, 0.5, 0.75, 1):
            ...     class_._interpolate_exponential(100, 200, mu, exponent=1)
            ...
            100
            125.0
            150.0
            175.0
            200

            Exponents greater than 1 generate ritardandi:

            >>> class_ = rmakers.AccelerandoRhythmMaker
            >>> for mu in (0, 0.25, 0.5, 0.75, 1):
            ...     class_._interpolate_exponential(100, 200, mu, exponent=2)
            ...
            100
            106.25
            125.0
            156.25
            200

            Exponents less than 1 generate accelerandi:

            >>> class_ = rmakers.AccelerandoRhythmMaker
            >>> for mu in (0, 0.25, 0.5, 0.75, 1):
            ...     class_._interpolate_exponential(100, 200, mu, exponent=0.5)
            ...
            100.0
            150.0
            170.71067811865476
            186.60254037844388
            200.0

        """
        result = y1 * (1 - mu ** exponent) + y2 * mu ** exponent
        return result

    @classmethod
    def _make_accelerando(
        class_, total_duration, interpolations, index, *, tag: str = None
    ) -> abjad.Tuplet:
        """
        Makes notes with LilyPond multipliers equal to ``total_duration``.

        Total number of notes not specified: total duration is specified
        instead.

        Selects interpolation specifier at ``index`` in
        ``interpolations``.

        Computes duration multipliers interpolated from interpolation specifier
        start to stop.

        Sets note written durations according to interpolation specifier.
        multipliers.
        """
        total_duration = abjad.Duration(total_duration)
        interpolation = interpolations[index]
        durations = AccelerandoRhythmMaker._interpolate_divide(
            total_duration=total_duration,
            start_duration=interpolation.start_duration,
            stop_duration=interpolation.stop_duration,
        )
        if durations == "too small":
            maker = abjad.NoteMaker(tag=tag)
            notes = list(maker([0], [total_duration]))
            tuplet = abjad.Tuplet((1, 1), notes, tag=tag)
            selection = abjad.select([tuplet])
            return selection
        durations = class_._round_durations(durations, 2 ** 10)
        notes = []
        for i, duration in enumerate(durations):
            written_duration = interpolation.written_duration
            multiplier = duration / written_duration
            note = abjad.Note(
                0, written_duration, multiplier=multiplier, tag=tag
            )
            notes.append(note)
        selection = abjad.select(notes)
        class_._fix_rounding_error(selection, total_duration, interpolation)
        pair = (abjad.inspect(selection).duration(), total_duration)
        tuplet = abjad.Tuplet((1, 1), selection, tag=tag)
        return tuplet

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        tuplets = []
        interpolations = self._get_interpolations()
        for i, division in enumerate(divisions):
            tuplet = self._make_accelerando(
                division, interpolations, i, tag=self.tag
            )
            tuplets.append(tuplet)
        return tuplets

    @staticmethod
    def _round_durations(durations, denominator):
        durations_ = []
        for duration in durations:
            numerator = int(round(duration * denominator))
            duration_ = abjad.Duration(numerator, denominator)
            durations_.append(duration_)
        return durations_

    ### PUBLIC PROPERTIES ###

    @property
    def commands(self) -> typing.List[_commands.Command]:
        r"""
        Gets commands.

        ..  container:: example

            Sets duration bracket with no beams:

            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.duration_bracket(),
            ...     interpolations=rmakers.interpolate(
            ...         (1, 8), (1, 20), (1, 16)
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
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            c'16 * 63/32
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            c'16 * 117/64
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            c'16 * 63/32
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            c'16 * 117/64
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                        }
                        \revert TupletNumber.text
                    }
                >>


        ..  container:: example

            Beams tuplets together without feathering:

            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.beam_groups(abjad.select().tuplets()),
            ...     rmakers.duration_bracket(),
            ...     interpolations=rmakers.interpolate(
            ...         (1, 8), (1, 20), (1, 16)
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
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 2
                            c'16 * 63/32
                            [
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 115/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 91/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 35/32
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 29/32
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 1
                            c'16 * 13/16
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 2
                            c'16 * 117/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 99/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 69/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 13/16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 1
                            c'16 * 47/64
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 2
                            c'16 * 63/32
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 115/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 91/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 35/32
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 29/32
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 1
                            c'16 * 13/16
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 2
                            c'16 * 117/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 99/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 69/64
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 2
                            c'16 * 13/16
                            \set stemLeftBeamCount = 2
                            \set stemRightBeamCount = 0
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                    }
                >>

            Leave feathering turned off here because LilyPond feathers conjoint
            beams poorly.

        ..  container:: example

            Ties across tuplets:

            >>> last_leaf = abjad.select().leaf(-1)
            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.duration_bracket(),
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.feather_beam(),
            ...     interpolations=rmakers.interpolate(
            ...         (1, 8), (1, 20), (1, 16)
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
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ~
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ~
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ~
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                    }
                >>

        ..  container:: example

            Ties across every other tuplet:

            >>> tuplets = abjad.select().tuplets().get([0], 2)
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.duration_bracket(),
            ...     rmakers.tie(tuplets.map(last_leaf)),
            ...     rmakers.feather_beam(),
            ...     interpolations=rmakers.interpolate(
            ...         (1, 8), (1, 20), (1, 16)
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
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ~
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ~
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                    }
                >>

        ..  container:: example

            Forces rests at first and last leaves:

            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.force_rest(abjad.select().leaves().get([0, -1])),
            ...     rmakers.feather_beam(
            ...         beam_rests=True,
            ...         stemlet_length=0.75,
            ...         ),
            ...     rmakers.duration_bracket(),
            ...     interpolations=[
            ...         rmakers.interpolate((1, 8), (1, 20), (1, 16)),
            ...         rmakers.interpolate((1, 20), (1, 8), (1, 16)),
            ...         ],
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
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            \override Staff.Stem.stemlet-length = 0.75
                            r16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            \revert Staff.Stem.stemlet-length
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            \override Staff.Stem.stemlet-length = 0.75
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            \revert Staff.Stem.stemlet-length
                            c'16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            \override Staff.Stem.stemlet-length = 0.75
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            \revert Staff.Stem.stemlet-length
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            \override Staff.Stem.stemlet-length = 0.75
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            \revert Staff.Stem.stemlet-length
                            r16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                    }
                >>
                

        ..  container:: example

            Forces rests in every other tuplet:

            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.force_rest(abjad.select().tuplets().get([1], 2)),
            ...     rmakers.rewrite_rest_filled(),
            ...     rmakers.extract_trivial(),
            ...     rmakers.duration_bracket(),
            ...     rmakers.feather_beam(),
            ...     interpolations=rmakers.interpolate(
            ...         (1, 8), (1, 20), (1, 16)
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
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        r4.
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        r4.
                    }
                >>

        """
        return super().commands

    @property
    def interpolations(
        self
    ) -> typing.Optional[typing.List[_specifiers.Interpolation]]:
        r"""
        Gets interpolations.

        ..  container:: example

            Alternates accelerandi and ritardandi:

            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.feather_beam(),
            ...     rmakers.duration_bracket(),
            ...     interpolations=[
            ...         rmakers.interpolate((1, 8), (1, 20), (1, 16)),
            ...         rmakers.interpolate((1, 20), (1, 8), (1, 16)),
            ...         ],
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
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            c'16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            c'16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                    }
                >>

        ..  container:: example

            Makes a single note in short division:

            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.feather_beam(),
            ...     rmakers.duration_bracket(),
            ...     rmakers.extract_trivial(),
            ...     interpolations=rmakers.interpolate(
            ...         (1, 8), (1, 20), (1, 16)
            ...     ),
            ... )

            >>> divisions = [(5, 8), (3, 8), (1, 8)]
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
                        \time 5/8
                        s1 * 5/8
                        \time 3/8
                        s1 * 3/8
                        \time 1/8
                        s1 * 1/8
                    }
                    \new RhythmicStaff
                    {
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                                ~
                                                c'8
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 61/32
                            [
                            c'16 * 115/64
                            c'16 * 49/32
                            c'16 * 5/4
                            c'16 * 33/32
                            c'16 * 57/64
                            c'16 * 13/16
                            c'16 * 25/32
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        c'8
                    }
                >>

        """
        if self._interpolations is not None:
            return list(self._interpolations)
        return None

    @property
    def state(self) -> abjad.OrderedDict:
        r"""
        Gets state dictionary.

        ..  container:: example

            Consumes 3 divisions:

            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.feather_beam(),
            ...     rmakers.duration_bracket(),
            ...     interpolations=[
            ...         rmakers.interpolate((1, 8), (1, 20), (1, 16)),
            ...         rmakers.interpolate((1, 20), (1, 8), (1, 16)),
            ...     ],
            ... )

            >>> divisions = [(3, 8), (4, 8), (3, 8)]
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
                    }
                    \new RhythmicStaff
                    {
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 3),
                    ('logical_ties_produced', 17),
                    ]
                )

            Advances 3 divisions; then consumes another 3 divisions:

            >>> divisions = [(4, 8), (3, 8), (4, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 6),
                    ('logical_ties_produced', 36),
                    ]
                )

            Advances 6 divisions; then consumes another 3 divisions:

            >>> divisions = [(3, 8), (4, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'2
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup {
                            \scale
                                #'(0.75 . 0.75)
                                \score
                                    {
                                        \new Score
                                        \with
                                        {
                                            \override SpacingSpanner.spacing-increment = #0.5
                                            proportionalNotationDuration = ##f
                                        }
                                        <<
                                            \new RhythmicStaff
                                            \with
                                            {
                                                \remove Time_signature_engraver
                                                \remove Staff_symbol_engraver
                                                \override Stem.direction = #up
                                                \override Stem.length = #5
                                                \override TupletBracket.bracket-visibility = ##t
                                                \override TupletBracket.direction = #up
                                                \override TupletBracket.minimum-length = #4
                                                \override TupletBracket.padding = #1.25
                                                \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                                \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                                \override TupletNumber.font-size = #0
                                                \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                                tupletFullLength = ##t
                                            }
                                            {
                                                c'4.
                                            }
                                        >>
                                        \layout {
                                            indent = #0
                                            ragged-right = ##t
                                        }
                                    }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 9),
                    ('logical_ties_produced', 53),
                    ]
                )

        """
        return super().state

    @property
    def tag(self) -> typing.Optional[str]:
        r"""
        Gets tag.

        ..  container:: example

            Tags LilyPond output:

            >>> rhythm_maker = rmakers.AccelerandoRhythmMaker(
            ...     rmakers.feather_beam(),
            ...     rmakers.duration_bracket(),
            ...     interpolations=rmakers.interpolate(
            ...         (1, 8), (1, 20), (1, 16)
            ...     ),
            ...     tag='ACCELERANDO_RHYTHM_MAKER',
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'2
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {          %! ACCELERANDO_RHYTHM_MAKER
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32      %! ACCELERANDO_RHYTHM_MAKER
                        [                 %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 115/64     %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 91/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 35/32      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 29/32      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16      %! ACCELERANDO_RHYTHM_MAKER
                        ]                 %! ACCELERANDO_RHYTHM_MAKER
                    }                     %! ACCELERANDO_RHYTHM_MAKER
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'4.
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {          %! ACCELERANDO_RHYTHM_MAKER
                        \once \override Beam.grow-direction = #right
                        c'16 * 117/64     %! ACCELERANDO_RHYTHM_MAKER
                        [                 %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 99/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 69/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 47/64      %! ACCELERANDO_RHYTHM_MAKER
                        ]                 %! ACCELERANDO_RHYTHM_MAKER
                    }                     %! ACCELERANDO_RHYTHM_MAKER
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'2
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {          %! ACCELERANDO_RHYTHM_MAKER
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32      %! ACCELERANDO_RHYTHM_MAKER
                        [                 %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 115/64     %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 91/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 35/32      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 29/32      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16      %! ACCELERANDO_RHYTHM_MAKER
                        ]                 %! ACCELERANDO_RHYTHM_MAKER
                    }                     %! ACCELERANDO_RHYTHM_MAKER
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup {
                        \scale
                            #'(0.75 . 0.75)
                            \score
                                {
                                    \new Score
                                    \with
                                    {
                                        \override SpacingSpanner.spacing-increment = #0.5
                                        proportionalNotationDuration = ##f
                                    }
                                    <<
                                        \new RhythmicStaff
                                        \with
                                        {
                                            \remove Time_signature_engraver
                                            \remove Staff_symbol_engraver
                                            \override Stem.direction = #up
                                            \override Stem.length = #5
                                            \override TupletBracket.bracket-visibility = ##t
                                            \override TupletBracket.direction = #up
                                            \override TupletBracket.minimum-length = #4
                                            \override TupletBracket.padding = #1.25
                                            \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                            \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                            \override TupletNumber.font-size = #0
                                            \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                            tupletFullLength = ##t
                                        }
                                        {
                                            c'4.
                                        }
                                    >>
                                    \layout {
                                        indent = #0
                                        ragged-right = ##t
                                    }
                                }
                        }
                    \times 1/1 {          %! ACCELERANDO_RHYTHM_MAKER
                        \once \override Beam.grow-direction = #right
                        c'16 * 117/64     %! ACCELERANDO_RHYTHM_MAKER
                        [                 %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 99/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 69/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 47/64      %! ACCELERANDO_RHYTHM_MAKER
                        ]                 %! ACCELERANDO_RHYTHM_MAKER
                    }                     %! ACCELERANDO_RHYTHM_MAKER
                    \revert TupletNumber.text
                }
            >>

        """
        return super().tag
