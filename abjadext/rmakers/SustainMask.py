import abjad
import inspect
import typing


class SustainMask(abjad.AbjadValueObject):
    r"""
    Sustain mask.

    ..  container:: example

        >>> mask = abjadext.rmakers.SustainMask(
        ...     pattern=abjad.index([0, 1, 7], 16),
        ...     )

        >>> abjad.f(mask)
        abjadext.rmakers.SustainMask(
            pattern=abjad.index([0, 1, 7], period=16),
            )

    ..  container:: example

        With composite pattern:

        >>> pattern_1 = abjad.index_all()
        >>> pattern_2 = abjad.index_first(1)
        >>> pattern_3 = abjad.index_last(1)
        >>> pattern = pattern_1 ^ pattern_2 ^ pattern_3
        >>> mask = abjadext.rmakers.SustainMask(pattern=pattern)

        >>> abjad.f(mask)
        abjadext.rmakers.SustainMask(
            pattern=abjad.Pattern(
                operator='xor',
                patterns=(
                    abjad.index_all(),
                    abjad.index_first(1),
                    abjad.index_last(1),
                    ),
                ),
            )

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     division_masks=[
        ...         abjadext.rmakers.silence([0], 1),
        ...         mask,
        ...         ],
        ...     )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
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
                    \time 7/16
                    r4..
                }   % measure
                {   % measure
                    \time 3/8
                    c'4.
                }   % measure
                {   % measure
                    \time 7/16
                    c'4..
                }   % measure
                {   % measure
                    \time 3/8
                    r4.
                }   % measure
            }

    ..  container:: example

        Works inverted composite pattern:

        >>> pattern_1 = abjad.index_all()
        >>> pattern_2 = abjad.index_first(1)
        >>> pattern_3 = abjad.index_last(1)
        >>> pattern = pattern_1 ^ pattern_2 ^ pattern_3
        >>> pattern = ~pattern
        >>> mask = abjadext.rmakers.SustainMask(pattern=pattern)

        >>> abjad.f(mask)
        abjadext.rmakers.SustainMask(
            pattern=abjad.Pattern(
                inverted=True,
                operator='xor',
                patterns=(
                    abjad.index_all(),
                    abjad.index_first(1),
                    abjad.index_last(1),
                    ),
                ),
            )

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     division_masks=[
        ...         abjadext.rmakers.silence([0], 1),
        ...         mask,
        ...         ],
        ...     )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
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
                    \time 7/16
                    c'4..
                }   % measure
                {   % measure
                    \time 3/8
                    r4.
                }   % measure
                {   % measure
                    \time 7/16
                    r4..
                }   % measure
                {   % measure
                    \time 3/8
                    c'4.
                }   % measure
            }

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Masks'

    __slots__ = (
        '_pattern',
        '_template',
        )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        pattern: abjad.Pattern = None,
        *,
        template: str = None,
        ) -> None:
        if pattern is None:
            pattern = abjad.index_all()
        assert isinstance(pattern, abjad.Pattern), repr(pattern)
        self._pattern = pattern
        self._template = template

    ### SPECIAL METHODS ###

    def __invert__(self) -> 'SustainMask':
        """
        Inverts pattern.
        """
        pattern = ~self.pattern
        inverted = pattern.inverted or None
        return SustainMask.sustain(pattern.indices, pattern.period, inverted)

    ### PRIVATE METHODS ###

    def _get_format_specification(self):
        if self.template is None:
            return super(SustainMask, self)._get_format_specification()
        return abjad.FormatSpecification(
            client=self,
            repr_is_indented=False,
            storage_format_is_indented=False,
            storage_format_args_values=[self.template],
            storage_format_forced_override=self.template,
            storage_format_kwargs_names=(),
            )

    @staticmethod
    def _get_template(frame):
        try:
            frame_info = inspect.getframeinfo(frame)
            function_name = frame_info.function
            arguments = abjad.Expression._wrap_arguments(
                frame,
                static_class=SustainMask,
                )
            template = f'abjadext.rmakers.{function_name}({arguments})'
        finally:
            del frame
        return template

    ### PUBLIC PROPERTIES ###

    @property
    def pattern(self) -> abjad.Pattern:
        """
        Gets pattern.
        """
        return self._pattern

    @property
    def template(self) -> typing.Optional[str]:
        """
        Gets template.
        """
        return self._template

    ### PUBLIC METHODS ###

    @staticmethod
    def sustain(
        indices: typing.Sequence[int],
        period: int = None,
        inverted: bool = None,
        ) -> 'SustainMask':
        r"""
        Makes sustain mask that matches ``indices``.

        ..  container:: example

            Sustains divisions 1 and 2:

            >>> mask = abjadext.rmakers.sustain([1, 2])

            >>> mask
            abjadext.rmakers.sustain([1, 2])

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     division_masks=[
            ...         abjadext.rmakers.silence([0], 1),
            ...         mask,
            ...         ],
            ...     )
            >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
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
                        \time 7/16
                        r4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'4.
                    }   % measure
                    {   % measure
                        \time 7/16
                        c'4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        r4.
                    }   % measure
                }

        ..  container:: example

            Sustains divisions -1 and -2:

            >>> mask = abjadext.rmakers.sustain([-1, -2])

            >>> mask
            abjadext.rmakers.sustain([-1, -2])

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     division_masks=[
            ...         abjadext.rmakers.silence([0], 1),
            ...         mask,
            ...         ],
            ...     )
            >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
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
                        \time 7/16
                        r4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        r4.
                    }   % measure
                    {   % measure
                        \time 7/16
                        c'4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'4.
                    }   % measure
                }


        Returns sustain mask.
        """
        pattern = abjad.index(indices, period=period, inverted=inverted)
        template = SustainMask._get_template(inspect.currentframe())
        return SustainMask(pattern=pattern, template=template)
