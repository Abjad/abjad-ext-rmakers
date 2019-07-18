import abjad
import typing

ClassTyping = typing.Union[int, type]


### CLASSES ###


class BurnishSpecifier(object):
    """
    Burnish specifier.

    ..  container:: example

        Forces first leaf of each division to be a rest:

        >>> burnish_specifier = rmakers.BurnishSpecifier(
        ...     left_classes=[abjad.Rest],
        ...     left_counts=[1],
        ...     )

    ..  container:: example

        Forces the first three leaves of each division to be rests:

        >>> burnish_specifier = rmakers.BurnishSpecifier(
        ...     left_classes=[abjad.Rest],
        ...     left_counts=[3],
        ...     )

    ..  container:: example

        Forces last leaf of each division to be a rest:

        >>> burnish_specifier = rmakers.BurnishSpecifier(
        ...     right_classes=[abjad.Rest],
        ...     right_counts=[1],
        ...     )

    ..  container:: example

        Forces the last three leaves of each division to be rests:

        >>> burnish_specifier = rmakers.BurnishSpecifier(
        ...     right_classes=[abjad.Rest],
        ...     right_counts=[3],
        ...     )

    ..  container:: example

        Forces the first leaf of every even-numbered division to be a rest;
        forces the first leaf of every odd-numbered division to be a note.

        >>> burnish_specifier = rmakers.BurnishSpecifier(
        ...     left_classes=[abjad.Rest, abjad.Note],
        ...     left_counts=[1],
        ...     )

    ..  container:: example

        Forces the last leaf of every even-numbered division to be a rest;
        forces the last leaf of every odd-numbered division to be a note.

        >>> burnish_specifier = rmakers.BurnishSpecifier(
        ...     right_classes=[abjad.Rest, abjad.Note],
        ...     right_counts=[1],
        ...     )

    ..  container:: example

        Forces the first leaf of every even-numbered division to be a rest;
        leave the first leaf of every odd-numbered division unchanged.

        >>> burnish_specifier = rmakers.BurnishSpecifier(
        ...     left_classes=[abjad.Rest, 0],
        ...     left_counts=[1],
        ...     )

    ..  container:: example

        Forces the last leaf of every even-numbered division to be a rest;
        leave the last leaf of every odd-numbered division unchanged.

        >>> burnish_specifier = rmakers.BurnishSpecifier(
        ...     right_classes=[abjad.Rest, 0],
        ...     right_counts=[1],
        ...     )

    Burnish specifiers are immutable.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = (
        "_left_classes",
        "_left_counts",
        "_middle_classes",
        "_outer_divisions_only",
        "_right_counts",
        "_right_classes",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        left_classes: typing.Sequence[ClassTyping] = None,
        left_counts: typing.Sequence[int] = None,
        middle_classes: typing.Sequence[ClassTyping] = None,
        outer_divisions_only: bool = None,
        right_classes: typing.Sequence[ClassTyping] = None,
        right_counts: typing.Sequence[int] = None,
    ) -> None:
        if outer_divisions_only is not None:
            outer_divisions_only = bool(outer_divisions_only)
        self._outer_divisions_only = outer_divisions_only
        if left_classes is not None:
            left_classes = tuple(left_classes)
        if middle_classes is not None:
            middle_classes = tuple(middle_classes)
        if middle_classes == (0,):
            middle_classes = ()
        if right_classes is not None:
            right_classes = tuple(right_classes)
        if left_counts is not None:
            left_counts = tuple(left_counts)
        if right_counts is not None:
            right_counts = tuple(right_counts)
        assert self._is_sign_tuple(left_classes)
        assert self._is_sign_tuple(middle_classes)
        assert self._is_sign_tuple(right_classes)
        assert self._is_length_tuple(left_counts)
        assert self._is_length_tuple(right_counts)
        self._left_classes = left_classes
        self._middle_classes = middle_classes
        self._right_classes = right_classes
        self._left_counts = left_counts
        self._right_counts = right_counts

    ### SPECIAL METHODS ###

    def __call__(self, divisions) -> typing.List[abjad.NonreducedFraction]:
        """
        Calls burnish specifier on ``divisions``.
        """
        input_ = self._prepare_input()
        if self.outer_divisions_only:
            return self._burnish_outer_divisions(input_, divisions)
        else:
            return self._burnish_each_division(input_, divisions)

    def __format__(self, format_specification="") -> str:
        """
        Formats burnish specifier.

        ..  container:: example

            >>> burnish_specifier = rmakers.BurnishSpecifier(
            ...     left_classes=[abjad.Rest, 0],
            ...     left_counts=[1],
            ...     )

            >>> abjad.f(burnish_specifier)
            abjadext.specifiers.BurnishSpecifier(
                left_classes=[
                    abjad.Rest,
                    0,
                    ],
                left_counts=[1],
                )

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> burnish_specifier = rmakers.BurnishSpecifier(
            ...     left_classes=[abjad.Rest, 0],
            ...     left_counts=[1],
            ...     )

            >>> burnish_specifier
            BurnishSpecifier(left_classes=[Rest, 0], left_counts=[1])

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    @staticmethod
    def _burnish_division_part(division_part, token):
        assert len(division_part) == len(token)
        new_division_part = []
        for number, i in zip(division_part, token):
            if i in (-1, abjad.Rest):
                new_division_part.append(-abs(number))
            elif i == 0:
                new_division_part.append(number)
            elif i in (1, abjad.Note):
                new_division_part.append(abs(number))
            else:
                raise ValueError("unknown burnshing: {i!r}.")
        new_division_part = type(division_part)(new_division_part)
        return new_division_part

    @classmethod
    def _burnish_each_division(class_, input_, divisions):
        left_classes = input_["left_classes"]
        middle_classes = input_["middle_classes"]
        right_classes = input_["right_classes"]
        left_counts = input_["left_counts"]
        left_counts = left_counts or abjad.CyclicTuple([0])
        right_counts = input_["right_counts"]
        right_counts = right_counts or abjad.CyclicTuple([0])
        lefts_index, rights_index = 0, 0
        burnished_divisions = []
        for division_index, division in enumerate(divisions):
            left_count = left_counts[division_index]
            left = left_classes[lefts_index : lefts_index + left_count]
            lefts_index += left_count
            right_count = right_counts[division_index]
            right = right_classes[rights_index : rights_index + right_count]
            rights_index += right_count
            available_left_count = len(division)
            left_count = min([left_count, available_left_count])
            available_right_count = len(division) - left_count
            right_count = min([right_count, available_right_count])
            middle_count = len(division) - left_count - right_count
            left = left[:left_count]
            if middle_classes:
                middle = middle_count * [middle_classes[division_index]]
            else:
                middle = middle_count * [0]
            right = right[:right_count]
            result = abjad.sequence(division).partition_by_counts(
                [left_count, middle_count, right_count],
                cyclic=False,
                overhang=False,
            )
            left_part, middle_part, right_part = result
            left_part = class_._burnish_division_part(left_part, left)
            middle_part = class_._burnish_division_part(middle_part, middle)
            right_part = class_._burnish_division_part(right_part, right)
            burnished_division = left_part + middle_part + right_part
            burnished_divisions.append(burnished_division)
        unburnished_weights = [abjad.mathtools.weight(x) for x in divisions]
        burnished_weights = [
            abjad.mathtools.weight(x) for x in burnished_divisions
        ]
        assert burnished_weights == unburnished_weights
        return burnished_divisions

    @classmethod
    def _burnish_outer_divisions(class_, input_, divisions):
        for list_ in divisions:
            assert all(isinstance(_, int) for _ in list_), repr(list_)
        left_classes = input_["left_classes"]
        middle_classes = input_["middle_classes"]
        right_classes = input_["right_classes"]
        left_counts = input_["left_counts"]
        left_counts = left_counts or abjad.CyclicTuple([0])
        right_counts = input_["right_counts"]
        right_counts = right_counts or abjad.CyclicTuple([0])
        burnished_divisions = []
        left_count = 0
        if left_counts:
            left_count = left_counts[0]
        left = left_classes[:left_count]
        right_count = 0
        if right_counts:
            right_count = right_counts[0]
        right = right_classes[:right_count]
        if len(divisions) == 1:
            available_left_count = len(divisions[0])
            left_count = min([left_count, available_left_count])
            available_right_count = len(divisions[0]) - left_count
            right_count = min([right_count, available_right_count])
            middle_count = len(divisions[0]) - left_count - right_count
            left = left[:left_count]
            if not middle_classes:
                middle_classes = [1]
            middle = [middle_classes[0]]
            middle = middle_count * middle
            right = right[:right_count]
            result = abjad.sequence(divisions[0]).partition_by_counts(
                [left_count, middle_count, right_count],
                cyclic=False,
                overhang=abjad.Exact,
            )
            left_part, middle_part, right_part = result
            left_part = class_._burnish_division_part(left_part, left)
            middle_part = class_._burnish_division_part(middle_part, middle)
            right_part = class_._burnish_division_part(right_part, right)
            burnished_division = left_part + middle_part + right_part
            burnished_divisions.append(burnished_division)
        else:
            # first division
            available_left_count = len(divisions[0])
            left_count = min([left_count, available_left_count])
            middle_count = len(divisions[0]) - left_count
            left = left[:left_count]
            if not middle_classes:
                middle_classes = [1]
            middle = [middle_classes[0]]
            middle = middle_count * middle
            result = abjad.sequence(divisions[0]).partition_by_counts(
                [left_count, middle_count], cyclic=False, overhang=abjad.Exact
            )
            left_part, middle_part = result
            left_part = class_._burnish_division_part(left_part, left)
            middle_part = class_._burnish_division_part(middle_part, middle)
            burnished_division = left_part + middle_part
            burnished_divisions.append(burnished_division)
            # middle divisions
            for division in divisions[1:-1]:
                middle_part = division
                middle = len(division) * [middle_classes[0]]
                middle_part = class_._burnish_division_part(
                    middle_part, middle
                )
                burnished_division = middle_part
                burnished_divisions.append(burnished_division)
            # last division:
            available_right_count = len(divisions[-1])
            right_count = min([right_count, available_right_count])
            middle_count = len(divisions[-1]) - right_count
            right = right[:right_count]
            middle = middle_count * [middle_classes[0]]
            result = abjad.sequence(divisions[-1]).partition_by_counts(
                [middle_count, right_count], cyclic=False, overhang=abjad.Exact
            )
            middle_part, right_part = result
            middle_part = class_._burnish_division_part(middle_part, middle)
            right_part = class_._burnish_division_part(right_part, right)
            burnished_division = middle_part + right_part
            burnished_divisions.append(burnished_division)
        unburnished_weights = [abjad.mathtools.weight(x) for x in divisions]
        burnished_weights = [
            abjad.mathtools.weight(x) for x in burnished_divisions
        ]
        assert burnished_weights == unburnished_weights
        assert tuple(burnished_weights) == tuple(unburnished_weights)
        return burnished_divisions

    @staticmethod
    def _is_length_tuple(argument):
        if argument is None:
            return True
        if abjad.mathtools.all_are_nonnegative_integer_equivalent_numbers(
            argument
        ):
            if isinstance(argument, tuple):
                return True
        return False

    @staticmethod
    def _is_sign_tuple(argument):
        if argument is None:
            return True
        if isinstance(argument, tuple):
            prototype = (-1, 0, 1, abjad.Note, abjad.Rest)
            return all(_ in prototype for _ in argument)
        return False

    def _prepare_input(self):
        input_ = {}
        names = (
            "left_classes",
            "left_counts",
            "middle_classes",
            "right_classes",
            "right_counts",
        )
        for name in names:
            value = getattr(self, name)
            value = value or ()
            value = abjad.CyclicTuple(value)
            input_[name] = value
        return input_

    ### PUBLIC PROPERTIES ###

    @property
    def left_classes(self) -> typing.Optional[typing.List[ClassTyping]]:
        """
        Gets left classes.

        ..  container:: example

            >>> burnish_specifier = rmakers.BurnishSpecifier(
            ...     left_classes=[abjad.Rest, 0],
            ...     right_classes=[abjad.Rest, abjad.Rest, 0],
            ...     left_counts=[2],
            ...     right_counts=[1],
            ...     )

            >>> burnish_specifier.left_classes
            [<class 'abjad.core.Rest.Rest'>, 0]

        """
        if self._left_classes:
            return list(self._left_classes)
        return None

    @property
    def left_counts(self) -> typing.Optional[typing.List[int]]:
        """
        Gets left counts.

        ..  container:: example

            >>> burnish_specifier = rmakers.BurnishSpecifier(
            ...     left_classes=[abjad.Rest, 0],
            ...     right_classes=[abjad.Rest, abjad.Rest, 0],
            ...     left_counts=[2],
            ...     right_counts=[1],
            ...     )

            >>> burnish_specifier.left_counts
            [2]

        """
        if self._left_counts:
            return list(self._left_counts)
        return None

    @property
    def middle_classes(self) -> typing.Optional[typing.List[ClassTyping]]:
        """
        Gets middle_classes.

        ..  container:: example

            >>> burnish_specifier = rmakers.BurnishSpecifier(
            ...     left_classes=[abjad.Rest, 0],
            ...     right_classes=[abjad.Rest, abjad.Rest, 0],
            ...     left_counts=[2],
            ...     right_counts=[1],
            ...     )

            >>> burnish_specifier.middle_classes is None
            True

        """
        if self._middle_classes:
            return list(self._middle_classes)
        return None

    @property
    def outer_divisions_only(self) -> typing.Optional[bool]:
        """
        Is true when rhythm-maker burnishes only first and last
        division in output.

        Is false when rhythm-maker burnishes all divisions.
        """
        return self._outer_divisions_only

    @property
    def right_classes(self) -> typing.Optional[typing.List[ClassTyping]]:
        """
        Gets right classes.

        ..  container:: example

            >>> burnish_specifier = rmakers.BurnishSpecifier(
            ...     left_classes=[abjad.Rest, 0],
            ...     right_classes=[abjad.Rest, abjad.Rest, 0],
            ...     left_counts=[2],
            ...     right_counts=[1],
            ...     )

            >>> burnish_specifier.right_classes
            [<class 'abjad.core.Rest.Rest'>, <class 'abjad.core.Rest.Rest'>, 0]

        """
        if self._right_classes:
            return list(self._right_classes)
        return None

    @property
    def right_counts(self) -> typing.Optional[typing.List[int]]:
        """
        Gets right counts.

        ..  container:: example

            >>> burnish_specifier = rmakers.BurnishSpecifier(
            ...     left_classes=[abjad.Rest, 0],
            ...     right_classes=[abjad.Rest, abjad.Rest, 0],
            ...     left_counts=[2],
            ...     right_counts=[1],
            ...     )

            >>> burnish_specifier.right_counts
            [1]

        """
        if self._right_counts:
            return list(self._right_counts)
        return None


