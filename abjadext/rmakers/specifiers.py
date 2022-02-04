"""
Rhythm-maker specifiers.
"""
import dataclasses
import typing

import abjad

ClassTyping = typing.Union[int, type]


@dataclasses.dataclass(slots=True)
class Incise:
    r"""
    Incise specifier.

    ..  container:: example

        Specifies one sixteenth rest cut out of the beginning of every division:

        >>> specifier = rmakers.Incise(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     talea_denominator=16,
        ... )

    ..  container:: example

        Specifies sixteenth rests cut out of the beginning and end of each division:

        >>> specifier = rmakers.Incise(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     suffix_talea=[-1],
        ...     suffix_counts=[1],
        ...     talea_denominator=16,
        ... )

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

        >>> lilypond_file = rmakers.helpers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/16
                    c'8
                    [
                    c'8
                    ]
                    r16
                    \time 5/16
                    r16
                    c'16.
                    [
                    c'16.
                    ]
                    r16
                    \time 5/16
                    c'8
                    [
                    c'8
                    ]
                    r16
                    \time 5/16
                    r16
                    c'16.
                    [
                    c'16.
                    ]
                    r16
                }
            >>

    """

    body_ratio: abjad.RatioTyping = None
    fill_with_rests: bool = None
    outer_divisions_only: bool = None
    prefix_counts: typing.Sequence[int] = None
    prefix_talea: typing.Sequence[int] = None
    suffix_counts: typing.Sequence[int] = None
    suffix_talea: typing.Sequence[int] = None
    talea_denominator: int = None

    __documentation_section__ = "Specifiers"

    def __post_init__(self):
        prefix_talea = self.prefix_talea or ()
        prefix_talea = tuple(prefix_talea)
        assert self._is_integer_tuple(prefix_talea)
        self.prefix_talea: typing.Tuple[int, ...] = prefix_talea
        prefix_counts = self.prefix_counts or ()
        prefix_counts = tuple(prefix_counts)
        assert self._is_length_tuple(prefix_counts)
        self.prefix_counts: typing.Tuple[int, ...] = prefix_counts
        if self.prefix_talea:
            assert self.prefix_counts
        suffix_talea = self.suffix_talea or ()
        suffix_talea = tuple(suffix_talea)
        assert self._is_integer_tuple(suffix_talea)
        if suffix_talea is not None:
            assert isinstance(suffix_talea, tuple)
        self.suffix_talea: typing.Tuple[int, ...] = suffix_talea
        suffix_counts = self.suffix_counts or ()
        suffix_counts = tuple(suffix_counts)
        if suffix_counts is not None:
            assert isinstance(suffix_counts, tuple)
            assert self._is_length_tuple(suffix_counts)
        self.suffix_counts: typing.Tuple[int, ...] = suffix_counts
        if self.suffix_talea:
            assert self.suffix_counts
        if self.talea_denominator is not None:
            if not abjad.math.is_nonnegative_integer_power_of_two(
                self.talea_denominator
            ):
                message = f"talea denominator {talea_denominator!r} must be nonnegative"
                message += " integer power of 2."
                raise Exception(message)
        if self.prefix_talea or self.suffix_talea:
            assert self.talea_denominator is not None
        if self.body_ratio is not None:
            self.body_ratio = abjad.Ratio(self.body_ratio)
        if self.fill_with_rests is not None:
            self.fill_with_rests = bool(self.fill_with_rests)
        if self.outer_divisions_only is not None:
            self.outer_divisions_only = bool(self.outer_divisions_only)

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


@dataclasses.dataclass(slots=True)
class Interpolation:
    """
    Interpolation specifier.

    ..  container:: example

        >>> rmakers.Interpolation(
        ...     start_duration=(1, 4),
        ...     stop_duration=(1, 16),
        ...     written_duration=(1, 16),
        ... )
        Interpolation(start_duration=Duration(1, 4), stop_duration=Duration(1, 16), written_duration=Duration(1, 16))

    """

    start_duration: typing.Tuple[int, int] = (1, 8)
    stop_duration: typing.Tuple[int, int] = (1, 16)
    written_duration: typing.Tuple[int, int] = (1, 16)

    __documentation_section__ = "Specifiers"

    def __post_init__(self) -> None:
        self.start_duration = abjad.Duration(self.start_duration)
        self.stop_duration = abjad.Duration(self.stop_duration)
        self.written_duration = abjad.Duration(self.written_duration)

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
            >>> specifier.reverse()
            Interpolation(start_duration=Duration(1, 16), stop_duration=Duration(1, 4), written_duration=Duration(1, 16))

        ..  container:: example

            Changes ritardando specifier to accelerando specifier:

            >>> specifier = rmakers.Interpolation(
            ...     start_duration=(1, 16),
            ...     stop_duration=(1, 4),
            ...     written_duration=(1, 16),
            ... )
            >>> specifier.reverse()
            Interpolation(start_duration=Duration(1, 4), stop_duration=Duration(1, 16), written_duration=Duration(1, 16))

        """
        return type(self)(
            start_duration=self.stop_duration,
            stop_duration=self.start_duration,
            written_duration=self.written_duration,
        )


@dataclasses.dataclass(slots=True)
class Spelling:
    r"""
    Duration spelling specifier.

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

        >>> lilypond_file = rmakers.helpers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
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
                    \time 3/4
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

        >>> lilypond_file = rmakers.helpers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
                    c'16
                    ~
                    c'4
                    c'16
                    ~
                    c'4
                    c'8
                    ~
                    \time 3/4
                    c'8.
                    [
                    c'16
                    ~
                    ]
                    c'4
                    c'4
                }
            >>

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

        >>> lilypond_file = rmakers.helpers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
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
                    \time 3/4
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

        >>> lilypond_file = rmakers.helpers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    c'4
                    r8
                    r8
                    \time 3/4
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

    forbidden_note_duration: abjad.DurationTyping = None
    forbidden_rest_duration: abjad.DurationTyping = None
    increase_monotonic: bool = None

    __documentation_section__ = "Specifiers"

    def __post_init__(self):
        if self.forbidden_note_duration is not None:
            self.forbidden_note_duration = abjad.Duration(self.forbidden_note_duration)
        if self.forbidden_rest_duration is not None:
            self.forbidden_rest_duration = abjad.Duration(self.forbidden_rest_duration)
        if self.increase_monotonic is not None:
            self.increase_monotonic = bool(self.increase_monotonic)


