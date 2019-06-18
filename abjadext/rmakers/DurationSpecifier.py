import abjad
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier


class DurationSpecifier(object):
    """
    Duration specifier.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = (
        "_forbidden_note_duration",
        "_forbidden_rest_duration",
        "_increase_monotonic",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        forbidden_note_duration: abjad.DurationTyping = None,
        forbidden_rest_duration: abjad.DurationTyping = None,
        increase_monotonic: bool = None,
    ) -> None:
        if forbidden_note_duration is None:
            forbidden_note_duration_ = None
        else:
            forbidden_note_duration_ = abjad.Duration(forbidden_note_duration)
        self._forbidden_note_duration = forbidden_note_duration_
        if forbidden_rest_duration is None:
            forbidden_rest_duration_ = None
        else:
            forbidden_rest_duration_ = abjad.Duration(forbidden_rest_duration)
        self._forbidden_rest_duration = forbidden_rest_duration_
        if increase_monotonic is not None:
            increase_monotonic = bool(increase_monotonic)
        self._increase_monotonic = increase_monotonic

    ### SPECIAL METHODS ###

    def __format__(self, format_specification="") -> str:
        """
        Formats duration specifier.

        ..  container:: example

            >>> specifier = abjadext.rmakers.DurationSpecifier()
            >>> abjad.f(specifier)
            abjadext.rmakers.DurationSpecifier()

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> abjadext.rmakers.DurationSpecifier()
            DurationSpecifier()

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC PROPERTIES ###

    @property
    def increase_monotonic(self) -> typing.Optional[bool]:
        r"""
        Is true when all durations spell as a tied series of monotonically
        increasing values.

        ..  container:: example

            Decreases monotically:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         increase_monotonic=False,
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
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
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        [
                        c'8
                        ~
                        ]
                        c'8.
                        c'4
                        ~
                        c'16
                        c'4
                    }
                >>

        ..  container:: example

            Increases monotically:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         increase_monotonic=True,
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
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
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'8
                        ~
                        c'8.
                        [
                        c'16
                        ~
                        ]
                        c'4
                        c'4
                    }
                >>

        """
        return self._increase_monotonic

    @property
    def forbidden_note_duration(self) -> typing.Optional[abjad.Duration]:
        r"""
        Gets forbidden note duration.

        ..  container:: example

            Forbids note durations equal to ``1/4`` or greater:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_note_duration=(1, 4),
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, 1, 4, -4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
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
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'8
                        ~
                        c'8
                        ]
                        r4
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'8
                        ~
                        c'8
                        ]
                        r4
                    }
                >>

        """
        return self._forbidden_note_duration

    @property
    def forbidden_rest_duration(self) -> typing.Optional[abjad.Duration]:
        r"""
        Gets forbidden rest duration.

        ..  container:: example

            Forbids rest durations equal to ``1/4`` or greater:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_rest_duration=(1, 4),
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, 1, 4, -4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
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
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        c'4
                        r8
                        r8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        c'4
                        r8
                        r8
                    }
                >>

        """
        return self._forbidden_rest_duration
