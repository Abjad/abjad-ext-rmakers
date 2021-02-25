import typing

import abjad

from . import commands as _commands
from .makers import RhythmMaker

RhythmMakerTyping = typing.Union["Assignment", RhythmMaker, "Stack", "Bind"]


# TODO: integrate tests
#    @property
#    def preprocessor(self) -> typing.Optional[abjad.Expression]:
#        r"""
#        Gets division preprocessor.
#
#        ..  container:: example
#
#            >>> weights = [abjad.NonreducedFraction(3, 8)]
#            >>> divisions = abjad.sequence().join()
#            >>> divisions = divisions.split(
#            ...     weights, cyclic=True, overhang=True,
#            ... )
#            >>> divisions = divisions.flatten(depth=-1)
#            >>> stack = rmakers.stack(rmakers.note(), preprocessor=divisions)
#            >>> divisions = [(4, 4), (4, 4)]
#            >>> selection = stack(divisions)
#            >>> lilypond_file = abjad.LilyPondFile.rhythm(
#            ...     selection,
#            ...     divisions,
#            ... )
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
#                >>> print(string)
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 4/4
#                        s1 * 1
#                        \time 4/4
#                        s1 * 1
#                    }
#                    \new RhythmicStaff
#                    {
#                        c'4.
#                        c'4.
#                        c'4.
#                        c'4.
#                        c'4.
#                        c'8
#                    }
#                >>
#
#        """
#        return super().preprocessor


### CLASSES ###


