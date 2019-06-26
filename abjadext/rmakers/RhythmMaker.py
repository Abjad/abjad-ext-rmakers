import abjad
import collections
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier
from .CacheState import CacheState
from .DurationSpecifier import DurationSpecifier
from .RewriteMeterCommand import RewriteMeterCommand
from .SilenceMask import SilenceMask
from .SplitCommand import SplitCommand
from .SustainMask import SustainMask
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier
from abjad.top.new import new

SpecifierClasses = (
    BeamSpecifier,
    CacheState,
    DurationSpecifier,
    RewriteMeterCommand,
    SilenceMask,
    SplitCommand,
    SustainMask,
    TieSpecifier,
    TupletSpecifier,
)


class RhythmMaker(object):
    """
    Abstract rhythm-maker.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = (
        "_already_cached_state",
        "_division_masks",
        "_duration_specifier",
        "_previous_state",
        "_specifiers",
        "_state",
        "_tag",
    )

    _positional_arguments_name = "specifiers"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *specifiers: typings.SpecifierTyping,
        division_masks: typings.MasksTyping = None,
        duration_specifier: DurationSpecifier = None,
        tag: str = None,
    ) -> None:
        specifiers = specifiers or ()
        for specifier in specifiers:
            assert isinstance(specifier, SpecifierClasses), repr(specifier)
        specifiers_ = tuple(specifiers)
        self._specifiers = specifiers_
        if duration_specifier is not None:
            assert isinstance(duration_specifier, DurationSpecifier)
        self._duration_specifier = duration_specifier
        division_masks = self._prepare_masks(division_masks)
        if division_masks is not None:
            assert isinstance(division_masks, abjad.PatternTuple)
        self._division_masks = division_masks
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
    ) -> typing.List[abjad.Selection]:
        """
        Calls rhythm-maker.
        """
        self._previous_state = abjad.OrderedDict(previous_state)
        time_signatures = [abjad.TimeSignature(_) for _ in divisions]
        divisions = self._coerce_divisions(divisions)
        staff = self._make_staff(time_signatures)
        selections = self._make_music(divisions)
        staff["MusicVoice"].extend(selections)
        self._apply_division_masks(staff)
        self._apply_specifiers(staff)
        if self._already_cached_state is not True:
            self._cache_state(staff)
        # self._check_wellformedness(staff)
        selections = self._select_by_measure(staff)
        staff["MusicVoice"][:] = []
        self._validate_selections(selections)
        self._validate_tuplets(selections)
        return selections

    def __eq__(self, argument) -> bool:
        """
        Is true when all initialization values of Abjad value object equal
        the initialization values of ``argument``.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __hash__(self) -> int:
        """
        Hashes Abjad value object.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __format__(self, format_specification="") -> str:
        """
        Formats Abjad object.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _apply_division_masks(self, staff):
        if not self.division_masks:
            return None
        selections = self._select_by_measure(staff)
        duration_specifier = self._get_duration_specifier()
        increase_monotonic = duration_specifier.increase_monotonic
        forbidden_note_duration = duration_specifier.forbidden_note_duration
        forbidden_rest_duration = duration_specifier.forbidden_rest_duration
        total_divisions = len(selections)
        division_masks = self.division_masks
        leaf_maker = abjad.LeafMaker(
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            tag=self.tag,
        )
        previous_divisions_consumed = self._previous_divisions_consumed()
        for i, selection in enumerate(selections):
            matching_division_mask = division_masks.get_matching_pattern(
                i + previous_divisions_consumed,
                total_divisions + previous_divisions_consumed,
                rotation=self.previous_state.get("rotation"),
            )
            if not matching_division_mask:
                continue
            duration = abjad.inspect(selection).duration()
            assert len(selection) != 0, repr(selection)
            if isinstance(matching_division_mask, SustainMask):
                leaf_maker = abjad.new(
                    leaf_maker, use_multimeasure_rests=False
                )
                new_selection = leaf_maker([0], [duration])
            else:
                use_multimeasure_rests = getattr(
                    matching_division_mask, "use_multimeasure_rests", False
                )
                leaf_maker = abjad.new(
                    leaf_maker, use_multimeasure_rests=use_multimeasure_rests
                )
                new_selection = leaf_maker([None], [duration])
                first_leaf = abjad.inspect(selection).leaf(0)
                previous_leaf = abjad.inspect(first_leaf).leaf(-1)
                if previous_leaf is not None:
                    abjad.detach(abjad.TieIndicator, previous_leaf)
                final_leaf = abjad.inspect(selection).leaf(-1)
                next_leaf = abjad.inspect(final_leaf).leaf(1)
                if next_leaf is not None:
                    abjad.detach(abjad.RepeatTie, next_leaf)
            abjad.mutate(selection).replace(new_selection)

    def _apply_specifiers(self, staff):
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        if self._previous_incomplete_last_note():
            previous_logical_ties_produced -= 1
        for specifier in self.specifiers or []:
            if isinstance(specifier, CacheState):
                self._cache_state(staff)
                self._already_cached_state = True
                continue
            elif isinstance(specifier, SilenceMask):
                specifier(
                    staff,
                    previous_logical_ties_produced=previous_logical_ties_produced,
                    tag=self.tag,
                )
            else:
                try:
                    specifier(staff, tag=self.tag)
                except TypeError:
                    raise Exception("AAA", specifier)

    def _cache_state(self, staff):
        music_voice = staff["MusicVoice"]
        time_signature_voice = staff["TimeSignatureVoice"]
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        logical_ties_produced = len(abjad.select(music_voice).logical_ties())
        logical_ties_produced += previous_logical_ties_produced
        if self._previous_incomplete_last_note():
            logical_ties_produced -= 1
        string = "divisions_consumed"
        self.state[string] = self.previous_state.get(string, 0)
        self.state[string] += len(time_signature_voice)
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

    @staticmethod
    def _coerce_divisions(divisions) -> typing.List[abjad.NonreducedFraction]:
        divisions_ = []
        for division in divisions:
            division = abjad.NonreducedFraction(division)
            divisions_.append(division)
        return divisions_

    def _get_duration_specifier(self):
        if self.duration_specifier is not None:
            return self.duration_specifier
        return DurationSpecifier()

    def _get_format_specification(self):
        specifiers = self.specifiers or []
        return abjad.FormatSpecification(
            self, storage_format_args_values=specifiers
        )

    @staticmethod
    def _select_by_measure(staff):
        selection = staff["MusicVoice"][:]
        assert isinstance(selection, abjad.Selection)
        time_signatures = [
            abjad.inspect(_).indicator(abjad.TimeSignature)
            for _ in staff["TimeSignatureVoice"]
        ]
        selections = selection.partition_by_durations(time_signatures)
        selections = list(selections)
        return selections

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

    @staticmethod
    def _prepare_masks(masks):
        prototype = (SilenceMask, SustainMask)
        if masks is None:
            return
        if isinstance(masks, abjad.Pattern):
            masks = (masks,)
        if isinstance(masks, prototype):
            masks = (masks,)
        masks = abjad.PatternTuple(items=masks)
        return masks

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

    def _validate_selections(self, selections):
        assert isinstance(selections, collections.Sequence), repr(selections)
        assert len(selections), repr(selections)
        for selection in selections:
            assert isinstance(selection, abjad.Selection), selection

    def _validate_tuplets(self, selections):
        for tuplet in abjad.iterate(selections).components(abjad.Tuplet):
            assert tuplet.multiplier.normalized(), repr(tuplet)
            assert len(tuplet), repr(tuplet)

    ### PUBLIC PROPERTIES ###

    @property
    def division_masks(self) -> typing.Optional[typings.MasksTyping]:
        """
        Gets division masks.
        """
        return self._division_masks

    @property
    def duration_specifier(self) -> typing.Optional[DurationSpecifier]:
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
    def specifiers(self) -> typing.List[typings.SpecifierTyping]:
        """
        Gets specifiers.
        """
        return list(self._specifiers)

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
