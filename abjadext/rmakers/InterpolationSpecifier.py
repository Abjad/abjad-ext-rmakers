import abjad
import typing


class InterpolationSpecifier(abjad.AbjadValueObject):
    """
    Interpolation specifier.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Specifiers'

    __slots__ = (
        '_start_duration',
        '_stop_duration',
        '_written_duration',
        )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        start_duration: typing.Tuple[int, int] = (1, 8),
        stop_duration: typing.Tuple[int, int] = (1, 16),
        written_duration: typing.Tuple[int, int] = (1, 16),
        ) -> None:
        self._start_duration = abjad.Duration(start_duration)
        self._stop_duration = abjad.Duration(stop_duration)
        self._written_duration = abjad.Duration(written_duration)

    ### PUBLIC METHODS ###

    def reverse(self) -> 'InterpolationSpecifier':
        """
        Swaps start duration and stop duration of interpolation specifier.

        ..  container:: example

            Changes accelerando specifier to ritardando specifier:

            >>> specifier = abjadext.rmakers.InterpolationSpecifier(
            ...     start_duration=(1, 4),
            ...     stop_duration=(1, 16),
            ...     written_duration=(1, 16),
            ...     )
            >>> specifier = specifier.reverse()
            >>> abjad.f(specifier)
            abjadext.rmakers.InterpolationSpecifier(
                start_duration=abjad.Duration(1, 16),
                stop_duration=abjad.Duration(1, 4),
                written_duration=abjad.Duration(1, 16),
                )

        ..  container:: example

            Changes ritardando specifier to accelerando specifier:

            >>> specifier = abjadext.rmakers.InterpolationSpecifier(
            ...     start_duration=(1, 16),
            ...     stop_duration=(1, 4),
            ...     written_duration=(1, 16),
            ...     )
            >>> specifier = specifier.reverse()
            >>> abjad.f(specifier)
            abjadext.rmakers.InterpolationSpecifier(
                start_duration=abjad.Duration(1, 4),
                stop_duration=abjad.Duration(1, 16),
                written_duration=abjad.Duration(1, 16),
                )

        """
        return type(self)(
            start_duration=self.stop_duration,
            stop_duration=self.start_duration,
            written_duration=self.written_duration,
            )

    ### PUBLIC PROPERTIES ###

    @property
    def start_duration(self) -> abjad.Duration:
        """
        Gets start duration.
        """
        return self._start_duration

    @property
    def stop_duration(self) -> abjad.Duration:
        """
        Gets stop duration.
        """
        return self._stop_duration

    @property
    def written_duration(self) -> abjad.Duration:
        """
        Gets written duration.
        """
        return self._written_duration
