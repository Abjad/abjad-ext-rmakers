import dataclasses
import math
import types
import typing

import abjad


def example(selection, time_signatures=None, *, includes=None):
    """
    Makes example LilyPond file.
    """
    lilypond_file = abjad.illustrators.selection(
        selection,
        time_signatures,
    )
    includes = [rf'\include "{_}"' for _ in includes or []]
    lilypond_file.items[0:0] = includes
    staff = lilypond_file["Staff"]
    staff.lilypond_type = "RhythmicStaff"
    abjad.override(staff).Clef.stencil = False
    return lilypond_file


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
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

        >>> lilypond_file = rmakers.example(selections, divisions)
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

    body_ratio: abjad.typings.Ratio = abjad.Ratio([1])
    fill_with_rests: bool = False
    outer_divisions_only: bool = False
    prefix_counts: typing.Sequence[int] = ()
    prefix_talea: typing.Sequence[int] = ()
    suffix_counts: typing.Sequence[int] = ()
    suffix_talea: typing.Sequence[int] = ()
    talea_denominator: int | None = None

    __documentation_section__ = "Specifiers"

    def __post_init__(self):
        assert isinstance(self.prefix_talea, typing.Sequence), repr(self.prefix_talea)
        assert self._is_integer_tuple(self.prefix_talea)
        assert isinstance(self.prefix_counts, typing.Sequence), repr(self.prefix_counts)
        assert self._is_length_tuple(self.prefix_counts)
        if self.prefix_talea:
            assert self.prefix_counts
        assert isinstance(self.suffix_talea, typing.Sequence), repr(self.suffix_talea)
        assert self._is_integer_tuple(self.suffix_talea)
        assert isinstance(self.suffix_counts, typing.Sequence), repr(self.suffix_counts)
        assert self._is_length_tuple(self.suffix_counts)
        if self.suffix_talea:
            assert self.suffix_counts
        if self.talea_denominator is not None:
            assert abjad.math.is_nonnegative_integer_power_of_two(
                self.talea_denominator
            )
        if self.prefix_talea or self.suffix_talea:
            assert self.talea_denominator is not None
        assert isinstance(self.body_ratio, abjad.Ratio), repr(self.body_ratio)
        assert isinstance(self.fill_with_rests, bool), repr(self.fill_with_rests)
        assert isinstance(self.outer_divisions_only, bool), repr(
            self.outer_divisions_only
        )

    @staticmethod
    def _is_integer_tuple(argument):
        if argument is None:
            return True
        if all(isinstance(_, int) for _ in argument):
            return True
        return False

    @staticmethod
    def _is_length_tuple(argument):
        if argument is None:
            return True
        if abjad.math.all_are_nonnegative_integer_equivalent_numbers(argument):
            if isinstance(argument, tuple | list):
                return True
        return False

    @staticmethod
    def _reverse_tuple(argument):
        if argument is not None:
            return tuple(reversed(argument))


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Interpolation:
    """
    Interpolation specifier.

    ..  container:: example

        >>> rmakers.Interpolation(
        ...     start_duration=abjad.Duration(1, 4),
        ...     stop_duration=abjad.Duration(1, 16),
        ...     written_duration=abjad.Duration(1, 16),
        ... )
        Interpolation(start_duration=Duration(1, 4), stop_duration=Duration(1, 16), written_duration=Duration(1, 16))

    """

    start_duration: abjad.Duration = abjad.Duration(1, 8)
    stop_duration: abjad.Duration = abjad.Duration(1, 16)
    written_duration: abjad.Duration = abjad.Duration(1, 16)

    __documentation_section__ = "Specifiers"

    def __post_init__(self) -> None:
        assert isinstance(self.start_duration, abjad.Duration), repr(
            self.start_duration
        )
        assert isinstance(self.stop_duration, abjad.Duration), repr(self.stop_duration)
        assert isinstance(self.written_duration, abjad.Duration), repr(
            self.written_duration
        )

    def reverse(self) -> "Interpolation":
        """
        Swaps start duration and stop duration of interpolation specifier.

        ..  container:: example

            Changes accelerando specifier to ritardando specifier:

            >>> specifier = rmakers.Interpolation(
            ...     start_duration=abjad.Duration(1, 4),
            ...     stop_duration=abjad.Duration(1, 16),
            ...     written_duration=abjad.Duration(1, 16),
            ... )
            >>> specifier.reverse()
            Interpolation(start_duration=Duration(1, 16), stop_duration=Duration(1, 4), written_duration=Duration(1, 16))

        ..  container:: example

            Changes ritardando specifier to accelerando specifier:

            >>> specifier = rmakers.Interpolation(
            ...     start_duration=abjad.Duration(1, 16),
            ...     stop_duration=abjad.Duration(1, 4),
            ...     written_duration=abjad.Duration(1, 16),
            ... )
            >>> specifier.reverse()
            Interpolation(start_duration=Duration(1, 4), stop_duration=Duration(1, 16), written_duration=Duration(1, 16))

        """
        return type(self)(
            start_duration=self.stop_duration,
            stop_duration=self.start_duration,
            written_duration=self.written_duration,
        )


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
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

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    ]
                    ~
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

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    ]
                    ~
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
        ...         spelling=rmakers.Spelling(forbidden_note_duration=abjad.Duration(1, 4)),
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
        ...         spelling=rmakers.Spelling(forbidden_rest_duration=abjad.Duration(1, 4)),
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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

    forbidden_note_duration: abjad.Duration | None = None
    forbidden_rest_duration: abjad.Duration | None = None
    increase_monotonic: bool = False

    __documentation_section__ = "Specifiers"

    def __post_init__(self):
        if self.forbidden_note_duration is not None:
            assert isinstance(self.forbidden_note_duration, abjad.Duration), repr(
                self.forbidden_note_duration
            )
        if self.forbidden_rest_duration is not None:
            assert isinstance(self.forbidden_rest_duration, abjad.Duration), repr(
                self.forbidden_rest_duration
            )
        assert isinstance(self.increase_monotonic, bool), repr(self.increase_monotonic)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
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

    counts: typing.Sequence[int | str]
    denominator: int
    end_counts: typing.Sequence[int] = ()
    preamble: typing.Sequence[int] = ()

    __documentation_section__ = "Specifiers"

    def __post_init__(self):
        assert isinstance(self.counts, typing.Sequence), repr(self.counts)
        for count in self.counts:
            assert isinstance(count, int) or count in "+-", repr(count)
        assert abjad.math.is_nonnegative_integer_power_of_two(self.denominator)
        assert isinstance(self.end_counts, typing.Sequence), repr(self.end_counts)
        assert all(isinstance(_, int) for _ in self.end_counts)
        assert isinstance(self.preamble, typing.Sequence), repr(self.preamble)
        assert all(isinstance(_, int) for _ in self.preamble)

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
            preamble = [abs(_) for _ in self.preamble]
            cumulative = abjad.math.cumulative_sums(preamble)[1:]
            if argument in cumulative:
                return True
            preamble_weight = abjad.sequence.weight(preamble)
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
    ) -> abjad.NonreducedFraction | list[abjad.NonreducedFraction]:
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
        preamble: list[int | str] = list(self.preamble)
        counts = list(self.counts)
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

    def __iter__(self) -> typing.Iterator[abjad.Duration]:
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
        for item in self.counts or []:
            assert isinstance(item, int)
            duration = abjad.Duration(item, self.denominator)
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
        return abjad.sequence.weight(self.counts)

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
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 1, 1, 1])

            >>> talea.advance(1)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 1, 1])

            >>> talea.advance(2)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 1])

            >>> talea.advance(3)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1])

            >>> talea.advance(4)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=())

            >>> talea.advance(5)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 1, 3, 2, 4, 1, 1])

            >>> talea.advance(6)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 3, 2, 4, 1, 1])

            >>> talea.advance(7)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[3, 2, 4, 1, 1])

            >>> talea.advance(8)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[2, 2, 4, 1, 1])

        ..  container:: example

            REGRESSION. Works when talea advances by period of talea:

            >>> talea = rmakers.Talea([1, 2, 3, 4], 16)
            >>> talea
            Talea(counts=[1, 2, 3, 4], denominator=16, end_counts=(), preamble=())

            >>> talea.advance(10)
            Talea(counts=[1, 2, 3, 4], denominator=16, end_counts=(), preamble=())

            >>> talea.advance(20)
            Talea(counts=[1, 2, 3, 4], denominator=16, end_counts=(), preamble=())

        """
        assert isinstance(weight, int), repr(weight)
        if weight < 0:
            raise Exception(f"weight {weight} must be nonnegative.")
        if weight == 0:
            return dataclasses.replace(self)
        preamble: list[int | str] = list(self.preamble)
        counts = list(self.counts)
        if weight < abjad.sequence.weight(preamble):
            consumed, remaining = abjad.sequence.split(
                preamble, [weight], overhang=True
            )
            preamble_ = remaining
        elif weight == abjad.sequence.weight(preamble):
            preamble_ = ()
        else:
            assert abjad.sequence.weight(preamble) < weight
            weight -= abjad.sequence.weight(preamble)
            preamble = counts[:]
            while True:
                if weight <= abjad.sequence.weight(preamble):
                    break
                preamble += counts
            if abjad.sequence.weight(preamble) == weight:
                consumed, remaining = preamble[:], ()
            else:
                consumed, remaining = abjad.sequence.split(
                    preamble, [weight], overhang=True
                )
            preamble_ = remaining
        return dataclasses.replace(
            self,
            counts=counts,
            denominator=self.denominator,
            preamble=preamble_,
        )


def interpolate(
    start_duration: abjad.typings.Duration,
    stop_duration: abjad.typings.Duration,
    written_duration: abjad.typings.Duration,
) -> Interpolation:
    """
    Makes interpolation.
    """
    return Interpolation(
        abjad.Duration(start_duration),
        abjad.Duration(stop_duration),
        abjad.Duration(written_duration),
    )


@dataclasses.dataclass(order=True, slots=True, unsafe_hash=True)
class RhythmMaker:
    """
    Rhythm-maker baseclass.
    """

    already_cached_state: bool = dataclasses.field(
        default=False, init=False, repr=False, compare=False
    )
    previous_state: dict = dataclasses.field(
        default_factory=dict, init=False, repr=False
    )
    spelling: Spelling = Spelling()
    state: dict = dataclasses.field(default_factory=dict, init=False, repr=False)
    tag: abjad.Tag = abjad.Tag()

    __documentation_section__ = "Rhythm-makers"

    def __post_init__(self):
        assert isinstance(self.already_cached_state, bool)
        assert isinstance(self.previous_state, dict), repr(self.previous_state)
        assert isinstance(self.spelling, Spelling), repr(self.spelling)
        assert isinstance(self.state, dict), repr(self.state)
        assert isinstance(self.tag, abjad.Tag), repr(self.tag)

    def __call__(
        self,
        divisions: typing.Sequence[tuple[int, int]],
        previous_state: dict = None,
    ) -> list[abjad.Component]:
        self.previous_state = dict(previous_state or [])
        music = self._make_music(divisions)
        music_voice = wrap_in_time_signature_staff(music, divisions)
        divisions_consumed = len(divisions)
        if self.already_cached_state is not True:
            self._cache_state(music_voice, divisions_consumed)
        selection = music_voice[:]
        music_voice[:] = []
        return list(selection)

    def _cache_state(self, voice, divisions_consumed):
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        logical_ties_produced = len(abjad.select.logical_ties(voice))
        logical_ties_produced += previous_logical_ties_produced
        if self._previous_incomplete_last_note():
            logical_ties_produced -= 1
        self.state["divisions_consumed"] = self.previous_state.get(
            "divisions_consumed", 0
        )
        self.state["divisions_consumed"] += divisions_consumed
        self.state["logical_ties_produced"] = logical_ties_produced
        items = self.state.items()
        state = dict(sorted(items))
        self.state = state

    def _make_music(self, divisions):
        return []

    def _previous_divisions_consumed(self):
        if not self.previous_state:
            return 0
        return self.previous_state.get("divisions_consumed", 0)

    def _previous_incomplete_last_note(self):
        if not self.previous_state:
            return False
        return self.previous_state.get("incomplete_last_note", False)

    def _previous_logical_ties_produced(self):
        if not self.previous_state:
            return 0
        return self.previous_state.get("logical_ties_produced", 0)


def _make_talea_rhythm_maker_tuplets(divisions, leaf_lists, tag):
    assert len(divisions) == len(leaf_lists)
    tuplets = []
    for division, leaf_list in zip(divisions, leaf_lists):
        duration = abjad.Duration(division)
        tuplet = abjad.Tuplet.from_duration(duration, leaf_list, tag=tag)
        tuplets.append(tuplet)
    return tuplets


def _make_leaves_from_talea(
    talea,
    talea_denominator,
    increase_monotonic=None,
    forbidden_note_duration=None,
    forbidden_rest_duration=None,
    tag: abjad.Tag = abjad.Tag(),
):
    assert all(_ != 0 for _ in talea), repr(talea)
    result: list[abjad.Leaf | abjad.Tuplet] = []
    leaf_maker = abjad.LeafMaker(
        increase_monotonic=increase_monotonic,
        forbidden_note_duration=forbidden_note_duration,
        forbidden_rest_duration=forbidden_rest_duration,
        tag=tag,
    )
    pitches: list[int | None]
    for note_value in talea:
        if 0 < note_value:
            pitches = [0]
        else:
            pitches = [None]
        division = abjad.Duration(abs(note_value), talea_denominator)
        durations = [division]
        leaves = leaf_maker(pitches, durations)
        if (
            1 < len(leaves)
            and abjad.get.logical_tie(leaves[0]).is_trivial
            and not isinstance(leaves[0], abjad.Rest)
        ):
            abjad.tie(leaves)
        result.extend(leaves)
    return result


def _scale_rhythm_maker_input(divisions, talea_denominator, counts):
    talea_denominator = talea_denominator or 1
    scaled_divisions = divisions[:]
    dummy_division = (1, talea_denominator)
    scaled_divisions.append(dummy_division)
    scaled_divisions = abjad.Duration.durations_to_nonreduced_fractions(
        scaled_divisions
    )
    dummy_division = scaled_divisions.pop()
    lcd = dummy_division.denominator
    multiplier = lcd / talea_denominator
    assert abjad.math.is_integer_equivalent(multiplier)
    multiplier = int(multiplier)
    scaled_counts = types.SimpleNamespace()
    for name, vector in counts.__dict__.items():
        vector = [multiplier * _ for _ in vector]
        cyclic_vector = abjad.CyclicTuple(vector)
        setattr(scaled_counts, name, cyclic_vector)
    assert len(scaled_divisions) == len(divisions)
    assert len(scaled_counts.__dict__) == len(counts.__dict__)
    return types.SimpleNamespace(
        divisions=scaled_divisions, lcd=lcd, counts=scaled_counts
    )


def _make_time_signature_staff(time_signatures):
    assert time_signatures, repr(time_signatures)
    staff = abjad.Staff(simultaneous=True)
    time_signature_voice = abjad.Voice(name="TimeSignatureVoice")
    for time_signature in time_signatures:
        duration = time_signature.pair
        skip = abjad.Skip(1, multiplier=duration)
        time_signature_voice.append(skip)
        abjad.attach(time_signature, skip, context="Staff")
    staff.append(time_signature_voice)
    staff.append(abjad.Voice(name="RhythmMaker.Music"))
    return staff


def _validate_tuplets(selections):
    for tuplet in abjad.iterate.components(selections, abjad.Tuplet):
        assert abjad.Multiplier(tuplet.multiplier).normalized(), repr(tuplet)
        assert len(tuplet), repr(tuplet)


def wrap_in_time_signature_staff(music, divisions):
    music = abjad.sequence.flatten(music, depth=-1)
    assert all(isinstance(_, abjad.Component) for _ in music), repr(music)
    assert isinstance(music, list), repr(music)
    time_signatures = [abjad.TimeSignature(_) for _ in divisions]
    staff = _make_time_signature_staff(time_signatures)
    music_voice = staff["RhythmMaker.Music"]
    music_voice.extend(music)
    _validate_tuplets(music_voice)
    return music_voice


@dataclasses.dataclass(order=True, slots=True, unsafe_hash=True)
class AccelerandoRhythmMaker(RhythmMaker):
    r"""
    Accelerando rhythm-maker.

    ..  container:: example

        Makes accelerandi:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 20), (1, 8), (1, 16)]),
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 3/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 3/8
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

        REGRESSION. Copy preserves commands:

        >>> import dataclasses
        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.force_fraction()
        ... )

        >>> dataclasses.replace(stack).commands
        (ForceFractionCommand(selector=None),)

    ..  container:: example

        Sets duration bracket with no beams:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \time 4/8
                        c'16 * 63/32
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \time 3/8
                        c'16 * 117/64
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \time 4/8
                        c'16 * 63/32
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \time 3/8
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

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.beam_groups(lambda _: abjad.select.tuplets(_)),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 2
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        \time 3/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        \time 3/8
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

        Leave feathering turned off here because LilyPond feathers conjoint beams poorly.

    ..  container:: example

        Ties across tuplets:

        >>> def selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     return [abjad.select.leaf(_, -1) for _ in result]

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.duration_bracket(),
        ...     rmakers.tie(selector),
        ...     rmakers.feather_beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> def selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [0], 2)
        ...     return [abjad.select.leaf(_, -1) for _ in result]

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.duration_bracket(),
        ...     rmakers.tie(selector),
        ...     rmakers.feather_beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> def selector(argument):
        ...     result = abjad.select.leaves(argument)
        ...     result = abjad.select.get(result, [0, -1])
        ...     return result

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando(
        ...         [(1, 8), (1, 20), (1, 16)],
        ...         [(1, 20), (1, 8), (1, 16)],
        ...     ),
        ...     rmakers.force_rest(selector),
        ...     rmakers.feather_beam(
        ...         beam_rests=True,
        ...         stemlet_length=0.75,
        ...     ),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \override Staff.Stem.stemlet-length = 0.75
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \override Staff.Stem.stemlet-length = 0.75
                        \time 3/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \override Staff.Stem.stemlet-length = 0.75
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \override Staff.Stem.stemlet-length = 0.75
                        \time 3/8
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

        >>> def selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [1], 2)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.force_rest(selector),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.extract_trivial(),
        ...     rmakers.duration_bracket(),
        ...     rmakers.feather_beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                    \time 3/8
                    r4.
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                    \time 3/8
                    r4.
                }
            >>

    ..  container:: example

        Alternates accelerandi and ritardandi:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando(
        ...         [(1, 8), (1, 20), (1, 16)],
        ...         [(1, 20), (1, 8), (1, 16)],
        ...     ),
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 3/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 3/8
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

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(5, 8), (3, 8), (1, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                    ~
                                    c'8
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 5/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                    \time 1/8
                    c'8
                }
            >>

    ..  container:: example

        Consumes 3 divisions:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando(
        ...         [(1, 8), (1, 20), (1, 16)],
        ...         [(1, 20), (1, 8), (1, 16)],
        ...     ),
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> state = stack.maker.state
        >>> state
        {'divisions_consumed': 3, 'logical_ties_produced': 17}

        Advances 3 divisions; then consumes another 3 divisions:

        >>> divisions = [(4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions, previous_state=state)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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

        >>> state = stack.maker.state
        >>> state
        {'divisions_consumed': 6, 'logical_ties_produced': 36}

        Advances 6 divisions; then consumes another 3 divisions:

        >>> divisions = [(3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions, previous_state=state)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> state = stack.maker.state
        >>> state
        {'divisions_consumed': 9, 'logical_ties_produced': 53}

    ..  container:: example

        Tags LilyPond output:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ...     tag=abjad.Tag("ACCELERANDO_RHYTHM_MAKER"),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    %! ACCELERANDO_RHYTHM_MAKER
                    \times 1/1
                    %! ACCELERANDO_RHYTHM_MAKER
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 63/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        [
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 115/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 91/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 35/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 29/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16
                        %! ACCELERANDO_RHYTHM_MAKER
                        ]
                    %! ACCELERANDO_RHYTHM_MAKER
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    %! ACCELERANDO_RHYTHM_MAKER
                    \times 1/1
                    %! ACCELERANDO_RHYTHM_MAKER
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 117/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        [
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 99/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 69/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 47/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        ]
                    %! ACCELERANDO_RHYTHM_MAKER
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    %! ACCELERANDO_RHYTHM_MAKER
                    \times 1/1
                    %! ACCELERANDO_RHYTHM_MAKER
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 63/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        [
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 115/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 91/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 35/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 29/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16
                        %! ACCELERANDO_RHYTHM_MAKER
                        ]
                    %! ACCELERANDO_RHYTHM_MAKER
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    %! ACCELERANDO_RHYTHM_MAKER
                    \times 1/1
                    %! ACCELERANDO_RHYTHM_MAKER
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 117/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        [
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 99/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 69/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 47/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        ]
                    %! ACCELERANDO_RHYTHM_MAKER
                    }
                    \revert TupletNumber.text
                }
            >>

    Set interpolations' ``written_duration`` to ``1/16`` or less for multiple beams.
    """

    interpolations: typing.Sequence[Interpolation] = (Interpolation(),)

    def __post_init__(self):
        RhythmMaker.__post_init__(self)
        assert isinstance(self.interpolations, typing.Sequence), repr(
            self.interpolations
        )
        assert all(isinstance(_, Interpolation) for _ in self.interpolations)

    @staticmethod
    def _fix_rounding_error(selection, total_duration, interpolation):
        selection_duration = abjad.get.duration(selection)
        if not selection_duration == total_duration:
            needed_duration = total_duration - abjad.get.duration(selection[:-1])
            multiplier = needed_duration / interpolation.written_duration
            selection[-1].multiplier = multiplier

    @staticmethod
    def _get_interpolations(self_interpolations, self_previous_state):
        specifiers_ = self_interpolations
        if specifiers_ is None:
            specifiers_ = abjad.CyclicTuple([Interpolation()])
        elif isinstance(specifiers_, Interpolation):
            specifiers_ = abjad.CyclicTuple([specifiers_])
        else:
            specifiers_ = abjad.CyclicTuple(specifiers_)
        string = "divisions_consumed"
        divisions_consumed = self_previous_state.get(string, 0)
        specifiers_ = abjad.sequence.rotate(specifiers_, n=-divisions_consumed)
        specifiers_ = abjad.CyclicTuple(specifiers_)
        return specifiers_

    @staticmethod
    def _interpolate_cosine(y1, y2, mu) -> float:
        mu2 = (1 - math.cos(mu * math.pi)) / 2
        return y1 * (1 - mu2) + y2 * mu2

    @staticmethod
    def _interpolate_divide(
        total_duration, start_duration, stop_duration, exponent="cosine"
    ) -> str | list[float]:
        """
        Divides ``total_duration`` into durations computed from interpolating between
        ``start_duration`` and ``stop_duration``.

        ..  container:: example

            >>> rmakers.AccelerandoRhythmMaker._interpolate_divide(
            ...     total_duration=10,
            ...     start_duration=1,
            ...     stop_duration=1,
            ...     exponent=1,
            ... )
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
            >>> sum(_)
            10.0

            >>> rmakers.AccelerandoRhythmMaker._interpolate_divide(
            ...     total_duration=10,
            ...     start_duration=5,
            ...     stop_duration=1,
            ... )
            [4.798..., 2.879..., 1.326..., 0.995...]
            >>> sum(_)
            10.0

        Set ``exponent`` to ``'cosine'`` for cosine interpolation.

        Set ``exponent`` to a numeric value for exponential interpolation with
        ``exponent`` as the exponent.

        Scales resulting durations so that their sum equals ``total_duration`` exactly.
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
        durations = [_ * total_duration / sum(durations) for _ in durations]
        return durations

    @staticmethod
    def _interpolate_divide_multiple(
        total_durations, reference_durations, exponent="cosine"
    ) -> list[float]:
        """
        Interpolates ``reference_durations`` such that the sum of the resulting
        interpolated values equals the given ``total_durations``.

        ..  container:: example

            >>> class_ = rmakers.AccelerandoRhythmMaker
            >>> durations = class_._interpolate_divide_multiple(
            ...     total_durations=[100, 50],
            ...     reference_durations=[20, 10, 20],
            ... )
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

        implemented on this class. But this function takes multiple
        total durations and multiple reference durations at one time.

        Precondition: ``len(totals_durations) == len(reference_durations)-1``.

        Set ``exponent`` to ``cosine`` for cosine interpolation. Set ``exponent`` to a
        number for exponential interpolation.
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
        result = y1 * (1 - mu**exponent) + y2 * mu**exponent
        return result

    @staticmethod
    def _make_accelerando(
        total_duration, interpolations, index, *, tag: abjad.Tag = abjad.Tag()
    ) -> abjad.Tuplet:
        """
        Makes notes with LilyPond multipliers equal to ``total_duration``.

        Total number of notes not specified: total duration is specified instead.

        Selects interpolation specifier at ``index`` in ``interpolations``.

        Computes duration multipliers interpolated from interpolation specifier start to
        stop.

        Sets note written durations according to interpolation specifier.
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
            return tuplet
        durations = AccelerandoRhythmMaker._round_durations(durations, 2**10)
        notes = []
        for i, duration in enumerate(durations):
            written_duration = interpolation.written_duration
            multiplier = duration / written_duration
            note = abjad.Note(0, written_duration, multiplier=multiplier, tag=tag)
            notes.append(note)
        AccelerandoRhythmMaker._fix_rounding_error(notes, total_duration, interpolation)
        tuplet = abjad.Tuplet((1, 1), notes, tag=tag)
        return tuplet

    def _make_music(self, divisions) -> list[abjad.Tuplet]:
        tuplets = _make_accelerando_rhythm_maker_music(
            divisions,
            *self.interpolations,
            self_previous_state=self.previous_state,
            self_spelling=self.spelling,
            self_tag=self.tag,
        )
        return tuplets

    @staticmethod
    def _round_durations(durations, denominator):
        durations_ = []
        for duration in durations:
            numerator = int(round(duration * denominator))
            duration_ = abjad.Duration(numerator, denominator)
            durations_.append(duration_)
        return durations_


