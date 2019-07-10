import abjad
import typing
from . import typings
from .RhythmMaker import RhythmMaker


RhythmMakerTyping = typing.Union[
    RhythmMaker, "DivisionAssignment", "DivisionAssignments"
]


class DivisionAssignment(object):
    """
    Division assignment.
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


class DivisionAssignments(object):
    """
    Division assignments.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_assignments",)

    _positional_arguments_name = "assignments"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(self, *assignments: DivisionAssignment) -> None:
        assignments = assignments or ()
        for assignment in assignments:
            assert isinstance(assignment, DivisionAssignment), repr(assignment)
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
    def assignments(self) -> typing.List[DivisionAssignment]:
        """
        Gets specifiers.
        """
        return list(self._assignments)


class DivisionMatch(object):
    """
    Division match.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_assignment", "_division")

    ### INITIALIZER ###

    def __init__(
        self,
        division: abjad.NonreducedFraction,
        assignment: DivisionAssignment,
    ) -> None:
        assert isinstance(division, abjad.NonreducedFraction), repr(division)
        self._division = division
        assert isinstance(assignment, DivisionAssignment), repr(assignment)
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
    def assignment(self) -> DivisionAssignment:
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
    """

    ### CLASS ATTRIBUTES ###

    __slots__ = (
        "_divisions",
        "_do_not_check_total_duration",
        "_rhythm_maker",
        "_state",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        # TODO: change name to "maker_assignments"
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

    def _make_selection(
        self,
        runtime: abjad.OrderedDict = None,
        time_signatures: typing.Iterable[abjad.TimeSignature] = None,
    ) -> abjad.Selection:
        """
        Calls ``RhythmCommand`` on ``start_offset`` and ``time_signatures``.
        """
        # runtime apparently needed for previous_segment_stop_state
        self._runtime = runtime or abjad.OrderedDict()
        selection = self._make_rhythm(time_signatures)
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
        prototype = (DivisionAssignment, DivisionAssignments, RhythmMaker)
        if isinstance(rhythm_maker, prototype):
            return
        message = '\n  Input parameter "rhythm_maker" accepts:'
        message += "\n    division assignment(s)"
        message += "\n    rhythm-maker"
        message += '\n  Input parameter "rhythm_maker" received:'
        message += f"\n    {format(rhythm_maker)}"
        raise Exception(message)

    def _make_rhythm(self, time_signatures) -> abjad.Selection:
        rhythm_maker = self.rhythm_maker
        if isinstance(rhythm_maker, abjad.Selection):
            selection = rhythm_maker
            total_duration = sum([_.duration for _ in time_signatures])
            selection_duration = abjad.inspect(selection).duration()
            if (
                not self.do_not_check_total_duration
                and selection_duration != total_duration
            ):
                message = f"selection duration ({selection_duration}) does not"
                message += f" equal total duration ({total_duration})."
                raise Exception(message)
            return selection
        assert all(isinstance(_, abjad.TimeSignature) for _ in time_signatures)
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
        assignments: typing.List[DivisionAssignment] = []
        if isinstance(rhythm_maker, RhythmMaker):
            assignment = DivisionAssignment(abjad.index([0], 1), rhythm_maker)
            assignments.append(assignment)
        elif isinstance(rhythm_maker, DivisionAssignment):
            assignments.append(rhythm_maker)
        elif isinstance(rhythm_maker, DivisionAssignments):
            for item in rhythm_maker.assignments:
                assert isinstance(item, DivisionAssignment)
                assignments.append(item)
        else:
            message = "must be rhythm-maker or division assignment(s)"
            message += f" (not {rhythm_maker})."
            raise TypeError(message)
        assert all(isinstance(_, DivisionAssignment) for _ in assignments)
        matches = []
        for i, division in enumerate(divisions):
            for assignment in assignments:
                if isinstance(
                    assignment.pattern, abjad.Pattern
                ) and assignment.pattern.matches_index(i, division_count):
                    match = DivisionMatch(division, assignment)
                    matches.append(match)
                    break
                elif isinstance(
                    assignment.pattern, abjad.DurationInequality
                ) and assignment.pattern(division):
                    match = DivisionMatch(division, assignment)
                    matches.append(match)
                    break
            else:
                raise Exception(f"no rhythm-maker match for division {i}.")
        assert len(divisions) == len(matches)
        groups = abjad.sequence(matches).group_by(
            lambda match: match.assignment.rhythm_maker
        )
        components: typing.List[abjad.Component] = []
        previous_segment_stop_state = self._previous_segment_stop_state()
        maker_to_previous_state = abjad.OrderedDict()
        for group in groups:
            rhythm_maker = group[0].assignment.rhythm_maker
            if isinstance(rhythm_maker, type(self)):
                rhythm_maker = rhythm_maker.rhythm_maker
            assert isinstance(rhythm_maker, RhythmMaker)
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
        return selection

    def _previous_segment_stop_state(self):
        previous_segment_stop_state = None
        dictionary = self.runtime.get("previous_segment_voice_metadata")
        if dictionary:
            previous_segment_stop_state = dictionary.get(const.RHYTHM)
            if (
                previous_segment_stop_state is not None
                and previous_segment_stop_state.get("name") != self.persist
            ):
                previous_segment_stop_state = None
        return previous_segment_stop_state

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
                division assignment(s)
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
