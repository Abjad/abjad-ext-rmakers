import abjad
import collections
import typing
from abjad.top.new import new
from . import commands as _commands
from . import specifiers as _specifiers


class RhythmMaker(object):
    """
    Rhythm-maker baseclass.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = (
        "_already_cached_state",
        "_previous_state",
        "_spelling",
        "_state",
        "_tag",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self, *, spelling: _specifiers.Spelling = None, tag: str = None
    ) -> None:
        if spelling is not None:
            assert isinstance(spelling, _specifiers.Spelling)
        self._spelling = spelling
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
        music = self._make_music(divisions)
        assert isinstance(music, list), repr(music)
        prototype = (abjad.Tuplet, abjad.Selection)
        for item in music:
            assert isinstance(item, prototype), repr(item)
        voice = staff["MusicVoice"]
        voice.extend(music)
        divisions_consumed = len(divisions)
        if self._already_cached_state is not True:
            self._cache_state(voice, divisions_consumed)
        # self._check_wellformedness(staff)
        self._validate_tuplets(voice)
        selection = voice[:]
        voice[:] = []
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

    def _cache_state(self, voice, divisions_consumed):
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        logical_ties_produced = len(abjad.select(voice).logical_ties())
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

    def _call_commands(self, voice, divisions_consumed):
        pass

    #    def _check_wellformedness(self, stafff):
    #        for component in abjad.iterate(staff).components():
    #            inspector = abjad.inspect(component)
    #            if not inspector.wellformed():
    #                report = inspector.tabulate_wellformedness()
    #                report = repr(component) + "\n" + report
    #                raise Exception(report)

    def _get_spelling_specifier(self):
        if self.spelling is not None:
            return self.spelling
        return _specifiers.Spelling()

    def _get_format_specification(self):
        return abjad.FormatSpecification(self)

    @staticmethod
    def _make_leaves_from_talea(
        talea,
        talea_denominator,
        increase_monotonic=None,
        forbidden_note_duration=None,
        forbidden_rest_duration=None,
        tag: str = None,
    ):
        assert all(x != 0 for x in talea), repr(talea)
        result: typing.List[abjad.Leaf] = []
        leaf_maker = abjad.LeafMaker(
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            tag=tag,
        )
        pitches: typing.List[typing.Union[int, None]]
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
                and abjad.inspect(leaves[0]).logical_tie().is_trivial
                and not isinstance(leaves[0], abjad.Rest)
            ):
                abjad.tie(leaves)
            result.extend(leaves)
        result = abjad.select(result)
        return result

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
    def previous_state(self) -> abjad.OrderedDict:
        """
        Gets previous state dictionary.
        """
        return self._previous_state

    @property
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        """
        Gets duration specifier.
        """
        return self._spelling

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