def _make_accelerando_rhythm_maker_music(
    divisions,
    *self_interpolations,
    self_previous_state,
    self_spelling,
    self_tag,
):
    interpolations = AccelerandoRhythmMaker._get_interpolations(
        self_interpolations, self_previous_state
    )
    tuplets = []
    for i, division in enumerate(divisions):
        tuplet = AccelerandoRhythmMaker._make_accelerando(
            division, interpolations, i, tag=self_tag
        )
        tuplets.append(tuplet)
    return tuplets


@dataclasses.dataclass(order=True, slots=True, unsafe_hash=True)
class EvenDivisionRhythmMaker(RhythmMaker):
    r"""
    Even division rhythm-maker.

    ..  container:: example

        Forces tuplet diminution:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[0, 0, 1]),
        ...     rmakers.force_diminution(),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(5, 16), (6, 16), (6, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/8
                    {
                        \time 5/16
                        c'4
                        c'4
                    }
                    \time 6/16
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 6/16
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        Forces tuplet augmentation:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[0, 0, 1]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ...     rmakers.force_augmentation(),
        ... )
        >>> divisions = [(5, 16), (6, 16), (6, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4
                    {
                        \time 5/16
                        c'8
                        [
                        c'8
                        ]
                    }
                    \time 6/16
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 6/16
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>


    ..  container:: example

        Ties nonlast tuplets:

        >>> def selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     return [abjad.select.leaf(_, -1) for _ in result]

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        (Equivalent to earlier tie-across-divisions pattern.)

    ..  container:: example

        Forces rest at every third logical tie:

        >>> def selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0], 3)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.force_rest(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        r8
                        c'8
                        [
                        c'8
                        ]
                        r8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        ]
                        r8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        ]
                        r8
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        r8
                        c'8
                    }
                }
            >>

        Forces rest at every fourth logical tie:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> def rest_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [3], 4)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        r8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        r8
                        c'8
                        [
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        ]
                        r8
                        c'8
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        (Forcing rests at the fourth logical tie produces two rests. Forcing rests at the
        eighth logical tie produces only one rest.)

        Forces rest at leaf 0 of every tuplet:

        >>> def selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.leaf(_, 0) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.force_rest(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        r8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        r8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        r8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        r8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Forces rest and rewrites every other tuplet:

        >>> def rest_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [0], 2)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    r2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                    \time 4/8
                    r2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        (Equivalent to ealier silence pattern.)

    ..  container:: example

        Ties and rewrites every other tuplet:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [0], 2)
        ...     result = [abjad.select.notes(_)[:-1] for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    c'2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                    \time 4/8
                    c'2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        (Equivalent to earlier sustain pattern.)

    ..  container:: example

        No preferred denominator:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([16], extra_counts=[4], denominator=None),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \times 2/3
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

        Expresses tuplet ratios in the usual way with numerator and denominator
        relatively prime.

    ..  container:: example

        Preferred denominator equal to 4:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division(
        ...         [16], extra_counts=[4], denominator=4
        ...     ),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/6
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \times 4/6
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

        Preferred denominator equal to 8:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division(
        ...         [16], extra_counts=[4], denominator=8
        ...     ),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 8/12
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \times 8/12
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

        Preferred denominator equal to 16:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division(
        ...         [16], extra_counts=[4], denominator=16
        ...     ),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 16/24
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \times 16/24
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Preferred denominator taken from count of elements in tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division(
        ...         [16], extra_counts=[4], denominator="from_counts"
        ...     ),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 8/12
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/10
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \times 8/12
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/10
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Fills tuplets with 16th notes and 8th notes, alternately:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([16, 8]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 16), (3, 8), (3, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/16
                    c'16
                    [
                    c'16
                    c'16
                    ]
                    \time 3/8
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \time 3/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                }
            >>

    ..  container:: example

        Fills tuplets with 8th notes:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 16), (3, 8), (3, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/16
                    c'8.
                    \time 3/8
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \time 3/4
                    c'8
                    [
                    c'8
                    c'8
                    c'8
                    c'8
                    c'8
                    ]
                }
            >>

        (Fills tuplets less than twice the duration of an eighth note with a single
        attack.)

        Fills tuplets with quarter notes:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 16), (3, 8), (3, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/16
                    c'8.
                    \time 3/8
                    c'4.
                    \time 3/4
                    c'4
                    c'4
                    c'4
                }
            >>

        (Fills tuplets less than twice the duration of a quarter note with a single
        attack.)

        Fills tuplets with half notes:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([2]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 16), (3, 8), (3, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/16
                    c'8.
                    \time 3/8
                    c'4.
                    \time 3/4
                    c'2.
                }
            >>

        (Fills tuplets less than twice the duration of a half note with a single
        attack.)


    ..  container:: example

        Adds extra counts to tuplets according to a pattern of three elements:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([16], extra_counts=[0, 1, 2]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/8
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        **Modular handling of positive values.** Denote by ``unprolated_note_count``
        the number counts included in a tuplet when ``extra_counts`` is set to zero.
        Then extra counts equals ``extra_counts % unprolated_note_count`` when
        ``extra_counts`` is positive.

        This is likely to be intuitive; compare with the handling of negative values,
        below.

        For positive extra counts, the modulus of transformation of a tuplet with six
        notes is six:

        >>> import math
        >>> unprolated_note_count = 6
        >>> modulus = unprolated_note_count
        >>> extra_counts = list(range(12))
        >>> labels = []
        >>> for count in extra_counts:
        ...     modular_count = count % modulus
        ...     label = rf"\markup {{ {count:3} becomes {modular_count:2} }}"
        ...     labels.append(label)

        Which produces the following pattern of changes:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([16], extra_counts=extra_counts),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = 12 * [(6, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> staff = lilypond_file["Staff"]
        >>> abjad.override(staff).TextScript.staff_padding = 7
        >>> leaves = abjad.select.leaves(staff)
        >>> groups = abjad.select.group_by_measure(leaves)
        >>> for group, label in zip(groups, labels):
        ...     markup = abjad.Markup(label)
        ...     abjad.attach(markup, group[0], direction=abjad.UP)
        ...

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
                    \override TextScript.staff-padding = 7
                }
                {
                    \time 6/16
                    c'16
                    ^ \markup {   0 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   1 becomes  1 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/8
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   2 becomes  2 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \times 6/9
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   3 becomes  3 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/10
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   4 becomes  4 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/11
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   5 becomes  5 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \time 6/16
                    c'16
                    ^ \markup {   6 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   7 becomes  1 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/8
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   8 becomes  2 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \times 6/9
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   9 becomes  3 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/10
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  10 becomes  4 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/11
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  11 becomes  5 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

        This modular formula ensures that rhythm-maker ``denominators`` are always
        respected: a very large number of extra counts never causes a
        ``16``-denominated tuplet to result in 32nd- or 64th-note rhythms.

    ..  container:: example

        **Modular handling of negative values.** Denote by ``unprolated_note_count``
        the number of counts included in a tuplet when ``extra_counts`` is set to
        zero. Further, let ``modulus = ceiling(unprolated_note_count / 2)``. Then
        extra counts equals ``-(abs(extra_counts) % modulus)`` when ``extra_counts``
        is negative.

        For negative extra counts, the modulus of transformation of a tuplet with six
        notes is three:

        >>> import math
        >>> unprolated_note_count = 6
        >>> modulus = math.ceil(unprolated_note_count / 2)
        >>> extra_counts = [0, -1, -2, -3, -4, -5, -6, -7, -8]
        >>> labels = []
        >>> for count in extra_counts:
        ...     modular_count = -(abs(count) % modulus)
        ...     label = rf"\markup {{ {count:3} becomes {modular_count:2} }}"
        ...     labels.append(label)

        Which produces the following pattern of changes:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([16], extra_counts=extra_counts),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = 9 * [(6, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> staff = lilypond_file["Staff"]
        >>> abjad.override(staff).TextScript.staff_padding = 8
        >>> leaves = abjad.select.leaves(staff)
        >>> groups = abjad.select.group_by_measure(leaves)
        >>> for group, label in zip(groups, labels):
        ...     markup = abjad.Markup(label)
        ...     abjad.attach(markup, group[0], direction=abjad.UP)
        ...

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
                    \override TextScript.staff-padding = 8
                }
                {
                    \time 6/16
                    c'16
                    ^ \markup {   0 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -1 becomes -1 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/4
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -2 becomes -2 }
                        [
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \time 6/16
                    c'16
                    ^ \markup {  -3 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -4 becomes -1 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/4
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -5 becomes -2 }
                        [
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \time 6/16
                    c'16
                    ^ \markup {  -6 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -7 becomes -1 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/4
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -8 becomes -2 }
                        [
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

        This modular formula ensures that rhythm-maker ``denominators`` are always
        respected: a very small number of extra counts never causes a ``16``-denominated
        tuplet to result in 8th- or quarter-note rhythms.

    ..  container:: example

        Fills divisions with 16th, 8th, quarter notes. Consumes 5:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([16, 8, 4], extra_counts=[0, 1]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 2/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \time 2/8
                    c'4
                    \times 4/5
                    {
                        \time 2/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \time 2/8
                    c'8
                    [
                    c'8
                    ]
                }
            >>

        >>> state = stack.maker.state
        >>> state
        {'divisions_consumed': 5, 'logical_ties_produced': 15}

        Advances 5 divisions; then consumes another 5 divisions:

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions, previous_state=state)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 2/8
                    c'4
                    \time 2/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \time 2/8
                    c'4
                    \times 4/5
                    {
                        \time 2/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

        >>> state = stack.maker.state
        >>> state
        {'divisions_consumed': 10, 'logical_ties_produced': 29}

    """

    denominator: str | int = "from_counts"
    denominators: typing.Sequence[int] = (8,)
    extra_counts: typing.Sequence[int] = (0,)

    def __post_init__(self):
        RhythmMaker.__post_init__(self)
        assert abjad.math.all_are_nonnegative_integer_powers_of_two(self.denominators)
        assert isinstance(self.denominators, typing.Sequence), repr(self.denominators)
        assert isinstance(self.extra_counts, typing.Sequence), repr(self.extra_counts)
        assert all(isinstance(_, int) for _ in self.extra_counts)

    def _make_music(self, divisions) -> list[abjad.Tuplet]:
        return _make_even_division_rhythm_maker_music(
            divisions,
            self.denominators,
            self_denominator=self.denominator,
            self_extra_counts=self.extra_counts,
            self_previous_state=self.previous_state,
            self_spelling=self.spelling,
            self_tag=self.tag,
        )


def _make_even_division_rhythm_maker_music(
    divisions,
    self_denominators,
    *,
    self_denominator=None,
    self_extra_counts=None,
    self_previous_state=None,
    self_spelling=None,
    self_tag=None,
):
    tuplets = []
    assert isinstance(self_previous_state, dict)
    divisions_consumed = self_previous_state.get("divisions_consumed", 0)
    divisions = [abjad.NonreducedFraction(_) for _ in divisions]
    denominators_ = list(self_denominators)
    denominators_ = abjad.sequence.rotate(denominators_, -divisions_consumed)
    denominators = abjad.CyclicTuple(denominators_)
    extra_counts_ = self_extra_counts or [0]
    extra_counts__ = list(extra_counts_)
    extra_counts__ = abjad.sequence.rotate(extra_counts__, -divisions_consumed)
    extra_counts = abjad.CyclicTuple(extra_counts__)
    for i, division in enumerate(divisions):
        if not abjad.math.is_positive_integer_power_of_two(division.denominator):
            message = "non-power-of-two divisions not implemented:"
            message += f" {division}."
            raise Exception(message)
        denominator_ = denominators[i]
        extra_count = extra_counts[i]
        basic_duration = abjad.Duration(1, denominator_)
        unprolated_note_count = None
        maker = abjad.NoteMaker(tag=self_tag)
        if division < 2 * basic_duration:
            notes = maker([0], [division])
        else:
            unprolated_note_count = division / basic_duration
            unprolated_note_count = int(unprolated_note_count)
            unprolated_note_count = unprolated_note_count or 1
            if 0 < extra_count:
                modulus = unprolated_note_count
                extra_count = extra_count % modulus
            elif extra_count < 0:
                modulus = int(math.ceil(unprolated_note_count / 2.0))
                extra_count = abs(extra_count) % modulus
                extra_count *= -1
            note_count = unprolated_note_count + extra_count
            durations = note_count * [basic_duration]
            notes = maker([0], durations)
            assert all(_.written_duration.denominator == denominator_ for _ in notes)
        tuplet_duration = abjad.Duration(division)
        tuplet = abjad.Tuplet.from_duration(tuplet_duration, notes, tag=self_tag)
        if self_denominator == "from_counts" and unprolated_note_count is not None:
            denominator = unprolated_note_count
            tuplet.denominator = denominator
        elif isinstance(self_denominator, int):
            tuplet.denominator = self_denominator
        tuplets.append(tuplet)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    return tuplets


