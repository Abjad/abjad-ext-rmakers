import abjad
import typing
from . import typings
from .RhythmMaker import RhythmMaker


RhythmMakerTyping = typing.Union[
    RhythmMaker, "MakerAssignment", "MakerAssignments"
]


class MakerAssignment(object):
    """
    Maker assignment.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_pattern", "_remember_state_across_gaps", "_rhythm_maker")

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        pattern: typing.Union[abjad.DurationInequality, abjad.Pattern],
        # TODO: eventually restore typecheck:
        ###rhythm_maker: typing.Union[RhythmMaker, "RhythmCommand"],
        rhythm_maker,
        *,
        remember_state_across_gaps: bool = None,
    ) -> None:
        prototype = (abjad.DurationInequality, abjad.Pattern)
        assert isinstance(pattern, prototype), repr(pattern)
        self._pattern = pattern
        ###r_prototype = (RhythmMaker, RhythmCommand)
        ###assert isinstance(rhythm_maker, r_prototype), repr(rhythm_maker)
        self._rhythm_maker = rhythm_maker
        if remember_state_across_gaps is None:
            remember_state_across_gaps = bool(remember_state_across_gaps)
        self._remember_state_across_gaps = remember_state_across_gaps

    ### SPECIAL METHODS ###

    def __format__(self, format_specification="") -> str:
        """
        Gets storage format.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC PROPERTIES ###

    @property
    def pattern(self) -> typing.Union[abjad.DurationInequality, abjad.Pattern]:
        """
        Gets pattern.
        """
        return self._pattern

    @property
    def remember_state_across_gaps(self) -> typing.Optional[bool]:
        """
        Is true when assignment remembers rhythm-maker state across gaps.
        """
        return self._remember_state_across_gaps

    # TODO: eventually restore typecheck
    @property
    ###def rhythm_maker(self) -> typing.Union[RhythmMaker, "RhythmCommand"]:
    def rhythm_maker(self):
        """
        Gets rhythm-maker.
        """
        return self._rhythm_maker


class MakerAssignments(object):
    """
    Maker assignments.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_assignments",)

    _positional_arguments_name = "assignments"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(self, *assignments: MakerAssignment) -> None:
        assignments = assignments or ()
        for assignment in assignments:
            assert isinstance(assignment, MakerAssignment), repr(assignment)
        assignments_ = tuple(assignments)
        self._assignments = assignments_

    ### SPECIAL METHODS ###

    def __format__(self, format_specification="") -> str:
        """
        Gets storage format.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _get_format_specification(self):
        # specifiers = self.specifiers or []
        return abjad.FormatSpecification(
            self, storage_format_args_values=self.assignments
        )

    ### PUBLIC PROPERTIES ###

    @property
    def assignments(self) -> typing.List[MakerAssignment]:
        """
        Gets specifiers.
        """
        return list(self._assignments)


class MakerMatch(object):
    """
    Maker match.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_assignment", "_division")

    ### INITIALIZER ###

    def __init__(
        self, division: abjad.NonreducedFraction, assignment: MakerAssignment
    ) -> None:
        prototype = (abjad.NonreducedFraction, abjad.TimeSignature)
        assert isinstance(division, prototype), repr(division)
        self._division = division
        assert isinstance(assignment, MakerAssignment), repr(assignment)
        self._assignment = assignment

    ### SPECIAL METHODS ###

    def __format__(self, format_specification="") -> str:
        """
        Gets storage format.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC PROPERTIES ###

    @property
    def assignment(self) -> MakerAssignment:
        """
        Gets assignment.
        """
        return self._assignment

    @property
    def division(self) -> abjad.NonreducedFraction:
        """
        Gets division.
        """
        return self._division


