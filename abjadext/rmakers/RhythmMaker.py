import abjad
import collections
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier
from .DurationSpecifier import DurationSpecifier
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier
from abjad.top.new import new


class RhythmMaker(object):
    """
    Abstract rhythm-maker.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = (
        "_division_masks",
        "_duration_specifier",
        "_previous_state",
        "_specifiers",
        "_state",
        "_tag",
        "_tie_specifier",
        "_tuplet_specifier",
    )

    _private_attributes_to_copy = ("_specifiers",)

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *specifiers: typings.SpecifierTyping,
        division_masks: typings.MasksTyping = None,
        duration_specifier: DurationSpecifier = None,
        tag: str = None,
        tie_specifier: TieSpecifier = None,
        tuplet_specifier: TupletSpecifier = None,
    ) -> None:
        specifiers = specifiers or ()
        specifiers_ = list(specifiers)
        self._specifiers = specifiers_
        if duration_specifier is not None:
            assert isinstance(duration_specifier, DurationSpecifier)
        self._duration_specifier = duration_specifier
        division_masks = self._prepare_masks(division_masks)
        if division_masks is not None:
            assert isinstance(division_masks, abjad.PatternTuple)
        self._division_masks = division_masks
        self._previous_state = abjad.OrderedDict()
        self._state = abjad.OrderedDict()
        if tag is not None:
            assert isinstance(tag, str), repr(tag)
        self._tag = tag
        if tie_specifier is not None:
            assert isinstance(tie_specifier, TieSpecifier)
        self._tie_specifier = tie_specifier
        if tuplet_specifier is not None:
            assert isinstance(tuplet_specifier, TupletSpecifier)
        self._tuplet_specifier = tuplet_specifier

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
        divisions = self._coerce_divisions(divisions)
        selections = self._make_music(divisions)
        selections = self._apply_tuplet_specifier(selections, divisions)
        selections = self._apply_division_masks(selections)
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        temporary_container = abjad.Container(selections)
        logical_ties_produced = len(abjad.select(selections).logical_ties())
        temporary_container[:] = []
        logical_ties_produced += previous_logical_ties_produced
        if self._previous_incomplete_last_note():
            logical_ties_produced -= 1
        selections = self._rewrite_meter(selections, divisions)
        self._cache_state(selections, divisions, logical_ties_produced)
        selections = self._apply_specifier_stack(selections, divisions)
        selections = self._apply_specifiers(selections)
        # self._check_wellformedness(selections)
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

    @staticmethod
    def _all_are_tuplets_or_all_are_leaf_selections(argument):
        if all(isinstance(_, abjad.Tuplet) for _ in argument):
            return True
        elif all(_.are_leaves() for _ in argument):
            return True
        else:
            return False

    def _apply_division_masks(self, selections):
        if not self.division_masks:
            return selections
        new_selections = []
        duration_specifier = self._get_duration_specifier()
        increase_monotonic = duration_specifier.increase_monotonic
        forbidden_note_duration = duration_specifier.forbidden_note_duration
        forbidden_rest_duration = duration_specifier.forbidden_rest_duration
        ###tie_specifier = self._get_tie_specifier()
        total_divisions = len(selections)
        division_masks = self.division_masks
        leaf_maker = abjad.LeafMaker(
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            ###repeat_ties=tie_specifier.repeat_ties,
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
                new_selections.append(selection)
                continue
            duration = abjad.inspect(selection).duration()
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
            for component in abjad.iterate(selection).components():
                abjad.detach(abjad.TieIndicator, component)
                abjad.detach(abjad.RepeatTie, component)
            if new_selections:
                previous_leaf = abjad.select(new_selections).leaf(-1)
                abjad.detach(abjad.TieIndicator, previous_leaf)
            new_selections.append(new_selection)
        return new_selections

    def _apply_specifiers(self, selections):
        ###self._apply_tie_specifier(selections)
        ###self._apply_beam_specifier(selections)
        self._validate_selections(selections)
        self._validate_tuplets(selections)
        return selections

    def _apply_specifier_stack(self, selections, divisions):
        if self.specifiers == []:
            return selections
        if not self.specifiers:
            return selections
        for specifier in self.specifiers:
            selections = specifier(
                selections, divisions=divisions, tag=self.tag
            )
        return selections

    #    def _apply_tie_specifier(self, selections):
    #        tie_specifier = self._get_tie_specifier()
    #        tie_specifier(selections)

    def _apply_tuplet_specifier(self, selections, divisions=None):
        tuplet_specifier = self._get_tuplet_specifier()
        selections = tuplet_specifier(selections, divisions)
        return selections

    def _cache_state(self, selections, divisions, logical_ties_produced):
        string = "divisions_consumed"
        self.state[string] = self.previous_state.get(string, 0)
        self.state[string] += len(divisions)
        self.state["logical_ties_produced"] = logical_ties_produced
        items = self.state.items()
        state = abjad.OrderedDict(sorted(items))
        self._state = state

    #    def _check_wellformedness(self, selections):
    #        for component in abjad.iterate(selections).components():
    #            inspector = abjad.inspect(component)
    #            if not inspector.is_well_formed():
    #                report = inspector.tabulate_wellformedness()
    #                report = repr(component) + '\n' + report
    #                raise Exception(report)

    @staticmethod
    def _coerce_divisions(divisions):
        divisions_ = []
        for division in divisions:
            if isinstance(division, abjad.NonreducedFraction):
                divisions_.append(division)
            else:
                division = abjad.NonreducedFraction(division)
                divisions_.append(division)
        divisions = divisions_
        prototype = abjad.NonreducedFraction
        assert all(isinstance(_, prototype) for _ in divisions)
        return divisions

    def _collect_state(self, state):
        state_ = abjad.OrderedDict()
        for key, value_ in state.items():
            assert hasattr(self, key)
            value = getattr(self, key)
            state_[key] = value
        return state_

    def _get_duration_specifier(self):
        if self.duration_specifier is not None:
            return self.duration_specifier
        return DurationSpecifier()

    def _get_format_specification(self):
        return abjad.FormatSpecification(client=self)

    #    def _get_tie_specifier(self):
    #        if self.tie_specifier is not None:
    #            return self.tie_specifier
    #        return TieSpecifier()

    def _get_tuplet_specifier(self):
        if self.tuplet_specifier is not None:
            return self.tuplet_specifier
        return TupletSpecifier()

    @staticmethod
    def _is_sign_tuple(argument):
        if isinstance(argument, tuple):
            prototype = (-1, 0, 1)
            return all(_ in prototype for _ in argument)
        return False

    @staticmethod
    def _make_cyclic_tuple_generator(iterable):
        cyclic_tuple = abjad.CyclicTuple(iterable)
        i = 0
        while True:
            yield cyclic_tuple[i]
            i += 1

    def _make_music(self, divisions):
        return []

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

    @staticmethod
    def _reverse_tuple(argument):
        if argument is not None:
            return tuple(reversed(argument))

    def _rewrite_meter(self, selections, divisions):
        duration_specifier = self._get_duration_specifier()
        if duration_specifier.rewrite_meter:
            #            tie_specifier = self._get_tie_specifier()
            #            selections = duration_specifier._rewrite_meter_(
            #                selections, divisions, repeat_ties=tie_specifier.repeat_ties
            #            )
            selections = duration_specifier._rewrite_meter_(
                selections, divisions
            )
        return selections

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

    def _sequence_to_ellipsized_string(self, sequence):
        if not sequence:
            return "[]"
        if len(sequence) <= 4:
            result = ", ".join([str(x) for x in sequence])
        else:
            result = ", ".join([str(x) for x in sequence[:4]])
            result += ", ..."
        result = "[${}$]".format(result)
        return result

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
        return self._specifiers

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

    @property
    def tie_specifier(self) -> typing.Optional[TieSpecifier]:
        """
        Gets tie specifier.
        """
        return self._tie_specifier

    @property
    def tuplet_specifier(self) -> typing.Optional[TupletSpecifier]:
        """
        Gets tuplet specifier.
        """
        return self._tuplet_specifier