@dataclasses.dataclass(order=True, slots=True, unsafe_hash=True)
class IncisedRhythmMaker(RhythmMaker):
    r"""
    Incised rhythm-maker.

    ..  container:: example

        Forces rest at every other tuplet:

        >>> def rest_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [1], 2)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=16,
        ...     ),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    r16
                    r4..
                    \time 3/8
                    c'4.
                    \time 4/8
                    r2
                    \time 3/8
                    c'4
                    ~
                    c'16
                    r16
                }
            >>

    ..  container:: example

        Ties nonlast tuplets:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         outer_divisions_only=True,
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     ),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 8/8
                    r8
                    c'2..
                    ~
                    \time 4/8
                    c'2
                    ~
                    \time 6/8
                    c'2
                    ~
                    c'8
                    r8
                }
            >>

    ..  container:: example

        Repeat-ties nonfirst tuplets:

        >>> def repeat_tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[1:]
        ...     result = [abjad.select.leaf(_, 0) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         outer_divisions_only=True,
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     ),
        ...     rmakers.repeat_tie(repeat_tie_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 8/8
                    r8
                    c'2..
                    \time 4/8
                    c'2
                    \repeatTie
                    \time 6/8
                    c'2
                    \repeatTie
                    ~
                    c'8
                    r8
                }
            >>

    ..  container:: example

        Add one extra count per tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         extra_counts=[1],
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         outer_divisions_only=True,
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     ),
        ...     rmakers.force_augmentation(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 16/9
                    {
                        \time 8/8
                        r16
                        c'2
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 8/5
                    {
                        \time 4/8
                        c'4
                        ~
                        c'16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/7
                    {
                        \time 6/8
                        c'4.
                        r16
                    }
                }
            >>

    ..  container:: example

        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[-1],
        ...         prefix_counts=[0, 1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=16,
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = 4 * [(5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    c'4
                    r16
                    \time 5/16
                    r16
                    c'8.
                    r16
                    \time 5/16
                    c'4
                    r16
                    \time 5/16
                    r16
                    c'8.
                    r16
                }
            >>

    ..  container:: example

        Fills divisions with notes. Incises outer divisions only:

        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[-8, -7],
        ...         prefix_counts=[2],
        ...         suffix_talea=[-3],
        ...         suffix_counts=[4],
        ...         talea_denominator=32,
        ...         outer_divisions_only=True,
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(5, 8), (5, 8), (5, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/8
                    r4
                    r8..
                    c'8
                    [
                    ~
                    c'32
                    ]
                    \time 5/8
                    c'2
                    ~
                    c'8
                    \time 5/8
                    c'4
                    r16.
                    r16.
                    r16.
                    r16.
                }
            >>

    ..  container:: example

        Fills divisions with rests. Incises outer divisions only:

        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[7, 8],
        ...         prefix_counts=[2],
        ...         suffix_talea=[3],
        ...         suffix_counts=[4],
        ...         talea_denominator=32,
        ...         fill_with_rests=True,
        ...         outer_divisions_only=True,
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(5, 8), (5, 8), (5, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/8
                    c'8..
                    c'4
                    r8
                    r32
                    \time 5/8
                    r2
                    r8
                    \time 5/8
                    r4
                    c'16.
                    [
                    c'16.
                    c'16.
                    c'16.
                    ]
                }
            >>

    ..  container:: example

        Spells durations with the fewest number of glyphs:

        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         outer_divisions_only=True,
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 8/8
                    r8
                    c'2..
                    \time 4/8
                    c'2
                    \time 6/8
                    c'2
                    ~
                    c'8
                    r8
                }
            >>

    ..  container:: example

        Forbids notes with written duration greater than or equal to ``1/2``:

        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         outer_divisions_only=True,
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...         spelling=rmakers.Spelling(forbidden_note_duration=abjad.Duration(1, 2)),
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 8/8
                    r8
                    c'4
                    ~
                    c'4
                    ~
                    c'4.
                    \time 4/8
                    c'4
                    ~
                    c'4
                    \time 6/8
                    c'4
                    ~
                    c'4
                    ~
                    c'8
                    r8
                }
            >>

    ..  container:: example

        Rewrites meter:

        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         outer_divisions_only=True,
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ...     rmakers.rewrite_meter(),
        ... )
        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> selections= stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 8/8
                    r8
                    c'2..
                    \time 4/8
                    c'2
                    \time 6/8
                    c'4.
                    ~
                    c'4
                    r8
                }
            >>

    ..  container:: example

        Makes augmentations:

        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         extra_counts=[1],
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         outer_divisions_only=True,
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     ),
        ...     rmakers.force_augmentation(),
        ...     rmakers.beam(),
        ...     tag=abjad.Tag("INCISED_RHYTHM_MAKER"),
        ... )
        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    %! INCISED_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! INCISED_RHYTHM_MAKER
                    \times 16/9
                    %! INCISED_RHYTHM_MAKER
                    {
                        \time 8/8
                        %! INCISED_RHYTHM_MAKER
                        r16
                        %! INCISED_RHYTHM_MAKER
                        c'2
                    %! INCISED_RHYTHM_MAKER
                    }
                    %! INCISED_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! INCISED_RHYTHM_MAKER
                    \times 8/5
                    %! INCISED_RHYTHM_MAKER
                    {
                        \time 4/8
                        %! INCISED_RHYTHM_MAKER
                        c'4
                        ~
                        %! INCISED_RHYTHM_MAKER
                        c'16
                    %! INCISED_RHYTHM_MAKER
                    }
                    %! INCISED_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! INCISED_RHYTHM_MAKER
                    \times 12/7
                    %! INCISED_RHYTHM_MAKER
                    {
                        \time 6/8
                        %! INCISED_RHYTHM_MAKER
                        c'4.
                        %! INCISED_RHYTHM_MAKER
                        r16
                    %! INCISED_RHYTHM_MAKER
                    }
                }
            >>

    """

    extra_counts: typing.Sequence[int] = ()
    incise: Incise = Incise()

    def __post_init__(self):
        RhythmMaker.__post_init__(self)
        assert isinstance(self.extra_counts, typing.Sequence), repr(self.extra_counts)
        assert abjad.math.all_are_nonnegative_integer_equivalent_numbers(
            self.extra_counts
        )
        assert isinstance(self.incise, Incise), repr(self.incise)

    @staticmethod
    def _make_division_incised_numeric_map(
        divisions,
        prefix_talea,
        prefix_counts,
        suffix_talea,
        suffix_counts,
        extra_counts,
        incise,
    ):
        numeric_map, prefix_talea_index, suffix_talea_index = [], 0, 0
        for pair_index, division in enumerate(divisions):
            prefix_length = prefix_counts[pair_index]
            suffix_length = suffix_counts[pair_index]
            start = prefix_talea_index
            stop = prefix_talea_index + prefix_length
            prefix = prefix_talea[start:stop]
            start = suffix_talea_index
            stop = suffix_talea_index + suffix_length
            suffix = suffix_talea[start:stop]
            prefix_talea_index += prefix_length
            suffix_talea_index += suffix_length
            prolation_addendum = extra_counts[pair_index]
            if isinstance(division, tuple):
                numerator = division[0] + (prolation_addendum % division[0])
            else:
                numerator = division.numerator + (
                    prolation_addendum % division.numerator
                )
            numeric_map_part = IncisedRhythmMaker._make_numeric_map_part(
                numerator, prefix, suffix, incise
            )
            numeric_map.append(numeric_map_part)
        return numeric_map

    @staticmethod
    def _make_middle_of_numeric_map_part(middle, incise):
        assert isinstance(incise, Incise), repr(incise)
        if not (incise.fill_with_rests):
            if not incise.outer_divisions_only:
                if 0 < middle:
                    if incise.body_ratio is not None:
                        shards = middle / incise.body_ratio
                        return tuple(shards)
                    else:
                        return (middle,)
                else:
                    return ()
            elif incise.outer_divisions_only:
                if 0 < middle:
                    return (middle,)
                else:
                    return ()
            else:
                raise Exception("must incise divisions or output.")
        else:
            if not incise.outer_divisions_only:
                if 0 < middle:
                    return (-abs(middle),)
                else:
                    return ()
            elif incise.outer_divisions_only:
                if 0 < middle:
                    return (-abs(middle),)
                else:
                    return ()
            else:
                raise Exception("must incise divisions or output.")

    def _make_music(self, divisions) -> list[abjad.Tuplet]:
        tuplets = _make_incised_rhythm_maker_music(
            divisions,
            extra_counts=self.extra_counts,
            incise=self.incise,
            spelling=self.spelling,
            tag=self.tag,
        )
        return tuplets

    @staticmethod
    def _make_numeric_map_part(
        numerator, prefix, suffix, incise, *, is_note_filled=True
    ):
        prefix_weight = abjad.math.weight(prefix)
        suffix_weight = abjad.math.weight(suffix)
        middle = numerator - prefix_weight - suffix_weight
        if numerator < prefix_weight:
            weights = [numerator]
            prefix = list(prefix)
            prefix = abjad.sequence.split(
                prefix, weights, cyclic=False, overhang=False
            )[0]
        middle = IncisedRhythmMaker._make_middle_of_numeric_map_part(middle, incise)
        suffix_space = numerator - prefix_weight
        if suffix_space <= 0:
            suffix = ()
        elif suffix_space < suffix_weight:
            weights = [suffix_space]
            suffix = list(suffix)
            suffix = abjad.sequence.split(
                suffix, weights, cyclic=False, overhang=False
            )[0]
        numeric_map_part = list(prefix) + list(middle) + list(suffix)
        return [abjad.Duration(_) for _ in numeric_map_part]

    @staticmethod
    def _make_output_incised_numeric_map(
        divisions,
        prefix_talea,
        prefix_counts,
        suffix_talea,
        suffix_counts,
        extra_counts,
        incise,
    ):
        numeric_map, prefix_talea_index, suffix_talea_index = [], 0, 0
        prefix_length, suffix_length = prefix_counts[0], suffix_counts[0]
        start = prefix_talea_index
        stop = prefix_talea_index + prefix_length
        prefix = prefix_talea[start:stop]
        start = suffix_talea_index
        stop = suffix_talea_index + suffix_length
        suffix = suffix_talea[start:stop]
        if len(divisions) == 1:
            prolation_addendum = extra_counts[0]
            if isinstance(divisions[0], abjad.NonreducedFraction):
                numerator = divisions[0].numerator
            else:
                numerator = divisions[0][0]
            numerator += prolation_addendum % numerator
            numeric_map_part = IncisedRhythmMaker._make_numeric_map_part(
                numerator, prefix, suffix, incise
            )
            numeric_map.append(numeric_map_part)
        else:
            prolation_addendum = extra_counts[0]
            if isinstance(divisions[0], tuple):
                numerator = divisions[0][0]
            else:
                numerator = divisions[0].numerator
            numerator += prolation_addendum % numerator
            numeric_map_part = IncisedRhythmMaker._make_numeric_map_part(
                numerator, prefix, (), incise
            )
            numeric_map.append(numeric_map_part)
            for i, division in enumerate(divisions[1:-1]):
                index = i + 1
                prolation_addendum = extra_counts[index]
                if isinstance(division, tuple):
                    numerator = division[0]
                else:
                    numerator = division.numerator
                numerator += prolation_addendum % numerator
                numeric_map_part = IncisedRhythmMaker._make_numeric_map_part(
                    numerator, (), (), incise
                )
                numeric_map.append(numeric_map_part)
            try:
                index = i + 2
                prolation_addendum = extra_counts[index]
            except UnboundLocalError:
                index = 1 + 2
                prolation_addendum = extra_counts[index]
            if isinstance(divisions[-1], tuple):
                numerator = divisions[-1][0]
            else:
                numerator = divisions[-1].numerator
            numerator += prolation_addendum % numerator
            numeric_map_part = IncisedRhythmMaker._make_numeric_map_part(
                numerator, (), suffix, incise
            )
            numeric_map.append(numeric_map_part)
        return numeric_map

    @staticmethod
    def _numeric_map_to_leaf_selections(numeric_map, lcd, *, spelling=None, tag=None):
        selections = []
        for numeric_map_part in numeric_map:
            numeric_map_part = [_ for _ in numeric_map_part if _ != abjad.Duration(0)]
            selection = _make_leaves_from_talea(
                numeric_map_part,
                lcd,
                forbidden_note_duration=spelling.forbidden_note_duration,
                forbidden_rest_duration=spelling.forbidden_rest_duration,
                increase_monotonic=spelling.increase_monotonic,
                tag=tag,
            )
            selections.append(selection)
        return selections

    @staticmethod
    def _prepare_input(incise, extra_counts):
        cyclic_prefix_talea = abjad.CyclicTuple(incise.prefix_talea)
        cyclic_prefix_counts = abjad.CyclicTuple(incise.prefix_counts or (0,))
        cyclic_suffix_talea = abjad.CyclicTuple(incise.suffix_talea)
        cyclic_suffix_counts = abjad.CyclicTuple(incise.suffix_counts or (0,))
        cyclic_extra_counts = abjad.CyclicTuple(extra_counts or (0,))
        return types.SimpleNamespace(
            prefix_talea=cyclic_prefix_talea,
            prefix_counts=cyclic_prefix_counts,
            suffix_talea=cyclic_suffix_talea,
            suffix_counts=cyclic_suffix_counts,
            extra_counts=cyclic_extra_counts,
        )


def _make_incised_rhythm_maker_music(
    divisions, *, extra_counts, incise, spelling, tag
) -> list[abjad.Tuplet]:
    prepared = IncisedRhythmMaker._prepare_input(incise, extra_counts)
    counts = types.SimpleNamespace(
        prefix_talea=prepared.prefix_talea,
        suffix_talea=prepared.suffix_talea,
        extra_counts=prepared.extra_counts,
    )
    talea_denominator = incise.talea_denominator
    scaled = _scale_rhythm_maker_input(divisions, talea_denominator, counts)
    if not incise.outer_divisions_only:
        numeric_map = IncisedRhythmMaker._make_division_incised_numeric_map(
            scaled.divisions,
            scaled.counts.prefix_talea,
            prepared.prefix_counts,
            scaled.counts.suffix_talea,
            prepared.suffix_counts,
            scaled.counts.extra_counts,
            incise,
        )
    else:
        assert incise.outer_divisions_only
        numeric_map = IncisedRhythmMaker._make_output_incised_numeric_map(
            scaled.divisions,
            scaled.counts.prefix_talea,
            prepared.prefix_counts,
            scaled.counts.suffix_talea,
            prepared.suffix_counts,
            scaled.counts.extra_counts,
            incise,
        )
    selections = IncisedRhythmMaker._numeric_map_to_leaf_selections(
        numeric_map, scaled.lcd, spelling=spelling, tag=tag
    )
    tuplets = _make_talea_rhythm_maker_tuplets(scaled.divisions, selections, tag)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets)
    return tuplets


@dataclasses.dataclass(order=True, slots=True, unsafe_hash=True)
class MultipliedDurationRhythmMaker(RhythmMaker):
    r"""
    Multiplied-duration rhythm-maker.

    ..  container:: example

        >>> rhythm_maker = rmakers.multiplied_duration()
        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    c'1 * 1/4
                    \time 3/16
                    c'1 * 3/16
                    \time 5/8
                    c'1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'1 * 1/3
                }
            >>

    ..  container:: example

        >>> rhythm_maker = rmakers.multiplied_duration()
        >>> rhythm_maker
        MultipliedDurationRhythmMaker(spelling=Spelling(forbidden_note_duration=None, forbidden_rest_duration=None, increase_monotonic=False), tag=Tag(string=''), prototype=<class 'abjad.score.Note'>, duration=Duration(1, 1))

    ..  container:: example

        Makes multiplied-duration whole notes when ``duration`` is unset:

        >>> rhythm_maker = rmakers.multiplied_duration()
        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    c'1 * 1/4
                    \time 3/16
                    c'1 * 3/16
                    \time 5/8
                    c'1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'1 * 1/3
                }
            >>

        Makes multiplied-duration half notes when ``duration=(1, 2)``:

        >>> rhythm_maker = rmakers.multiplied_duration(duration=(1, 2))
        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    c'2 * 2/4
                    \time 3/16
                    c'2 * 6/16
                    \time 5/8
                    c'2 * 10/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'2 * 2/3
                }
            >>

        Makes multiplied-duration quarter notes when ``duration=(1, 4)``:

        >>> rhythm_maker = rmakers.multiplied_duration(duration=(1, 4))
        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    c'4 * 4/4
                    \time 3/16
                    c'4 * 12/16
                    \time 5/8
                    c'4 * 20/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'4 * 4/3
                }
            >>

    ..  container:: example

        Makes multiplied-duration notes when ``prototype`` is unset:

        >>> rhythm_maker = rmakers.multiplied_duration()
        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    c'1 * 1/4
                    \time 3/16
                    c'1 * 3/16
                    \time 5/8
                    c'1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'1 * 1/3
                }
            >>

    ..  container:: example

        Makes multiplied-duration rests when ``prototype=abjad.Rest``:

        >>> rhythm_maker = rmakers.multiplied_duration(abjad.Rest)
        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    r1 * 1/4
                    \time 3/16
                    r1 * 3/16
                    \time 5/8
                    r1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    r1 * 1/3
                }
            >>

    ..  container:: example

        Makes multiplied-duration multimeasures rests when
        ``prototype=abjad.MultimeasureRest``:

        >>> rhythm_maker = rmakers.multiplied_duration(
        ...     abjad.MultimeasureRest
        ... )
        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    R1 * 1/4
                    \time 3/16
                    R1 * 3/16
                    \time 5/8
                    R1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    R1 * 1/3
                }
            >>

    ..  container:: example

        Makes multiplied-duration skips when ``prototype=abjad.Skip``:

        >>> rhythm_maker = rmakers.multiplied_duration(abjad.Skip)
        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    s1 * 1/4
                    \time 3/16
                    s1 * 3/16
                    \time 5/8
                    s1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    s1 * 1/3
                }
            >>

    """

    prototype: type = abjad.Note
    duration: abjad.Duration = abjad.Duration(1, 1)

    _prototypes = (abjad.MultimeasureRest, abjad.Note, abjad.Rest, abjad.Skip)

    def __post_init__(self):
        RhythmMaker.__post_init__(self)
        if self.prototype not in self._prototypes:
            message = "must be note, (multimeasure) rest, skip:\n"
            message += f"   {repr(self.prototype)}"
            raise Exception(message)
        assert isinstance(self.duration, abjad.Duration), repr(self.duration)

    def _make_music(self, divisions) -> list[abjad.MultimeasureRest | abjad.Skip]:
        component: abjad.MultimeasureRest | abjad.Skip
        components = []
        for division in divisions:
            division = abjad.NonreducedFraction(division)
            assert isinstance(division, abjad.NonreducedFraction)
            multiplier = division / self.duration
            if self.prototype is abjad.Note:
                component = self.prototype(
                    "c'", self.duration, multiplier=multiplier, tag=self.tag
                )
            else:
                component = self.prototype(
                    self.duration, multiplier=multiplier, tag=self.tag
                )
            components.append(component)
        return components


@dataclasses.dataclass(order=True, slots=True, unsafe_hash=True)
class NoteRhythmMaker(RhythmMaker):
    r"""
    Note rhtyhm-maker.

    ..  container:: example

        Silences every other logical tie:

        >>> def rest_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0], 2)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(rest_selector),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    r2
                    \time 3/8
                    c'4.
                    \time 4/8
                    r2
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Forces rest at every logical tie:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(lambda _: abjad.select.logical_ties(_)),
        ... )

        >>> divisions = [(4, 8), (3, 8), (4, 8), (5, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    r2
                    \time 3/8
                    r4.
                    \time 4/8
                    r2
                    \time 5/8
                    r2
                    r8
                }
            >>

    ..  container:: example

        Silences every other output division except for the first and last:

        >>> def rest_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0], 2)[1:-1]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(rest_selector),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    c'2
                    \time 3/8
                    c'4.
                    \time 4/8
                    r2
                    \time 3/8
                    c'4.
                    \time 2/8
                    c'4
                }
            >>

    ..  container:: example

        Beams each division:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.beam(lambda _: abjad.select.logical_ties(_, pitched=True)),
        ... )
        >>> divisions = [(5, 32), (5, 32)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/32
                    c'8
                    [
                    ~
                    c'32
                    ]
                    \time 5/32
                    c'8
                    [
                    ~
                    c'32
                    ]
                }
            >>

    ..  container:: example

        Beams divisions together:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.beam_groups(lambda _: abjad.select.logical_ties(_)),
        ... )
        >>> divisions = [(5, 32), (5, 32)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \set stemLeftBeamCount = 0
                    \set stemRightBeamCount = 1
                    \time 5/32
                    c'8
                    [
                    ~
                    \set stemLeftBeamCount = 3
                    \set stemRightBeamCount = 1
                    c'32
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 1
                    \time 5/32
                    c'8
                    ~
                    \set stemLeftBeamCount = 3
                    \set stemRightBeamCount = 0
                    c'32
                    ]
                }
            >>

    ..  container:: example

        Makes no beams:

        >>> stack = rmakers.NoteRhythmMaker()
        >>> divisions = [(5, 32), (5, 32)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/32
                    c'8
                    ~
                    c'32
                    \time 5/32
                    c'8
                    ~
                    c'32
                }
            >>

    ..  container:: example

        Does not tie across divisions:

        >>> stack = rmakers.NoteRhythmMaker()

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    c'2
                    \time 3/8
                    c'4.
                    \time 4/8
                    c'2
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Ties across divisions:

        >>> def tie_selector(argument):
        ...     result = abjad.select.logical_ties(argument)[:-1]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.tie(tie_selector),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'4.
                    ~
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Ties across every other logical tie:

        >>> def tie_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0], 2)
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.tie(tie_selector),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'4.
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Strips all ties:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.untie(),
        ... )
        >>> divisions = [(7, 16), (1, 4), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 7/16
                    c'4..
                    \time 1/4
                    c'4
                    \time 5/16
                    c'4
                    c'16
                }
            >>

    ..  container:: example

        Spells tuplets as diminutions:

        >>> stack = rmakers.NoteRhythmMaker()
        >>> divisions = [(5, 14), (3, 7)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak edge-height #'(0.7 . 0)
                    \times 8/14
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 5/14
                        c'2
                        ~
                        c'8
                    }
                    \tweak edge-height #'(0.7 . 0)
                    \times 4/7
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 3/7
                        c'2.
                    }
                }
            >>

    ..  container:: example

        Spells tuplets as augmentations:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_augmentation(),
        ... )
        >>> divisions = [(5, 14), (3, 7)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \tweak edge-height #'(0.7 . 0)
                    \times 16/14
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 5/14
                        c'4
                        ~
                        c'16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \tweak edge-height #'(0.7 . 0)
                    \times 8/7
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 3/7
                        c'4.
                    }
                }
            >>

    ..  container:: example

        Forces rest in logical tie 0:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(lambda _: abjad.select.logical_tie(_, 0)),
        ... )
        >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/8
                    r2
                    r8
                    \time 2/8
                    c'4
                    \time 2/8
                    c'4
                    \time 5/8
                    c'2
                    ~
                    c'8
                }
            >>

    ..  container:: example

        Forces rests in first two logical ties:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(lambda _: abjad.select.logical_ties(_)[:2]),
        ... )
        >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/8
                    r2
                    r8
                    \time 2/8
                    r4
                    \time 2/8
                    c'4
                    \time 5/8
                    c'2
                    ~
                    c'8
                }
            >>

    ..  container:: example

        Forces rests in first and last logical ties:

        >>> def rest_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0, -1])
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(rest_selector),
        ... )
        >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/8
                    r2
                    r8
                    \time 2/8
                    c'4
                    \time 2/8
                    c'4
                    \time 5/8
                    r2
                    r8
                }
            >>

    ..  container:: example

        Spells durations with the fewest number of glyphs:

        >>> rhythm_maker = rmakers.NoteRhythmMaker()
        >>> divisions = [(5, 8), (3, 8)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/8
                    c'2
                    ~
                    c'8
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Forbids notes with written duration greater than or equal to ``1/2``:

        >>> rhythm_maker = rmakers.NoteRhythmMaker(
        ...     spelling=rmakers.Spelling(forbidden_note_duration=abjad.Duration(1, 2))
        ... )
        >>> divisions = [(5, 8), (3, 8)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/8
                    c'4
                    ~
                    c'4
                    ~
                    c'8
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Rewrites meter:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.rewrite_meter(),
        ... )
        >>> divisions = [(3, 4), (6, 16), (9, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    c'2.
                    \time 6/16
                    c'4.
                    \time 9/16
                    c'4.
                    ~
                    c'8.
                }
            >>

    ..  container:: example

        >>> rhythm_maker = rmakers.NoteRhythmMaker(
        ...     tag=abjad.Tag("NOTE_RHYTHM_MAKER"),
        ... )
        >>> divisions = [(5, 8), (3, 8)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/8
                    %! NOTE_RHYTHM_MAKER
                    c'2
                    ~
                    %! NOTE_RHYTHM_MAKER
                    c'8
                    \time 3/8
                    %! NOTE_RHYTHM_MAKER
                    c'4.
                }
            >>

    """

    def _make_music(self, divisions) -> list[list[abjad.Leaf | abjad.Tuplet]]:
        return _make_note_rhythm_maker_music(
            divisions,
            spelling=self.spelling,
            tag=self.tag,
        )


def _make_note_rhythm_maker_music(
    divisions,
    *,
    spelling=None,
    tag=None,
) -> list[list[abjad.Leaf | abjad.Tuplet]]:
    selections = []
    leaf_maker = abjad.LeafMaker(
        increase_monotonic=spelling.increase_monotonic,
        forbidden_note_duration=spelling.forbidden_note_duration,
        forbidden_rest_duration=spelling.forbidden_rest_duration,
        tag=tag,
    )
    for division in divisions:
        selection = leaf_maker(pitches=0, durations=[division])
        selections.append(list(selection))
    return selections