class RhythmCommand(object):
    r"""
    Rhythm command.

    ..  container:: example

        >>> even_divisions = abjadext.rmakers.EvenDivisionRhythmMaker(
        ...     denominator=16,
        ...     extra_counts_per_division=[1],
        ... )
        >>> notes = abjadext.rmakers.NoteRhythmMaker()

        >>> command = abjadext.rmakers.RhythmCommand(
        ...     abjadext.rmakers.MakerAssignments(
        ...         abjadext.rmakers.MakerAssignment(
        ...             abjad.index([1], 2),
        ...             even_divisions,
        ...         ),
        ...         abjadext.rmakers.MakerAssignment(
        ...             abjad.index([0], 1),
        ...             notes,
        ...         ),
        ...     ),
        ... )

        >>> divisions = [(4, 8), (4, 8), (3, 8), (3, 8)]
        >>> selection = command(divisions)
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
                    \time 4/8
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'2
                    \times 16/20 {
                        c'8
                        c'8
                        c'8
                        c'8
                        c'8
                    }
                    c'4.
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'8
                        c'8
                        c'8
                        c'8
                    }
                }
            >>

    """

    ### CLASS ATTRIBUTES ###

    ###__slots__ = ("_divisions", "_rhythm_maker", "_runtime", "_state")
    __slots__ = ("_divisions", "_rhythm_maker", "_state")

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        # TODO: change to "*assignments"
        rhythm_maker: RhythmMakerTyping,
        *,
        divisions: abjad.Expression = None,
    ) -> None:
        if divisions is not None:
            assert isinstance(divisions, abjad.Expression)
        self._divisions = divisions
        self._check_rhythm_maker_input(rhythm_maker)
        self._rhythm_maker = rhythm_maker
        self._state = abjad.OrderedDict()

    ### SPECIAL METHODS ###

    def __call__(
        self,
        time_signatures: typing.Iterable[abjad.TimeSignature],
        previous_segment_stop_state: abjad.OrderedDict = None,
    ) -> abjad.Selection:
        """
        Calls ``RhythmCommand`` on ``time_signatures``.
        """
        rhythm_maker = self.rhythm_maker
        time_signatures = [abjad.TimeSignature(_) for _ in time_signatures]
        original_duration = sum(_.duration for _ in time_signatures)
        divisions = self._apply_division_expression(time_signatures)
        transformed_duration = sum(_.duration for _ in divisions)
        if transformed_duration != original_duration:
            message = "original duration ...\n"
            message += f"    {original_duration}\n"
            message += "... does not equal ...\n"
            message += f"    {transformed_duration}\n"
            message += "... transformed duration."
            raise Exception(message)
        division_count = len(divisions)
        assignments: typing.List[MakerAssignment] = []
        if isinstance(rhythm_maker, RhythmMaker):
            assignment = MakerAssignment(abjad.index([0], 1), rhythm_maker)
            assignments.append(assignment)
        elif isinstance(rhythm_maker, MakerAssignment):
            assignments.append(rhythm_maker)
        elif isinstance(rhythm_maker, MakerAssignments):
            for item in rhythm_maker.assignments:
                assert isinstance(item, MakerAssignment)
                assignments.append(item)
        else:
            message = "must be rhythm-maker or division assignment(s)"
            message += f" (not {rhythm_maker})."
            raise TypeError(message)
        assert all(isinstance(_, MakerAssignment) for _ in assignments)
        matches = []
        for i, division in enumerate(divisions):
            for assignment in assignments:
                if isinstance(
                    assignment.pattern, abjad.Pattern
                ) and assignment.pattern.matches_index(i, division_count):
                    match = MakerMatch(division, assignment)
                    matches.append(match)
                    break
                elif isinstance(
                    assignment.pattern, abjad.DurationInequality
                ) and assignment.pattern(division):
                    match = MakerMatch(division, assignment)
                    matches.append(match)
                    break
            else:
                raise Exception(f"no rhythm-maker match for division {i}.")
        assert len(divisions) == len(matches)
        groups = abjad.sequence(matches).group_by(
            lambda match: match.assignment.rhythm_maker
        )
        components: typing.List[abjad.Component] = []
        ###previous_segment_stop_state = self._previous_segment_stop_state()
        maker_to_previous_state = abjad.OrderedDict()
        for group in groups:
            rhythm_maker = group[0].assignment.rhythm_maker
            if isinstance(rhythm_maker, type(self)):
                rhythm_maker = rhythm_maker.rhythm_maker
            assert isinstance(rhythm_maker, RhythmMaker), repr(rhythm_maker)
            divisions_ = [match.division for match in group]
            # TODO: eventually allow previous segment stop state
            #       and local stop state to work together
            previous_state = previous_segment_stop_state
            if (
                previous_state is None
                and group[0].assignment.remember_state_across_gaps
            ):
                previous_state = maker_to_previous_state.get(
                    rhythm_maker, None
                )
            selection = rhythm_maker(divisions_, previous_state=previous_state)
            assert isinstance(selection, abjad.Selection), repr(selection)
            components.extend(selection)
            maker_to_previous_state[rhythm_maker] = rhythm_maker.state
        assert isinstance(rhythm_maker, RhythmMaker)
        self._state = rhythm_maker.state
        selection = abjad.select(components)
        assert isinstance(selection, abjad.Selection), repr(selection)
        return selection

    ### PRIVATE METHODS ###

    def _apply_division_expression(self, divisions) -> abjad.Sequence:
        if self.divisions is not None:
            result = self.divisions(divisions)
            if not isinstance(result, abjad.Sequence):
                message = "division expression must return sequence:\n"
                message += f"  Input divisions:\n"
                message += f"    {divisions}\n"
                message += f"  Division expression:\n"
                message += f"    {self.divisions}\n"
                message += f"  Result:\n"
                message += f"    {result}"
                raise Exception(message)
            divisions = result
        divisions = abjad.sequence(divisions)
        divisions = divisions.flatten(depth=-1)
        return divisions

    def _check_rhythm_maker_input(self, rhythm_maker):
        prototype = (MakerAssignment, MakerAssignments, RhythmMaker)
        if isinstance(rhythm_maker, prototype):
            return
        message = '\n  Input parameter "rhythm_maker" accepts:'
        message += "\n    maker assignment(s)"
        message += "\n    rhythm-maker"
        message += '\n  Input parameter "rhythm_maker" received:'
        message += f"\n    {format(rhythm_maker)}"
        raise Exception(message)

    ### PUBLIC PROPERTIES ###

    @property
    def divisions(self) -> typing.Optional[abjad.Expression]:
        r"""
        Gets division preprocessor expression.
        """
        return self._divisions

    @property
    def rhythm_maker(self) -> RhythmMakerTyping:
        r"""
        Gets maker assignments.

        ..  container:: example exception

            Raises exception on invalid input:

            >>> command = abjadext.rmakers.RhythmCommand(
            ...     rhythm_maker='text',
            ...     )
            Traceback (most recent call last):
                ...
            Exception:
              Input parameter "rhythm_maker" accepts:
                maker assignment(s)
                rhythm-maker
              Input parameter "rhythm_maker" received:
                text

        """
        return self._rhythm_maker

    @property
    def state(self) -> abjad.OrderedDict:
        """
        Gets postcall state of rhythm command.
        """
        return self._state