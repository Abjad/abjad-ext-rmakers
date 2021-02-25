import typing

import abjad

ClassTyping = typing.Union[int, type]


### CLASSES ###


class Incise:
    """
    Incise specifier.

    ..  container:: example

        Specifies one sixteenth rest cut out of the beginning of every
        division:

        >>> specifier = rmakers.Incise(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     talea_denominator=16,
        ... )

    ..  container:: example

        Specifies sixteenth rests cut out of the beginning and end of each
        division:

        >>> specifier = rmakers.Incise(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     suffix_talea=[-1],
        ...     suffix_counts=[1],
        ...     talea_denominator=16,
        ... )

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = (
        "_body_ratio",
        "_fill_with_rests",
        "_outer_divisions_only",
        "_prefix_counts",
        "_prefix_talea",
        "_suffix_counts",
        "_suffix_talea",
        "_talea_denominator",
    )

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        body_ratio: abjad.RatioTyping = None,
        fill_with_rests: bool = None,
        outer_divisions_only: bool = None,
        prefix_counts: typing.Sequence[int] = None,
        prefix_talea: typing.Sequence[int] = None,
        suffix_counts: typing.Sequence[int] = None,
        suffix_talea: typing.Sequence[int] = None,
        talea_denominator: int = None,
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
            if not abjad.math.is_nonnegative_integer_power_of_two(talea_denominator):
                message = f"talea denominator {talea_denominator!r} must be nonnegative"
                message += " integer power of 2."
                raise Exception(message)
        self._talea_denominator: typing.Optional[int] = talea_denominator
        if prefix_talea or suffix_talea:
            assert talea_denominator is not None
        if body_ratio is not None:
            body_ratio = abjad.Ratio(body_ratio)
        self._body_ratio: typing.Optional[abjad.Ratio] = body_ratio
        if fill_with_rests is not None:
            fill_with_rests = bool(fill_with_rests)
        self._fill_with_rests: typing.Optional[bool] = fill_with_rests
        if outer_divisions_only is not None:
            outer_divisions_only = bool(outer_divisions_only)
        self._outer_divisions_only: typing.Optional[bool] = outer_divisions_only

    ### SPECIAL METHODS ###

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

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
        if abjad.math.all_are_nonnegative_integer_equivalent_numbers(argument):
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

            >>> stack = rmakers.stack(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[0, 1],
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=16,
            ...         body_ratio=abjad.Ratio((1, 1)),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = 4 * [(5, 16)]
            >>> selections = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        c'8
                        [
                        c'8
                        ]
                        r16
                        r16
                        c'16.
                        [
                        c'16.
                        ]
                        r16
                        c'8
                        [
                        c'8
                        ]
                        r16
                        r16
                        c'16.
                        [
                        c'16.
                        ]
                        r16
                    }
                >>

        """
        return self._body_ratio

    @property
    def fill_with_rests(self) -> typing.Optional[bool]:
        """
        Is true when rhythm-maker fills divisions with rests instead of notes.

        ..  todo:: Add examples.

        """
        return self._fill_with_rests

    @property
    def outer_divisions_only(self) -> typing.Optional[bool]:
        """
        Is true when rhythm-maker incises outer divisions only.
        Is false when rhythm-maker incises all divisions.

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


class Interpolation:
    """
    Interpolation specifier.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = ("_start_duration", "_stop_duration", "_written_duration")

    ### INITIALIZER ###

    def __init__(
        self,
        start_duration: typing.Tuple[int, int] = (1, 8),
        stop_duration: typing.Tuple[int, int] = (1, 16),
        written_duration: typing.Tuple[int, int] = (1, 16),
    ) -> None:
        self._start_duration = abjad.Duration(start_duration)
        self._stop_duration = abjad.Duration(stop_duration)
        self._written_duration = abjad.Duration(written_duration)

    ### SPECIAL METHODS ###

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.

        ..  container:: example

            >>> rmakers.Interpolation(
            ...     start_duration=(1, 4),
            ...     stop_duration=(1, 16),
            ...     written_duration=(1, 16),
            ... )
            Interpolation(start_duration=Duration(1, 4), stop_duration=Duration(1, 16), written_duration=Duration(1, 16))

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC METHODS ###

    def reverse(self) -> "Interpolation":
        """
        Swaps start duration and stop duration of interpolation specifier.

        ..  container:: example

            Changes accelerando specifier to ritardando specifier:

            >>> specifier = rmakers.Interpolation(
            ...     start_duration=(1, 4),
            ...     stop_duration=(1, 16),
            ...     written_duration=(1, 16),
            ... )
            >>> specifier = specifier.reverse()
            >>> string = abjad.storage(specifier)
            >>> print(string)
            rmakers.Interpolation(
                start_duration=abjad.Duration(1, 16),
                stop_duration=abjad.Duration(1, 4),
                written_duration=abjad.Duration(1, 16),
                )

        ..  container:: example

            Changes ritardando specifier to accelerando specifier:

            >>> specifier = rmakers.Interpolation(
            ...     start_duration=(1, 16),
            ...     stop_duration=(1, 4),
            ...     written_duration=(1, 16),
            ... )
            >>> specifier = specifier.reverse()
            >>> string = abjad.storage(specifier)
            >>> print(string)
            rmakers.Interpolation(
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


class Spelling:
    """
    Duration spelling specifier.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = (
        "_forbidden_note_duration",
        "_forbidden_rest_duration",
        "_increase_monotonic",
    )

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

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> rmakers.Spelling()
            Spelling()

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

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [5],
            ...         16,
            ...         spelling=rmakers.Spelling(increase_monotonic=False),
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 4), (3, 4)]
            >>> selections = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [5],
            ...         16,
            ...         spelling=rmakers.Spelling(increase_monotonic=True),
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 4), (3, 4)]
            >>> selections = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [1, 1, 1, 1, 4, -4],
            ...         16,
            ...         spelling=rmakers.Spelling(forbidden_note_duration=(1, 4)),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 4), (3, 4)]
            >>> selections = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [1, 1, 1, 1, 4, -4],
            ...         16,
            ...         spelling=rmakers.Spelling(forbidden_rest_duration=(1, 4)),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 4), (3, 4)]
            >>> selections = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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