@dataclasses.dataclass(order=True, slots=True, unsafe_hash=True)
class TaleaRhythmMaker(RhythmMaker):
    r"""
    Talea rhythm-maker.

    ..  container:: example

        Repeats talea of 1/16, 2/16, 3/16, 4/16:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'8
                    c'8.
                    ]
                    \time 4/8
                    c'4
                    c'16
                    [
                    c'8
                    c'16
                    ]
                    ~
                    \time 3/8
                    c'8
                    c'4
                    \time 4/8
                    c'16
                    [
                    c'8
                    c'8.
                    c'8
                    ]
                }
            >>

    ..  container:: example

        Silences first and last logical ties:

        >>> def rest_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0, -1])
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    r16
                    c'8
                    [
                    c'8.
                    ]
                    \time 4/8
                    c'4
                    c'16
                    [
                    c'8
                    c'16
                    ]
                    ~
                    \time 3/8
                    c'8
                    c'4
                    \time 4/8
                    c'16
                    [
                    c'8
                    c'8.
                    ]
                    r8
                }
            >>

    ..  container:: example

        Silences all logical ties. Then sustains first and last logical ties:

        >>> def rest_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0, -1])
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.force_rest(lambda _: abjad.select.logical_ties(_)),
        ...     rmakers.force_note(rest_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    r8
                    r8.
                    \time 4/8
                    r4
                    r16
                    r8
                    r16
                    \time 3/8
                    r8
                    r4
                    \time 4/8
                    r16
                    r8
                    r8.
                    c'8
                }
            >>

    ..  container:: example

        REGRESSION. Nonperiodic rest commands respect state.

        Only logical ties 0 and 2 are rested here:

        >>> def rest_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0, 2, 12])
        ...     return result
        >>> command = rmakers.stack(
        ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = command(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    r4
                    c'8
                    ~
                    \times 8/9
                    {
                        \time 4/8
                        c'8
                        r4
                        c'8.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'16
                        c'4
                        c'8.
                        ~
                    }
                    \time 4/8
                    c'16
                    c'4
                    c'8.
                }
            >>

        >>> state = command.maker.state
        >>> state
        {'divisions_consumed': 4, 'incomplete_last_note': True, 'logical_ties_produced': 8, 'talea_weight_consumed': 31}

    ..  container:: example

        REGRESSION. Spells tuplet denominator in terms of duration when denominator is
        given as a duration:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[1, 1, 2, 2]),
        ...     rmakers.denominator((1, 16)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        c'16
                        ]
                        ~
                    }
                    \times 8/9
                    {
                        \time 4/8
                        c'8.
                        [
                        c'16
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/8
                    {
                        \time 3/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                    }
                    \times 8/10
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Beams each division:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1], 16),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \time 4/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \time 4/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                }
            >>

    ..  container:: example

        Beams tuplets together:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1], 16),
        ...     rmakers.beam_groups(lambda _: abjad.select.tuplets(_)),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \set stemLeftBeamCount = 0
                    \set stemRightBeamCount = 2
                    \time 3/8
                    c'16
                    [
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 1
                    c'16
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 2
                    \time 4/8
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 1
                    c'16
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 2
                    \time 3/8
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 1
                    c'16
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 2
                    \time 4/8
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 0
                    c'16
                    ]
                }
            >>

    ..  container:: example

        Beams nothing:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1], 16),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    \time 4/8
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    \time 3/8
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    \time 4/8
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                }
            >>

    ..  container:: example

        Does not beam rests:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 1, 1, -1], 16),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    ]
                    r16
                    c'16
                    [
                    c'16
                    ]
                    \time 4/8
                    c'16
                    r16
                    c'16
                    [
                    c'16
                    c'16
                    ]
                    r16
                    c'16
                    [
                    c'16
                    ]
                    \time 3/8
                    c'16
                    r16
                    c'16
                    [
                    c'16
                    c'16
                    ]
                    r16
                    \time 4/8
                    c'16
                    [
                    c'16
                    c'16
                    ]
                    r16
                    c'16
                    [
                    c'16
                    c'16
                    ]
                    r16
                }
            >>

    ..  container:: example

        Does beam rests:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 1, 1, -1], 16),
        ...     rmakers.beam(beam_rests=True),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    r16
                    c'16
                    c'16
                    ]
                    \time 4/8
                    c'16
                    [
                    r16
                    c'16
                    c'16
                    c'16
                    r16
                    c'16
                    c'16
                    ]
                    \time 3/8
                    c'16
                    [
                    r16
                    c'16
                    c'16
                    c'16
                    r16
                    ]
                    \time 4/8
                    c'16
                    [
                    c'16
                    c'16
                    r16
                    c'16
                    c'16
                    c'16
                    r16
                    ]
                }
            >>

    ..  container:: example

        Beams rests with stemlets:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 1, 1, -1], 16),
        ...     rmakers.beam(
        ...         beam_rests=True,
        ...         stemlet_length=0.75,
        ...     ),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \override Staff.Stem.stemlet-length = 0.75
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    r16
                    c'16
                    \revert Staff.Stem.stemlet-length
                    c'16
                    ]
                    \override Staff.Stem.stemlet-length = 0.75
                    \time 4/8
                    c'16
                    [
                    r16
                    c'16
                    c'16
                    c'16
                    r16
                    c'16
                    \revert Staff.Stem.stemlet-length
                    c'16
                    ]
                    \override Staff.Stem.stemlet-length = 0.75
                    \time 3/8
                    c'16
                    [
                    r16
                    c'16
                    c'16
                    c'16
                    \revert Staff.Stem.stemlet-length
                    r16
                    ]
                    \override Staff.Stem.stemlet-length = 0.75
                    \time 4/8
                    c'16
                    [
                    c'16
                    c'16
                    r16
                    c'16
                    c'16
                    c'16
                    \revert Staff.Stem.stemlet-length
                    r16
                    ]
                }
            >>

    ..  container:: example

        Does not tie across divisions:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([5, 3, 3, 3], 16),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    c'4
                    ~
                    c'16
                    [
                    c'8.
                    ]
                    \time 3/8
                    c'8.
                    [
                    c'8.
                    ]
                    \time 4/8
                    c'4
                    ~
                    c'16
                    [
                    c'8.
                    ]
                    \time 3/8
                    c'8.
                    [
                    c'8.
                    ]
                }
            >>

    ..  container:: example

        Ties across divisions:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([5, 3, 3, 3], 16),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    c'4
                    ~
                    c'16
                    [
                    c'8.
                    ]
                    ~
                    \time 3/8
                    c'8.
                    [
                    c'8.
                    ]
                    ~
                    \time 4/8
                    c'4
                    ~
                    c'16
                    [
                    c'8.
                    ]
                    ~
                    \time 3/8
                    c'8.
                    [
                    c'8.
                    ]
                }
            >>

    ..  container:: example

        Ties across every other tuplet:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [0], 2)
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([5, 3, 3, 3], 16),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    c'4
                    ~
                    c'16
                    [
                    c'8.
                    ]
                    ~
                    \time 3/8
                    c'8.
                    [
                    c'8.
                    ]
                    \time 4/8
                    c'4
                    ~
                    c'16
                    [
                    c'8.
                    ]
                    ~
                    \time 3/8
                    c'8.
                    [
                    c'8.
                    ]
                }
            >>

    ..  container:: example

        TIE-CONSECUTIVE-NOTES RECIPE:

        >>> def selector(argument):
        ...     result = abjad.select.runs(argument)
        ...     result = [abjad.select.notes(_)[:-1] for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([5, -3, 3, 3], 16),
        ...     rmakers.untie(selector),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/8
                    c'4
                    ~
                    c'16
                    r8.
                    \time 3/8
                    c'8.
                    [
                    ~
                    c'8.
                    ]
                    ~
                    \time 4/8
                    c'4
                    ~
                    c'16
                    r8.
                    \time 3/8
                    c'8.
                    [
                    ~
                    c'8.
                    ]
                }
            >>

    ..  container:: example

        REGRESSION. Commands survive copy:

        >>> import dataclasses
        >>> command = rmakers.stack(
        ...     rmakers.talea([5, -3, 3, 3], 16),
        ...     rmakers.extract_trivial(),
        ... )
        >>> new_command = dataclasses.replace(command)
        >>> new_command
        Stack(maker=TaleaRhythmMaker(spelling=Spelling(forbidden_note_duration=None, forbidden_rest_duration=None, increase_monotonic=False), tag=Tag(string=''), extra_counts=(), read_talea_once_only=False, talea=Talea(counts=[5, -3, 3, 3], denominator=16, end_counts=(), preamble=())), commands=(ExtractTrivialCommand(selector=None),), preprocessor=None, tag=Tag(string=''))

        >>> command == new_command
        True

    ..  container:: example

        Working with ``denominator``.

        Reduces terms in tuplet ratio to relative primes when no tuplet command is given:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[1, 1, 2, 2]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        c'16
                        ]
                        ~
                    }
                    \times 8/9
                    {
                        \time 4/8
                        c'8.
                        [
                        c'16
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                    }
                }
            >>

        REGRESSION. Spells tuplet denominator in terms of duration when denominator is
        given as a duration:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[1, 1, 2, 2]),
        ...     rmakers.denominator((1, 16)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        c'16
                        ]
                        ~
                    }
                    \times 8/9
                    {
                        \time 4/8
                        c'8.
                        [
                        c'16
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/8
                    {
                        \time 3/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                    }
                    \times 8/10
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Working with ``diminution``.

        Makes diminished tuplets when ``diminution`` is true (or when no tuplet command
        is given):

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1], 16, extra_counts=[0, -1]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                }
            >>

        Makes augmented tuplets when ``diminution`` is set to false:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1], 16, extra_counts=[0, -1]),
        ...     rmakers.beam(),
        ...     rmakers.force_augmentation(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Working with ``trivialize``.

        Leaves trivializable tuplets as-is when no tuplet command is given. The tuplets
        in measures 2 and 4 can be written as trivial tuplets, but they are not:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([3, 3, 6, 6], 16, extra_counts=[0, 4]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \times 2/3
                    {
                        \time 4/8
                        c'4.
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \times 2/3
                    {
                        \time 4/8
                        c'4.
                        c'4.
                    }
                }
            >>

        Rewrites trivializable tuplets as trivial (1:1) tuplets when ``trivialize`` is
        true:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([3, 3, 6, 6], 16, extra_counts=[0, 4]),
        ...     rmakers.trivialize(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        c'4
                    }
                }
            >>

        REGRESSION #907a. Rewrites trivializable tuplets even when tuplets contain
        multiple ties:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([3, 3, 6, 6], 16, extra_counts=[0, 4]),
        ...     rmakers.trivialize(),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        c'4
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        c'4
                    }
                }
            >>

        REGRESSION #907b. Rewrites trivializable tuplets even when tuplets contain very
        long ties:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([3, 3, 6, 6], 16, extra_counts=[0, 4]),
        ...     rmakers.trivialize(),
        ...     rmakers.tie(lambda _: abjad.select.notes(_)[:-1]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        ~
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        ~
                        c'4
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        ~
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        ~
                        c'4
                    }
                }
            >>

    ..  container:: example

        Working with ``rewrite_rest_filled``.

        Makes rest-filled tuplets when ``rewrite_rest_filled`` is false (or when no
        tuplet command is given):

        >>> stack = rmakers.stack(
        ...     rmakers.talea([3, 3, -6, -6], 16, extra_counts=[1, 0]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        r16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        r4
                        r16
                        r8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        r8.
                        c'8.
                        [
                        c'16
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'8
                        r4.
                    }
                }
            >>

        Rewrites rest-filled tuplets when ``rewrite_rest_filled`` is true:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([3, 3, -6, -6], 16, extra_counts=[1, 0]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_rest_filled(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        r16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        r2
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        r8.
                        c'8.
                        [
                        c'16
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'8
                        r4.
                    }
                }
            >>

    ..  container:: example

        No rest commands:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'8
                    c'8.
                    ]
                    \time 4/8
                    c'4
                    c'16
                    [
                    c'8
                    c'16
                    ]
                    ~
                    \time 3/8
                    c'8
                    c'4
                    \time 4/8
                    c'16
                    [
                    c'8
                    c'8.
                    c'8
                    ]
                }
            >>

    ..  container:: example

        Silences every other output division:

        >>> def rest_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [1], 2)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'8
                    c'8.
                    ]
                    \time 4/8
                    r2
                    \time 3/8
                    c'8
                    c'4
                    \time 4/8
                    r2
                }
            >>

    ..  container:: example

        Sustains every other output division:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [1], 2)
        ...     result = [abjad.select.notes(_)[:-1] for _ in result]
        ...     return result
        >>> def sustained_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [1], 2)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.rewrite_sustained(sustained_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'8
                    c'8.
                    ]
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'8
                    c'4
                    \time 4/8
                    c'2
                }
            >>

    ..  container:: example

        REGRESSION. Nonperiodic rest commands respect state.

        TODO: change TUPLET selector to GROUP_BY_MEASURE selector and allow to be statal
        with divisions_produced. Possibly also allow tuplet selectors to be statal by
        tallying tuplet_produced in state metadata.

        Only tuplets 0 and 2 are rested here:

        >>> def rest_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [0, 2, 7])
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    r4.
                    \times 8/9
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'8.
                    }
                    \time 3/8
                    r4.
                    \time 4/8
                    c'16
                    c'4
                    c'8.
                }
            >>

        >>> state = stack.maker.state
        >>> state
        {'divisions_consumed': 4, 'incomplete_last_note': True, 'logical_ties_produced': 8, 'talea_weight_consumed': 31}

    ..  container:: example

        REGRESSION. Periodic rest commands also respect state.

        >>> def rest_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [2], 3)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'4
                    c'8
                    ~
                    \times 8/9
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'8.
                    }
                    \time 3/8
                    r4.
                    \time 4/8
                    c'16
                    c'4
                    c'8.
                }
            >>

        >>> state = stack.maker.state
        >>> state
        {'divisions_consumed': 4, 'incomplete_last_note': True, 'logical_ties_produced': 8, 'talea_weight_consumed': 31}

    ..  container:: example

        Forces the first leaf and the last two leaves to be rests:

        >>> def rest_selector(argument):
        ...     result = abjad.select.leaves(argument)
        ...     result = abjad.select.get(result, [0, -2, -1])
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    r16
                    c'8
                    [
                    c'8.
                    ]
                    \time 4/8
                    c'4
                    c'16
                    [
                    c'8
                    c'16
                    ]
                    ~
                    \time 3/8
                    c'8
                    c'4
                    \time 4/8
                    c'16
                    [
                    c'8
                    ]
                    r8.
                    r8
                }
            >>

    ..  container:: example

        Forces rest at last leaf of every tuplet:

        >>> def rest_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.leaf(_, 0) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.force_rest(rest_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    r16
                    c'8
                    [
                    c'8.
                    ]
                    \time 4/8
                    r4
                    c'16
                    [
                    c'8
                    c'16
                    ]
                    \time 3/8
                    r8
                    c'4
                    \time 4/8
                    r16
                    c'8
                    [
                    c'8.
                    c'8
                    ]
                }
            >>

    ..  container:: example

        Spells nonassignable durations with monontonically decreasing durations:

        >>> stack = rmakers.stack(
        ...     rmakers.talea(
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=False),
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(5, 8), (5, 8), (5, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/8
                    c'4
                    ~
                    c'16
                    c'4
                    ~
                    c'16
                    \time 5/8
                    c'4
                    ~
                    c'16
                    c'4
                    ~
                    c'16
                    \time 5/8
                    c'4
                    ~
                    c'16
                    c'4
                    ~
                    c'16
                }
            >>

    ..  container:: example

        Spells nonassignable durations with monontonically increasing durations:

        >>> stack = rmakers.stack(
        ...     rmakers.talea(
        ...         [5], 16,
        ...         spelling=rmakers.Spelling(increase_monotonic=True),
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(5, 8), (5, 8), (5, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 5/8
                    c'16
                    ~
                    c'4
                    c'16
                    ~
                    c'4
                    \time 5/8
                    c'16
                    ~
                    c'4
                    c'16
                    ~
                    c'4
                    \time 5/8
                    c'16
                    ~
                    c'4
                    c'16
                    ~
                    c'4
                }
            >>

    ..  container:: example

        Forbids no durations:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 1, 1, 1, 4, 4], 16),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    c'4
                    \time 3/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    c'4
                    c'4
                }
            >>

    ..  container:: example

        Forbids durations equal to ``1/4`` or greater:

        >>> stack = rmakers.stack(
        ...     rmakers.talea(
        ...         [1, 1, 1, 1, 4, 4], 16,
        ...         spelling=rmakers.Spelling(forbidden_note_duration=abjad.Duration(1, 4)),
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    c'8
                    ~
                    c'8
                    ]
                    \time 3/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'8
                    ~
                    c'8
                    c'8
                    ~
                    c'8
                    ]
                }
            >>

        Rewrites forbidden durations with smaller durations tied together.

    ..  container:: example

        Rewrites meter:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([5, 4], 16),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ...     rmakers.rewrite_meter(),
        ... )
        >>> divisions = [(3, 4), (3, 4), (3, 4)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    [
                    c'8.
                    ]
                    ~
                    c'16
                    [
                    c'8.
                    ]
                    ~
                    \time 3/4
                    c'8
                    [
                    c'8
                    ]
                    ~
                    c'8
                    [
                    c'8
                    ]
                    ~
                    c'8.
                    [
                    c'16
                    ]
                    ~
                    \time 3/4
                    c'8.
                    [
                    c'16
                    ]
                    ~
                    c'4
                    c'4
                }
            >>

    ..  container:: example

        No extra counts:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'8
                    c'8.
                    ]
                    \time 4/8
                    c'4
                    c'16
                    [
                    c'8
                    c'16
                    ]
                    ~
                    \time 3/8
                    c'8
                    c'4
                    \time 4/8
                    c'16
                    [
                    c'8
                    c'8.
                    c'8
                    ]
                }
            >>

    ..  container:: example

        Adds one extra count to every other division:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[0, 1]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                    }
                    \times 8/9
                    {
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16
                        c'4
                        c'16
                    }
                    \times 8/9
                    {
                        \time 4/8
                        c'8
                        [
                        c'8.
                        ]
                        c'4
                    }
                }
            >>

    ..  container:: example

        Adds two extra counts to every other division:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[0, 2]),
        ...     rmakers.beam(),
        ... )

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'4
                        c'16
                        [
                        c'16
                        ]
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'16
                        [
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'16
                        ]
                    }
                }
            >>

        The duration of each added count equals the duration of each count in the
        rhythm-maker's input talea.

    ..  container:: example

        Removes one count from every other division:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[0, -1]),
        ...     rmakers.beam(),
        ... )

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 8/7
                    {
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 8/7
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'8
                        c'8.
                        ]
                    }
                }
            >>

    ..  container:: example

        Reads talea cyclically:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )

        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'16
                    [
                    c'8
                    c'8.
                    ]
                    \time 3/8
                    c'4
                    c'16
                    [
                    c'16
                    ]
                    ~
                    \time 3/8
                    c'16
                    [
                    c'8.
                    c'8
                    ]
                    ~
                    \time 3/8
                    c'8
                    [
                    c'16
                    c'8
                    c'16
                    ]
                }
            >>

    ..  container:: example

        Reads talea once only:

        >>> stack = rmakers.stack(
        ...     rmakers.talea(
        ...         [1, 2, 3, 4],
        ...         16,
        ...         read_talea_once_only=True,
        ...     ),
        ...     rmakers.beam(),
        ... )

        Calling stack on these divisions raises an exception because talea is too
        short to read once only:

        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> stack(divisions)
        Traceback (most recent call last):
            ...
        Exception: CyclicTuple(items=()) + CyclicTuple(items=(1, 2, 3, 4)) is too short to read [6, 6, 6, 6] once.

        Set to true to ensure talea is long enough to cover all divisions without
        repeating.

        Provides way of using talea noncyclically when, for example, interpolating from
        short durations to long durations.

    ..  container:: example

        Consumes 4 divisions and 31 counts:

        >>> command = rmakers.stack(
        ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = command(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'4
                    c'8
                    ~
                    \times 8/9
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'8.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'16
                        c'4
                        c'8.
                        ~
                    }
                    \time 4/8
                    c'16
                    c'4
                    c'8.
                }
            >>

        >>> state = command.maker.state
        >>> state
        {'divisions_consumed': 4, 'incomplete_last_note': True, 'logical_ties_produced': 8, 'talea_weight_consumed': 31}

        Advances 4 divisions and 31 counts; then consumes another 4 divisions and 31
        counts:

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = command(divisions, previous_state=state)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        c'4
                        c'8
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'4
                    }
                    \time 3/8
                    c'4
                    c'8
                    ~
                    \times 8/9
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'8.
                    }
                }
            >>

        >>> state = command.maker.state
        >>> state
        {'divisions_consumed': 8, 'incomplete_last_note': True, 'logical_ties_produced': 16, 'talea_weight_consumed': 63}

        Advances 8 divisions and 62 counts; then consumes 4 divisions and 31 counts:

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = command(divisions, previous_state=state)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'16
                        c'4
                        c'8.
                        ~
                    }
                    \time 4/8
                    c'16
                    c'4
                    c'8.
                    ~
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        c'4
                        c'8
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'4
                    }
                }
            >>

        >>> state = command.maker.state
        >>> state
        {'divisions_consumed': 12, 'incomplete_last_note': True, 'logical_ties_produced': 24, 'talea_weight_consumed': 96}

    ..  container:: example

        >>> stack = rmakers.stack(
        ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[0, 1]),
        ...     rmakers.beam(),
        ...     tag=abjad.Tag("TALEA_RHYTHM_MAKER"),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    %! TALEA_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TALEA_RHYTHM_MAKER
                    \times 1/1
                    %! TALEA_RHYTHM_MAKER
                    {
                        \time 3/8
                        %! TALEA_RHYTHM_MAKER
                        c'16
                        %! TALEA_RHYTHM_MAKER
                        [
                        %! TALEA_RHYTHM_MAKER
                        c'8
                        %! TALEA_RHYTHM_MAKER
                        c'8.
                        %! TALEA_RHYTHM_MAKER
                        ]
                    %! TALEA_RHYTHM_MAKER
                    }
                    %! TALEA_RHYTHM_MAKER
                    \times 8/9
                    %! TALEA_RHYTHM_MAKER
                    {
                        \time 4/8
                        %! TALEA_RHYTHM_MAKER
                        c'4
                        %! TALEA_RHYTHM_MAKER
                        c'16
                        %! TALEA_RHYTHM_MAKER
                        [
                        %! TALEA_RHYTHM_MAKER
                        c'8
                        %! TALEA_RHYTHM_MAKER
                        c'8
                        %! TALEA_RHYTHM_MAKER
                        ]
                        ~
                    %! TALEA_RHYTHM_MAKER
                    }
                    %! TALEA_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TALEA_RHYTHM_MAKER
                    \times 1/1
                    %! TALEA_RHYTHM_MAKER
                    {
                        \time 3/8
                        %! TALEA_RHYTHM_MAKER
                        c'16
                        %! TALEA_RHYTHM_MAKER
                        c'4
                        %! TALEA_RHYTHM_MAKER
                        c'16
                    %! TALEA_RHYTHM_MAKER
                    }
                    %! TALEA_RHYTHM_MAKER
                    \times 8/9
                    %! TALEA_RHYTHM_MAKER
                    {
                        \time 4/8
                        %! TALEA_RHYTHM_MAKER
                        c'8
                        %! TALEA_RHYTHM_MAKER
                        [
                        %! TALEA_RHYTHM_MAKER
                        c'8.
                        %! TALEA_RHYTHM_MAKER
                        ]
                        %! TALEA_RHYTHM_MAKER
                        c'4
                    %! TALEA_RHYTHM_MAKER
                    }
                }
            >>

    ..  container:: example

        Working with ``preamble``.

        Preamble less than total duration:

        >>> stack = rmakers.stack(
        ...     rmakers.talea(
        ...         [8, -4, 8],
        ...         32,
        ...         preamble=[1, 1, 1, 1],
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'32
                    [
                    c'32
                    c'32
                    c'32
                    ]
                    c'4
                    \time 4/8
                    r8
                    c'4
                    c'8
                    ~
                    \time 3/8
                    c'8
                    r8
                    c'8
                    ~
                    \time 4/8
                    c'8
                    c'4
                    r8
                }
            >>

        Preamble more than total duration; ignores counts:

        >>> stack = rmakers.stack(
        ...     rmakers.talea(
        ...         [8, -4, 8],
        ...         32,
        ...         preamble=[32, 32, 32, 32],
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'4.
                    ~
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'8
                    c'4
                    ~
                    \time 4/8
                    c'2
                }
            >>

    ..  container:: example

        Working with ``end_counts``.

        >>> stack = rmakers.stack(
        ...     rmakers.talea(
        ...         [8, -4, 8],
        ...         32,
        ...         end_counts=[1, 1, 1, 1],
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'4
                    r8
                    \time 4/8
                    c'4
                    c'4
                    \time 3/8
                    r8
                    c'4
                    \time 4/8
                    c'4
                    r8
                    c'32
                    [
                    c'32
                    c'32
                    c'32
                    ]
                }
            >>

    ..  container:: example

        REGRESSION. End counts leave 5-durated tie in tact:

        >>> stack = rmakers.stack(
        ...     rmakers.talea(
        ...         [6],
        ...         16,
        ...         end_counts=[1],
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 3/8
                    c'4.
                    \time 3/8
                    c'4
                    ~
                    c'16
                    [
                    c'16
                    ]
                }
            >>

    """

    extra_counts: typing.Sequence[int] = ()
    read_talea_once_only: bool = False
    spelling: Spelling = Spelling()
    talea: Talea = Talea(counts=[1], denominator=16)

    def __post_init__(self):
        RhythmMaker.__post_init__(self)
        assert all(isinstance(_, int) for _ in self.extra_counts)
        assert isinstance(self.read_talea_once_only, bool)
        assert isinstance(self.talea, Talea), repr(self.talea)

    def _make_music(self, divisions) -> list[abjad.Tuplet]:
        tuplets = _make_talea_rhythm_maker_music(
            divisions,
            self.extra_counts,
            self.previous_state,
            self.read_talea_once_only,
            self.spelling,
            self.state,
            self.talea,
            self.tag,
        )
        return tuplets


