import abjad
import typing
from . import commands as _commands
from .RhythmMaker import RhythmMaker

RhythmMakerTyping = typing.Union[
    RhythmMaker, "RhythmAssignment", "RhythmAssignments"
]


### CLASSES ###


class Stack(object):
    """
    Stack.
    """

    ### CLASS ATTRIBUTES ###

    __slots__ = ("_commands", "_maker", "_preprocessor", "_tag")

    # to make sure abjad.new() copies commands
    _positional_arguments_name = "commands"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        maker,
        *commands,
        preprocessor: abjad.Expression = None,
        tag: str = None,
    ) -> None:
        prototype = (RhythmCommand, RhythmMaker, Stack, Tesselation)
        assert isinstance(maker, prototype), repr(maker)
        self._maker = maker
        commands = commands or ()
        commands_ = tuple(commands)
        self._commands = commands_
        if preprocessor is not None:
            assert isinstance(preprocessor, abjad.Expression)
        self._preprocessor = preprocessor
        if tag is not None:
            assert isinstance(tag, str), repr(tag)
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
        maker = self.maker
        if self.tag is not None:
            maker = abjad.new(maker, tag=self.tag)
        time_signatures_ = [abjad.TimeSignature(_) for _ in time_signatures]
        divisions = self._apply_division_expression(time_signatures_)
        if isinstance(maker, RhythmCommand):
            selection = maker(
                divisions, previous_segment_stop_state=previous_state
            )
        else:
            selection = maker(divisions, previous_state=previous_state)
        staff = RhythmMaker._make_staff(time_signatures_)
        staff["MusicVoice"].extend(selection)
        for command in self.commands:
            try:
                command(staff["MusicVoice"], tag=self.tag)
            except:
                message = "exception while calling:\n"
                message += f"   {format(command)}"
                raise Exception(message)
        result = staff["MusicVoice"][:]
        assert isinstance(result, abjad.Selection)
        staff["MusicVoice"][:] = []
        return result

    def __eq__(self, argument) -> bool:
        """
        Delegates to format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __format__(self, format_specification="") -> str:
        """
        Delegates to format manager.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

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
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _apply_division_expression(self, divisions) -> abjad.Sequence:
        if self.preprocessor is not None:
            result = self.preprocessor(divisions)
            if not isinstance(result, abjad.Sequence):
                message = "division preprocessor must return sequence:\n"
                message += f"  Input divisions:\n"
                message += f"    {divisions}\n"
                message += f"  Division preprocessor:\n"
                message += f"    {self.preprocessor}\n"
                message += f"  Result:\n"
                message += f"    {result}"
                raise Exception(message)
            divisions = result
        divisions = abjad.sequence(divisions)
        divisions = divisions.flatten(depth=-1)
        return divisions

    def _get_format_specification(self):
        manager = abjad.StorageFormatManager(self)
        values = []
        values.append(self.maker)
        values.extend(self.commands)
        return abjad.FormatSpecification(
            self, storage_format_args_values=values
        )

    ### PUBLIC PROPERTIES ###

    @property
    def commands(self):
        """
        Gets commands.
        """
        return list(self._commands)

    @property
    def maker(
        self
    ) -> typing.Union["RhythmCommand", RhythmMaker, "Stack", "Tesselation"]:
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
    def tag(self) -> typing.Optional[str]:
        """
        Gets tag.
        """
        return self._tag