class Talea:
    """
    Talea specifier.

    ..  container:: example

        >>> talea = rmakers.Talea(
        ...     [2, 1, 3, 2, 4, 1, 1],
        ...     16,
        ...     preamble=[1, 1, 1, 1],
        ... )

        >>> string = abjad.storage(talea)
        >>> print(string)
        rmakers.Talea(
            [2, 1, 3, 2, 4, 1, 1],
            16,
            preamble=[1, 1, 1, 1],
            )

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = ("_counts", "_end_counts", "_denominator", "_preamble")

    ### INITIALIZER ###

    def __init__(
        self,
        counts,
        denominator,
        *,
        end_counts: abjad.IntegerSequence = None,
        preamble: abjad.IntegerSequence = None,
    ) -> None:
        for count in counts:
            assert isinstance(count, int) or count in "+-", repr(count)
        self._counts = counts
        if not abjad.math.is_nonnegative_integer_power_of_two(denominator):
            message = f"denominator {denominator} must be integer power of 2."
            raise Exception(message)
        self._denominator = denominator
        end_counts_ = None
        if end_counts is not None:
            assert all(isinstance(_, int) for _ in end_counts)
            end_counts_ = tuple(end_counts)
        self._end_counts = end_counts_
        if preamble is not None:
            assert all(isinstance(_, int) for _ in preamble), repr(preamble)
        self._preamble = preamble

    ### SPECIAL METHODS ###

    def __contains__(self, argument: int) -> bool:
        """
        Is true when talea contains ``argument``.

        ..  container:: example

            With preamble:

            >>> talea = rmakers.Talea(
            ...     [10],
            ...     16,
            ...     preamble=[1, -1, 1],
            ...     )

            >>> for i in range(1, 23 + 1):
            ...     i, i in talea
            ...
            (1, True)
            (2, True)
            (3, True)
            (4, False)
            (5, False)
            (6, False)
            (7, False)
            (8, False)
            (9, False)
            (10, False)
            (11, False)
            (12, False)
            (13, True)
            (14, False)
            (15, False)
            (16, False)
            (17, False)
            (18, False)
            (19, False)
            (20, False)
            (21, False)
            (22, False)
            (23, True)

        """
        assert isinstance(argument, int), repr(argument)
        assert 0 < argument, repr(argument)
        if self.preamble:
            preamble = abjad.Sequence([abs(_) for _ in self.preamble])
            cumulative = abjad.math.cumulative_sums(preamble)[1:]
            if argument in cumulative:
                return True
            preamble_weight = preamble.weight()
        else:
            preamble_weight = 0
        if self.counts is not None:
            counts = [abs(_) for _ in self.counts]
        else:
            counts = []
        cumulative = abjad.math.cumulative_sums(counts)[:-1]
        argument -= preamble_weight
        argument %= self.period
        return argument in cumulative

    def __eq__(self, argument) -> bool:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __getitem__(
        self, argument
    ) -> typing.Union[abjad.NonreducedFraction, typing.List[abjad.NonreducedFraction]]:
        """
        Gets item or slice identified by ``argument``.

        ..  container:: example

            Gets item at index:

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> talea[0]
            NonreducedFraction(1, 16)

            >>> talea[1]
            NonreducedFraction(1, 16)

        ..  container:: example

            Gets items in slice:

            >>> for duration in talea[:6]:
            ...     duration
            ...
            NonreducedFraction(1, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(2, 16)
            NonreducedFraction(1, 16)

            >>> for duration in talea[2:8]:
            ...     duration
            ...
            NonreducedFraction(1, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(2, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(3, 16)
            NonreducedFraction(2, 16)

        """
        if self.preamble:
            preamble = self.preamble
        else:
            preamble = []
        if self.counts:
            counts = self.counts
        else:
            counts = []
        counts_ = abjad.CyclicTuple(preamble + counts)
        if isinstance(argument, int):
            count = counts_.__getitem__(argument)
            return abjad.NonreducedFraction(count, self.denominator)
        elif isinstance(argument, slice):
            counts_ = counts_.__getitem__(argument)
            result = [
                abjad.NonreducedFraction(count, self.denominator) for count in counts_
            ]
            return result
        raise ValueError(argument)

    def __hash__(self) -> int:
        """
        Delegates to storage format manager.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __iter__(self) -> typing.Generator:
        """
        Iterates talea.

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> for duration in talea:
            ...     duration
            ...
            Duration(1, 16)
            Duration(1, 16)
            Duration(1, 16)
            Duration(1, 16)
            Duration(1, 8)
            Duration(1, 16)
            Duration(3, 16)
            Duration(1, 8)
            Duration(1, 4)
            Duration(1, 16)
            Duration(1, 16)

        """
        for count in self.preamble or []:
            duration = abjad.Duration(count, self.denominator)
            yield duration
        for count in self.counts or []:
            duration = abjad.Duration(count, self.denominator)
            yield duration

    def __len__(self) -> int:
        """
        Gets length.

        ..  container:: example

            >>> len(rmakers.Talea([2, 1, 3, 2, 4, 1, 1], 16))
            7

        Defined equal to length of counts.
        """
        return len(self.counts or [])

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _get_format_specification(self):
        return abjad.FormatSpecification(client=self)

    ### PUBLIC PROPERTIES ###

    @property
    def counts(self):
        """
        Gets counts.

        ..  container:: example

            >>> rmakers.Talea([2, 1, 3, 2, 4, 1, 1], 16).counts
            [2, 1, 3, 2, 4, 1, 1]

        """
        if self._counts:
            return list(self._counts)
        else:
            return None

    @property
    def denominator(self) -> int:
        """
        Gets denominator.

        ..  container:: example

            >>> rmakers.Talea([2, 1, 3, 2, 4, 1, 1], 16).denominator
            16

        Set to nonnegative integer power of two.

        Defaults to 16.
        """
        return self._denominator

    @property
    def end_counts(self) -> typing.Optional[typing.List[int]]:
        """
        Gets counts.

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [3, 4],
            ...     16,
            ...     end_counts=[1, 1],
            ... )

            >>> talea.end_counts
            [1, 1]

        """
        if self._end_counts:
            return list(self._end_counts)
        else:
            return None

    @property
    def period(self) -> int:
        """
        Gets period of talea.

        ..  container:: example

            Equal to weight of counts:

            >>> rmakers.Talea([1, 2, 3, 4], 16).period
            10

            Rests make no difference:

            >>> rmakers.Talea([1, 2, -3, 4], 16).period
            10

            Denominator makes no difference:

            >>> rmakers.Talea([1, 2, -3, 4], 32).period
            10

            Preamble makes no difference:

            >>> talea = rmakers.Talea(
            ...     [1, 2, -3, 4],
            ...     32,
            ...     preamble=[1, 1, 1],
            ... )

            >>> talea.period
            10

        """
        return abjad.Sequence(self.counts).weight()

    @property
    def preamble(self) -> typing.Optional[typing.List[int]]:
        """
        Gets preamble.

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> talea.preamble
            [1, 1, 1, 1]

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [16, -4, 16],
            ...     16,
            ...     preamble=[1],
            ... )

            >>> for i, duration in enumerate(talea):
            ...     duration
            ...
            Duration(1, 16)
            Duration(1, 1)
            Duration(-1, 4)
            Duration(1, 1)

        """
        if self._preamble:
            return list(self._preamble)
        else:
            return None

    ### PUBLIC METHODS ###

    def advance(self, weight: int) -> "Talea":
        """
        Advances talea by ``weight``.

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> string = abjad.storage(talea.advance(0))
            >>> print(string)
            rmakers.Talea(
                [2, 1, 3, 2, 4, 1, 1],
                16,
                preamble=[1, 1, 1, 1],
                )

            >>> string = abjad.storage(talea.advance(1))
            >>> print(string)
            rmakers.Talea(
                [2, 1, 3, 2, 4, 1, 1],
                16,
                preamble=[1, 1, 1],
                )

            >>> string = abjad.storage(talea.advance(2))
            >>> print(string)
            rmakers.Talea(
                [2, 1, 3, 2, 4, 1, 1],
                16,
                preamble=[1, 1],
                )

            >>> string = abjad.storage(talea.advance(3))
            >>> print(string)
            rmakers.Talea(
                [2, 1, 3, 2, 4, 1, 1],
                16,
                preamble=[1],
                )

            >>> string = abjad.storage(talea.advance(4))
            >>> print(string)
            rmakers.Talea(
                [2, 1, 3, 2, 4, 1, 1],
                16
                )

            >>> string = abjad.storage(talea.advance(5))
            >>> print(string)
            rmakers.Talea(
                [2, 1, 3, 2, 4, 1, 1],
                16,
                preamble=[1, 1, 3, 2, 4, 1, 1],
                )

            >>> string = abjad.storage(talea.advance(6))
            >>> print(string)
            rmakers.Talea(
                [2, 1, 3, 2, 4, 1, 1],
                16,
                preamble=[1, 3, 2, 4, 1, 1],
                )

            >>> string = abjad.storage(talea.advance(7))
            >>> print(string)
            rmakers.Talea(
                [2, 1, 3, 2, 4, 1, 1],
                16,
                preamble=[3, 2, 4, 1, 1],
                )

            >>> string = abjad.storage(talea.advance(8))
            >>> print(string)
            rmakers.Talea(
                [2, 1, 3, 2, 4, 1, 1],
                16,
                preamble=[2, 2, 4, 1, 1],
                )

        ..  container:: example

            REGRESSION. Works when talea advances by period of talea:

            >>> talea = rmakers.Talea([1, 2, 3, 4], 16)

            >>> string = abjad.storage(talea.advance(10))
            >>> print(string)
            rmakers.Talea(
                [1, 2, 3, 4],
                16
                )

            >>> string = abjad.storage(talea.advance(20))
            >>> print(string)
            rmakers.Talea(
                [1, 2, 3, 4],
                16
                )

        """
        assert isinstance(weight, int), repr(weight)
        if weight < 0:
            raise Exception(f"weight {weight} must be nonnegative.")
        if weight == 0:
            return abjad.new(self)
        preamble = abjad.Sequence(self.preamble or ())
        counts = abjad.Sequence(self.counts or ())
        preamble_: typing.Optional[abjad.Sequence]
        if weight < preamble.weight():
            consumed, remaining = preamble.split([weight], overhang=True)
            preamble_ = remaining
        elif weight == preamble.weight():
            preamble_ = None
        else:
            assert preamble.weight() < weight
            weight -= preamble.weight()
            preamble = counts[:]
            while True:
                if weight <= preamble.weight():
                    break
                preamble += counts
            if preamble.weight() == weight:
                consumed, remaining = preamble[:], None
            else:
                consumed, remaining = preamble.split([weight], overhang=True)
            preamble_ = remaining
        return abjad.new(
            self,
            counts=counts,
            denominator=self.denominator,
            preamble=preamble_,
        )


### FACTORY FUNCTIONS ###


def interpolate(
    start_duration: abjad.DurationTyping,
    stop_duration: abjad.DurationTyping,
    written_duration: abjad.DurationTyping,
) -> Interpolation:
    """
    Makes interpolation.
    """
    return Interpolation(start_duration, stop_duration, written_duration)