def _make_talea_rhythm_maker_music(
    divisions,
    self_extra_counts,
    self_previous_state,
    self_read_talea_once_only,
    self_spelling,
    self_state,
    self_talea,
    self_tag,
):
    prepared = _prepare_talea_rhythm_maker_input(
        self_extra_counts, self_previous_state, self_talea
    )
    divisions = list(divisions)
    scaled = _scale_rhythm_maker_input(divisions, self_talea.denominator, prepared)
    assert scaled.counts.talea
    if scaled.counts.talea:
        numeric_map, expanded_talea = _make_numeric_map(
            scaled.divisions,
            scaled.counts.preamble,
            scaled.counts.talea,
            scaled.counts.extra_counts,
            scaled.counts.end_counts,
            self_read_talea_once_only,
        )
        if expanded_talea is not None:
            unscaled_talea = expanded_talea
        else:
            unscaled_talea = prepared.talea
        talea_weight_consumed = sum(abjad.sequence.weight(_) for _ in numeric_map)
        leaf_lists = _make_talea_rhythm_make_leaf_lists(
            numeric_map, scaled.lcd, self_spelling, self_tag
        )
        if not scaled.counts.extra_counts:
            tuplets = [abjad.Tuplet(1, _) for _ in leaf_lists]
        else:
            tuplets = _make_talea_rhythm_maker_tuplets(
                scaled.divisions, leaf_lists, self_tag
            )
        _apply_ties_to_split_notes(
            tuplets,
            prepared.end_counts,
            prepared.preamble,
            unscaled_talea,
            self_talea,
        )
    for tuplet in abjad.iterate.components(tuplets, abjad.Tuplet):
        tuplet.normalize_multiplier()
    assert isinstance(self_state, dict)
    advanced_talea = Talea(
        counts=prepared.talea,
        denominator=self_talea.denominator,
        end_counts=prepared.end_counts,
        preamble=prepared.preamble,
    )
    if "+" in prepared.talea or "-" in prepared.talea:
        pass
    elif talea_weight_consumed not in advanced_talea:
        last_leaf = abjad.get.leaf(tuplets, -1)
        if isinstance(last_leaf, abjad.Note):
            self_state["incomplete_last_note"] = True
    string = "talea_weight_consumed"
    assert isinstance(self_previous_state, dict)
    self_state[string] = self_previous_state.get(string, 0)
    self_state[string] += talea_weight_consumed
    return tuplets


def _apply_ties_to_split_notes(
    tuplets,
    unscaled_end_counts,
    unscaled_preamble,
    unscaled_talea,
    self_talea,
):
    leaves = abjad.select.leaves(tuplets)
    written_durations = [leaf.written_duration for leaf in leaves]
    written_durations = list(written_durations)
    total_duration = abjad.sequence.weight(written_durations)
    preamble_weights = []
    if unscaled_preamble:
        preamble_weights = []
        for numerator in unscaled_preamble:
            pair = (numerator, self_talea.denominator)
            duration = abjad.Duration(*pair)
            weight = abs(duration)
            preamble_weights.append(weight)
    preamble_duration = sum(preamble_weights)
    if total_duration <= preamble_duration:
        preamble_parts = abjad.sequence.partition_by_weights(
            written_durations,
            weights=preamble_weights,
            allow_part_weights=abjad.MORE,
            cyclic=True,
            overhang=True,
        )
        talea_parts = []
    else:
        assert preamble_duration < total_duration
        preamble_parts = abjad.sequence.partition_by_weights(
            written_durations,
            weights=preamble_weights,
            allow_part_weights=abjad.EXACT,
            cyclic=False,
            overhang=False,
        )
        talea_weights = []
        for numerator in unscaled_talea:
            pair = (numerator, self_talea.denominator)
            weight = abs(abjad.Duration(*pair))
            talea_weights.append(weight)
        preamble_length = len(abjad.sequence.flatten(preamble_parts))
        talea_written_durations = written_durations[preamble_length:]
        talea_parts = abjad.sequence.partition_by_weights(
            talea_written_durations,
            weights=talea_weights,
            allow_part_weights=abjad.MORE,
            cyclic=True,
            overhang=True,
        )
    parts = preamble_parts + talea_parts
    part_durations = abjad.sequence.flatten(parts)
    assert part_durations == list(written_durations)
    counts = [len(part) for part in parts]
    parts = abjad.sequence.partition_by_counts(leaves, counts)
    for i, part in enumerate(parts):
        if any(isinstance(_, abjad.Rest) for _ in part):
            continue
        if len(part) == 1:
            continue
        abjad.tie(part)
    # TODO: this will need to be generalized and better tested:
    if unscaled_end_counts:
        total = len(unscaled_end_counts)
        end_leaves = leaves[-total:]
        for leaf in reversed(end_leaves):
            previous_leaf = abjad.get.leaf(leaf, -1)
            if previous_leaf is not None:
                abjad.detach(abjad.Tie, previous_leaf)


