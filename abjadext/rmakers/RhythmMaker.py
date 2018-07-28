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


class RhythmMaker(abjad.AbjadValueObject):
    """
    Abstract rhythm-maker.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Rhythm-makers'

    __slots__ = (
        '_beam_specifier',
        '_division_masks',
        '_duration_specifier',
        '_logical_tie_masks',
        '_previous_state',
        '_state',
        '_tie_specifier',
        '_tuplet_specifier',
        )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        beam_specifier: BeamSpecifier = None,
        division_masks: typings.MaskKeyword = None,
        duration_specifier=None,
        logical_tie_masks: typings.MaskKeyword = None,
        tie_specifier=None,
        tuplet_specifier=None,
        ) -> None:
        if beam_specifier is not None:
            assert isinstance(beam_specifier, BeamSpecifier)
        self._beam_specifier = beam_specifier
        logical_tie_masks = self._prepare_masks(logical_tie_masks)
        if logical_tie_masks is not None:
            assert isinstance(logical_tie_masks, abjad.PatternTuple)
        self._logical_tie_masks = logical_tie_masks
        if duration_specifier is not None:
            assert isinstance(duration_specifier, DurationSpecifier)
        self._duration_specifier = duration_specifier
        division_masks = self._prepare_masks(division_masks)
        if division_masks is not None:
            assert isinstance(division_masks, abjad.PatternTuple)
        self._division_masks = division_masks
        self._previous_state = abjad.OrderedDict()
        self._state = abjad.OrderedDict()
        if tie_specifier is not None:
            assert isinstance(tie_specifier, TieSpecifier)
        self._tie_specifier = tie_specifier
        if tuplet_specifier is not None:
            assert isinstance(tuplet_specifier, TupletSpecifier)
        self._tuplet_specifier = tuplet_specifier

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.List[typing.Tuple[int, int]],
        previous_state: abjad.OrderedDict = None,
        ) -> typing.List[abjad.Selection]:
        """
        Calls rhythm-maker.
        """
        self._previous_state = abjad.OrderedDict(previous_state)
        divisions = self._coerce_divisions(divisions)
        selections = self._make_music(divisions)
        selections = self._apply_specifiers(selections, divisions)
        #self._check_wellformedness(selections)
        return selections

    def __illustrate__(self, divisions=((3, 8), (4, 8), (3, 16), (4, 16))):
        """
        Illustrates rhythm-maker.

        Returns LilyPond file.
        """
        selections = self(divisions)
        lilypond_file = abjad.LilyPondFile.rhythm(
            selections,
            divisions,
            )
        return lilypond_file

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
        decrease_monotonic = duration_specifier.decrease_monotonic
        forbidden_duration = duration_specifier.forbidden_duration
        tie_specifier = self._get_tie_specifier()
        total_divisions = len(selections)
        division_masks = self.division_masks
        leaf_maker = abjad.LeafMaker(
            decrease_monotonic=decrease_monotonic,
            forbidden_duration=forbidden_duration,
            repeat_ties=tie_specifier.repeat_ties,
            )
        previous_divisions_consumed = self._previous_divisions_consumed()
        for i, selection in enumerate(selections):
            matching_division_mask = division_masks.get_matching_pattern(
                i + previous_divisions_consumed,
                total_divisions + previous_divisions_consumed,
                rotation=self.previous_state.get('rotation'),
                )
            if not matching_division_mask:
                new_selections.append(selection)
                continue
            duration = abjad.inspect(selection).duration()
            if isinstance(matching_division_mask, SustainMask):
                leaf_maker = abjad.new(
                    leaf_maker,
                    use_multimeasure_rests=False,
                    )
                new_selection = leaf_maker([0], [duration])
            else:
                use_multimeasure_rests = getattr(
                    matching_division_mask,
                    'use_multimeasure_rests',
                    False,
                    )
                leaf_maker = abjad.new(
                    leaf_maker,
                    use_multimeasure_rests=use_multimeasure_rests,
                    )
                new_selection = leaf_maker([None], [duration])
            for component in abjad.iterate(selection).components():
                abjad.detach(abjad.Tie, component)
            new_selections.append(new_selection)
        return new_selections

    def _apply_logical_tie_masks(self, selections):
        if self.logical_tie_masks is None:
            return selections
        # wrap every selection in a temporary container;
        # this allows the call to abjad.mutate().replace() to work
        containers = []
        for selection in selections:
            container = abjad.Container(selection)
            abjad.attach(abjad.tags.TEMPORARY_CONTAINER, container)
            containers.append(container)
        logical_ties = abjad.iterate(selections).logical_ties()
        logical_ties = list(logical_ties)
        total_logical_ties = len(logical_ties)
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        if self._previous_incomplete_last_note():
            previous_logical_ties_produced -= 1
        for index, logical_tie in enumerate(logical_ties[:]):
            matching_mask = self.logical_tie_masks.get_matching_pattern(
                index + previous_logical_ties_produced,
                total_logical_ties + previous_logical_ties_produced,
                )
            if not isinstance(matching_mask, SilenceMask):
                continue
            if isinstance(logical_tie.head, abjad.Rest):
                continue
            for leaf in logical_tie:
                rest = abjad.Rest(leaf.written_duration)
                inspector = abjad.inspect(leaf)
                if inspector.has_indicator(abjad.Multiplier):
                    multiplier = inspector.indicator(abjad.Multiplier)
                    multiplier = abjad.Multiplier(multiplier)
                    abjad.attach(multiplier, rest)
                abjad.mutate(leaf).replace([rest])
                abjad.detach(abjad.Tie, rest)
        # remove every temporary container and recreate selections
        new_selections = []
        for container in containers:
            inspector = abjad.inspect(container)
            assert inspector.indicator(abjad.tags.TEMPORARY_CONTAINER)
            new_selection = abjad.mutate(container).eject_contents()
            new_selections.append(new_selection)
        return new_selections

    def _apply_specifiers(self, selections, divisions=None):
        selections = self._apply_tuplet_specifier(
            selections,
            divisions,
            )
        self._apply_tie_specifier(selections)
        selections = self._apply_logical_tie_masks(selections)
        self._validate_selections(selections)
        self._validate_tuplets(selections)
        return selections

    def _apply_tie_specifier(self, selections):
        tie_specifier = self._get_tie_specifier()
        tie_specifier(selections)

    def _apply_tuplet_specifier(self, selections, divisions):
        tuplet_specifier = self._get_tuplet_specifier()
        selections = tuplet_specifier(selections, divisions)
        return selections

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

    def _get_beam_specifier(self):
        if self.beam_specifier is not None:
            return self.beam_specifier
        return BeamSpecifier()

    def _get_duration_specifier(self):
        if self.duration_specifier is not None:
            return self.duration_specifier
        return DurationSpecifier()

    def _get_tie_specifier(self):
        if self.tie_specifier is not None:
            return self.tie_specifier
        return TieSpecifier()

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

    def _make_secondary_divisions(
        self,
        divisions,
        split_divisions_by_counts,
        ):
        if not split_divisions_by_counts:
            return divisions[:]
        numerators = [
            division.numerator
            for division in divisions
            ]
        secondary_numerators = abjad.sequence(numerators)
        secondary_numerators = secondary_numerators.split(
            split_divisions_by_counts,
            cyclic=True,
            overhang=True,
            )
        secondary_numerators = abjad.sequence(secondary_numerators)
        secondary_numerators = secondary_numerators.flatten(depth=-1)
        denominator = divisions[0].denominator
        secondary_divisions = [
            (n, denominator)
            for n in secondary_numerators
            ]
        return secondary_divisions

    def _make_tuplets(self, divisions, leaf_lists):
        assert len(divisions) == len(leaf_lists)
        tuplets = []
        for division, leaf_list in zip(divisions, leaf_lists):
            duration = abjad.Duration(division)
            tuplet = abjad.Tuplet.from_duration(duration, leaf_list)
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
        return self.previous_state.get('divisions_consumed', 0)

    def _previous_incomplete_last_note(self):
        if not self.previous_state:
            return False
        return self.previous_state.get('incomplete_last_note', False)

    def _previous_logical_ties_produced(self):
        if not self.previous_state:
            return 0
        return self.previous_state.get('logical_ties_produced', 0)

    @staticmethod
    def _reverse_tuple(argument):
        if argument is not None:
            return tuple(reversed(argument))

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
        return {
            'divisions': scaled_divisions,
            'lcd': lcd,
            'counts': scaled_counts,
            }

    def _sequence_to_ellipsized_string(self, sequence):
        if not sequence:
            return '[]'
        if len(sequence) <= 4:
            result = ', '.join([str(x) for x in sequence])
        else:
            result = ', '.join([str(x) for x in sequence[:4]])
            result += ', ...'
        result = '[${}$]'.format(result)
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
    def beam_specifier(self) -> typing.Optional[BeamSpecifier]:
        """
        Gets beam specifier.
        """
        return self._beam_specifier

    @property
    def division_masks(self) -> typing.Optional[abjad.PatternTuple]:
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
    def logical_tie_masks(self) -> typing.Optional[abjad.PatternTuple]:
        """
        Gets logical tie masks.
        """
        return self._logical_tie_masks

    @property
    def previous_state(self) -> abjad.OrderedDict:
        """
        Gets previous state dictionary.
        """
        return self._previous_state

    @property
    def state(self) -> abjad.OrderedDict:
        """
        Gets state dictionary.
        """
        return self._state

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