@dataclasses.dataclass(slots=True)
class Talea:
    """
    Talea specifier.

    ..  container:: example

        >>> talea = rmakers.Talea(
        ...     [2, 1, 3, 2, 4, 1, 1],
        ...     16,
        ...     preamble=[1, 1, 1, 1],
        ... )

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

    counts: typing.Any
    denominator: int
    end_counts: abjad.IntegerSequence = None
    preamble: abjad.IntegerSequence = None

    __documentation_section__ = "Specifiers"

    def __post_init__(self):
        for count in self.counts:
            assert isinstance(count, int) or count in "+-", repr(count)
        if not abjad.math.is_nonnegative_integer_power_of_two(self.denominator):
            message = f"denominator {self.denominator} must be integer power of 2."
            raise Exception(message)
        end_counts_ = None
        if self.end_counts is not None:
            assert all(isinstance(_, int) for _ in self.end_counts)
            end_counts_ = tuple(self.end_counts)
        self.end_counts = end_counts_
        if self.preamble is not None:
            assert all(isinstance(_, int) for _ in self.preamble), repr(self.preamble)

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

    def advance(self, weight: int) -> "Talea":
        """
        Advances talea by ``weight``.

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> talea.advance(0)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=None, preamble=[1, 1, 1, 1])

            >>> talea.advance(1)
            Talea(counts=Sequence([2, 1, 3, 2, 4, 1, 1]), denominator=16, end_counts=None, preamble=Sequence([1, 1, 1]))

            >>> talea.advance(2)
            Talea(counts=Sequence([2, 1, 3, 2, 4, 1, 1]), denominator=16, end_counts=None, preamble=Sequence([1, 1]))

            >>> talea.advance(3)
            Talea(counts=Sequence([2, 1, 3, 2, 4, 1, 1]), denominator=16, end_counts=None, preamble=Sequence([1]))

            >>> talea.advance(4)
            Talea(counts=Sequence([2, 1, 3, 2, 4, 1, 1]), denominator=16, end_counts=None, preamble=None)

            >>> talea.advance(5)
            Talea(counts=Sequence([2, 1, 3, 2, 4, 1, 1]), denominator=16, end_counts=None, preamble=Sequence([1, 1, 3, 2, 4, 1, 1]))

            >>> talea.advance(6)
            Talea(counts=Sequence([2, 1, 3, 2, 4, 1, 1]), denominator=16, end_counts=None, preamble=Sequence([1, 3, 2, 4, 1, 1]))

            >>> talea.advance(7)
            Talea(counts=Sequence([2, 1, 3, 2, 4, 1, 1]), denominator=16, end_counts=None, preamble=Sequence([3, 2, 4, 1, 1]))

            >>> talea.advance(8)
            Talea(counts=Sequence([2, 1, 3, 2, 4, 1, 1]), denominator=16, end_counts=None, preamble=Sequence([2, 2, 4, 1, 1]))

        ..  container:: example

            REGRESSION. Works when talea advances by period of talea:

            >>> talea = rmakers.Talea([1, 2, 3, 4], 16)
            >>> talea
            Talea(counts=[1, 2, 3, 4], denominator=16, end_counts=None, preamble=None)

            >>> talea.advance(10)
            Talea(counts=Sequence([1, 2, 3, 4]), denominator=16, end_counts=None, preamble=None)

            >>> talea.advance(20)
            Talea(counts=Sequence([1, 2, 3, 4]), denominator=16, end_counts=None, preamble=None)

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


def interpolate(
    start_duration: abjad.DurationTyping,
    stop_duration: abjad.DurationTyping,
    written_duration: abjad.DurationTyping,
) -> Interpolation:
    """
    Makes interpolation.
    """
    return Interpolation(start_duration, stop_duration, written_duration)