def _make_talea_rhythm_make_leaf_lists(numeric_map, talea_denominator, spelling, tag):
    leaf_lists = []
    for map_division in numeric_map:
        leaf_list = _make_leaves_from_talea(
            map_division,
            talea_denominator,
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        leaf_lists.append(leaf_list)
    return leaf_lists


def _prepare_talea_rhythm_maker_input(
    self_extra_counts, self_previous_state, self_talea
):
    talea_weight_consumed = self_previous_state.get("talea_weight_consumed", 0)
    talea = self_talea.advance(talea_weight_consumed)
    end_counts = talea.end_counts or ()
    preamble = talea.preamble or ()
    talea = talea.counts or ()
    talea = abjad.CyclicTuple(talea)
    extra_counts = list(self_extra_counts or [])
    divisions_consumed = self_previous_state.get("divisions_consumed", 0)
    extra_counts = abjad.sequence.rotate(extra_counts, -divisions_consumed)
    extra_counts = abjad.CyclicTuple(extra_counts)
    return types.SimpleNamespace(
        end_counts=end_counts,
        extra_counts=extra_counts,
        preamble=preamble,
        talea=talea,
    )


def _make_numeric_map(
    divisions, preamble, talea, extra_counts, end_counts, read_talea_once_only
):
    assert all(isinstance(_, int) for _ in end_counts), repr(end_counts)
    assert all(isinstance(_, int) for _ in preamble), repr(preamble)
    for count in talea:
        assert isinstance(count, int) or count in "+-", repr(talea)
    if "+" in talea or "-" in talea:
        assert not preamble, repr(preamble)
    prolated_divisions = _make_prolated_divisions(divisions, extra_counts)
    prolated_divisions = [abjad.NonreducedFraction(_) for _ in prolated_divisions]
    if not preamble and not talea:
        return prolated_divisions, None
    prolated_numerators = [_.numerator for _ in prolated_divisions]
    expanded_talea = None
    if "-" in talea or "+" in talea:
        total_weight = sum(prolated_numerators)
        talea_ = list(talea)
        if "-" in talea:
            index = talea_.index("-")
        else:
            index = talea_.index("+")
        talea_[index] = 0
        explicit_weight = sum([abs(_) for _ in talea_])
        implicit_weight = total_weight - explicit_weight
        if "-" in talea:
            implicit_weight *= -1
        talea_[index] = implicit_weight
        expanded_talea = tuple(talea_)
        talea = abjad.CyclicTuple(expanded_talea)
    result = _split_talea_extended_to_weights(
        preamble, read_talea_once_only, talea, prolated_numerators
    )
    if end_counts:
        end_counts = list(end_counts)
        end_weight = abjad.sequence.weight(end_counts)
        division_weights = [abjad.sequence.weight(_) for _ in result]
        counts = abjad.sequence.flatten(result)
        counts_weight = abjad.sequence.weight(counts)
        assert end_weight <= counts_weight, repr(end_counts)
        left = counts_weight - end_weight
        right = end_weight
        counts = abjad.sequence.split(counts, [left, right])
        counts = counts[0] + end_counts
        assert abjad.sequence.weight(counts) == counts_weight
        result = abjad.sequence.partition_by_weights(counts, division_weights)
    for sequence in result:
        assert all(isinstance(_, int) for _ in sequence), repr(sequence)
    return result, expanded_talea


def _make_prolated_divisions(divisions, extra_counts):
    prolated_divisions = []
    for i, division in enumerate(divisions):
        if not extra_counts:
            prolated_divisions.append(division)
            continue
        prolation_addendum = extra_counts[i]
        try:
            numerator = division.numerator
        except AttributeError:
            numerator = division[0]
        if 0 <= prolation_addendum:
            prolation_addendum %= numerator
        else:
            # NOTE: do not remove the following (nonfunctional) if-else;
            #       preserved for backwards compatability.
            use_old_extra_counts_logic = False
            if use_old_extra_counts_logic:
                prolation_addendum %= numerator
            else:
                prolation_addendum %= -numerator
        if isinstance(division, tuple):
            numerator, denominator = division
        else:
            numerator, denominator = division.pair
        prolated_division = (numerator + prolation_addendum, denominator)
        prolated_divisions.append(prolated_division)
    return prolated_divisions


def _split_talea_extended_to_weights(preamble, read_talea_once_only, talea, weights):
    assert abjad.math.all_are_positive_integers(weights)
    preamble_weight = abjad.math.weight(preamble)
    talea_weight = abjad.math.weight(talea)
    weight = abjad.math.weight(weights)
    if read_talea_once_only and preamble_weight + talea_weight < weight:
        message = f"{preamble!s} + {talea!s} is too short"
        message += f" to read {weights} once."
        raise Exception(message)
    if weight <= preamble_weight:
        talea = list(preamble)
        talea = abjad.sequence.truncate(talea, weight=weight)
    else:
        weight -= preamble_weight
        talea = abjad.sequence.repeat_to_weight(talea, weight)
        talea = list(preamble) + list(talea)
    talea = abjad.sequence.split(talea, weights, cyclic=True)
    return talea


@dataclasses.dataclass(order=True, slots=True, unsafe_hash=True)
class TupletRhythmMaker(RhythmMaker):
    r"""
    Tuplet rhythm-maker.

    ..  container:: example

        Makes tuplets with ``3:2`` ratios:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, 2)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 1/2
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8.
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8.
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, -1), (3, 1)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 1/2
                        c'4
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'4.
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/16
                        c'8.
                        r8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4
                    {
                        \time 5/16
                        c'8.
                        [
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Beams each division:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1, 1, 1)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/8
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        [
                        c'16.
                        c'16.
                        c'16.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 6/8
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
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

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1, 1, 1)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/8
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        [
                        c'16.
                        c'16.
                        c'16.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 6/8
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
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

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1, 2, 1, 1), (3, 1, 1)]),
        ...     rmakers.beam_groups(lambda _: abjad.select.tuplets(_)),
        ... )
        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/9
                    {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        \time 5/8
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
                    \times 3/5
                    {
                        \time 3/8
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
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 1
                        \time 6/8
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
                    \times 4/5
                    {
                        \time 4/8
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

        >>> rhythm_maker = rmakers.tuplet([(1, 1, 2, 1, 1), (3, 1, 1)])
        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/9
                    {
                        \time 5/8
                        c'8.
                        c'8.
                        c'4.
                        c'8.
                        c'8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        c'8
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 6/8
                        c'8
                        c'8
                        c'4
                        c'8
                        c'8
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'4.
                        c'8
                        c'8
                    }
                }
            >>

    ..  container:: example

        Ties nothing:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, -2, 1)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 1/2
                        c'4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        r8.
                        c'16.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8
                        [
                        c'8.
                        ]
                    }
                }
            >>

    ..  container:: example

        Ties across all divisions:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, -2, 1)]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 1/2
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        r8.
                        c'16.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8
                        [
                        c'8.
                        ]
                    }
                }
            >>

    ..  container:: example

        Ties across every other division:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [0], 2)
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, -2, 1)]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 1/2
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        r8.
                        c'16.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8
                        [
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/16
                        c'16.
                        r8.
                        c'16.
                    }
                }
            >>

    ..  container:: example

        Makes diminished tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 1)]),
        ...     rmakers.force_diminution(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'4
                        c'8
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'4
                        c'8
                    }
                    \times 2/3
                    {
                        \time 4/8
                        c'2
                        c'4
                    }
                }
            >>

    ..  container:: example

        Makes augmented tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 1)]),
        ...     rmakers.force_augmentation(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 4/8
                        c'4
                        c'8
                    }
                }
            >>

    ..  container:: example

        Makes diminished tuplets and does not rewrite dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.force_diminution(),
        ... )
        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 7/16
                        c'8..
                        [
                        c'8..
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes diminished tuplets and rewrites dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.force_diminution(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'4
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 7/8
                    {
                        \time 7/16
                        c'4
                        c'4
                    }
                }
            >>

    ..  container:: example

        Makes augmented tuplets and does not rewrite dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.force_augmentation(),
        ... )
        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 7/16
                        c'8..
                        [
                        c'8..
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes augmented tuplets and rewrites dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.force_augmentation(),
        ... )
        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 7/4
                    {
                        \time 7/16
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Leaves trivializable tuplets as-is when ``trivialize`` is false:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, -2), (1,), (-2, 3), (1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        r4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Rewrites trivializable tuplets when ``trivialize`` is true. Measures 2 and 4
        contain trivial tuplets with 1:1 ratios. To remove these trivial tuplets, set
        ``extract_trivial`` as shown in the next example:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, -2), (1,), (-2, 3), (1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.trivialize(),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        r4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                }
            >>

        REGRESSION: Ignores ``trivialize`` and respects ``rewrite_dots`` when both are
        true. Measures 2 and 4 are first rewritten as trivial but then supplied again
        with nontrivial prolation when removing dots. The result is that measures 2 and 4
        carry nontrivial prolation with no dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, -2), (1,), (-2, 3), (1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.trivialize(),
        ...     rmakers.rewrite_dots(),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        r4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Leaves trivial tuplets as-is when ``extract_trivial`` is false:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, 1)]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Extracts trivial tuplets when ``extract_trivial`` is true. Measures 2 and 4 in
        the example below now contain only a flat list of notes:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, 1)]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        c'4.
                        ~
                    }
                    \time 2/8
                    c'8
                    [
                    c'8
                    ]
                    ~
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        c'4.
                        ~
                    }
                    \time 2/8
                    c'8
                    [
                    c'8
                    ]
                }
            >>

        .. note:: Flattening trivial tuplets makes it possible
            subsequently to rewrite the meter of the untupletted notes.

    ..  container:: example

        REGRESSION: Very long ties are preserved when ``extract_trivial`` is true:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ...     rmakers.tie(lambda _: abjad.select.notes(_)[:-1]),
        ... )
        >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        ~
                        c'4.
                        ~
                    }
                    \time 2/8
                    c'8
                    [
                    ~
                    c'8
                    ]
                    ~
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        ~
                        c'4.
                        ~
                    }
                    \time 2/8
                    c'8
                    [
                    ~
                    c'8
                    ]
                }
            >>

    ..  container:: example

        No rest commands:

        >>> rhythm_maker = rmakers.tuplet([(4, 1)])
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = rhythm_maker(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 3/8
                        c'4.
                        c'16.
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'2
                        c'8
                    }
                    \times 4/5
                    {
                        \time 3/8
                        c'4.
                        c'16.
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'2
                        c'8
                    }
                }
            >>

    ..  container:: example

        Masks every other output division:

        >>> def selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [1], 2)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(4, 1)]),
        ...     rmakers.force_rest(selector),
        ...     rmakers.rewrite_rest_filled(selector),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 3/8
                        c'4.
                        c'16.
                    }
                    \time 4/8
                    r2
                    \times 4/5
                    {
                        \time 3/8
                        c'4.
                        c'16.
                    }
                    \time 4/8
                    r2
                }
            >>


    ..  container:: example

        Tuplet numerators and denominators are reduced to numbers that are relatively
        prime when ``denominator`` is set to none. This means that ratios like
        ``6:4`` and ``10:8`` do not arise:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 4/5
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set in terms of a unit duration
        when ``denominator`` is set to a duration. The setting does not affect the
        first tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 16)),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 8/10
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet in terms 32nd notes. The
        setting affects all tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 32)),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 16/20
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator each tuplet in terms 64th notes. The setting
        affects all tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 64)),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 8/10
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 16/20
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 24/20
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 32/40
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set directly when ``denominator``
        is set to a positive integer. This example sets the preferred denominator of
        each tuplet to ``8``. Setting does not affect the third tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(8),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 8/10
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 8/10
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``12``. Setting affects all
        tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(12),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 12/15
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 12/15
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 12/15
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``13``. Setting does not
        affect any tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(13),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 4/5
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, 2)]),
        ...     rmakers.beam(),
        ...     tag=abjad.Tag("TUPLET_RHYTHM_MAKER"),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    %! TUPLET_RHYTHM_MAKER
                    \times 4/5
                    %! TUPLET_RHYTHM_MAKER
                    {
                        \time 1/2
                        %! TUPLET_RHYTHM_MAKER
                        c'4.
                        %! TUPLET_RHYTHM_MAKER
                        c'4
                    %! TUPLET_RHYTHM_MAKER
                    }
                    %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TUPLET_RHYTHM_MAKER
                    \times 3/5
                    %! TUPLET_RHYTHM_MAKER
                    {
                        \time 3/8
                        %! TUPLET_RHYTHM_MAKER
                        c'4.
                        %! TUPLET_RHYTHM_MAKER
                        c'4
                    %! TUPLET_RHYTHM_MAKER
                    }
                    %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TUPLET_RHYTHM_MAKER
                    \times 1/1
                    %! TUPLET_RHYTHM_MAKER
                    {
                        \time 5/16
                        %! TUPLET_RHYTHM_MAKER
                        c'8.
                        %! TUPLET_RHYTHM_MAKER
                        [
                        %! TUPLET_RHYTHM_MAKER
                        c'8
                        %! TUPLET_RHYTHM_MAKER
                        ]
                    %! TUPLET_RHYTHM_MAKER
                    }
                    %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TUPLET_RHYTHM_MAKER
                    \times 1/1
                    %! TUPLET_RHYTHM_MAKER
                    {
                        \time 5/16
                        %! TUPLET_RHYTHM_MAKER
                        c'8.
                        %! TUPLET_RHYTHM_MAKER
                        [
                        %! TUPLET_RHYTHM_MAKER
                        c'8
                        %! TUPLET_RHYTHM_MAKER
                        ]
                    %! TUPLET_RHYTHM_MAKER
                    }
                }
            >>

    ..  container:: example

        Makes tuplets with ``3:2`` ratios:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, 2)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 1/2
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8.
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8.
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, -1), (3, 1)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 1/2
                        c'4
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'4.
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/16
                        c'8.
                        r8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4
                    {
                        \time 5/16
                        c'8.
                        [
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes length-1 tuplets:

        >>> stack = rmakers.stack(rmakers.tuplet([(1,)]))
        >>> divisions = [(1, 5), (1, 4), (1, 6), (7, 9)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak edge-height #'(0.7 . 0)
                    \times 4/5
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 1/5
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 1/4
                        c'4
                    }
                    \tweak edge-height #'(0.7 . 0)
                    \times 2/3
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 1/6
                        c'4
                    }
                    \tweak edge-height #'(0.7 . 0)
                    \times 8/9
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 7/9
                        c'2..
                    }
                }
            >>

    """

    # TODO: is 'denominator' unused?
    denominator: int | abjad.Duration | str | None = None
    tuplet_ratios: typing.Sequence[abjad.Ratio] = ()

    def __post_init__(self):
        RhythmMaker.__post_init__(self)
        if self.denominator is not None:
            prototype = (abjad.Duration, int)
            assert self.denominator == "divisions" or isinstance(
                self.denominator, prototype
            )
        assert isinstance(self.tuplet_ratios, typing.Sequence), repr(self.tuplet_ratios)
        assert all(isinstance(_, abjad.Ratio) for _ in self.tuplet_ratios), repr(
            self.tuplet_ratios
        )

    def _make_music(self, divisions) -> list[abjad.Tuplet]:
        assert self.tuplet_ratios is not None
        return _make_tuplet_rhythm_maker_music(
            divisions, self.tuplet_ratios, self_tag=self.tag
        )


def _make_tuplet_rhythm_maker_music(
    divisions,
    self_tuplet_ratios,
    *,
    self_tag=None,
):
    tuplets = []
    tuplet_ratios = abjad.CyclicTuple(self_tuplet_ratios)
    for i, division in enumerate(divisions):
        ratio = tuplet_ratios[i]
        tuplet = abjad.makers.tuplet_from_duration_and_ratio(
            division, ratio, tag=self_tag
        )
        tuplets.append(tuplet)
    return tuplets


def accelerando(
    *interpolations: typing.Sequence[abjad.typings.Duration],
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
) -> AccelerandoRhythmMaker:
    """
    Makes accelerando rhythm-maker.
    """
    interpolations_ = []
    for interpolation in interpolations:
        interpolation_durations = [abjad.Duration(_) for _ in interpolation]
        interpolation_ = Interpolation(*interpolation_durations)
        interpolations_.append(interpolation_)
    return AccelerandoRhythmMaker(
        interpolations=interpolations_, spelling=spelling, tag=tag
    )


def accelerando_function(
    divisions,
    *interpolations: typing.Sequence[abjad.typings.Duration],
    previous_state: dict = None,
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
):
    """
    Makes accelerandi in ``divisions``.
    """
    interpolations_ = []
    for interpolation in interpolations:
        interpolation_durations = [abjad.Duration(_) for _ in interpolation]
        interpolation_ = Interpolation(*interpolation_durations)
        interpolations_.append(interpolation_)
    previous_state = previous_state or {}
    return _make_accelerando_rhythm_maker_music(
        divisions,
        *interpolations_,
        self_previous_state=previous_state,
        self_spelling=spelling,
        self_tag=tag,
    )


def even_division(
    denominators: typing.Sequence[int],
    *,
    denominator: str | int = "from_counts",
    extra_counts: typing.Sequence[int] = (0,),
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
) -> EvenDivisionRhythmMaker:
    """
    Makes even-division rhythm-maker.
    """
    return EvenDivisionRhythmMaker(
        denominator=denominator,
        denominators=denominators,
        extra_counts=extra_counts,
        spelling=spelling,
        tag=tag,
    )


def even_division_function(
    divisions,
    denominators: typing.Sequence[int],
    *,
    denominator: str | int = "from_counts",
    extra_counts: typing.Sequence[int] = (0,),
    previous_state: dict = None,
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
):
    """
    Makes even-division tuplets in ``divisions``.
    """
    previous_state = previous_state or {}
    return _make_even_division_rhythm_maker_music(
        divisions,
        denominators,
        self_denominator=denominator,
        self_extra_counts=extra_counts,
        self_previous_state=previous_state,
        self_spelling=spelling,
        self_tag=tag,
    )


def incised(
    extra_counts: typing.Sequence[int] = (),
    *,
    body_ratio: abjad.typings.Ratio = abjad.Ratio((1,)),
    fill_with_rests: bool = False,
    outer_divisions_only: bool = False,
    prefix_talea: typing.Sequence[int] = (),
    prefix_counts: typing.Sequence[int] = (),
    suffix_talea: typing.Sequence[int] = (),
    suffix_counts: typing.Sequence[int] = (),
    talea_denominator: int = None,
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
) -> IncisedRhythmMaker:
    """
    Makes incised rhythm-maker
    """
    return IncisedRhythmMaker(
        extra_counts=extra_counts,
        incise=Incise(
            body_ratio=body_ratio,
            fill_with_rests=fill_with_rests,
            outer_divisions_only=outer_divisions_only,
            prefix_talea=prefix_talea,
            prefix_counts=prefix_counts,
            suffix_talea=suffix_talea,
            suffix_counts=suffix_counts,
            talea_denominator=talea_denominator,
        ),
        spelling=spelling,
        tag=tag,
    )


def incised_function(
    divisions,
    extra_counts: typing.Sequence[int] = (),
    *,
    body_ratio: abjad.typings.Ratio = abjad.Ratio((1,)),
    fill_with_rests: bool = False,
    outer_divisions_only: bool = False,
    prefix_talea: typing.Sequence[int] = (),
    prefix_counts: typing.Sequence[int] = (),
    suffix_talea: typing.Sequence[int] = (),
    suffix_counts: typing.Sequence[int] = (),
    talea_denominator: int = None,
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
):
    divisions_ = [abjad.NonreducedFraction(_) for _ in divisions]
    return _make_incised_rhythm_maker_music(
        divisions_,
        extra_counts=extra_counts,
        incise=Incise(
            body_ratio=body_ratio,
            fill_with_rests=fill_with_rests,
            outer_divisions_only=outer_divisions_only,
            prefix_talea=prefix_talea,
            prefix_counts=prefix_counts,
            suffix_talea=suffix_talea,
            suffix_counts=suffix_counts,
            talea_denominator=talea_denominator,
        ),
        spelling=spelling,
        tag=tag,
    )


def multiplied_duration(
    prototype: type = abjad.Note,
    *,
    duration: abjad.typings.Duration = (1, 1),
    tag: abjad.Tag = abjad.Tag(),
) -> MultipliedDurationRhythmMaker:
    """
    Makes multiplied-duration rhythm-maker.
    """
    duration_ = abjad.Duration(duration)
    return MultipliedDurationRhythmMaker(
        prototype=prototype, duration=duration_, tag=tag
    )


def note(
    spelling: Spelling = Spelling(), tag: abjad.Tag = abjad.Tag()
) -> NoteRhythmMaker:
    """
    Makes note rhythm-maker.
    """
    return NoteRhythmMaker(spelling=spelling, tag=tag)


def note_function(
    divisions, *, spelling: Spelling = Spelling(), tag: abjad.Tag = abjad.Tag()
) -> list[list[abjad.Leaf | abjad.Tuplet]]:
    return _make_note_rhythm_maker_music(divisions, spelling=spelling, tag=tag)


def talea(
    counts: typing.Sequence[int],
    denominator: int,
    advance: int = 0,
    end_counts: typing.Sequence[int] = (),
    extra_counts: typing.Sequence[int] = (),
    preamble: typing.Sequence[int] = (),
    read_talea_once_only: bool = False,
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
) -> TaleaRhythmMaker:
    """
    Makes talea rhythm-maker.
    """
    talea = Talea(
        counts=counts,
        denominator=denominator,
        end_counts=end_counts,
        preamble=preamble,
    )
    talea = talea.advance(advance)
    return TaleaRhythmMaker(
        extra_counts=extra_counts,
        read_talea_once_only=read_talea_once_only,
        spelling=spelling,
        tag=tag,
        talea=talea,
    )


def talea_function(
    divisions,
    counts: typing.Sequence[int],
    denominator: int,
    *,
    advance: int = 0,
    end_counts: typing.Sequence[int] = (),
    extra_counts: typing.Sequence[int] = (),
    preamble: typing.Sequence[int] = (),
    previous_state: dict = None,
    read_talea_once_only: bool = False,
    spelling: Spelling = Spelling(),
    state: dict = None,
    tag: abjad.Tag = abjad.Tag(),
) -> list[abjad.Tuplet]:
    talea = Talea(
        counts=counts,
        denominator=denominator,
        end_counts=end_counts,
        preamble=preamble,
    )
    talea = talea.advance(advance)
    previous_state = previous_state or {}
    state = state or {}
    tuplets = _make_talea_rhythm_maker_music(
        divisions,
        extra_counts,
        previous_state,
        read_talea_once_only,
        spelling,
        state,
        talea,
        tag,
    )
    return tuplets


def tuplet(
    tuplet_ratios: typing.Sequence[abjad.typings.Ratio],
    *,
    # TODO: is 'denominator' unused?
    # TODO: remove in favor of dedicated denominator control commands:
    denominator: int | abjad.Duration | str | None = None,
    # TODO: is 'spelling' unused?
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
) -> TupletRhythmMaker:
    """
    Makes tuplet rhythm-maker.
    """
    tuplet_ratios_ = [abjad.Ratio(_) for _ in tuplet_ratios]
    return TupletRhythmMaker(
        denominator=denominator,
        spelling=spelling,
        tag=tag,
        tuplet_ratios=tuplet_ratios_,
    )


def tuplet_function(
    divisions,
    tuplet_ratios: typing.Sequence[abjad.typings.Ratio],
    *,
    # TODO: is 'denominator' unused?
    # TODO: remove in favor of dedicated denominator control commands:
    denominator: int | abjad.Duration | str | None = None,
    # TODO: is 'spelling' unused?
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
) -> TupletRhythmMaker:
    """
    Makes tuplets in ``divisions``.
    """
    tuplet_ratios_ = [abjad.Ratio(_) for _ in tuplet_ratios]
    return _make_tuplet_rhythm_maker_music(
        divisions,
        tuplet_ratios_,
        # denominator=denominator,
        # spelling=spelling,
        self_tag=tag,
    )


# COMMANDS


def _do_beam_command(
    argument,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = None,
):
    for selection in argument:
        unbeam_function(selection)
        leaves = abjad.select.leaves(selection)
        abjad.beam(
            leaves,
            beam_lone_notes=beam_lone_notes,
            beam_rests=beam_rests,
            stemlet_length=stemlet_length,
            tag=tag,
        )


def _do_beam_groups_command(
    argument,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = None,
):
    unbeam_function(argument)
    durations = []
    components: list[abjad.Component] = []
    for selection in argument:
        duration = abjad.get.duration(selection)
        durations.append(duration)
    for selection in argument:
        if isinstance(selection, abjad.Tuplet):
            components.append(selection)
        else:
            components.extend(selection)
    leaves = abjad.select.leaves(components)
    abjad.beam(
        leaves,
        beam_lone_notes=beam_lone_notes,
        beam_rests=beam_rests,
        durations=durations,
        span_beam_count=1,
        stemlet_length=stemlet_length,
        tag=tag,
    )


def _do_duration_bracket_command(argument):
    for tuplet in abjad.select.tuplets(argument):
        duration_ = abjad.get.duration(tuplet)
        notes = abjad.LeafMaker()([0], [duration_])
        string = abjad.illustrators.selection_to_score_markup_string(notes)
        string = rf"\markup \scale #'(0.75 . 0.75) {string}"
        abjad.override(tuplet).TupletNumber.text = string


def _do_extract_trivial_command(argument):
    tuplets = abjad.select.tuplets(argument)
    for tuplet in tuplets:
        if tuplet.trivial():
            abjad.mutate.extract(tuplet)


def _do_feather_beam_command(
    argument, *, beam_rests: bool = False, stemlet_length=None, tag=None
):
    for selection in argument:
        unbeam_function(selection)
        leaves = abjad.select.leaves(selection)
        abjad.beam(
            leaves,
            beam_rests=beam_rests,
            stemlet_length=stemlet_length,
            tag=tag,
        )
    for selection in argument:
        first_leaf = abjad.select.leaf(selection, 0)
        if FeatherBeamCommand._is_accelerando(selection):
            abjad.override(first_leaf).Beam.grow_direction = abjad.RIGHT
        elif FeatherBeamCommand._is_ritardando(selection):
            abjad.override(first_leaf).Beam.grow_direction = abjad.LEFT


def _do_force_augmentation_command(argument):
    for tuplet in abjad.select.tuplets(argument):
        if not tuplet.augmentation():
            tuplet.toggle_prolation()


def _do_force_repeat_tie_command(container, *, threshold=None) -> None:
    assert isinstance(container, abjad.Container), container
    if callable(threshold):
        inequality = threshold
    elif threshold in (None, False):

        def inequality(item):
            return item < 0

    elif threshold is True:

        def inequality(item):
            return item >= 0

    else:
        assert isinstance(threshold, tuple) and len(threshold) == 2, repr(threshold)

        def inequality(item):
            return item >= abjad.Duration(threshold)

    attach_repeat_ties = []
    for leaf in abjad.select.leaves(container):
        if abjad.get.has_indicator(leaf, abjad.Tie):
            next_leaf = abjad.get.leaf(leaf, 1)
            if next_leaf is None:
                continue
            if not isinstance(next_leaf, abjad.Chord | abjad.Note):
                continue
            if abjad.get.has_indicator(next_leaf, abjad.RepeatTie):
                continue
            duration = abjad.get.duration(leaf)
            if not inequality(duration):
                continue
            attach_repeat_ties.append(next_leaf)
            abjad.detach(abjad.Tie, leaf)
    for leaf in attach_repeat_ties:
        repeat_tie = abjad.RepeatTie()
        abjad.attach(repeat_tie, leaf)


def _do_force_rest_command(selections, previous_logical_ties_produced=None, tag=None):
    # will need to restore for statal rhythm-makers:
    # logical_ties = abjad.select.logical_ties(selections)
    # logical_ties = list(logical_ties)
    # total_logical_ties = len(logical_ties)
    # previous_logical_ties_produced = self._previous_logical_ties_produced()
    # if self._previous_incomplete_last_note():
    #    previous_logical_ties_produced -= 1
    leaves = abjad.select.leaves(selections)
    for leaf in leaves:
        rest = abjad.Rest(leaf.written_duration, tag=tag)
        if leaf.multiplier is not None:
            rest.multiplier = leaf.multiplier
        previous_leaf = abjad.get.leaf(leaf, -1)
        next_leaf = abjad.get.leaf(leaf, 1)
        abjad.mutate.replace(leaf, [rest])
        if previous_leaf is not None:
            abjad.detach(abjad.Tie, previous_leaf)
        abjad.detach(abjad.Tie, rest)
        abjad.detach(abjad.RepeatTie, rest)
        if next_leaf is not None:
            abjad.detach(abjad.RepeatTie, next_leaf)


def _do_reduce_multiplier_command(argument):
    for tuplet in abjad.select.tuplets(argument):
        tuplet.multiplier = abjad.Multiplier(tuplet.multiplier)


def _do_repeat_tie_command(argument, *, tag):
    for note in abjad.select.notes(argument):
        tie = abjad.RepeatTie()
        abjad.attach(tie, note, tag=tag)


def _do_rewrite_dots_command(argument, *, tag=None):
    for tuplet in abjad.select.tuplets(argument):
        tuplet.rewrite_dots()


def _do_rewrite_meter_command(
    voice, *, boundary_depth=None, reference_meters=None, tag=None
):
    tag = tag or abjad.Tag()
    tag = tag.append(abjad.Tag("rmakers.RewriteMeterCommand.__call__"))
    staff = abjad.get.parentage(voice).parent
    assert isinstance(staff, abjad.Staff), repr(staff)
    time_signature_voice = staff["TimeSignatureVoice"]
    assert isinstance(time_signature_voice, abjad.Voice)
    meters, preferred_meters = [], []
    for skip in time_signature_voice:
        time_signature = abjad.get.indicator(skip, abjad.TimeSignature)
        meter = abjad.Meter(time_signature)
        meters.append(meter)
    durations = [abjad.Duration(_) for _ in meters]
    reference_meters = reference_meters or ()
    split_measures_function(voice, durations=durations)
    selections = abjad.select.group_by_measure(voice[:])
    for meter, selection in zip(meters, selections):
        for reference_meter in reference_meters:
            if reference_meter == meter:
                meter = reference_meter
                break
        preferred_meters.append(meter)
        nontupletted_leaves = []
        for leaf in abjad.iterate.leaves(selection):
            if not abjad.get.parentage(leaf).count(abjad.Tuplet):
                nontupletted_leaves.append(leaf)
        unbeam_function(nontupletted_leaves)
        abjad.Meter.rewrite_meter(
            selection,
            meter,
            boundary_depth=boundary_depth,
            rewrite_tuplets=False,
        )
    selections = abjad.select.group_by_measure(voice[:])
    for meter, selection in zip(preferred_meters, selections):
        leaves = abjad.select.leaves(selection, grace=False)
        beat_durations = []
        beat_offsets = meter.depthwise_offset_inventory[1]
        for start, stop in abjad.sequence.nwise(beat_offsets):
            beat_duration = stop - start
            beat_durations.append(beat_duration)
        beamable_groups = _make_beamable_groups(leaves, beat_durations)
        for beamable_group in beamable_groups:
            if not beamable_group:
                continue
            abjad.beam(
                beamable_group,
                beam_rests=False,
                tag=tag,
            )


def _do_rewrite_rest_filled_command(selection, *, spelling=None, tag=None):
    if spelling is not None:
        increase_monotonic = spelling.increase_monotonic
        forbidden_note_duration = spelling.forbidden_note_duration
        forbidden_rest_duration = spelling.forbidden_rest_duration
    else:
        increase_monotonic = None
        forbidden_note_duration = None
        forbidden_rest_duration = None
    maker = abjad.LeafMaker(
        increase_monotonic=increase_monotonic,
        forbidden_note_duration=forbidden_note_duration,
        forbidden_rest_duration=forbidden_rest_duration,
        tag=tag,
    )
    for tuplet in abjad.select.tuplets(selection):
        if not tuplet.rest_filled():
            continue
        duration = abjad.get.duration(tuplet)
        rests = maker([None], [duration])
        abjad.mutate.replace(tuplet[:], rests)
        tuplet.multiplier = abjad.Multiplier(1)


def _do_rewrite_sustained_command(argument):
    for tuplet in abjad.select.tuplets(argument):
        if not abjad.get.sustained(tuplet):
            continue
        duration = abjad.get.duration(tuplet)
        leaves = abjad.select.leaves(tuplet)
        last_leaf = leaves[-1]
        if abjad.get.has_indicator(last_leaf, abjad.Tie):
            last_leaf_has_tie = True
        else:
            last_leaf_has_tie = False
        for leaf in leaves[1:]:
            tuplet.remove(leaf)
        assert len(tuplet) == 1, repr(tuplet)
        if not last_leaf_has_tie:
            abjad.detach(abjad.Tie, tuplet[-1])
        abjad.mutate._set_leaf_duration(tuplet[0], duration)
        tuplet.multiplier = abjad.Multiplier(1)


def _do_split_measures_command(voice, *, durations=None, tag=None):
    if not durations:
        # TODO: implement abjad.get() method for measure durations
        staff = abjad.get.parentage(voice).parent
        assert isinstance(staff, abjad.Staff)
        voice_ = staff["TimeSignatureVoice"]
        assert isinstance(voice_, abjad.Voice)
        durations = [abjad.get.duration(_) for _ in voice_]
    total_duration = abjad.sequence.sum(durations)
    music_duration = abjad.get.duration(voice)
    if total_duration != music_duration:
        message = f"Total duration of splits is {total_duration!s}"
        message += f" but duration of music is {music_duration!s}:"
        message += f"\ndurations: {durations}."
        message += f"\nvoice: {voice[:]}."
        raise Exception(message)
    abjad.mutate.split(voice[:], durations=durations)


def _do_tie_command(argument, *, tag=None):
    for note in abjad.select.notes(argument):
        tie = abjad.Tie()
        abjad.attach(tie, note, tag=tag)


def _do_untie_command(argument):
    for leaf in abjad.select.leaves(argument):
        abjad.detach(abjad.Tie, leaf)
        abjad.detach(abjad.RepeatTie, leaf)


def _do_written_duration_command(argument, written_duration):
    leaves = abjad.select.leaves(argument)
    for leaf in leaves:
        old_duration = leaf.written_duration
        if written_duration == old_duration:
            continue
        leaf.written_duration = written_duration
        multiplier = old_duration / written_duration
        leaf.multiplier = multiplier


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Command:
    """
    Command baseclass.
    """

    selector: typing.Callable | None = None

    __documentation_section__ = "Commands"

    def __post_init__(self):
        # raise Exception("ASDF")
        if self.selector is not None:
            assert callable(self.selector), repr(self.selector)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        pass


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class BeamCommand(Command):
    """
    Beam command.
    """

    beam_lone_notes: bool = False
    beam_rests: bool = False
    stemlet_length: int | float | None = None

    def __post_init__(self):
        Command.__post_init__(self)
        assert isinstance(self.beam_lone_notes, bool), repr(self.beam_lone_notes)
        assert isinstance(self.beam_rests, bool), repr(self.beam_rests)
        if self.stemlet_length is not None:
            assert isinstance(self.stemlet_length, int | float)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selections = self.selector(selection)
        else:
            selections = [selection]
        _do_beam_command(
            selections,
            beam_lone_notes=self.beam_lone_notes,
            beam_rests=self.beam_rests,
            stemlet_length=self.stemlet_length,
            tag=tag,
        )


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class BeamGroupsCommand(Command):
    """
    Beam groups command.
    """

    beam_lone_notes: bool = False
    beam_rests: bool = False
    stemlet_length: int | float | None = None
    tag: abjad.Tag = abjad.Tag()

    def __post_init__(self):
        Command.__post_init__(self)
        assert isinstance(self.beam_lone_notes, bool), repr(self.beam_lone_notes)
        assert isinstance(self.beam_rests, bool), repr(self.beam_rests)
        if self.stemlet_length is not None:
            assert isinstance(self.stemlet_length, int | float)
        assert isinstance(self.tag, abjad.Tag), repr(self.tag)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        if not isinstance(voice, abjad.Voice):
            selections = voice
            if self.selector is not None:
                selections = self.selector(selections)
        else:
            assert self.selector is not None
            selections = self.selector(voice)
        _do_beam_groups_command(
            selections,
            beam_lone_notes=self.beam_lone_notes,
            beam_rests=self.beam_rests,
            stemlet_length=self.stemlet_length,
            tag=self.tag,
        )


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class CacheStateCommand(Command):
    """
    Cache state command.
    """

    pass


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class DenominatorCommand(Command):
    """
    Denominator command.
    """

    denominator: int | abjad.typings.Duration | None = None

    def __post_init__(self):
        Command.__post_init__(self)
        if self.denominator is not None:
            prototype = (int, abjad.Duration)
            assert isinstance(self.denominator, prototype), repr(self.denominator)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        assert self.denominator is not None
        denominator_function(selection, self.denominator)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class DurationBracketCommand(Command):
    """
    Duration bracket command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_duration_bracket_command(selection)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class WrittenDurationCommand(Command):
    """
    Written duration command.
    """

    selector: typing.Callable | None = lambda _: abjad.select.leaf(_, 0)
    duration: abjad.typings.Duration | None = None

    def __post_init__(self):
        Command.__post_init__(self)
        assert isinstance(self.duration, abjad.Duration), repr(self.duration)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_written_duration_command(selection, self.duration)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class ExtractTrivialCommand(Command):
    """
    Extract trivial command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_extract_trivial_command(selection)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class FeatherBeamCommand(Command):
    """
    Feather beam command.
    """

    beam_rests: bool = False
    stemlet_length: int | float | None = None

    def __post_init__(self):
        Command.__post_init__(self)
        assert isinstance(self.beam_rests, bool), repr(self.beam_rests)
        if self.stemlet_length is not None:
            assert isinstance(self.stemlet_length, int | float)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selections = self.selector(selection)
        else:
            selections = [selection]
        _do_feather_beam_command(
            selections,
            beam_rests=self.beam_rests,
            stemlet_length=self.stemlet_length,
            tag=tag,
        )

    @staticmethod
    def _is_accelerando(selection):
        first_leaf = abjad.select.leaf(selection, 0)
        last_leaf = abjad.select.leaf(selection, -1)
        first_duration = abjad.get.duration(first_leaf)
        last_duration = abjad.get.duration(last_leaf)
        if last_duration < first_duration:
            return True
        return False

    @staticmethod
    def _is_ritardando(selection):
        first_leaf = abjad.select.leaf(selection, 0)
        last_leaf = abjad.select.leaf(selection, -1)
        first_duration = abjad.get.duration(first_leaf)
        last_duration = abjad.get.duration(last_leaf)
        if first_duration < last_duration:
            return True
        return False


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class ForceAugmentationCommand(Command):
    """
    Force augmentation command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_force_augmentation_command(selection)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class ForceDiminutionCommand(Command):
    """
    Force diminution command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select.tuplets(selection):
            if not tuplet.diminution():
                tuplet.toggle_prolation()


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class ForceFractionCommand(Command):
    """
    Force fraction command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        force_fraction_function(selection)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class ForceNoteCommand(Command):
    r"""
    Note command.

    ..  container:: example

        Changes logical ties 1 and 2 to notes:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(lambda _: abjad.select.leaves(_)),
        ...     rmakers.force_note(lambda _: abjad.select.logical_ties(_)[1:3]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 7/16
                    r4..
                    \time 3/8
                    c'4.
                    \time 7/16
                    c'4..
                    \time 3/8
                    r4.
                }
            >>

    ..  container:: example

        Changes patterned selection of leave to notes. Works inverted composite pattern:

        >>> def force_note_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0, -1])
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(lambda _: abjad.select.leaves(_)),
        ...     rmakers.force_note(force_note_selector),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 7/16
                    c'4..
                    \time 3/8
                    r4.
                    \time 7/16
                    r4..
                    \time 3/8
                    c'4.
                }
            >>

    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()):
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)

        # will need to restore for statal rhythm-makers:
        # logical_ties = abjad.select.logical_ties(selections)
        # logical_ties = list(logical_ties)
        # total_logical_ties = len(logical_ties)
        # previous_logical_ties_produced = self._previous_logical_ties_produced()
        # if self._previous_incomplete_last_note():
        #    previous_logical_ties_produced -= 1

        leaves = abjad.select.leaves(selection)
        for leaf in leaves:
            if isinstance(leaf, abjad.Note):
                continue
            note = abjad.Note("C4", leaf.written_duration, tag=tag)
            if leaf.multiplier is not None:
                note.multiplier = leaf.multiplier
            abjad.mutate.replace(leaf, [note])


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class ForceRepeatTieCommand(Command):
    """
    Force repeat-tie command.
    """

    threshold: bool | tuple[int, int] | typing.Callable = False
    inequality: typing.Callable = dataclasses.field(init=False, repr=False)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_force_repeat_tie_command(selection, threshold=self.threshold)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class ForceRestCommand(Command):
    r"""
    Rest command.

    ..  container:: example

        Changes logical ties 1 and 2 to rests:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(lambda _: abjad.select.logical_ties(_)[1:3]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 7/16
                    c'4..
                    \time 3/8
                    r4.
                    \time 7/16
                    r4..
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Changes logical ties -1 and -2 to rests:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(lambda _: abjad.select.logical_ties(_)[-2:]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 7/16
                    c'4..
                    \time 3/8
                    c'4.
                    \time 7/16
                    r4..
                    \time 3/8
                    r4.
                }
            >>

    ..  container:: example

        Changes patterned selection of logical ties to rests:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(lambda _: abjad.select.logical_ties(_)[1:-1]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 7/16
                    c'4..
                    \time 3/8
                    r4.
                    \time 7/16
                    r4..
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Changes patterned selection of logical ties to rests. Works with inverted
        composite pattern:

        >>> def rest_selector(argument):
        ...     result = abjad.select.logical_ties(argument)
        ...     result = abjad.select.get(result, [0, -1])
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(rest_selector),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 7/16
                    r4..
                    \time 3/8
                    c'4.
                    \time 7/16
                    c'4..
                    \time 3/8
                    r4.
                }
            >>

    """

    def __call__(
        self,
        voice,
        *,
        previous_logical_ties_produced=None,
        tag: abjad.Tag = abjad.Tag(),
    ):
        selection = voice
        if self.selector is not None:
            selections = self.selector([selection])
        _do_force_rest_command(selections, tag=tag)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class GraceContainerCommand(Command):
    """
    Grace container command.
    """

    counts: typing.Sequence[int] | None = None
    class_: type = abjad.BeforeGraceContainer
    beam_and_slash: bool = False
    talea: Talea = Talea([1], 8)

    _classes = (abjad.BeforeGraceContainer, abjad.AfterGraceContainer)

    def __post_init__(self):
        Command.__post_init__(self)
        assert all(isinstance(_, int) for _ in self.counts), repr(self.counts)
        assert self.class_ in self._classes, repr(self.class_)
        assert isinstance(self.beam_and_slash, bool), repr(self.beam_and_slash)
        assert isinstance(self.talea, Talea), repr(talea)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        leaves = abjad.select.leaves(selection, grace=False)
        assert self.counts is not None
        counts = abjad.CyclicTuple(self.counts)
        maker = abjad.LeafMaker()
        start = 0
        for i, leaf in enumerate(leaves):
            count = counts[i]
            if not count:
                continue
            stop = start + count
            durations = self.talea[start:stop]
            notes = maker([0], durations)
            if self.beam_and_slash:
                abjad.beam(notes)
                literal = abjad.LilyPondLiteral(r"\slash")
                abjad.attach(literal, notes[0])
            container = self.class_(notes)
            abjad.attach(container, leaf)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class InvisibleMusicCommand(Command):
    """
    Invisible music command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        tag_1 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COMMAND"))
        literal_1 = abjad.LilyPondLiteral(r"\abjad-invisible-music")
        tag_2 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COLORING"))
        literal_2 = abjad.LilyPondLiteral(r"\abjad-invisible-music-coloring")
        for leaf in abjad.select.leaves(selection):
            abjad.attach(literal_1, leaf, tag=tag_1, deactivate=True)
            abjad.attach(literal_2, leaf, tag=tag_2)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class OnBeatGraceContainerCommand(Command):
    """
    On-beat grace container command.
    """

    counts: typing.Sequence[int] | None = None
    leaf_duration: abjad.typings.Duration | None = None
    talea: Talea = Talea([1], 8)
    voice_name: str = ""

    def __post_init__(self):
        Command.__post_init__(self)
        assert all(isinstance(_, int) for _ in self.counts), repr(self.counts)
        if self.leaf_duration is not None:
            assert isinstance(self.leaf_duration, abjad.Duration), repr(
                self.leaf_duration
            )
        assert isinstance(self.talea, Talea), repr(self.talea)
        assert isinstance(self.voice_name, str), repr(self.voice_name)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        assert isinstance(voice, abjad.Voice), repr(voice)
        if self.voice_name:
            voice.name = self.voice_name
        selections = voice
        if self.selector is not None:
            selections = self.selector(selections)
        assert self.counts is not None
        counts = abjad.CyclicTuple(self.counts)
        maker = abjad.LeafMaker()
        start = 0
        for i, selection in enumerate(selections):
            count = counts[i]
            if not count:
                continue
            stop = start + count
            durations = self.talea[start:stop]
            notes = maker([0], durations)
            abjad.on_beat_grace_container(
                notes,
                selection,
                anchor_voice_number=2,
                grace_voice_number=1,
                leaf_duration=self.leaf_duration,
            )


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class ReduceMultiplierCommand(Command):
    """
    Reduce multiplier command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_reduce_multiplier_command(selection)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class RepeatTieCommand(Command):
    """
    Repeat-tie command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_repeat_tie_command(selection, tag=tag)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class RewriteDotsCommand(Command):
    """
    Rewrite dots command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_rewrite_dots_command(selection, tag=tag)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class RewriteMeterCommand(Command):
    """
    Rewrite meter command.
    """

    boundary_depth: int | None = None
    reference_meters: typing.Sequence[abjad.Meter] = ()

    def __post_init__(self):
        if self.boundary_depth is not None:
            assert isinstance(self.boundary_depth, int)
        if not all(isinstance(_, abjad.Meter) for _ in self.reference_meters):
            message = "must be sequence of meters:\n"
            message += f"   {repr(self.reference_meters)}"
            raise Exception(message)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        assert isinstance(voice, abjad.Voice), repr(voice)
        _do_rewrite_meter_command(
            voice,
            boundary_depth=self.boundary_depth,
            reference_meters=self.reference_meters,
            tag=tag,
        )


