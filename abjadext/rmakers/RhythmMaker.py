import abjad
import collections
import typing
from abjad.top.new import new
from . import commands as _commands
from . import specifiers as specifiers


class RhythmMaker(object):
    """
    Rhythm-maker baseclass.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = (
        "_already_cached_state",
        "_divisions",
        "_duration_specifier",
        "_previous_state",
        "_commands",
        "_state",
        "_tag",
    )

    # to make sure abjad.new() copies commands
    _positional_arguments_name = "commands"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *commands: _commands.Command,
        divisions: abjad.Expression = None,
        duration_specifier: specifiers.DurationSpecifier = None,
        tag: str = None,
    ) -> None:
        commands = commands or ()
        for command in commands:
            assert isinstance(command, _commands.Command), repr(command)
        commands_ = tuple(commands)
        self._commands = commands_
        if divisions is not None:
            assert isinstance(divisions, abjad.Expression)
        self._divisions = divisions
        if duration_specifier is not None:
            assert isinstance(duration_specifier, specifiers.DurationSpecifier)
        self._duration_specifier = duration_specifier
        self._already_cached_state = None
        self._previous_state = abjad.OrderedDict()
        self._state = abjad.OrderedDict()
        if tag is not None:
            assert isinstance(tag, str), repr(tag)
        self._tag = tag

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.Sequence[abjad.IntegerPair],
        previous_state: abjad.OrderedDict = None,
    ) -> abjad.Selection:
        """
        Calls rhythm-maker.
        """
        self._previous_state = abjad.OrderedDict(previous_state)
        time_signatures = [abjad.TimeSignature(_) for _ in divisions]
        divisions = [abjad.NonreducedFraction(_) for _ in divisions]
        staff = self._make_staff(time_signatures)
        if self.divisions is not None:
            divisions = self.divisions(divisions)
            assert isinstance(divisions, abjad.Sequence), repr(divisions)
            divisions = divisions.flatten(depth=-1)
            divisions = list(divisions)
        music = self._make_music(divisions)
        assert isinstance(music, list), repr(music)
        prototype = (abjad.Tuplet, abjad.Selection)
        for item in music:
            assert isinstance(item, prototype), repr(item)
        staff["MusicVoice"].extend(music)
        divisions_consumed = len(divisions)
        self._apply_specifiers(staff, divisions_consumed)
        if self._already_cached_state is not True:
            self._cache_state(staff, divisions_consumed)
        # self._check_wellformedness(staff)
        self._validate_tuplets(staff)
        selection = staff["MusicVoice"][:]
        staff["MusicVoice"][:] = []
        return selection

    def __eq__(self, argument) -> bool:
        """
        Is true when all initialization values of rhythm-maker equal
        initialization values of ``argument``.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __hash__(self) -> int:
        """
        Hashes rhythm-maker.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __format__(self, format_specification="") -> str:
        """
        Formats rhythm-maker.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _apply_specifiers(self, staff, divisions_consumed):
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        if self._previous_incomplete_last_note():
            previous_logical_ties_produced -= 1
        for command in self.commands or []:
            if isinstance(command, _commands.CacheStateCommand):
                self._cache_state(staff, divisions_consumed)
                self._already_cached_state = True
                continue
            elif isinstance(command, _commands.RestCommand):
                command(
                    staff,
                    previous_logical_ties_produced=previous_logical_ties_produced,
                    tag=self.tag,
                )
            else:
                command(staff, tag=self.tag)

    def _cache_state(self, staff, divisions_consumed):
        music_voice = staff["MusicVoice"]
        time_signature_voice = staff["TimeSignatureVoice"]
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        logical_ties_produced = len(abjad.select(music_voice).logical_ties())
        logical_ties_produced += previous_logical_ties_produced
        if self._previous_incomplete_last_note():
            logical_ties_produced -= 1
        self.state["divisions_consumed"] = self.previous_state.get(
            "divisions_consumed", 0
        )
        self.state["divisions_consumed"] += divisions_consumed
        self.state["logical_ties_produced"] = logical_ties_produced
        items = self.state.items()
        state = abjad.OrderedDict(sorted(items))
        self._state = state

    #    def _check_wellformedness(self, stafff):
    #        for component in abjad.iterate(staff).components():
    #            inspector = abjad.inspect(component)
    #            if not inspector.wellformed():
    #                report = inspector.tabulate_wellformedness()
    #                report = repr(component) + "\n" + report
    #                raise Exception(report)

    def _get_duration_specifier(self):
        if self.duration_specifier is not None:
            return self.duration_specifier
        return specifiers.DurationSpecifier()

    def _get_format_specification(self):
        commands = self.commands or []
        return abjad.FormatSpecification(
            self, storage_format_args_values=commands
        )

    def _make_music(self, divisions):
        return []

    @staticmethod
    def _make_staff(time_signatures):
        assert time_signatures, repr(time_signatures)
        staff = abjad.Staff(is_simultaneous=True)
        time_signature_voice = abjad.Voice(name="TimeSignatureVoice")
        for time_signature in time_signatures:
            duration = time_signature.pair
            skip = abjad.Skip(1, multiplier=duration)
            time_signature_voice.append(skip)
            abjad.attach(time_signature, skip, context="Staff")
        staff.append(time_signature_voice)
        staff.append(abjad.Voice(name="MusicVoice"))
        return staff

    def _make_tuplets(self, divisions, leaf_lists):
        assert len(divisions) == len(leaf_lists)
        tuplets = []
        for division, leaf_list in zip(divisions, leaf_lists):
            duration = abjad.Duration(division)
            tuplet = abjad.Tuplet.from_duration(
                duration, leaf_list, tag=self.tag
            )
            tuplets.append(tuplet)
        return tuplets

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

    def _scale_counts(self, divisions, talea_denominator, counts):
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
        assert abjad.mathtools.is_integer_equivalent(multiplier)
        multiplier = int(multiplier)
        scaled_counts = {}
        for name, vector in counts.items():
            vector = [multiplier * _ for _ in vector]
            vector = abjad.CyclicTuple(vector)
            scaled_counts[name] = vector
        assert len(scaled_divisions) == len(divisions)
        assert len(scaled_counts) == len(counts)
        return abjad.OrderedDict(
            {
                "divisions": scaled_divisions,
                "lcd": lcd,
                "counts": scaled_counts,
            }
        )

    def _validate_tuplets(self, selections):
        for tuplet in abjad.iterate(selections).components(abjad.Tuplet):
            assert tuplet.multiplier.normalized(), repr(tuplet)
            assert len(tuplet), repr(tuplet)

    ### PUBLIC PROPERTIES ###

    @property
    def divisions(self) -> typing.Optional[abjad.Expression]:
        r"""
        Gets division expression.
        """
        return self._divisions

    @property
    def duration_specifier(
        self
    ) -> typing.Optional[specifiers.DurationSpecifier]:
        """
        Gets duration specifier.
        """
        return self._duration_specifier

    @property
    def previous_state(self) -> abjad.OrderedDict:
        """
        Gets previous state dictionary.
        """
        return self._previous_state

    @property
    def commands(self) -> typing.List[_commands.Command]:
        """
        Gets commands.
        """
        return list(self._commands)

    @property
    def state(self) -> abjad.OrderedDict:
        """
        Gets state dictionary.
        """
        return self._state

    @property
    def tag(self) -> typing.Optional[str]:
        """
        Gets tag.
        """
        return self._tag
