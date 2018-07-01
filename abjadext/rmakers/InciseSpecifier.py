import abjad
import typing


class InciseSpecifier(abjad.AbjadValueObject):
    """
    Incise specifier.

    ..  container:: example

        Specifies one sixteenth rest cut out of the beginning of every
        division:

        >>> specifier = abjadext.rmakers.InciseSpecifier(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     talea_denominator=16,
        ...     )

    ..  container:: example

        Specifies sixteenth rests cut out of the beginning and end of each
        division:

        >>> specifier = abjadext.rmakers.InciseSpecifier(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     suffix_talea=[-1],
        ...     suffix_counts=[1],
        ...     talea_denominator=16,
        ...     )

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Specifiers'

    __slots__ = (
        '_body_ratio',
        '_fill_with_notes',
        '_outer_divisions_only',
        '_prefix_counts',
        '_prefix_talea',
        '_suffix_counts',
        '_suffix_talea',
        '_talea_denominator',
        )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        prefix_talea: typing.Sequence[int] = None,
        prefix_counts: typing.Sequence[int] = None,
        suffix_talea: typing.Sequence[int] = None,
        suffix_counts: typing.Sequence[int] = None,
        talea_denominator: int = None,
        body_ratio: abjad.Ratio = None,
        fill_with_notes: bool = True,
        outer_divisions_only: bool = None,
        ) -> None:
        prefix_talea = prefix_talea or ()
        prefix_talea = tuple(prefix_talea)
        assert self._is_integer_tuple(prefix_talea)
        self._prefix_talea: typing.Tuple[int, ...] = prefix_talea
        prefix_counts = prefix_counts or ()
        prefix_counts = tuple(prefix_counts)
        assert self._is_length_tuple(prefix_counts)
        self._prefix_counts: typing.Tuple[int, ...] = prefix_counts
        if prefix_talea:
            assert prefix_counts
        suffix_talea = suffix_talea or ()
        suffix_talea = tuple(suffix_talea)
        assert self._is_integer_tuple(suffix_talea)
        if suffix_talea is not None:
            assert isinstance(suffix_talea, tuple)
        self._suffix_talea: typing.Tuple[int, ...] = suffix_talea
        assert self._is_length_tuple(suffix_counts)
        suffix_counts = suffix_counts or ()
        suffix_counts = tuple(suffix_counts)
        if suffix_counts is not None:
            assert isinstance(suffix_counts, tuple)
        self._suffix_counts: typing.Tuple[int, ...] = suffix_counts
        if suffix_talea:
            assert suffix_counts
        if talea_denominator is not None:
            if not abjad.mathtools.is_nonnegative_integer_power_of_two(
                talea_denominator):
                message = 'talea denominator {!r} must be nonnegative'
                message += ' integer power of 2.'
                message = message.format(talea_denominator)
                raise Exception(message)
        self._talea_denominator: typing.Optional[int] = talea_denominator
        if prefix_talea or suffix_talea:
            assert talea_denominator is not None
        if body_ratio is not None:
            body_ratio = abjad.Ratio(body_ratio)
        self._body_ratio: typing.Optional[abjad.Ratio] = body_ratio
        if fill_with_notes is not None:
            fill_with_notes = bool(fill_with_notes)
        self._fill_with_notes: typing.Optional[bool] = fill_with_notes
        if outer_divisions_only is not None:
            outer_divisions_only = bool(outer_divisions_only)
        self._outer_divisions_only: typing.Optional[bool] = outer_divisions_only

    ### SPECIAL METHODS ###

    def __format__(self, format_specification='') -> str:
        """
        Formats incise specifier.

        ..  container:: example

            Formats incise specifier:

            >>> specifier = abjadext.rmakers.InciseSpecifier(
            ...     prefix_talea=[-1],
            ...     prefix_counts=[1],
            ...     talea_denominator=16,
            ...     )

            >>> abjad.f(specifier)
            abjadext.rmakers.InciseSpecifier(
                prefix_talea=[-1],
                prefix_counts=[1],
                suffix_talea=(),
                suffix_counts=(),
                talea_denominator=16,
                fill_with_notes=True,
                )

        ..  container:: example

            Formats incise specifier:

            >>> specifier = abjadext.rmakers.InciseSpecifier(
            ...     prefix_talea=[-1],
            ...     prefix_counts=[0, 1],
            ...     suffix_talea=[-1],
            ...     suffix_counts=[1],
            ...     talea_denominator=16,
            ...     )

            >>> abjad.f(specifier)
            abjadext.rmakers.InciseSpecifier(
                prefix_talea=[-1],
                prefix_counts=[0, 1],
                suffix_talea=[-1],
                suffix_counts=[1],
                talea_denominator=16,
                fill_with_notes=True,
                )

        """
        return super(InciseSpecifier, self).__format__(
            format_specification=format_specification,
            )

    ### PRIVATE METHODS ###

    @staticmethod
    def _is_integer_tuple(argument):
        if argument is None:
            return True
        if all(isinstance(x, int) for x in argument):
            return True
        return False

    @staticmethod
    def _is_length_tuple(argument):
        if argument is None:
            return True
        if abjad.mathtools.all_are_nonnegative_integer_equivalent_numbers(
            argument):
            if isinstance(argument, (tuple, list)):
                return True
        return False

    @staticmethod
    def _reverse_tuple(argument):
        if argument is not None:
            return tuple(reversed(argument))

    ### PUBLIC PROPERTIES ###

    @property
    def body_ratio(self) -> typing.Optional[abjad.Ratio]:
        r"""
        Gets body ratio.

        ..  container:: example

            Divides middle part of every division ``1:1``:

            >>> specifier = abjadext.rmakers.InciseSpecifier(
            ...     prefix_talea=[-1],
            ...     prefix_counts=[0, 1],
            ...     suffix_talea=[-1],
            ...     suffix_counts=[1],
            ...     talea_denominator=16,
            ...     body_ratio=abjad.Ratio((1, 1)),
            ...     )
            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=specifier,
            ...     )

            >>> divisions = 4 * [(5, 16)]
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
                        \time 5/16
                        c'8
                        [
                        c'8
                        ]
                        r16
                    }   % measure
                    {   % measure
                        r16
                        c'16.
                        [
                        c'16.
                        ]
                        r16
                    }   % measure
                    {   % measure
                        c'8
                        [
                        c'8
                        ]
                        r16
                    }   % measure
                    {   % measure
                        r16
                        c'16.
                        [
                        c'16.
                        ]
                        r16
                    }   % measure
                }

        """
        return self._body_ratio

    @property
    def fill_with_notes(self) -> typing.Optional[bool]:
        """
        Is true when rhythm-maker should fill divisions with notes.

        ..  todo:: Add examples.

        """
        return self._fill_with_notes

    @property
    def outer_divisions_only(self) -> typing.Optional[bool]:
        """
        Is true when rhythm-maker should incise outer divisions only.
        Is false when rhythm-maker should incise all divisions.

        ..  todo:: Add examples.

        """
        return self._outer_divisions_only

    @property
    def prefix_counts(self) -> typing.Optional[typing.List[int]]:
        """
        Gets prefix counts.

        ..  todo:: Add examples.

        """
        if self._prefix_counts:
            return list(self._prefix_counts)
        return None

    @property
    def prefix_talea(self) -> typing.Optional[typing.List[int]]:
        """
        Gets prefix talea.

        ..  todo:: Add examples.

        """
        if self._prefix_talea:
            return list(self._prefix_talea)
        return None

    @property
    def suffix_counts(self) -> typing.Optional[typing.List[int]]:
        """
        Gets suffix counts.

        ..  todo:: Add examples.

        """
        if self._suffix_counts:
            return list(self._suffix_counts)
        return None

    @property
    def suffix_talea(self) -> typing.Optional[typing.List[int]]:
        """
        Gets suffix talea.

        ..  todo:: Add examples.

        """
        if self._suffix_talea:
            return list(self._suffix_talea)
        return None

    @property
    def talea_denominator(self) -> typing.Optional[int]:
        """
        Gets talea denominator.

        ..  todo:: Add examples.

        """
        return self._talea_denominator