def _make_beamable_groups(components, durations):
    music_duration = abjad.get.duration(components)
    if music_duration != sum(durations):
        message = f"music duration {music_duration} does not equal"
        message += f" total duration {sum(durations)}:\n"
        message += f"   {components}\n"
        message += f"   {durations}"
        raise Exception(message)
    component_to_timespan = []
    start_offset = abjad.Offset(0)
    for component in components:
        duration = abjad.get.duration(component)
        stop_offset = start_offset + duration
        timespan = abjad.Timespan(start_offset, stop_offset)
        pair = (component, timespan)
        component_to_timespan.append(pair)
        start_offset = stop_offset
    group_to_target_duration = []
    start_offset = abjad.Offset(0)
    for target_duration in durations:
        stop_offset = start_offset + target_duration
        group_timespan = abjad.Timespan(start_offset, stop_offset)
        start_offset = stop_offset
        group = []
        for component, component_timespan in component_to_timespan:
            if component_timespan.happens_during_timespan(group_timespan):
                group.append(component)
        pair = ([group], target_duration)
        group_to_target_duration.append(pair)
    beamable_groups = []
    for group, target_duration in group_to_target_duration:
        group_duration = abjad.get.duration(group)
        assert group_duration <= target_duration
        if group_duration == target_duration:
            beamable_groups.append(group)
        else:
            beamable_groups.append([])
    return beamable_groups


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class RewriteRestFilledCommand(Command):
    """
    Rewrite rest-filled command.
    """

    spelling: Spelling = Spelling()

    def __post_init__(self):
        Command.__post_init__(self)
        assert isinstance(self.spelling, Spelling)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_rewrite_rest_filled_command(selection, spelling=self.spelling, tag=tag)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class RewriteSustainedCommand(Command):
    """
    Rewrite sustained command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_rewrite_sustained_command(selection)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class SplitMeasuresCommand(Command):
    """
    Split measures command.
    """

    def __call__(
        self,
        voice,
        *,
        durations: typing.Sequence[abjad.typings.Duration] = (),
        tag: abjad.Tag = abjad.Tag(),
    ) -> None:
        _do_split_measures_command(voice, durations=durations, tag=tag)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class TieCommand(Command):
    """
    Tie command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_tie_command(selection, tag=tag)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class TremoloContainerCommand(Command):
    """
    Tremolo container command.
    """

    count: int = 0

    def __post_init__(self):
        Command.__post_init__(self)
        assert isinstance(self.count, int), repr(self.count)
        assert 0 < self.count, repr(self.count)

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        assert self.count is not None
        for note in abjad.select.notes(selection):
            container_duration = note.written_duration
            note_duration = container_duration / (2 * self.count)
            left_note = abjad.Note("c'", note_duration)
            right_note = abjad.Note("c'", note_duration)
            container = abjad.TremoloContainer(
                self.count, [left_note, right_note], tag=tag
            )
            abjad.mutate.replace(note, container)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class TrivializeCommand(Command):
    """
    Trivialize command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select.tuplets(selection):
            tuplet.trivialize()


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class UnbeamCommand(Command):
    """
    Unbeam command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selections = self.selector(selection)
        else:
            selections = selection
        unbeam_function(selections)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class UntieCommand(Command):
    """
    Untie command.
    """

    def __call__(self, voice, *, tag: abjad.Tag = abjad.Tag()) -> None:
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        _do_untie_command(selection)


def nongrace_leaves_in_each_tuplet(level: int = -1):
    """
    Makes nongrace leaves in each tuplet selector.
    """
    return lambda _: nongrace_leaves_in_each_tuplet_function(_, level=level)


def nongrace_leaves_in_each_tuplet_function(argument, level: int = -1):
    """
    Selects nongrace leaves in each tuplet.
    """
    tuplets = abjad.select.tuplets(argument, level=level)
    leaves = [abjad.select.leaves(_, grace=False) for _ in tuplets]
    return leaves


def after_grace_container(
    counts: typing.Sequence[int],
    selector: typing.Callable | None = None,
    *,
    beam_and_slash: bool = False,
    talea: Talea = Talea([1], 8),
) -> GraceContainerCommand:
    r"""
    Makes after-grace container command.

    ..  container:: example

        Single after-graces with slurs applied manually:

        >>> def after_grace_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.note(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4], extra_counts=[2]),
        ...     rmakers.after_grace_container([1], after_grace_selector),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> staff = lilypond_file["Staff"]

        >>> def slur_selector(argument):
        ...     result = abjad.select.components(argument, abjad.AfterGraceContainer)
        ...     result = [abjad.select.with_next_leaf(_) for _ in result]
        ...     return result
        >>> result = [abjad.slur(_) for _ in slur_selector(staff)]
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            c'8
                            (
                        }
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        )
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            c'8
                            )
                            (
                        }
                    }
                }
            >>

    ..  container:: example

        Multiple after-graces with ``beam_and_slash=True`` and with slurs applied
        manually:

        >>> def after_grace_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.note(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4], extra_counts=[2]),
        ...     rmakers.after_grace_container(
        ...         [2, 4], after_grace_selector, beam_and_slash=True,
        ...     ),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> lilypond_file = rmakers.example(
        ...     selections, divisions, includes=["abjad.ily"]
        ... )

        >>> def slur_selector(argument):
        ...     result = abjad.select.components(argument, abjad.AfterGraceContainer)
        ...     result = [abjad.select.with_next_leaf(_) for _ in result]
        ...     return result
        >>> staff = lilypond_file["Staff"]
        >>> result = [abjad.slur(_) for _ in slur_selector(staff)]
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        )
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            )
                            ]
                        }
                    }
                }
            >>

    """
    return GraceContainerCommand(
        selector=selector,
        counts=counts,
        beam_and_slash=beam_and_slash,
        class_=abjad.AfterGraceContainer,
        talea=talea,
    )


def beam(
    selector: typing.Callable | None = nongrace_leaves_in_each_tuplet(),
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
) -> BeamCommand:
    """
    Makes beam command.
    """
    return BeamCommand(
        selector=selector,
        beam_rests=beam_rests,
        beam_lone_notes=beam_lone_notes,
        stemlet_length=stemlet_length,
    )


def beam_function(
    argument,
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag("rmakers.beam()"),
) -> None:
    """
    Beams ``argument``.
    """
    _do_beam_command(
        argument,
        beam_lone_notes=beam_lone_notes,
        beam_rests=beam_rests,
        stemlet_length=stemlet_length,
        tag=tag,
    )


