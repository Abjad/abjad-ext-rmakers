"""
The rmakers classes.
"""

import dataclasses
import typing

import abjad


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Incise:
    """
    Incise specifier.
    """

    body_ratio: tuple[int, ...] = (1,)
    fill_with_rests: bool = False
    outer_tuplets_only: bool = False
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
        assert isinstance(self.body_ratio, tuple), repr(self.body_ratio)
        assert isinstance(self.fill_with_rests, bool), repr(self.fill_with_rests)
        assert isinstance(self.outer_tuplets_only, bool), repr(self.outer_tuplets_only)

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

        Changes accelerando specifier to ritardando specifier:

        ..  container:: example

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

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in pairs]
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=False),
        ...     )
        ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file_["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file_

        >>> lilypond_file = make_lilypond_file([(3, 4), (3, 4)])
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
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
                        c'8.
                        c'4
                        ~
                        c'16
                        c'4
                    }
                }
            }

    ..  container:: example

        Increases monotically:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=True),
        ...     )
        ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file_["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file_

        >>> pairs = [(3, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
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
                        c'8.
                        [
                        c'16
                        ]
                        ~
                        c'4
                        c'4
                    }
                }
            }

    ..  container:: example

        Forbids note durations equal to ``1/4`` or greater:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [1, 1, 1, 1, 4, -4],
        ...         16,
        ...         spelling=rmakers.Spelling(
        ...             forbidden_note_duration=abjad.Duration(1, 4)
        ...         ),
        ...     )
        ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file_["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file_

        >>> pairs = [(3, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
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
                }
            }

    ..  container:: example

        Forbids rest durations equal to ``1/4`` or greater:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [1, 1, 1, 1, 4, -4],
        ...         16,
        ...         spelling=rmakers.Spelling(
        ...             forbidden_rest_duration=abjad.Duration(1, 4)
        ...         ),
        ...     )
        ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file_["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file_

        >>> pairs = [(3, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
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
                }
            }

    ..  container:: example

        Spells nonassignable durations with monontonically decreasing durations:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=False),
        ...     )
        ...     container = abjad.Container(tuplets)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (5, 8), (5, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 5/8
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                    }
                }
            }

    ..  container:: example

        Spells nonassignable durations with monontonically increasing durations:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=True),
        ...     )
        ...     container = abjad.Container(tuplets)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (5, 8), (5, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 5/8
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                    }
                }
            }

    ..  container:: example

        Forbids durations equal to ``1/4`` or greater:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [1, 1, 1, 1, 4, 4], 16,
        ...         spelling=rmakers.Spelling(
        ...             forbidden_note_duration=abjad.Duration(1, 4)
        ...         ),
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
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
                }
            }

        Rewrites forbidden durations with smaller durations tied together.

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

        With preamble:

        ..  container:: example

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

    def __getitem__(self, argument) -> tuple[int, int] | list[tuple[int, int]]:
        """
        Gets item or slice identified by ``argument``.

        Gets item at index:

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> talea[0]
            (1, 16)

            >>> talea[1]
            (1, 16)

        ..  container:: example

            Gets items in slice:

            >>> for duration in talea[:6]:
            ...     duration
            ...
            (1, 16)
            (1, 16)
            (1, 16)
            (1, 16)
            (2, 16)
            (1, 16)

            >>> for duration in talea[2:8]:
            ...     duration
            ...
            (1, 16)
            (1, 16)
            (2, 16)
            (1, 16)
            (3, 16)
            (2, 16)

        """
        preamble: list[int | str] = list(self.preamble)
        counts = list(self.counts)
        counts_ = abjad.CyclicTuple(preamble + counts)
        if isinstance(argument, int):
            count = counts_.__getitem__(argument)
            return (count, self.denominator)
        elif isinstance(argument, slice):
            counts_ = counts_.__getitem__(argument)
            result = [(count, self.denominator) for count in counts_]
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