class MakerMatch(object):
    """
    Maker match.
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

    def __format__(self, format_specification="") -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

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


class RhythmCommand(object):
    r"""
    Rhythm command.

    ..  container:: example

        >>> command = rmakers.command(
        ...     rmakers.RhythmAssignments(
        ...         rmakers.assign(
        ...             rmakers.even_division(
        ...                 [8], denominator=16, extra_counts=[1]
        ...             ),
        ...             abjad.index([1], 2),
        ...         ),
        ...         rmakers.assign(rmakers.note()),
        ...     ),
        ... )

        >>> divisions = [(4, 8), (4, 8), (3, 8), (3, 8)]
        >>> selection = command(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection,
        ...     divisions,
        ... )
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

    __slots__ = (
        "_commands",
        "_preprocessor",
        "_rhythm_maker",
        "_state",
        "_tag",
    )

    # to make sure abjad.new() copies commands
    _positional_arguments_name = "commands"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        rhythm_maker: RhythmMakerTyping,
        *commands: _commands.Command,
        preprocessor: abjad.Expression = None,
        tag: str = None,
    ) -> None:
        if preprocessor is not None:
            assert isinstance(preprocessor, abjad.Expression)
        self._preprocessor = preprocessor
        self._check_rhythm_maker_input(rhythm_maker)
        self._rhythm_maker = rhythm_maker
        commands = commands or ()
        for command in commands:
            assert isinstance(command, _commands.Command), repr(command)
        commands_ = tuple(commands)
        self._commands = commands_
        self._state = abjad.OrderedDict()
        if tag is not None:
            assert isinstance(tag, str), repr(tag)
        self._tag = tag

    ### SPECIAL METHODS ###

    def __call__(
        self,
        time_signatures: typing.Sequence[abjad.IntegerPair],
        previous_segment_stop_state: abjad.OrderedDict = None,
    ) -> abjad.Selection:
        """
        Calls ``RhythmCommand`` on ``time_signatures``.
        """
        rhythm_maker = self.rhythm_maker
        time_signatures_ = [abjad.TimeSignature(_) for _ in time_signatures]
        original_duration = sum(_.duration for _ in time_signatures_)
        divisions = self._apply_division_expression(time_signatures_)
        transformed_duration = sum(_.duration for _ in divisions)
        if transformed_duration != original_duration:
            message = "original duration ...\n"
            message += f"    {original_duration}\n"
            message += "... does not equal ...\n"
            message += f"    {transformed_duration}\n"
            message += "... transformed duration."
            raise Exception(message)
        division_count = len(divisions)
        assignments: typing.List[RhythmAssignment] = []
        if isinstance(rhythm_maker, (RhythmMaker, RhythmCommand)):
            assignment = RhythmAssignment(rhythm_maker, abjad.index([0], 1))
            assignments.append(assignment)
        elif isinstance(rhythm_maker, RhythmAssignment):
            assignments.append(rhythm_maker)
        elif isinstance(rhythm_maker, RhythmAssignments):
            for item in rhythm_maker.assignments:
                assert isinstance(item, RhythmAssignment)
                assignments.append(item)
        else:
            message = "must be rhythm-maker or division assignment(s)"
            message += f" (not {rhythm_maker})."
            raise TypeError(message)
        assert all(isinstance(_, RhythmAssignment) for _ in assignments)
        matches = []
        for i, division in enumerate(divisions):
            for assignment in assignments:
                if assignment.predicate is None:
                    match = MakerMatch(assignment, division)
                    matches.append(match)
                    break
                elif isinstance(assignment.predicate, abjad.Pattern):
                    if assignment.predicate.matches_index(i, division_count):
                        match = MakerMatch(assignment, division)
                        matches.append(match)
                        break
                elif assignment.predicate(division):
                    match = MakerMatch(assignment, division)
                    matches.append(match)
                    break
            else:
                raise Exception(f"no rhythm-maker match for division {i}.")
        assert len(divisions) == len(matches)
        groups = abjad.sequence(matches).group_by(
            lambda match: match.assignment.rhythm_maker
        )
        components: typing.List[abjad.Component] = []
        maker_to_previous_state = abjad.OrderedDict()
        for group in groups:
            rhythm_maker = group[0].assignment.rhythm_maker
            rhythm_command = None
            if isinstance(rhythm_maker, type(self)):
                rhythm_command = rhythm_maker
                rhythm_maker = rhythm_maker.rhythm_maker
            if self.tag is not None:
                rhythm_maker = abjad.new(rhythm_maker, tag=self.tag)
            pcc = (RhythmMaker, Stack)
            assert isinstance(rhythm_maker, pcc), repr(rhythm_maker)
            divisions_ = [match.payload for match in group]
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
            if rhythm_command is not None:
                if self.tag is not None:
                    rhythm_command = abjad.new(rhythm_command, tag=self.tag)
                voice = abjad.Voice(selection)
                divisions_consumed = len(divisions_)
                rhythm_command._call_commands(
                    voice, divisions_consumed, rhythm_maker
                )
                selection = voice[:]
                voice[:] = []
            assert isinstance(selection, abjad.Selection), repr(selection)
            components.extend(selection)
            if isinstance(rhythm_maker, RhythmMaker):
                maker_to_previous_state[rhythm_maker] = rhythm_maker.state
            else:
                assert isinstance(rhythm_maker, Stack)
                maker_to_previous_state[
                    rhythm_maker
                ] = rhythm_maker.maker.state
        if isinstance(rhythm_maker, RhythmMaker):
            self._state = rhythm_maker.state
        else:
            self._state = rhythm_maker.maker.state
        selection = abjad.select(components)
        assert isinstance(selection, abjad.Selection), repr(selection)
        staff = RhythmMaker._make_staff(time_signatures_)
        voice = staff["MusicVoice"]
        voice.extend(selection)
        divisions_consumed = division_count
        self._call_commands(voice, divisions_consumed, rhythm_maker)
        self._validate_tuplets(voice)
        selection = voice[:]
        voice[:] = []
        return selection

    def __eq__(self, argument) -> bool:
        """
        Is true when all initialization values of object equal
        the initialization values of ``argument``.

        ..  container:: example

            >>> command_1 = rmakers.command(
            ...     rmakers.tuplet([(1, 2)]),
            ...     rmakers.force_fraction(),
            ... )
            >>> command_2 = rmakers.command(
            ...     rmakers.tuplet([(1, 2)]),
            ...     rmakers.force_fraction(),
            ... )
            >>> command_3 = rmakers.command(
            ...     rmakers.tuplet([(1, 2)]),
            ... )

            >>> command_1 == command_1
            True
            >>> command_1 == command_2
            True
            >>> command_1 == command_3
            False
            >>> command_2 == command_1
            True
            >>> command_2 == command_2
            True
            >>> command_2 == command_3
            False
            >>> command_3 == command_1
            False
            >>> command_3 == command_2
            False
            >>> command_3 == command_3
            True

        """
        if abjad.StorageFormatManager.compare_objects(self, argument):
            return self.commands == argument.commands
        return False

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

    def __format__(self, format_specification="") -> str:
        """
        Delegates to storage format manager.

        ..  container:: example

            REGRESSION. Commands appear in format:

            >>> command = rmakers.command(
            ...     rmakers.tuplet([(1, 2)]),
            ...     rmakers.force_fraction(),
            ... )
            >>> abjad.f(command)
            abjadext.rmakers.RhythmCommand(
                abjadext.rmakers.TupletRhythmMaker(
                    tuplet_ratios=[
                        abjad.Ratio((1, 2)),
                        ],
                    ),
                ForceFractionCommand()
                )

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.

        ..  container:: example

            >>> rmakers.command(
            ...     rmakers.tuplet([(1, 2)]),
            ...     rmakers.force_fraction(),
            ... )
            RhythmCommand(TupletRhythmMaker(tuplet_ratios=[Ratio((1, 2))]), ForceFractionCommand())

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _apply_division_expression(self, divisions) -> abjad.Sequence:
        if self.preprocessor is not None:
            result = self.preprocessor(divisions)
            if not isinstance(result, abjad.Sequence):
                message = "division preprocessor must return sequence:\n"
                message += f"  Input divisions:\n"
                message += f"    {divisions}\n"
                message += f"  Division preprocessor:\n"
                message += f"    {self.preprocessor}\n"
                message += f"  Result:\n"
                message += f"    {result}"
                raise Exception(message)
            divisions = result
        divisions = abjad.sequence(divisions)
        divisions = divisions.flatten(depth=-1)
        return divisions

    def _call_commands(self, voice, divisions_consumed, rhythm_maker):
        # TODO: will need to restore:
        #        previous_logical_ties_produced = self._previous_logical_ties_produced()
        #        if self._previous_incomplete_last_note():
        #            previous_logical_ties_produced -= 1
        for command in self.commands or []:
            if isinstance(command, _commands.CacheStateCommand):
                rhythm_maker._cache_state(voice, divisions_consumed)
                rhythm_maker._already_cached_state = True
                continue
            elif isinstance(command, _commands.ForceRestCommand):
                command(
                    voice,
                    # TODO: restore
                    ###previous_logical_ties_produced=previous_logical_ties_produced,
                    tag=self.tag,
                )
            else:
                command(voice, tag=self.tag)

    def _check_rhythm_maker_input(self, rhythm_maker):
        prototype = (
            RhythmAssignment,
            RhythmAssignments,
            RhythmCommand,
            RhythmMaker,
        )
        if isinstance(rhythm_maker, prototype):
            return
        message = '\n  Input parameter "rhythm_maker" accepts:'
        message += "\n    maker assignment(s)"
        message += "\n    rhythm-maker"
        message += '\n  Input parameter "rhythm_maker" received:'
        message += f"\n    {format(rhythm_maker)}"
        raise Exception(message)

    def _get_format_specification(self):
        values = [self.rhythm_maker] + self.commands
        return abjad.FormatSpecification(
            self, storage_format_args_values=values
        )

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

    def _validate_tuplets(self, selections):
        for tuplet in abjad.iterate(selections).components(abjad.Tuplet):
            assert tuplet.multiplier.normalized(), repr(tuplet)
            assert len(tuplet), repr(tuplet)

    ### PUBLIC PROPERTIES ###

    @property
    def commands(self) -> typing.List[_commands.Command]:
        """
        Gets commands.

        ..  container:: example

            REGRESSION. ``abjad.new()`` copies commands:

            >>> command_1 = rmakers.command(
            ...     rmakers.tuplet([(1, 2)]),
            ...     rmakers.force_fraction(),
            ... )
            >>> command_2 = abjad.new(command_1)

            >>> abjad.f(command_1)
            abjadext.rmakers.RhythmCommand(
                abjadext.rmakers.TupletRhythmMaker(
                    tuplet_ratios=[
                        abjad.Ratio((1, 2)),
                        ],
                    ),
                ForceFractionCommand()
                )

            >>> abjad.f(command_2)
            abjadext.rmakers.RhythmCommand(
                abjadext.rmakers.TupletRhythmMaker(
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
    def preprocessor(self) -> typing.Optional[abjad.Expression]:
        r"""
        Gets division preprocessor.
        """
        return self._preprocessor

    @property
    def rhythm_maker(self) -> RhythmMakerTyping:
        r"""
        Gets maker assignments.

        ..  container:: example exception

            Raises exception on invalid input:

            >>> command = rmakers.command(
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

    @property
    def tag(self) -> typing.Optional[str]:
        """
        Gets tag.
        """
        return self._tag


class RhythmAssignment(object):
    """
    Rhythm assignment.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_predicate", "_remember_state_across_gaps", "_rhythm_maker")

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        rhythm_maker: typing.Union[RhythmMaker, RhythmCommand],
        predicate: typing.Union[typing.Callable, abjad.Pattern] = None,
        *,
        remember_state_across_gaps: bool = None,
    ) -> None:
        if predicate is not None and not isinstance(predicate, abjad.Pattern):
            assert callable(predicate)
        self._predicate = predicate
        prototype = (RhythmMaker, RhythmCommand, Stack)
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

    def __format__(self, format_specification="") -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

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
    def rhythm_maker(self) -> typing.Union[RhythmMaker, RhythmCommand]:
        """
        Gets rhythm-maker.
        """
        return self._rhythm_maker


class RhythmAssignments(object):
    """
    Rhythm assignments.
    """

    ### CLASS VARIABLES ###

    __slots__ = "_assignments"

    # to make sure abjad.new() copies sassignments
    _positional_arguments_name = "assignments"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(self, *assignments: RhythmAssignment) -> None:
        assignments = assignments or ()
        for assignment in assignments:
            if not isinstance(assignment, RhythmAssignment):
                message = "must be maker assignment:\n"
                message += f"   {repr(assignment)}"
                raise Exception(message)
        assignments_ = tuple(assignments)
        self._assignments = assignments_

    ### SPECIAL METHODS ###

    def __eq__(self, argument) -> bool:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __format__(self, format_specification="") -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

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
    def assignments(self) -> typing.List[RhythmAssignment]:
        """
        Gets assignments.
        """
        return list(self._assignments)


class Tesselation(object):
    """
    Tesselation.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_assignments", "_state", "_tag")

    # to make sure abjad.new() copies sassignments
    _positional_arguments_name = "assignments"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self, *assignments: RhythmAssignment, tag: str = None
    ) -> None:
        assignments = assignments or ()
        for assignment in assignments:
            if not isinstance(assignment, RhythmAssignment):
                message = "must be assignment:\n"
                message += f"   {repr(assignment)}"
                raise Exception(message)
        assignments_ = tuple(assignments)
        self._assignments = assignments_
        self._state = abjad.OrderedDict()
        if tag is not None:
            assert isinstance(tag, str), repr(tag)
        self._tag = tag

    ### SPECIAL METHODS ###

    def __call__(
        self, divisions, previous_state: abjad.OrderedDict = None
    ) -> abjad.Selection:
        """
        Calls tesselation.
        """
        division_count = len(divisions)
        matches = []
        for i, division in enumerate(divisions):
            for assignment in self.assignments:
                if assignment.predicate is None:
                    match = MakerMatch(assignment, division)
                    matches.append(match)
                    break
                elif isinstance(assignment.predicate, abjad.Pattern):
                    if assignment.predicate.matches_index(i, division_count):
                        match = MakerMatch(assignment, division)
                        matches.append(match)
                        break
                elif assignment.predicate(division):
                    match = MakerMatch(assignment, division)
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
        pp = (RhythmMaker, RhythmCommand)
        for group in groups:
            rhythm_maker = group[0].assignment.rhythm_maker
            if self.tag is not None:
                rhythm_maker = abjad.new(rhythm_maker, tag=self.tag)
            assert isinstance(rhythm_maker, pp), repr(rhythm_maker)
            divisions_ = [match.payload for match in group]
            ###previous_state = previous_segment_stop_state
            if (
                previous_state is None
                and group[0].assignment.remember_state_across_gaps
            ):
                previous_state = maker_to_previous_state.get(
                    rhythm_maker, None
                )
            if isinstance(rhythm_maker, RhythmMaker):
                selection = rhythm_maker(
                    divisions_, previous_state=previous_state
                )
            else:
                selection = rhythm_maker(
                    divisions_, previous_segment_stop_state=previous_state
                )
            assert isinstance(selection, abjad.Selection), repr(selection)
            components.extend(selection)
            maker_to_previous_state[rhythm_maker] = rhythm_maker.state
        if isinstance(rhythm_maker, RhythmCommand):
            rhythm_maker = rhythm_maker.rhythm_maker
        assert isinstance(rhythm_maker, RhythmMaker), repr(rhythm_maker)
        self._state = rhythm_maker.state
        selection = abjad.select(components)
        return selection

    def __eq__(self, argument) -> bool:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __format__(self, format_specification="") -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

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
    def assignments(self) -> typing.List[RhythmAssignment]:
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
    def tag(self) -> typing.Optional[str]:
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
) -> RhythmAssignment:
    """
    Makes rhythm assignment.
    """
    return RhythmAssignment(
        rhythm_maker,
        predicate,
        remember_state_across_gaps=remember_state_across_gaps,
    )


def command(
    rhythm_maker: RhythmMakerTyping,
    *commands: _commands.Command,
    preprocessor: abjad.Expression = None,
    tag: str = None,
):
    """
    Makes rhythm command.
    """
    return RhythmCommand(
        rhythm_maker, *commands, preprocessor=preprocessor, tag=tag
    )


def stack(
    maker, *commands, preprocessor: abjad.Expression = None, tag: str = None
) -> Stack:
    """
    Makes stack.
    """
    return Stack(maker, *commands, preprocessor=preprocessor, tag=tag)


def tesselate(*assignments: RhythmAssignment, tag: str = None) -> Tesselation:
    """
    Makes tesselation.
    """
    return Tesselation(*assignments, tag=tag)