class Stack:
    """
    Stack.
    """

    ### CLASS ATTRIBUTES ###

    __slots__ = ("_commands", "_maker", "_preprocessor", "_tag")

    # to make sure abjad.new() copies commands
    _positional_arguments_name = "commands"

    ### INITIALIZER ###

    def __init__(
        self,
        maker,
        *commands,
        preprocessor: abjad.Expression = None,
        tag: abjad.Tag = None,
    ) -> None:
        prototype = (RhythmMaker, Stack, Bind)
        assert isinstance(maker, prototype), repr(maker)
        if tag is not None:
            maker = abjad.new(maker, tag=tag)
        self._maker = maker
        commands = commands or ()
        commands_ = tuple(commands)
        self._commands = commands_
        if preprocessor is not None:
            assert isinstance(preprocessor, abjad.Expression)
        self._preprocessor = preprocessor
        if tag is not None:
            assert isinstance(tag, abjad.Tag), repr(tag)
        self._tag = tag

    ### SPECIAL METHODS ###

    def __call__(
        self,
        time_signatures: typing.Sequence[abjad.IntegerPair],
        previous_state: abjad.OrderedDict = None,
    ) -> abjad.Selection:
        """
        Calls stack.
        """
        time_signatures_ = [abjad.TimeSignature(_) for _ in time_signatures]
        divisions_ = [abjad.NonreducedFraction(_) for _ in time_signatures]
        staff = RhythmMaker._make_staff(time_signatures_)
        music_voice = staff["Rhythm_Maker_Music_Voice"]
        divisions = self._apply_division_expression(divisions_)
        selection = self.maker(divisions, previous_state=previous_state)
        music_voice.extend(selection)
        for command in self.commands:
            if isinstance(command, _commands.CacheStateCommand):
                assert isinstance(self.maker, RhythmMaker), repr(self.maker)
                self.maker._cache_state(music_voice, len(divisions))
                self.maker._already_cached_state = True
            try:
                command(music_voice, tag=self.tag)
            except Exception:
                message = "exception while calling:\n"
                message += f"   {format(command)}"
                raise Exception(message)
        result = music_voice[:]
        assert isinstance(result, abjad.Selection)
        music_voice[:] = []
        return result

    def __eq__(self, argument) -> bool:
        """
        Delegates to format manager.
        """
        if abjad.StorageFormatManager.compare_objects(self, argument):
            return self.commands == argument.commands
        return False

    def __hash__(self) -> int:
        """
        Delegates to format manager.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __repr__(self) -> str:
        """
        Delegates to format manager.

        ..  container:: example

            >>> rmakers.stack(
            ...     rmakers.tuplet([(1, 2)]),
            ...     rmakers.force_fraction(),
            ... )
            Stack(TupletRhythmMaker(tuplet_ratios=[Ratio((1, 2))]), ForceFractionCommand())

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _apply_division_expression(self, divisions) -> abjad.Sequence:
        prototype = abjad.NonreducedFraction
        if not all(isinstance(_, prototype) for _ in divisions):
            message = "must be nonreduced fractions:\n"
            message += f"   {repr(divisions)}"
            raise Exception(message)
        original_duration = abjad.Duration(sum(divisions))
        if self.preprocessor is not None:
            result = self.preprocessor(divisions)
            if not isinstance(result, abjad.Sequence):
                message = "division preprocessor must return sequence:\n"
                message += "  Input divisions:\n"
                message += f"    {divisions}\n"
                message += "  Division preprocessor:\n"
                message += f"    {self.preprocessor}\n"
                message += "  Result:\n"
                message += f"    {result}"
                raise Exception(message)
            divisions = result
        divisions = abjad.sequence(divisions)
        divisions = divisions.flatten(depth=-1)
        transformed_duration = abjad.Duration(sum(divisions))
        if transformed_duration != original_duration:
            message = "original duration ...\n"
            message += f"    {original_duration}\n"
            message += "... does not equal ...\n"
            message += f"    {transformed_duration}\n"
            message += "... transformed duration."
            raise Exception(message)
        return divisions

    def _get_format_specification(self):
        values = []
        values.append(self.maker)
        values.extend(self.commands)
        return abjad.FormatSpecification(self, storage_format_args_values=values)

    ### PUBLIC PROPERTIES ###

    @property
    def commands(self):
        """
        Gets commands.

        ..  container:: example

            REGRESSION. ``abjad.new()`` copies commands:

            >>> command_1 = rmakers.stack(
            ...     rmakers.tuplet([(1, 2)]),
            ...     rmakers.force_fraction(),
            ... )
            >>> command_2 = abjad.new(command_1)

            >>> string = abjad.storage(command_1)
            >>> print(string)
            rmakers.Stack(
                rmakers.TupletRhythmMaker(
                    tuplet_ratios=[
                        abjad.Ratio((1, 2)),
                        ],
                    ),
                ForceFractionCommand()
                )

            >>> string = abjad.storage(command_2)
            >>> print(string)
            rmakers.Stack(
                rmakers.TupletRhythmMaker(
                    tuplet_ratios=[
                        abjad.Ratio((1, 2)),
                        ],
                    ),
                ForceFractionCommand()
                )

            >>> command_1 == command_2
            True

        """
        return list(self._commands)

    @property
    def maker(self) -> typing.Union[RhythmMaker, "Stack", "Bind"]:
        """
        Gets maker.
        """
        return self._maker

    @property
    def preprocessor(self) -> typing.Optional[abjad.Expression]:
        """
        Gets preprocessor.
        """
        return self._preprocessor

    @property
    def state(self) -> abjad.OrderedDict:
        """
        Gets state.
        """
        return self.maker.state

    @property
    def tag(self) -> typing.Optional[abjad.Tag]:
        """
        Gets tag.
        """
        return self._tag


class Match:
    """
    Match.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_assignment", "_payload")

    ### INITIALIZER ###

    def __init__(self, assignment, payload) -> None:
        self._assignment = assignment
        self._payload = payload

    ### SPECIAL METHODS ###

    def __eq__(self, argument) -> bool:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

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

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC PROPERTIES ###

    @property
    def assignment(self):
        """
        Gets assignment.
        """
        return self._assignment

    @property
    def payload(self) -> typing.Any:
        """
        Gets payload.
        """
        return self._payload


class Assignment:
    """
    Assignment.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_predicate", "_remember_state_across_gaps", "_rhythm_maker")

    ### INITIALIZER ###

    def __init__(
        self,
        rhythm_maker: typing.Union[RhythmMaker, Stack],
        predicate: typing.Union[typing.Callable, abjad.Pattern] = None,
        *,
        remember_state_across_gaps: bool = None,
    ) -> None:
        if predicate is not None and not isinstance(predicate, abjad.Pattern):
            assert callable(predicate)
        self._predicate = predicate
        prototype = (RhythmMaker, Stack)
        assert isinstance(rhythm_maker, prototype), repr(rhythm_maker)
        self._rhythm_maker = rhythm_maker
        if remember_state_across_gaps is None:
            remember_state_across_gaps = bool(remember_state_across_gaps)
        self._remember_state_across_gaps = remember_state_across_gaps

    ### SPECIAL METHODS ###

    def __eq__(self, argument) -> bool:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

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

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC PROPERTIES ###

    @property
    def predicate(self) -> typing.Union[typing.Callable, abjad.Pattern, None]:
        """
        Gets predicate.
        """
        return self._predicate

    @property
    def remember_state_across_gaps(self) -> typing.Optional[bool]:
        """
        Is true when assignment remembers rhythm-maker state across gaps.
        """
        return self._remember_state_across_gaps

    @property
    def rhythm_maker(self) -> typing.Union[RhythmMaker, Stack]:
        """
        Gets rhythm-maker.
        """
        return self._rhythm_maker