def beam_groups(
    selector: typing.Callable | None = nongrace_leaves_in_each_tuplet(level=-1),
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> BeamGroupsCommand:
    """
    Makes beam-groups command.
    """
    return BeamGroupsCommand(
        selector=selector,
        beam_lone_notes=beam_lone_notes,
        beam_rests=beam_rests,
        stemlet_length=stemlet_length,
        tag=tag,
    )


def beam_groups_function(
    argument,
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag("rmakers.beam_groups()"),
) -> None:
    """
    Beams ``argument`` groups.
    """
    _do_beam_groups_command(
        argument,
        beam_lone_notes=beam_lone_notes,
        beam_rests=beam_rests,
        stemlet_length=stemlet_length,
        tag=tag,
    )


def before_grace_container(
    counts: typing.Sequence[int],
    selector: typing.Callable | None = None,
    *,
    talea: Talea = Talea([1], 8),
) -> GraceContainerCommand:
    r"""
    Makes grace container command.

    ..  container:: example

        >>> def before_grace_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.notes(_) for _ in result]
        ...     result = [abjad.select.exclude(_, [0, -1]) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4], extra_counts=[2]),
        ...     rmakers.before_grace_container([2, 4], before_grace_selector),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> lilypond_file = rmakers.example(
        ...     selections, divisions, includes=["abjad.ily"]
        ... )
        >>> staff = lilypond_file["Staff"]

        >>> def container_selector(argument):
        ...     result = abjad.select.components(argument, abjad.BeforeGraceContainer)
        ...     return result
        >>> result = [abjad.beam(_) for _ in container_selector(staff)]

        >>> def slur_selector(argument):
        ...     result = abjad.select.components(argument, abjad.BeforeGraceContainer)
        ...     result = [abjad.select.with_next_leaf(_) for _ in result]
        ...     return result
        >>> result = [abjad.slur(_) for _ in slur_selector(staff)]

        >>> slash = abjad.LilyPondLiteral(r"\slash")
        >>> result = [abjad.attach(slash, _[0]) for _ in container_selector(staff)]

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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                        c'4
                        )
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        )
                        c'4
                    }
                }
            >>

    """
    return GraceContainerCommand(selector=selector, counts=counts, talea=talea)


def cache_state() -> CacheStateCommand:
    """
    Makes cache state command.
    """
    return CacheStateCommand()


def denominator(
    denominator: int | abjad.typings.Duration,
    selector: typing.Callable | None = lambda _: abjad.select.tuplets(_),
) -> DenominatorCommand:
    r"""
    Makes tuplet denominator command.

    ..  container:: example

        Tuplet numerators and denominators are reduced to numbers that are relatively
        prime when ``denominator`` is set to none. This means that ratios like ``6:4``
        and ``10:8`` do not arise:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 4/5
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set in terms of a unit duration when
        ``denominator`` is set to a duration. The setting does not affect the first
        tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 16)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 8/10
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet in terms 32nd notes. The setting
        affects all tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 32)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 16/20
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator each tuplet in terms 64th notes. The setting
        affects all tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 64)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 8/10
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 16/20
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 24/20
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 32/40
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set directly when ``denominator`` is
        set to a positive integer. This example sets the preferred denominator of each
        tuplet to ``8``. Setting does not affect the third tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(8),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 8/10
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 8/10
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``12``. Setting affects all
        tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(12),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.setting(score).proportionalNotationDuration = "#(ly:make-moment 1 28)"
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
                proportionalNotationDuration = #(ly:make-moment 1 28)
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 12/15
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 12/15
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 12/15
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``13``. Setting does not affect
        any tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(13),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 4/5
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    """
    if isinstance(denominator, tuple):
        denominator = abjad.Duration(denominator)
    return DenominatorCommand(selector=selector, denominator=denominator)


def denominator_function(argument, denominator: int | abjad.typings.Duration) -> None:
    r"""
    Sets denominator of every tuplet in ``argument`` to ``denominator``.
    """
    if isinstance(denominator, tuple):
        denominator = abjad.Duration(denominator)
    for tuplet in abjad.select.tuplets(argument):
        if isinstance(denominator, abjad.Duration):
            unit_duration = denominator
            assert unit_duration.numerator == 1
            duration = abjad.get.duration(tuplet)
            denominator_ = unit_duration.denominator
            nonreduced_fraction = duration.with_denominator(denominator_)
            tuplet.denominator = nonreduced_fraction.numerator
        elif abjad.math.is_positive_integer(denominator):
            tuplet.denominator = denominator
        else:
            raise Exception(f"invalid preferred denominator: {denominator!r}.")


def duration_bracket(
    selector: typing.Callable | None = None,
) -> DurationBracketCommand:
    """
    Makes duration bracket command.
    """
    return DurationBracketCommand(selector=selector)


def duration_bracket_function(argument) -> None:
    """
    Applies durtaion bracket to tuplets in ``argument``.
    """
    _do_duration_bracket_command(argument)


def extract_trivial(
    selector: typing.Callable | None = None,
) -> ExtractTrivialCommand:
    r"""
    Makes extract trivial command.

    ..  container:: example

        With selector:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(lambda _: abjad.select.tuplets(_)[-2:]),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \time 3/8
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \time 3/8
                    c'8
                    [
                    c'8
                    c'8
                    ]
                }
            >>

    """
    return ExtractTrivialCommand(selector=selector)


def extract_trivial_function(argument) -> None:
    """
    Extracts trivial tuplets in ``argument``.
    """
    _do_extract_trivial_command(argument)


def feather_beam(
    selector: typing.Callable | None = nongrace_leaves_in_each_tuplet(),
    *,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
) -> FeatherBeamCommand:
    """
    Makes feather beam command.
    """
    return FeatherBeamCommand(
        selector=selector, beam_rests=beam_rests, stemlet_length=stemlet_length
    )


def feather_beam_function(
    argument,
    # selector: typing.Callable | None = nongrace_leaves_in_each_tuplet(),
    *,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    _do_feather_beam_command(
        argument,
        beam_rests=beam_rests,
        stemlet_length=stemlet_length,
        tag=tag,
    )


def force_augmentation(
    selector: typing.Callable | None = None,
) -> ForceAugmentationCommand:
    r"""
    Makes force augmentation command.

    ..  container:: example

        Without forced augmentation:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.force_fraction(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        With forced augmentation:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.force_augmentation(),
        ...     rmakers.force_fraction(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                }
            >>

    """
    return ForceAugmentationCommand(selector=selector)


def force_augmentation_function(argument) -> None:
    """
    Forces each tuplet in ``argument`` to notate as an augmentation.
    """
    _do_force_augmentation_command(argument)


def force_diminution(
    selector: typing.Callable | None = None,
) -> ForceDiminutionCommand:
    """
    Makes force diminution command.
    """
    return ForceDiminutionCommand(selector=selector)


def force_fraction(
    selector: typing.Callable | None = None,
) -> ForceFractionCommand:
    """
    Makes force fraction command.
    """
    return ForceFractionCommand(selector=selector)


def force_fraction_function(argument) -> None:
    """
    Sets ``force_fraction=True`` on all tuplets in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        tuplet.force_fraction = True


def force_note(
    selector: typing.Callable | None = None,
) -> ForceNoteCommand:
    """
    Makes force note command.
    """
    return ForceNoteCommand(selector=selector)


def force_repeat_tie(
    threshold: bool | tuple[int, int] | typing.Callable = True,
    selector: typing.Callable | None = None,
) -> ForceRepeatTieCommand:
    """
    Makes force repeat-ties command.
    """
    return ForceRepeatTieCommand(selector=selector, threshold=threshold)


def force_repeat_tie_function(
    argument,
    *,
    threshold: bool | tuple[int, int] | typing.Callable = True,
) -> None:
    _do_force_repeat_tie_command(argument, threshold=threshold)


def force_rest(selector: typing.Callable | None) -> ForceRestCommand:
    """
    Makes force rest command.
    """
    return ForceRestCommand(selector=selector)


def force_rest_function(argument, *, tag=None) -> None:
    """
    Forces rests in ``argument``.
    """
    _do_force_rest_command(argument, tag=tag)


def invisible_music(selector: typing.Callable | None) -> InvisibleMusicCommand:
    """
    Makes invisible music command.
    """
    return InvisibleMusicCommand(selector=selector)


def on_beat_grace_container(
    counts: typing.Sequence[int],
    selector: typing.Callable | None = None,
    *,
    leaf_duration: abjad.typings.Duration = None,
    talea: Talea = Talea([1], 8),
    voice_name: str = "",
) -> OnBeatGraceContainerCommand:
    r"""
    Makes on-beat grace container command.

    ..  container:: example

        >>> def grace_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.notes(_) for _ in result]
        ...     result = [abjad.select.exclude(_, [0, -1]) for _ in result]
        ...     result = abjad.select.notes(result)
        ...     return [[_] for _ in result]
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4], extra_counts=[2]),
        ...     rmakers.on_beat_grace_container(
        ...         [2, 4], grace_selector, leaf_duration=(1, 28)
        ...     ),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> music_voice = abjad.Voice(selections, name="RhythmMaker.Music")

        >>> lilypond_file = rmakers.example(
        ...     [music_voice], divisions, includes=["abjad.ily"]
        ... )
        >>> staff = lilypond_file["Staff"]
        >>> abjad.override(staff).TupletBracket.direction = abjad.UP
        >>> abjad.override(staff).TupletBracket.staff_padding = 5
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
                    \override TupletBracket.direction = #up
                    \override TupletBracket.staff-padding = 5
                }
                {
                    \context Voice = "RhythmMaker.Music"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5
                        {
                            \time 3/4
                            c'4
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            \oneVoice
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5
                        {
                            \time 3/4
                            c'4
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            \oneVoice
                            c'4
                        }
                    }
                }
            >>

    ..  container:: example

        >>> stack = rmakers.stack(
        ...     rmakers.talea([5], 16),
        ...     rmakers.extract_trivial(),
        ...     rmakers.on_beat_grace_container(
        ...         [6, 2], lambda _: abjad.select.logical_ties(_), leaf_duration=(1, 28)
        ...     ),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> music_voice = abjad.Voice(selections, name="RhythmMaker.Music")

        >>> lilypond_file = rmakers.example(
        ...     [music_voice], divisions, includes=["abjad.ily"]
        ... )
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
                    \context Voice = "RhythmMaker.Music"
                    {
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "RhythmMaker.Music"
                            {
                                \time 3/4
                                \voiceTwo
                                c'4
                                ~
                                c'16
                            }
                        >>
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "RhythmMaker.Music"
                            {
                                \voiceTwo
                                c'4
                                ~
                                c'16
                            }
                        >>
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "RhythmMaker.Music"
                            {
                                \voiceTwo
                                c'8
                                ~
                                \time 3/4
                                c'8.
                            }
                        >>
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "RhythmMaker.Music"
                            {
                                \voiceTwo
                                c'4
                                ~
                                c'16
                            }
                        >>
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "RhythmMaker.Music"
                            {
                                \voiceTwo
                                c'4
                            }
                        >>
                    }
                }
            >>

    """
    return OnBeatGraceContainerCommand(
        selector=selector,
        counts=counts,
        leaf_duration=abjad.Duration(leaf_duration),
        talea=talea,
        voice_name=voice_name,
    )


def repeat_tie(selector: typing.Callable | None = None) -> RepeatTieCommand:
    r"""
    Makes repeat-tie command.

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE. Attaches repeat-ties to first note in nonfirst
        tuplets:

        >>> def repeat_tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[1:]
        ...     result = [abjad.select.note(_, 0) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.repeat_tie(repeat_tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        With pattern:

        >>> def repeat_tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [1], 2)
        ...     result = [abjad.select.note(_, 0) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.repeat_tie(repeat_tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    """
    return RepeatTieCommand(selector=selector)


def repeat_tie_function(argument, *, tag=None) -> None:
    _do_repeat_tie_command(argument, tag=tag)


def reduce_multiplier(
    selector: typing.Callable | None = None,
) -> ReduceMultiplierCommand:
    """
    Makes reduce multiplier command.
    """
    return ReduceMultiplierCommand(selector=selector)


def reduce_multiplier_function(argument) -> None:
    """
    Reduces multipliers of tuplets in ``argument``.
    """
    _do_reduce_multiplier_command(argument)


def rewrite_dots(selector: typing.Callable | None = None) -> RewriteDotsCommand:
    """
    Makes rewrite dots command.
    """
    return RewriteDotsCommand(selector=selector)


def rewrite_dots_function(argument, *, tag: abjad.Tag = abjad.Tag()) -> None:
    """
    Rewrites dots of tuplets in ``argument``.
    """
    _do_rewrite_dots_command(argument, tag=tag)


def rewrite_meter(
    *, boundary_depth: int = None, reference_meters: typing.Sequence[abjad.Meter] = ()
) -> RewriteMeterCommand:
    """
    Makes rewrite meter command.
    """
    return RewriteMeterCommand(
        boundary_depth=boundary_depth, reference_meters=reference_meters
    )


def rewrite_meter_function(
    argument,
    *,
    boundary_depth: int = None,
    reference_meters: typing.Sequence[abjad.Meter] = (),
    tag=None,
) -> None:
    _do_rewrite_meter_command(
        argument,
        boundary_depth=boundary_depth,
        reference_meters=reference_meters,
        tag=tag,
    )


def rewrite_rest_filled(
    selector: typing.Callable | None = None, spelling: Spelling = Spelling()
) -> RewriteRestFilledCommand:
    r"""
    Makes rewrite rest-filled command.

    ..  container:: example

        Does not rewrite rest-filled tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 4/16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \times 4/5
                    {
                        \time 4/16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/16
                        r16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/16
                        r16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                }
            >>

        Rewrites rest-filled tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/16
                    r4
                    \time 4/16
                    r4
                    \time 5/16
                    r4
                    r16
                    \time 5/16
                    r4
                    r16
                }
            >>

        With spelling specifier:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.rewrite_rest_filled(
        ...         spelling=rmakers.Spelling(increase_monotonic=True)
        ...     ),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/16
                    r4
                    \time 4/16
                    r4
                    \time 5/16
                    r16
                    r4
                    \time 5/16
                    r16
                    r4
                }
            >>

        With selector:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.rewrite_rest_filled(lambda _: abjad.select.tuplets(_)[-2:]),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/5
                    {
                        \time 4/16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \times 4/5
                    {
                        \time 4/16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \time 5/16
                    r4
                    r16
                    \time 5/16
                    r4
                    r16
                }
            >>

        Note that nonassignable divisions necessitate multiple rests even after
        rewriting.

    """
    return RewriteRestFilledCommand(selector=selector, spelling=spelling)


def rewrite_rest_filled_function(argument, *, spelling=None, tag=None) -> None:
    """
    Rewrites rest-filled tuplets in ``argument``.
    """
    _do_rewrite_rest_filled_command(argument, spelling=spelling, tag=tag)


def rewrite_sustained(
    selector: typing.Callable | None = lambda _: abjad.select.tuplets(_),
) -> RewriteSustainedCommand:
    r"""
    Makes tuplet command.

    ..  container:: example

        Sustained tuplets generalize a class of rhythms composers are likely to rewrite:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[1:3]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 4/16
                        c'4.
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        ~
                        c'16
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        ~
                        c'16
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        c'16
                    }
                }
            >>

        The first three tuplets in the example above qualify as sustained:

            >>> staff = lilypond_file["Score"]
            >>> for tuplet in abjad.select.tuplets(staff):
            ...     abjad.get.sustained(tuplet)
            ...
            True
            True
            True
            False

        Tuplets 0 and 1 each contain only a single **tuplet-initial** attack. Tuplet 2
        contains no attack at all. All three fill their duration completely.

        Tuplet 3 contains a **nonintial** attack that rearticulates the tuplet's duration
        midway through the course of the figure. Tuplet 3 does not qualify as sustained.

    ..  container:: example

        Rewrite sustained tuplets like this:

        >>> def selector(argument):
        ...     result = abjad.select.tuplets(argument)[1:3]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result

        >>> stack = rmakers.stack(
        ...     rmakers.talea([6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]),
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/16
                        c'4
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/16
                        c'4
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        c'16
                    }
                }
            >>

    ..  container:: example

        Rewrite sustained tuplets -- and then extract the trivial tuplets that result --
        like this:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[1:3]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.talea([6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]),
        ...     rmakers.beam(),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \time 4/16
                    c'4
                    \time 4/16
                    c'4
                    ~
                    \time 4/16
                    c'4
                    ~
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        c'16
                    }
                }
            >>

    ..  container:: example

        With selector:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.notes(_)[:-1] for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.rewrite_sustained(lambda _: abjad.select.tuplets(_)[-2:]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/2
                    {
                        \time 2/8
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/2
                    {
                        \time 2/8
                        c'4
                    }
                }
            >>

    """
    return RewriteSustainedCommand(selector=selector)


def rewrite_sustained_function(argument) -> None:
    """
    Rewrite sustained tuplets in ``argument``.
    """
    _do_rewrite_sustained_command(argument)


def split_measures() -> SplitMeasuresCommand:
    """
    Makes split measures command.
    """
    return SplitMeasuresCommand()


def split_measures_function(argument, *, durations=None, tag=None) -> None:
    _do_split_measures_command(argument, durations=durations, tag=tag)


def tie(selector: typing.Callable | None = None) -> TieCommand:
    r"""
    Makes tie command.

    ..  container:: example

        TIE-CONSECUTIVE-NOTES RECIPE. Attaches ties notes in selection:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(lambda _: abjad.select.notes(_)[5:15]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE. Attaches ties to last note in nonlast tuplets:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     result = [abjad.select.note(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        With pattern:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [0], 2)
        ...     result = [abjad.select.note(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)[:-1]
        ...     result = [abjad.select.leaf(_, -1) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(5, 2)]),
        ...     rmakers.tie(tie_selector),
        ... )
        >>> divisions = [(4, 8), (4, 8), (4, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 4/7
                    {
                        \time 4/8
                        c'2
                        ~
                        c'8
                        c'4
                        ~
                    }
                    \times 4/7
                    {
                        \time 4/8
                        c'2
                        ~
                        c'8
                        c'4
                        ~
                    }
                    \times 4/7
                    {
                        \time 4/8
                        c'2
                        ~
                        c'8
                        c'4
                    }
                }
            >>

    ..  container:: example

        TIE-WITHIN-DIVISIONS RECIPE:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.notes(_)[:-1] for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.untie(tie_selector),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                }
            >>

        With pattern:

        >>> def tie_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = abjad.select.get(result, [0], 2)
        ...     result = [abjad.select.notes(_)[:-1] for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(tie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    """
    return TieCommand(selector=selector)


def tie_function(argument, *, tag: abjad.Tag = abjad.Tag()) -> None:
    """
    Attaches ties to notes in ``argument``.
    """
    _do_tie_command(argument, tag=tag)


def tremolo_container(
    count: int, selector: typing.Callable | None = None
) -> TremoloContainerCommand:
    r"""
    Makes tremolo container command.

    ..  container:: example

        Repeats figures two times each:

        >>> def tremolo_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.notes(_) for _ in result]
        ...     result = [abjad.select.get(_, [0, -1]) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4]),
        ...     rmakers.tremolo_container(2, tremolo_selector),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 4), (3, 4)]
        >>> selections = stack(divisions)

        >>> def slur_selector(argument):
        ...     return abjad.select.components(argument, abjad.TremoloContainer)
        >>> result = [abjad.slur(_) for _ in slur_selector(selections)]

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \repeat tremolo 2 {
                        \time 4/4
                        c'16
                        (
                        c'16
                        )
                    }
                    c'4
                    c'4
                    \repeat tremolo 2 {
                        c'16
                        (
                        c'16
                        )
                    }
                    \repeat tremolo 2 {
                        \time 3/4
                        c'16
                        (
                        c'16
                        )
                    }
                    c'4
                    \repeat tremolo 2 {
                        c'16
                        (
                        c'16
                        )
                    }
                }
            >>

        Repeats figures four times each:

        >>> def tremolo_selector(argument):
        ...     result = abjad.select.tuplets(argument)
        ...     result = [abjad.select.notes(_) for _ in result]
        ...     result = [abjad.select.get(_, [0, -1]) for _ in result]
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4]),
        ...     rmakers.tremolo_container(4, tremolo_selector),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 4), (3, 4)]
        >>> selections = stack(divisions)

        >>> def slur_selector(argument):
        ...     result = abjad.select.components(argument, abjad.TremoloContainer)
        ...     return result
        >>> result = [abjad.slur(_) for _ in slur_selector(selections)]

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \repeat tremolo 4 {
                        \time 4/4
                        c'32
                        (
                        c'32
                        )
                    }
                    c'4
                    c'4
                    \repeat tremolo 4 {
                        c'32
                        (
                        c'32
                        )
                    }
                    \repeat tremolo 4 {
                        \time 3/4
                        c'32
                        (
                        c'32
                        )
                    }
                    c'4
                    \repeat tremolo 4 {
                        c'32
                        (
                        c'32
                        )
                    }
                }
            >>

    """
    return TremoloContainerCommand(selector=selector, count=count)


def trivialize(selector: typing.Callable | None = None) -> TrivializeCommand:
    """
    Makes trivialize command.
    """
    return TrivializeCommand(selector=selector)


def trivialize_function(argument) -> None:
    """
    Trivializes tuplets in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        tuplet.trivialize()


def unbeam(
    selector: typing.Callable | None = lambda _: abjad.select.leaves(_),
) -> UnbeamCommand:
    """
    Makes unbeam command.
    """
    return UnbeamCommand(selector=selector)


def unbeam_function(argument) -> None:
    """
    Unbeams leaves in ``argument``.
    """
    leaves = abjad.select.leaves(argument)
    for leaf in leaves:
        abjad.detach(abjad.BeamCount, leaf)
        abjad.detach(abjad.StartBeam, leaf)
        abjad.detach(abjad.StopBeam, leaf)


def untie(selector: typing.Callable | None = None) -> UntieCommand:
    r"""
    Makes untie command.

    ..  container:: example

        Attaches ties to nonlast notes; then detaches ties from select notes:

        >>> def untie_selector(argument):
        ...     result = abjad.select.notes(argument)
        ...     result = abjad.select.get(result, [0], 4)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(lambda _: abjad.select.notes(_)[:-1]),
        ...     rmakers.untie(untie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Attaches repeat-ties to nonfirst notes; then detaches ties from select notes:

        >>> def untie_selector(argument):
        ...     result = abjad.select.notes(argument)
        ...     result = abjad.select.get(result, [0], 4)
        ...     return result
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.repeat_tie(lambda _: abjad.select.notes(_)[1:]),
        ...     rmakers.untie(untie_selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)

        >>> lilypond_file = rmakers.example(selections, divisions)
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        \repeatTie
                        c'8
                        ]
                        \repeatTie
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                        \repeatTie
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        \repeatTie
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        \repeatTie
                        c'8
                        ]
                        \repeatTie
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        \repeatTie
                        c'8
                        ]
                        \repeatTie
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                        \repeatTie
                    }
                }
            >>

    """
    return UntieCommand(selector=selector)


def untie_function(argument) -> None:
    """
    Removes ties in ``argument``.
    """
    _do_untie_command(argument)


def written_duration(
    duration: abjad.typings.Duration,
    selector: typing.Callable | None = lambda _: abjad.select.leaves(_),
) -> WrittenDurationCommand:
    """
    Makes written duration command.
    """
    duration_ = abjad.Duration(duration)
    return WrittenDurationCommand(selector=selector, duration=duration_)


def written_duration_function(argument, duration: abjad.typings.Duration) -> None:
    """
    Sets written duration of each leaf in ``argument`` to ``duration``.
    """
    duration_ = abjad.Duration(duration)
    _do_written_duration_command(argument, duration_)


RhythmMakerTyping: typing.TypeAlias = typing.Union[
    "Assignment", RhythmMaker, "Stack", "Bind"
]


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Match:
    """
    Match.
    """

    assignment: typing.Any
    payload: typing.Any


@dataclasses.dataclass(unsafe_hash=True)
class Bind:
    """
    Bind.
    """

    assignments: typing.Any = None
    tag: abjad.Tag = abjad.Tag()

    def __post_init__(self):
        self.assignments = self.assignments or ()
        for assignment in self.assignments:
            if not isinstance(assignment, Assignment):
                message = "must be assignment:\n"
                message += f"   {repr(assignment)}"
                raise Exception(message)
        self.assignments = tuple(self.assignments)
        self._state = dict()
        if self.tag:
            assert isinstance(self.tag, abjad.Tag), repr(self.tag)

    def __call__(self, divisions, previous_state: dict = None) -> list[abjad.Component]:
        division_count = len(divisions)
        matches = []
        for i, division in enumerate(divisions):
            for assignment in self.assignments:
                if assignment.predicate is None:
                    match = Match(assignment, division)
                    matches.append(match)
                    break
                elif isinstance(assignment.predicate, abjad.Pattern):
                    if assignment.predicate.matches_index(i, division_count):
                        match = Match(assignment, division)
                        matches.append(match)
                        break
                elif assignment.predicate(division):
                    match = Match(assignment, division)
                    matches.append(match)
                    break
            else:
                raise Exception(f"no match for division {i}.")
        assert len(divisions) == len(matches)
        groups = abjad.sequence.group_by(
            matches, lambda match: match.assignment.rhythm_maker
        )
        components: list[abjad.Component] = []
        maker_to_previous_state: dict = dict()
        for group in groups:
            rhythm_maker = group[0].assignment.rhythm_maker
            assert callable(rhythm_maker), repr(rhythm_maker)
            if self.tag and hasattr(rhythm_maker, "tag"):
                rhythm_maker = dataclasses.replace(rhythm_maker, tag=self.tag)
            divisions_ = [match.payload for match in group]
            previous_state_ = previous_state
            if previous_state_ is None:
                previous_state_ = maker_to_previous_state.get(rhythm_maker, None)
            state = None
            if isinstance(rhythm_maker, RhythmMaker | Stack):
                selection = rhythm_maker(divisions_, previous_state=previous_state_)
            elif previous_state_ is not None:
                result = rhythm_maker(divisions_, previous_state=previous_state_)
                assert isinstance(result, tuple), repr(result)
                assert len(result) == 2
                selection, state = result
            else:
                result = rhythm_maker(divisions_)
                if isinstance(result, tuple):
                    assert len(result) == 2
                    selection, state = result
                else:
                    assert isinstance(result, list)
                    selection = result
            assert isinstance(selection, list), repr(selection)
            components.extend(selection)
            if hasattr(rhythm_maker, "state"):
                maker_to_previous_state[rhythm_maker] = rhythm_maker.state
            elif state is not None:
                maker_to_previous_state[rhythm_maker] = state
        assert callable(rhythm_maker), repr(rhythm_maker)
        if hasattr(rhythm_maker, "state"):
            self._state = rhythm_maker.state
        elif state is not None:
            self._state = state
        return components

    @property
    def state(self) -> dict:
        """
        Gets state.
        """
        return self._state


@dataclasses.dataclass
class Stack:
    """
    Stack.

    ..  container:: example

        Repr looks like this:

        >>> rmakers.stack(
        ...     rmakers.tuplet([(1, 2)]),
        ...     rmakers.force_fraction(),
        ... )
        Stack(maker=TupletRhythmMaker(spelling=Spelling(forbidden_note_duration=None, forbidden_rest_duration=None, increase_monotonic=False), tag=Tag(string=''), denominator=None, tuplet_ratios=[Ratio(numbers=(1, 2))]), commands=(ForceFractionCommand(selector=None),), preprocessor=None, tag=Tag(string=''))

    ..  container:: example

        REGRESSION. Copy preserves commands:

        >>> import dataclasses
        >>> command_1 = rmakers.stack(
        ...     rmakers.tuplet([(1, 2)]),
        ...     rmakers.force_fraction(),
        ... )
        >>> command_2 = dataclasses.replace(command_1)

        >>> command_1
        Stack(maker=TupletRhythmMaker(spelling=Spelling(forbidden_note_duration=None, forbidden_rest_duration=None, increase_monotonic=False), tag=Tag(string=''), denominator=None, tuplet_ratios=[Ratio(numbers=(1, 2))]), commands=(ForceFractionCommand(selector=None),), preprocessor=None, tag=Tag(string=''))

        >>> command_2
        Stack(maker=TupletRhythmMaker(spelling=Spelling(forbidden_note_duration=None, forbidden_rest_duration=None, increase_monotonic=False), tag=Tag(string=''), denominator=None, tuplet_ratios=[Ratio(numbers=(1, 2))]), commands=(ForceFractionCommand(selector=None),), preprocessor=None, tag=Tag(string=''))

        >>> command_1 == command_2
        True

    """

    maker: typing.Union[RhythmMaker, "Stack", Bind]
    commands: typing.Sequence[Command] = ()
    preprocessor: typing.Callable | None = None
    tag: abjad.Tag = abjad.Tag()

    def __post_init__(self):
        prototype = (list, RhythmMaker, Stack, Bind)
        assert isinstance(self.maker, prototype), repr(self.maker)
        assert isinstance(self.tag, abjad.Tag), repr(self.tag)
        if self.tag.string:
            self.maker = dataclasses.replace(self.maker, tag=self.tag)
        self.commands = tuple(self.commands or ())

    def __call__(
        self,
        time_signatures: typing.Sequence[tuple[int, int]],
        previous_state: dict = None,
    ) -> list[abjad.Component]:
        time_signatures_ = [abjad.TimeSignature(_) for _ in time_signatures]
        divisions_ = [abjad.NonreducedFraction(_) for _ in time_signatures]
        staff = _make_time_signature_staff(time_signatures_)
        music_voice = staff["RhythmMaker.Music"]
        divisions = self._apply_division_expression(divisions_)
        selection = self.maker(divisions, previous_state=previous_state)
        music_voice.extend(selection)
        for command in self.commands:
            if isinstance(command, CacheStateCommand):
                assert isinstance(self.maker, RhythmMaker), repr(self.maker)
                self.maker._cache_state(music_voice, len(divisions))
                self.maker.already_cached_state = True
            try:
                command(music_voice, tag=self.tag)
            except Exception:
                message = "exception while calling:\n"
                message += f"   {format(command)}"
                raise Exception(message)
        result = music_voice[:]
        music_voice[:] = []
        return list(result)

    def __hash__(self):
        """
        Gets hash.
        """
        return hash(repr(self))

    def _apply_division_expression(self, divisions):
        prototype = abjad.NonreducedFraction
        if not all(isinstance(_, prototype) for _ in divisions):
            message = "must be nonreduced fractions:\n"
            message += f"   {repr(divisions)}"
            raise Exception(message)
        original_duration = abjad.Duration(sum(divisions))
        if self.preprocessor is not None:
            result = self.preprocessor(divisions)
            if not isinstance(result, list):
                message = "division preprocessor must return list:\n"
                message += "  Input divisions:\n"
                message += f"    {divisions}\n"
                message += "  Division preprocessor:\n"
                message += f"    {self.preprocessor}\n"
                message += "  Result:\n"
                message += f"    {result}"
                raise Exception(message)
            divisions = result
        divisions = abjad.sequence.flatten(divisions, depth=-1)
        transformed_duration = abjad.Duration(sum(divisions))
        if transformed_duration != original_duration:
            message = "original duration ...\n"
            message += f"    {original_duration}\n"
            message += "... does not equal ...\n"
            message += f"    {transformed_duration}\n"
            message += "... transformed duration."
            raise Exception(message)
        return divisions

    @property
    def state(self) -> dict:
        """
        Gets state.
        """
        return self.maker.state


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Assignment:
    """
    Assignment.
    """

    rhythm_maker: RhythmMaker | Stack
    predicate: typing.Callable | abjad.Pattern | None = None

    def __post_init__(self):
        assert (
            self.predicate is None
            or isinstance(self.predicate, abjad.Pattern)
            or callable(self.predicate)
        )
        assert callable(self.rhythm_maker), repr(self.rhythm_maker)


def assign(
    rhythm_maker: RhythmMaker | Stack,
    predicate: typing.Callable | abjad.Pattern | None = None,
) -> Assignment:
    """
    Makes assignment.
    """
    return Assignment(
        rhythm_maker,
        predicate,
    )


def bind(*assignments: Assignment, tag: abjad.Tag = abjad.Tag()) -> Bind:
    """
    Makes bind.
    """
    assert isinstance(assignments, tuple)
    return Bind(assignments, tag=tag)


def stack(
    maker: RhythmMaker | Stack | Bind,
    *commands: Command,
    preprocessor: typing.Callable | None = None,
    tag: abjad.Tag = abjad.Tag(),
) -> Stack:
    """
    Makes stack.
    """
    assert isinstance(commands, tuple)
    return Stack(maker, commands, preprocessor=preprocessor, tag=tag)