class DurationSpecifier(object):
    """
    Duration specifier.
    """

    ### CLASS VARIABLES ###

    ###__documentation_section__ = "Specifiers"

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

            >>> specifier = rmakers.DurationSpecifier()
            >>> abjad.f(specifier)
            abjadext.specifiers.DurationSpecifier()

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> rmakers.DurationSpecifier()
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     duration_specifier=rmakers.DurationSpecifier(
            ...         increase_monotonic=False,
            ...         ),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     duration_specifier=rmakers.DurationSpecifier(
            ...         increase_monotonic=True,
            ...         ),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     duration_specifier=rmakers.DurationSpecifier(
            ...         forbidden_note_duration=(1, 4),
            ...         ),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     duration_specifier=rmakers.DurationSpecifier(
            ...         forbidden_rest_duration=(1, 4),
            ...         ),
            ...     talea=rmakers.Talea(
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


class InciseSpecifier(object):
    """
    Incise specifier.

    ..  container:: example

        Specifies one sixteenth rest cut out of the beginning of every
        division:

        >>> specifier = rmakers.InciseSpecifier(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     talea_denominator=16,
        ...     )

    ..  container:: example

        Specifies sixteenth rests cut out of the beginning and end of each
        division:

        >>> specifier = rmakers.InciseSpecifier(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     suffix_talea=[-1],
        ...     suffix_counts=[1],
        ...     talea_denominator=16,
        ...     )

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

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        body_ratio: abjad.Ratio = None,
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
            if not abjad.mathtools.is_nonnegative_integer_power_of_two(
                talea_denominator
            ):
                message = "talea denominator {!r} must be nonnegative"
                message += " integer power of 2."
                message = message.format(talea_denominator)
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
        self._outer_divisions_only: typing.Optional[
            bool
        ] = outer_divisions_only

    ### SPECIAL METHODS ###

    def __format__(self, format_specification="") -> str:
        """
        Formats incise specifier.

        ..  container:: example

            Formats incise specifier:

            >>> specifier = rmakers.InciseSpecifier(
            ...     prefix_talea=[-1],
            ...     prefix_counts=[1],
            ...     talea_denominator=16,
            ...     )

            >>> abjad.f(specifier)
            abjadext.specifiers.InciseSpecifier(
                prefix_counts=[1],
                prefix_talea=[-1],
                suffix_counts=(),
                suffix_talea=(),
                talea_denominator=16,
                )

        ..  container:: example

            Formats incise specifier:

            >>> specifier = rmakers.InciseSpecifier(
            ...     prefix_talea=[-1],
            ...     prefix_counts=[0, 1],
            ...     suffix_talea=[-1],
            ...     suffix_counts=[1],
            ...     talea_denominator=16,
            ...     )

            >>> abjad.f(specifier)
            abjadext.specifiers.InciseSpecifier(
                prefix_counts=[0, 1],
                prefix_talea=[-1],
                suffix_counts=[1],
                suffix_talea=[-1],
                talea_denominator=16,
                )

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
        if abjad.mathtools.all_are_nonnegative_integer_equivalent_numbers(
            argument
        ):
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

            >>> specifier = rmakers.InciseSpecifier(
            ...     prefix_talea=[-1],
            ...     prefix_counts=[0, 1],
            ...     suffix_talea=[-1],
            ...     suffix_counts=[1],
            ...     talea_denominator=16,
            ...     body_ratio=abjad.Ratio((1, 1)),
            ...     )
            >>> rhythm_maker = rmakers.IncisedRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
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

                >>> abjad.f(lilypond_file[abjad.Score])
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


class InterpolationSpecifier(object):
    """
    Interpolation specifier.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = ("_start_duration", "_stop_duration", "_written_duration")

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

    ### SPECIAL METHODS ###

    def __format__(self, format_specification="") -> str:
        """
        Formats interpolation specifier.

        ..  container:: example

            >>> specifier = rmakers.InterpolationSpecifier(
            ...     start_duration=(1, 4),
            ...     stop_duration=(1, 16),
            ...     written_duration=(1, 16),
            ...     )
            >>> abjad.f(specifier)
            abjadext.specifiers.InterpolationSpecifier(
                start_duration=abjad.Duration(1, 4),
                stop_duration=abjad.Duration(1, 16),
                written_duration=abjad.Duration(1, 16),
                )

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of interpolation specifier.

        ..  container:: example

            >>> rmakers.InterpolationSpecifier(
            ...     start_duration=(1, 4),
            ...     stop_duration=(1, 16),
            ...     written_duration=(1, 16),
            ...     )
            InterpolationSpecifier(start_duration=Duration(1, 4), stop_duration=Duration(1, 16), written_duration=Duration(1, 16))

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC METHODS ###

    def reverse(self) -> "InterpolationSpecifier":
        """
        Swaps start duration and stop duration of interpolation specifier.

        ..  container:: example

            Changes accelerando specifier to ritardando specifier:

            >>> specifier = rmakers.InterpolationSpecifier(
            ...     start_duration=(1, 4),
            ...     stop_duration=(1, 16),
            ...     written_duration=(1, 16),
            ...     )
            >>> specifier = specifier.reverse()
            >>> abjad.f(specifier)
            abjadext.specifiers.InterpolationSpecifier(
                start_duration=abjad.Duration(1, 16),
                stop_duration=abjad.Duration(1, 4),
                written_duration=abjad.Duration(1, 16),
                )

        ..  container:: example

            Changes ritardando specifier to accelerando specifier:

            >>> specifier = rmakers.InterpolationSpecifier(
            ...     start_duration=(1, 16),
            ...     stop_duration=(1, 4),
            ...     written_duration=(1, 16),
            ...     )
            >>> specifier = specifier.reverse()
            >>> abjad.f(specifier)
            abjadext.specifiers.InterpolationSpecifier(
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