class Bind:
    """
    Bind.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_assignments", "_state", "_tag")

    # to make sure abjad.new() copies sassignments
    _positional_arguments_name = "assignments"

    ### INITIALIZER ###

    def __init__(self, *assignments: Assignment, tag: abjad.Tag = None) -> None:
        assignments = assignments or ()
        for assignment in assignments:
            if not isinstance(assignment, Assignment):
                message = "must be assignment:\n"
                message += f"   {repr(assignment)}"
                raise Exception(message)
        assignments_ = tuple(assignments)
        self._assignments = assignments_
        self._state = abjad.OrderedDict()
        if tag is not None:
            assert isinstance(tag, abjad.Tag), repr(tag)
        self._tag = tag

    ### SPECIAL METHODS ###

    def __call__(
        self, divisions, previous_state: abjad.OrderedDict = None
    ) -> abjad.Selection:
        """
        Calls bind.
        """
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
        groups = abjad.sequence(matches).group_by(
            lambda match: match.assignment.rhythm_maker
        )
        components: typing.List[abjad.Component] = []
        maker_to_previous_state = abjad.OrderedDict()
        pp = (RhythmMaker, Stack)
        for group in groups:
            rhythm_maker = group[0].assignment.rhythm_maker
            if self.tag is not None:
                rhythm_maker = abjad.new(rhythm_maker, tag=self.tag)
            assert isinstance(rhythm_maker, pp), repr(rhythm_maker)
            divisions_ = [match.payload for match in group]
            previous_state_ = previous_state
            if (
                previous_state_ is None
                and group[0].assignment.remember_state_across_gaps
            ):
                previous_state_ = maker_to_previous_state.get(rhythm_maker, None)
            if isinstance(rhythm_maker, (RhythmMaker, Stack)):
                selection = rhythm_maker(divisions_, previous_state=previous_state_)
            else:
                selection = rhythm_maker(
                    divisions_, previous_segment_stop_state=previous_state_
                )
            assert isinstance(selection, abjad.Selection), repr(selection)
            components.extend(selection)
            maker_to_previous_state[rhythm_maker] = rhythm_maker.state
        assert isinstance(rhythm_maker, (RhythmMaker, Stack)), repr(rhythm_maker)
        self._state = rhythm_maker.state
        selection = abjad.select(components)
        return selection

    def __eq__(self, argument) -> bool:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

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

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _get_format_specification(self):
        return abjad.FormatSpecification(
            self, storage_format_args_values=self.assignments
        )

    ### PUBLIC PROPERTIES ###

    @property
    def assignments(self) -> typing.List[Assignment]:
        """
        Gets assignments.
        """
        return list(self._assignments)

    @property
    def state(self) -> abjad.OrderedDict:
        """
        Gets state.
        """
        return self._state

    @property
    def tag(self) -> typing.Optional[abjad.Tag]:
        """
        Gets tag.
        """
        return self._tag


### FACTORY FUNCTIONS ###


def assign(
    rhythm_maker,
    predicate: typing.Union[typing.Callable, abjad.Pattern] = None,
    *,
    remember_state_across_gaps: bool = None,
) -> Assignment:
    """
    Makes assignment.
    """
    return Assignment(
        rhythm_maker,
        predicate,
        remember_state_across_gaps=remember_state_across_gaps,
    )


def bind(*assignments: Assignment, tag: abjad.Tag = None) -> Bind:
    """
    Makes bind.
    """
    return Bind(*assignments, tag=tag)


def stack(
    maker,
    *commands,
    preprocessor: abjad.Expression = None,
    tag: abjad.Tag = None,
) -> Stack:
    """
    Makes stack.
    """
    return Stack(maker, *commands, preprocessor=preprocessor, tag=tag)
