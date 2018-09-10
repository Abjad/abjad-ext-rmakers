import abjad
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier
from .BurnishSpecifier import BurnishSpecifier
from .DurationSpecifier import DurationSpecifier
from .RhythmMaker import RhythmMaker
from .Talea import Talea
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier


class TaleaRhythmMaker(RhythmMaker):
    r"""
    Talea rhythm-maker.

    ..  container:: example

        Repeats talea of 1/16, 2/16, 3/16, 4/16:

        >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
        ...     talea=abjadext.rmakers.Talea(
        ...         counts=[1, 2, 3, 4],
        ...         denominator=16,
        ...         ),
        ...     )

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    c'16
                    [
                    c'8
                    c'8.
                    ]
                    c'4
                    c'16
                    [
                    c'8
                    c'16
                    ~
                    ]
                    c'8
                    c'4
                    c'16
                    [
                    c'8
                    c'8.
                    c'8
                    ]
                }
            >>

    Follows the configure-once / call-repeatedly pattern shown here.

    Object model of a partially evaluated function. Function accepts a list of
    divisions as input. Function returns a list of selections as output. Length
    of input equals length of output.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Rhythm-makers'

    __slots__ = (
        '_burnish_specifier',
        '_extra_counts_per_division',
        '_read_talea_once_only',
        '_rest_tied_notes',
        '_split_divisions_by_counts',
        '_talea',
        '_tie_split_notes',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        talea: Talea = None,
        beam_specifier: BeamSpecifier = None,
        burnish_specifier: BurnishSpecifier = None,
        division_masks: typings.MaskKeyword = None,
        duration_specifier: DurationSpecifier = None,
        extra_counts_per_division: typing.List[int] = None,
        logical_tie_masks: typings.MaskKeyword = None,
        read_talea_once_only: bool = None,
        rest_tied_notes: bool = None,
        split_divisions_by_counts: typing.List[int] = None,
        tag: str = None,
        tie_specifier: TieSpecifier = None,
        tie_split_notes: bool = True,
        tuplet_specifier: TupletSpecifier = None,
        ) -> None:
        RhythmMaker.__init__(
            self,
            beam_specifier=beam_specifier,
            duration_specifier=duration_specifier,
            division_masks=division_masks,
            logical_tie_masks=logical_tie_masks,
            tag=tag,
            tie_specifier=tie_specifier,
            tuplet_specifier=tuplet_specifier,
            )
        if talea is not None:
            assert isinstance(talea, Talea), repr(talea)
        self._talea = talea
        if burnish_specifier is not None:
            assert isinstance(burnish_specifier, BurnishSpecifier)
        self._burnish_specifier = burnish_specifier
        if extra_counts_per_division is not None:
            assert abjad.mathtools.all_are_integer_equivalent_numbers(
                extra_counts_per_division)
        self._extra_counts_per_division = extra_counts_per_division
        if read_talea_once_only is not None:
            read_talea_once_only = bool(read_talea_once_only)
        self._read_talea_once_only = read_talea_once_only
        if rest_tied_notes is not None:
            rest_tied_notes = bool(rest_tied_notes)
        self._rest_tied_notes = rest_tied_notes
        split_divisions_by_counts_ = None
        if split_divisions_by_counts is not None:
            split_divisions_by_counts_ = tuple(split_divisions_by_counts)
            assert all(isinstance(_, int) for _ in split_divisions_by_counts_)
        self._split_divisions_by_counts = split_divisions_by_counts_
        if tie_split_notes is not None:
            tie_split_notes = bool(tie_split_notes)
        self._tie_split_notes = tie_split_notes

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.List[typing.Tuple[int, int]],
        previous_state: abjad.OrderedDict = None,
        ) -> typing.List[abjad.Selection]:
        """
        Calls talea rhythm-maker on ``divisions``.

        ..  container:: example

                >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
                ...     talea=abjadext.rmakers.Talea(
                ...         counts=[1, 2, 3, 4],
                ...         denominator=16,
                ...         ),
                ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)

            >>> for selection in selections:
            ...     selection
            Selection([Note("c'16"), Note("c'8"), Note("c'8.")])
            Selection([Note("c'4"), Note("c'16"), Note("c'8"), Note("c'16")])
            Selection([Note("c'8"), Note("c'4")])
            Selection([Note("c'16"), Note("c'8"), Note("c'8."), Note("c'8")])

        """
        return RhythmMaker.__call__(
            self,
            divisions,
            previous_state=previous_state,
            )

    def __format__(self, format_specification='') -> str:
        """
        Formats talea rhythm-maker.

        ..  container:: example

            Formats talea rhythm-maker:

                >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
                ...     talea=abjadext.rmakers.Talea(
                ...         counts=[1, 2, 3, 4],
                ...         denominator=16,
                ...         ),
                ...     )

            >>> abjad.f(rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                talea=abjadext.rmakers.Talea(
                    counts=[1, 2, 3, 4],
                    denominator=16,
                    ),
                )

        ..  container:: example

            Storage formats talea rhythm-maker:

                >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
                ...     talea=abjadext.rmakers.Talea(
                ...         counts=[1, 2, 3, 4],
                ...         denominator=16,
                ...         ),
                ...     )

            >>> abjad.f(rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                talea=abjadext.rmakers.Talea(
                    counts=[1, 2, 3, 4],
                    denominator=16,
                    ),
                )

        """
        return super(TaleaRhythmMaker, self).__format__(
            format_specification=format_specification,
            )

    def __illustrate__(
        self,
        divisions: typing.List[typing.Tuple[int, int]] = [
            (3, 8), (4, 8), (3, 16), (4, 16)
            ],
        ) -> abjad.LilyPondFile:
        r"""
        Illustrates talea rhythm-maker.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )
            >>> abjad.show(rhythm_maker) # doctest: +SKIP

            ..  docs::

                >>> lilypond_file = rhythm_maker.__illustrate__()
                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/16
                        s1 * 3/16
                        \time 4/16
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8
                        [
                        c'16
                        ~
                        ]
                        c'8.
                        [
                        c'16
                        ]
                    }
                >>

        Defaults ``divisions`` to ``3/8``, ``4/8``, ``3/16``, ``4/16``.

        Returns LilyPond file.
        """
        return RhythmMaker.__illustrate__(self, divisions=divisions)

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )
            TaleaRhythmMaker(talea=Talea(counts=[1, 2, 3, 4], denominator=16))

        Returns string.
        """
        return super(TaleaRhythmMaker, self).__repr__()

    ### PRIVATE METHODS ###

    def _apply_burnish_specifier(self, divisions):
        burnish_specifier = self._get_burnish_specifier()
        return burnish_specifier(divisions)

    def _apply_ties_to_split_notes(
        self,
        result,
        unscaled_end_counts,
        unscaled_preamble,
        unscaled_talea,
        ):
        if not self.tie_split_notes:
            return
        leaves = abjad.select(result).leaves()
        written_durations = [leaf.written_duration for leaf in leaves]
        written_durations = abjad.sequence(written_durations)
        total_duration = written_durations.weight()
        if unscaled_preamble is None:
            preamble_weights = []
        else:
            preamble_weights = []
            for numerator in unscaled_preamble:
                pair = (numerator, self.talea.denominator)
                duration = abjad.Duration(*pair)
                weight = abs(duration)
                preamble_weights.append(weight)
        preamble_duration = sum(preamble_weights)
        if total_duration <= preamble_duration:
            preamble_parts = written_durations.partition_by_weights(
                weights=preamble_weights,
                allow_part_weights=abjad.More,
                cyclic=True,
                overhang=True,
                )
            talea_parts = []
        else:
            assert preamble_duration < total_duration
            preamble_parts = written_durations.partition_by_weights(
                weights=preamble_weights,
                allow_part_weights=abjad.Exact,
                cyclic=False,
                overhang=False,
                )
            talea_weights = []
            for numerator in unscaled_talea:
                pair = (numerator, self.talea.denominator)
                weight = abs(abjad.Duration(*pair))
                talea_weights.append(weight)
            preamble_length = len(preamble_parts.flatten())
            talea_written_durations = written_durations[preamble_length:]
            talea_parts = talea_written_durations.partition_by_weights(
                weights=talea_weights,
                allow_part_weights=abjad.More,
                cyclic=True,
                overhang=True,
                )
        parts = preamble_parts + talea_parts
        part_durations = parts.flatten()
        assert part_durations == abjad.sequence(written_durations)
        counts = [len(part) for part in parts]
        parts = abjad.sequence(leaves).partition_by_counts(counts)
        for part in parts:
            if any(isinstance(_, abjad.Rest) for _ in part):
                continue
            part = abjad.select(part)
            tie = abjad.Tie()
            # voodoo to temporarily neuter the contiguity constraint
            tie._unconstrain_contiguity()
            for component in part:
                # TODO: make top-level abjad.detach() work here
                for spanner in component._get_spanners(abjad.Tie):
                    spanner._sever_all_leaves()
                #abjad.detach(abjad.Tie, component)
            # TODO: remove usage of Spanner._extend()
            tie._extend(part)
            tie._constrain_contiguity()
        # TODO: this will need to be generalized and better tested:
        if unscaled_end_counts:
            total = len(unscaled_end_counts)
            end_leaves = leaves[-total:]
            for leaf in reversed(end_leaves):
                tie = abjad.inspect(leaf).spanner(abjad.Tie)
                if tie is None:
                    continue
                assert leaf is tie[-1]
                leaves = tie.leaves[:-1]
                abjad.detach(abjad.Tie, leaf)
                if 2 <= len(leaves):
                    tie = abjad.new(tie)
                    abjad.attach(tie, leaves)

    def _get_burnish_specifier(self):
        if self.burnish_specifier is not None:
            return self.burnish_specifier
        return BurnishSpecifier()

    def _get_format_specification(self):
        agent = abjad.StorageFormatManager(self)
        names = list(agent.signature_keyword_names)
        if self.tie_split_notes:
            names.remove('tie_split_notes')
        return abjad.FormatSpecification(
            self,
            storage_format_kwargs_names=names,
            )

    def _get_talea(self):
        if self.talea is not None:
            return self.talea
        return Talea()

    def _handle_rest_tied_notes(self, selections):
        if not self.rest_tied_notes:
            return selections
        # wrap every selection in a temporary container;
        # this allows the call to abjad.mutate().replace() to work
        containers = []
        for selection in selections:
            container = abjad.Container(selection)
            abjad.attach('temporary container', container)
            containers.append(container)
        for logical_tie in abjad.iterate(selections).logical_ties():
            if not logical_tie.is_trivial:
                for note in logical_tie[1:]:
                    rest = abjad.Rest(note)
                    abjad.mutate(note).replace(rest)
                abjad.detach(abjad.Tie, logical_tie.head)
        # remove every temporary container and recreate selections
        new_selections = []
        for container in containers:
            inspection = abjad.inspect(container)
            assert inspection.indicator(str) == 'temporary container'
            new_selection = abjad.mutate(container).eject_contents()
            new_selections.append(new_selection)
        return new_selections

    def _make_leaf_lists(self, numeric_map, talea_denominator):
        leaf_lists = []
        specifier = self._get_duration_specifier()
        for map_division in numeric_map:
            leaf_list = self._make_leaves_from_talea(
                map_division,
                talea_denominator,
                increase_monotonic=specifier.increase_monotonic,
                forbidden_note_duration=specifier.forbidden_note_duration,
                forbidden_rest_duration=specifier.forbidden_rest_duration,
                spell_metrically=specifier.spell_metrically,
                tag=self.tag,
                )
            leaf_lists.append(leaf_list)
        return leaf_lists

    @staticmethod
    def _make_leaves_from_talea(
        talea,
        talea_denominator,
        increase_monotonic=None,
        forbidden_note_duration=None,
        forbidden_rest_duration=None,
        spell_metrically=None,
        repeat_ties=False,
        tag: str = None,
        ):
        assert all(x != 0 for x in talea), repr(talea)
        result: typing.List[abjad.Leaf] = []
        leaf_maker = abjad.LeafMaker(
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            repeat_ties=repeat_ties,
            tag=tag,
            )
        pitches: typing.List[typing.Union[int, None]]
        for note_value in talea:
            if 0 < note_value:
                pitches = [0]
            else:
                pitches = [None]
            division = abjad.Duration(
                abs(note_value),
                talea_denominator,
                )
            if (spell_metrically is True or
                (spell_metrically == 'unassignable' and
                not abjad.mathtools.is_assignable_integer(
                    division.numerator))):
                meter = abjad.Meter(division)
                rhythm_tree_container = meter.root_node
                durations = [_.duration for _ in rhythm_tree_container]
            else:
                durations = [division]
            leaves = leaf_maker(pitches, durations)
            if (1 < len(leaves) and
                not leaves[0]._has_spanner(abjad.Tie) and
                not isinstance(leaves[0], abjad.Rest)):
                tie = abjad.Tie(repeat=repeat_ties)
                abjad.attach(tie, leaves[:])
            result.extend(leaves)
        result = abjad.select(result)
        return result

    def _make_music(self, divisions):
        input_divisions = divisions[:]
        input_ = self._prepare_input()
        end_counts = input_['end_counts']
        preamble = input_['preamble']
        talea = input_['talea']
        if talea:
            advanced_talea = Talea(
                counts=talea,
                denominator=self.talea.denominator,
                end_counts=end_counts,
                preamble=preamble,
                )
        else:
            advanced_talea = None
        extra_counts_per_division = input_['extra_counts_per_division']
        unscaled_end_counts = tuple(end_counts)
        unscaled_preamble = tuple(preamble)
        unscaled_talea = tuple(talea)
        split_divisions_by_counts = input_['split_divisions_by_counts']
        counts = {
            'end_counts': end_counts,
            'extra_counts_per_division': extra_counts_per_division,
            'preamble': preamble,
            'split_divisions_by_counts': split_divisions_by_counts,
            'talea': talea,
            }
        if self.talea is not None:
            talea_denominator = self.talea.denominator
        else:
            talea_denominator = None
        result = self._scale_counts(divisions, talea_denominator, counts)
        divisions = result['divisions']
        lcd = result['lcd']
        counts = result['counts']
        preamble = counts['preamble']
        secondary_divisions = self._make_secondary_divisions(
            divisions,
            counts['split_divisions_by_counts'],
            )
        if counts['talea']:
            numeric_map = self._make_numeric_map(
                secondary_divisions,
                counts['preamble'],
                counts['talea'],
                counts['extra_counts_per_division'],
                counts['end_counts'],
                )
            talea_weight_consumed = sum(_.weight() for _ in numeric_map)
            leaf_lists = self._make_leaf_lists(numeric_map, lcd)
            if not counts['extra_counts_per_division']:
                result = leaf_lists
            else:
                tuplets = self._make_tuplets(secondary_divisions, leaf_lists)
                result = tuplets
            selections = [abjad.select(_) for _ in result]
        else:
            talea_weight_consumed = 0
            leaf_maker = abjad.LeafMaker(tag=self.tag)
            selections = []
            for division in secondary_divisions:
                selection = leaf_maker([0], [division])
                selections.append(selection)
        #self._apply_beam_specifier(selections)
        if counts['talea']:
            self._apply_ties_to_split_notes(
                selections,
                unscaled_end_counts,
                unscaled_preamble,
                unscaled_talea,
                )
        selections = self._handle_rest_tied_notes(selections)
        selections = self._apply_division_masks(selections)
        specifier = self._get_duration_specifier()
        if specifier.rewrite_meter:
            selections = specifier._rewrite_meter_(selections, input_divisions)
        string = 'divisions_consumed'
        self.state[string] = self.previous_state.get(string, 0)
        self.state[string] += len(divisions)
        if talea and talea_weight_consumed not in advanced_talea:
            last_leaf = abjad.inspect(selections).leaf(-1)
            if isinstance(last_leaf, abjad.Note):
                self.state['incomplete_last_note'] = True
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        logical_ties_produced = len(abjad.select(selections).logical_ties())
        logical_ties_produced += previous_logical_ties_produced
        if self._previous_incomplete_last_note():
            logical_ties_produced -= 1
        self.state['logical_ties_produced'] = logical_ties_produced
        string = 'talea_weight_consumed'
        self.state[string] = self.previous_state.get(string, 0)
        self.state[string] += talea_weight_consumed
        items = self.state.items()
        state = abjad.OrderedDict(sorted(items))
        self._state = state
        return selections

    def _make_numeric_map(
        self,
        divisions,
        preamble,
        talea,
        extra_counts_per_division,
        end_counts,
        ):
        assert all(isinstance(_, int) for _ in end_counts), repr(end_counts)
        assert all(isinstance(_, int) for _ in preamble), repr(preamble)
        assert all(isinstance(_, int) for _ in talea), repr(talea)
        prolated_divisions = self._make_prolated_divisions(
            divisions,
            extra_counts_per_division,
            )
        prolated_divisions = [
            abjad.NonreducedFraction(_) for _ in prolated_divisions
            ]
        if not preamble and not talea:
            return prolated_divisions
        prolated_numerators = [_.numerator for _ in prolated_divisions]
        result = self._split_talea_extended_to_weights(
            preamble,
            talea,
            prolated_numerators,
            )
        if end_counts:
            end_counts = abjad.sequence(end_counts)
            end_weight = end_counts.weight()
            division_weights = [_.weight() for _ in result]
            counts = result.flatten()
            counts_weight = counts.weight()
            assert end_weight <= counts_weight, repr(end_counts)
            left = counts_weight - end_weight
            right = end_weight
            counts = counts.split([left, right])
            counts = counts[0] + end_counts
            assert counts.weight() == counts_weight
            result = counts.partition_by_weights(division_weights)
        for sequence in result:
            assert all(isinstance(_, int) for _ in sequence), repr(sequence)
        if self.burnish_specifier is not None:
            result = self._apply_burnish_specifier(result)
        return result

    def _make_prolated_divisions(self, divisions, extra_counts_per_division):
        prolated_divisions = []
        for i, division in enumerate(divisions):
            if not extra_counts_per_division:
                prolated_divisions.append(division)
                continue
            prolation_addendum = extra_counts_per_division[i]
            try:
                numerator = division.numerator
            except AttributeError:
                numerator = division[0]
            if 0 <= prolation_addendum:
                prolation_addendum %= numerator
            else:
                # NOTE: do not remove the following (nonfunctional) if-else;
                #       preserved for backwards compatability.
                use_old_extra_counts_logic = False
                if use_old_extra_counts_logic:
                    prolation_addendum %= numerator
                else:
                    prolation_addendum %= -numerator
            if isinstance(division, tuple):
                numerator, denominator = division
            else:
                numerator, denominator = division.pair
            prolated_division = (
                numerator + prolation_addendum,
                denominator,
                )
            prolated_divisions.append(prolated_division)
        return prolated_divisions

    def _prepare_input(self):
        talea_weight_consumed = self.previous_state.get(
            'talea_weight_consumed',
            0,
            )
        if self.talea is None:
            end_counts = ()
            preamble = ()
            talea = ()
        else:
            talea = self.talea.advance(talea_weight_consumed)
            end_counts = talea.end_counts or ()
            preamble = talea.preamble or ()
            talea = talea.counts or ()
        talea = abjad.CyclicTuple(talea)
        extra_counts_per_division = self.extra_counts_per_division or ()
        extra_counts_per_division = abjad.sequence(
            extra_counts_per_division
            )
        divisions_consumed = self.previous_state.get('divisions_consumed', 0)
        extra_counts_per_division = extra_counts_per_division.rotate(
            -divisions_consumed
            )
        extra_counts_per_division = abjad.CyclicTuple(
            extra_counts_per_division
            )
        split_divisions_by_counts = self.split_divisions_by_counts or ()
        split_divisions_by_counts = abjad.CyclicTuple(
            split_divisions_by_counts)
        return {
            'end_counts': end_counts,
            'extra_counts_per_division': extra_counts_per_division,
            'preamble': preamble,
            'split_divisions_by_counts': split_divisions_by_counts,
            'talea': talea,
            }

    def _split_talea_extended_to_weights(self, preamble, talea, weights):
        assert abjad.mathtools.all_are_positive_integers(weights)
        preamble_weight = abjad.mathtools.weight(preamble)
        talea_weight = abjad.mathtools.weight(talea)
        weight = abjad.mathtools.weight(weights)
        if (self.read_talea_once_only and
            preamble_weight + talea_weight < weight):
            message = f'{preamble!s} + {talea!s} is too short'
            message += f' to read {weights} once.'
            raise Exception(message)
        if weight <= preamble_weight:
            talea = abjad.sequence(preamble)
            talea = talea.truncate(weight=weight)
        else:
            weight -= preamble_weight
            talea = abjad.sequence(talea).repeat_to_weight(weight)
            talea = preamble + talea
        talea = talea.split(weights, cyclic=True)
        return talea

    ### PUBLIC PROPERTIES ###

    @property
    def beam_specifier(self) -> typing.Optional[BeamSpecifier]:
        r"""
        Gets beam specifier.

        ..  container:: example

            Beams each division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                >>

        ..  container:: example

            Beams divisions together:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 2
                        c'16
                        [
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 1
                        c'16
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 1
                        c'16
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 1
                        c'16
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 0
                        c'16
                        ]
                    }
                >>

        ..  container:: example

            Beams nothing:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=False,
            ...         beam_divisions_together=False,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                    }
                >>

        ..  container:: example

            Does not beam rests:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, -1],
            ...         denominator=16,
            ...         ),
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                        c'16
                        [
                        c'16
                        ]
                        c'16
                        r16
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                        c'16
                        [
                        c'16
                        ]
                        c'16
                        r16
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                    }
                >>

        ..  container:: example

            Does beam rests:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, -1],
            ...         denominator=16,
            ...         ),
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         beam_rests=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        r16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        r16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        c'16
                        c'16
                        r16
                        ]
                    }
                >>

        ..  container:: example

            Beams rests with stemlets:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, -1],
            ...         denominator=16,
            ...         ),
            ...     beam_specifier=abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...         beam_rests=True,
            ...         stemlet_length=0.75,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \override RhythmicStaff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        \revert RhythmicStaff.Stem.stemlet-length
                        c'16
                        ]
                        \override RhythmicStaff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        r16
                        c'16
                        \revert RhythmicStaff.Stem.stemlet-length
                        c'16
                        ]
                        \override RhythmicStaff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        \revert RhythmicStaff.Stem.stemlet-length
                        r16
                        ]
                        \override RhythmicStaff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        c'16
                        c'16
                        \revert RhythmicStaff.Stem.stemlet-length
                        r16
                        ]
                    }
                >>

        """
        return super(TaleaRhythmMaker, self).beam_specifier

    @property
    def burnish_specifier(self) -> typing.Optional[BurnishSpecifier]:
        r"""
        Gets burnish specifier.

        ..  container:: example

            Forces the first leaf and the last two leaves to be rests:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[1],
            ...         right_classes=[abjad.Rest],
            ...         right_counts=[2],
            ...         outer_divisions_only=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        ]
                        r8.
                        r8
                    }
                >>

        ..  container:: example

            Forces the first leaf of every division to be a rest:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[1],
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        r4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        r8
                        c'4
                        r16
                        c'8
                        [
                        c'8.
                        c'8
                        ]
                    }
                >>

        """
        return self._burnish_specifier

    @property
    def division_masks(self) -> typing.Optional[abjad.PatternTuple]:
        r"""
        Gets division masks.

        ..  container:: example

            No division masks:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        c'8.
                        c'8
                        ]
                    }
                >>

        ..  container:: example

            Silences every other output division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     division_masks=[
            ...         abjadext.rmakers.SilenceMask(
            ...             pattern=abjad.index([1], 2),
            ...             ),
            ...         ],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        r2
                        c'8
                        c'4
                        r2
                    }
                >>

        ..  container:: example

            Sustains every other output division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     division_masks=[
            ...         abjadext.rmakers.sustain([1], 2),
            ...         ],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'2
                        c'8
                        c'4
                        c'2
                    }
                >>

        ..  container:: example

            Silences every other secondary output division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     split_divisions_by_counts=[9],
            ...     division_masks=[
            ...         abjadext.rmakers.SilenceMask(
            ...             pattern=abjad.index([1], 2),
            ...             ),
            ...         ],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        r8.
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        r4
                        c'16
                        [
                        c'16
                        ]
                        r4..
                        c'16
                    }
                >>

        ..  container:: example

            Sustains every other secondary output division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     split_divisions_by_counts=[9],
            ...     division_masks=[
            ...         abjadext.rmakers.sustain([1], 2),
            ...         ],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'8.
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'4
                        c'16
                        [
                        c'16
                        ]
                        c'4..
                        c'16
                    }
                >>

        ..  container:: example

            REGRESSION. Nonperiodic division masks respect state.

            Only divisions 0 and 2 are masked here:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, 1, 2],
            ...     division_masks=[abjadext.rmakers.silence([0, 2, 7])],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[4],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        r4.
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                        }
                        r4.
                        c'16
                        c'4
                        c'8.
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 4),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 8),
                    ('talea_weight_consumed', 31),
                    ]
                )

            Only division 7 is masked here:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions, previous_state=state)
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            c'4
                            c'8
                            ~
                        }
                        \times 4/5 {
                            c'8
                            c'4
                            c'4
                        }
                        c'4
                        c'8
                        r2
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 8),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 15),
                    ('talea_weight_consumed', 63),
                    ]
                )

        ..  container:: example

            REGRESSION. Periodic division masks also respect state.

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, 1, 2],
            ...     division_masks=[abjadext.rmakers.silence([2], period=3)],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[4],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                        }
                        r4.
                        c'16
                        c'4
                        c'8.
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 4),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 8),
                    ('talea_weight_consumed', 31),
                    ]
                )

            Incomplete first note is masked here:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions, previous_state=state)
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            c'4
                            c'8
                        }
                        r2
                        c'4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                        }
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 8),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 15),
                    ('talea_weight_consumed', 63),
                    ]
                )

        """
        return super(TaleaRhythmMaker, self).division_masks

    @property
    def duration_specifier(self) -> typing.Optional[DurationSpecifier]:
        r"""
        Gets duration specifier.

        Several duration specifier configurations are available.

        ..  container:: example

            Spells nonassignable durations with monontonically decreasing
            durations:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5],
            ...         denominator=16,
            ...         ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         increase_monotonic=False,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (5, 8), (5, 8)]
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
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                    }
                >>

        ..  container:: example

            Spells nonassignable durations with monontonically increasing
            durations:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5],
            ...         denominator=16,
            ...         ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         increase_monotonic=True,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (5, 8), (5, 8)]
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
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                    }
                >>

        ..  container:: example

            Forbids no durations:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, 1, 4, 4],
            ...         denominator=16,
            ...         ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_note_duration=None,
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
                        c'4
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        c'4
                        c'4
                    }
                >>

        ..  container:: example

            Forbids durations equal to ``1/4`` or greater:

                >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
                ...     talea=abjadext.rmakers.Talea(
                ...         counts=[1, 1, 1, 1, 4, 4],
                ...         denominator=16,
                ...         ),
                ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
                ...         forbidden_note_duration=(1, 4),
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
                        c'8
                        ~
                        c'8
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'8
                        ~
                        c'8
                        c'8
                        ~
                        c'8
                        ]
                    }
                >>

            Rewrites forbidden durations with smaller durations tied together.

        ..  container:: example

            Spells all durations metrically:

                >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
                ...     talea=abjadext.rmakers.Talea(
                ...         counts=[5, 4],
                ...         denominator=16,
                ...         ),
                ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
                ...         spell_metrically=True,
                ...         ),
                ...     )

            >>> divisions = [(3, 4), (3, 4), (3, 4)]
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
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'8.
                        ~
                        [
                        c'8
                        ]
                        c'4
                        c'16
                        ~
                        [
                        c'16
                        ~
                        c'16
                        ~
                        ]
                        c'8
                        c'4
                        c'8.
                        ~
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'16
                        ~
                        [
                        c'16
                        ~
                        c'16
                        c'8.
                        ~
                        c'8
                        ]
                        c'4
                    }
                >>

        ..  container:: example

            Spells unassignable durations metrically:

                >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
                ...     talea=abjadext.rmakers.Talea(
                ...         counts=[5, 4],
                ...         denominator=16,
                ...         ),
                ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
                ...         spell_metrically='unassignable',
                ...         ),
                ...     )

            >>> divisions = [(3, 4), (3, 4), (3, 4)]
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
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'8.
                        ~
                        [
                        c'8
                        ]
                        c'4
                        c'8.
                        ~
                        c'8
                        c'4
                        c'8.
                        ~
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8.
                        [
                        c'8.
                        ~
                        c'8
                        ]
                        c'4
                    }
                >>

        ..  container:: example

            Rewrites meter:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, 4],
            ...         denominator=16,
            ...         ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         rewrite_meter=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4), (3, 4)]
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
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ~
                        c'16
                        c'8.
                        ~
                        ]
                        c'8
                        [
                        c'8
                        ~
                        c'8
                        c'8
                        ~
                        c'8.
                        c'16
                        ~
                        ]
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
        return super(TaleaRhythmMaker, self).duration_specifier

    @property
    def extra_counts_per_division(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets extra counts per division.

        ..  container:: example

            No extra counts per division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        c'8.
                        c'8
                        ]
                    }
                >>

        ..  container:: example

            Adds one extra count to every other division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     extra_counts_per_division=[0, 1],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            [
                            c'8
                            c'8.
                            ]
                        }
                        \times 8/9 {
                            c'4
                            c'16
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            c'4
                            c'16
                        }
                        \times 8/9 {
                            c'8
                            [
                            c'8.
                            ]
                            c'4
                        }
                    }
                >>

        ..  container:: example

            Adds two extra counts to every other division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     extra_counts_per_division=[0, 2],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            [
                            c'8
                            c'8.
                            ]
                        }
                        \times 4/5 {
                            c'4
                            c'16
                            [
                            c'8
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'16
                            [
                            c'16
                            ~
                            ]
                        }
                        \times 4/5 {
                            c'16
                            [
                            c'8.
                            ]
                            c'4
                            c'16
                            [
                            c'16
                            ]
                        }
                    }
                >>

            The duration of each added count equals the duration
            of each count in the rhythm-maker's input talea.

        ..  container:: example

            Removes one count from every other division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     extra_counts_per_division=[0, -1],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            [
                            c'8
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 8/7 {
                            c'4
                            c'16
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 8/7 {
                            c'16
                            [
                            c'16
                            c'8
                            c'8.
                            ]
                        }
                    }
                >>

        """
        if self._extra_counts_per_division:
            return list(self._extra_counts_per_division)
        else:
            return None

    @property
    def logical_tie_masks(self) -> typing.Optional[abjad.PatternTuple]:
        r"""
        Gets logical tie masks.

        ..  container:: example

            Silences every third logical tie:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     logical_tie_masks=[
            ...         abjadext.rmakers.silence([2], 3),
            ...         ],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        ]
                        r8.
                        c'4
                        c'16
                        r16
                        r16
                        c'8.
                        [
                        c'8
                        ~
                        ]
                        c'8
                        r16
                        c'8
                        [
                        c'16
                        ]
                    }
                >>

            Silences the first and last logical ties:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     logical_tie_masks=[
            ...         abjadext.rmakers.silence([0]),
            ...         abjadext.rmakers.silence([-1]),
            ...         ],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'16
                        ~
                        ]
                        c'16
                        [
                        c'8.
                        c'8
                        ~
                        ]
                        c'8
                        [
                        c'16
                        c'8
                        ]
                        r16
                    }
                >>

        ..  container:: example

            REGRESSION. Nonperiodic logical tie masks respect state.

            Only logical ties 0 and 2 are masked here:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, 1, 2],
            ...     logical_tie_masks=[abjadext.rmakers.silence([0, 2, 12])],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[4],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        r4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            r4
                            c'8.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'16
                            c'4
                            c'8.
                            ~
                        }
                        c'16
                        c'4
                        c'8.
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 4),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 8),
                    ('talea_weight_consumed', 31),
                    ]
                )

            Only logical tie 12 is masked here:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions, previous_state=state)
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            c'4
                            c'8
                            ~
                        }
                        \times 4/5 {
                            c'8
                            c'4
                            c'4
                        }
                        r4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                        }
                    }
                >>
            
            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 8),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 16),
                    ('talea_weight_consumed', 63),
                    ]
                )

        ..  container:: example

            REGRESSION. Periodic logical tie masks also respect state.

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, 1, 2],
            ...     logical_tie_masks=[
            ...         abjadext.rmakers.silence([3], period=4),
            ...     ],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[4],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     )

            Incomplete last note is masked here:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            r16
                            c'4
                            c'8.
                            ~
                        }
                        c'16
                        c'4
                        r8.
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 4),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 8),
                    ('talea_weight_consumed', 31),
                    ]
                )

            Incomplete first note is masked here:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions, previous_state=state)
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            r16
                            c'4
                            c'8
                            ~
                        }
                        \times 4/5 {
                            c'8
                            c'4
                            r4
                        }
                        c'4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            r8.
                        }
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 8),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 16),
                    ('talea_weight_consumed', 63),
                    ]
                )

        """
        return super(TaleaRhythmMaker, self).logical_tie_masks

    @property
    def read_talea_once_only(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker should read talea once only.

        ..  container:: example

            Reads talea cyclically:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'16
                        ~
                        ]
                        c'16
                        [
                        c'8.
                        c'8
                        ~
                        ]
                        c'8
                        [
                        c'16
                        c'8
                        c'16
                        ]
                    }
                >>

        ..  container:: example

            Reads talea once only:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     read_talea_once_only=True,
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            Calling rhythm_maker on these divisions raises an exception because talea
            is too short to read once only:

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> rhythm_maker(divisions)
            Traceback (most recent call last):
                ...
            Exception: () + (1, 2, 3, 4) is too short to read [6, 6, 6, 6] once.

        Set to true to ensure talea is long enough to cover all divisions
        without repeating.

        Provides way of using talea noncyclically when, for example,
        interpolating from short durations to long durations.
        """
        return self._read_talea_once_only

    @property
    def rest_tied_notes(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker should leave the head of each logical
        tie but change tied notes to rests and remove ties.

        ..  container:: example

            Does not rest tied notes:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'16
                        ~
                        ]
                        c'16
                        [
                        c'8.
                        c'8
                        ~
                        ]
                        c'8
                        [
                        c'16
                        c'8
                        c'16
                        ]
                    }
                >>

        ..  container:: example

            Rests tied notes:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     rest_tied_notes=True,
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'16
                        ]
                        r16
                        c'8.
                        [
                        c'8
                        ]
                        r8
                        c'16
                        [
                        c'8
                        c'16
                        ]
                    }
                >>

        """
        return self._rest_tied_notes

    # TODO: remove
    @property
    def split_divisions_by_counts(self) -> typing.Optional[
        typing.Tuple[int, ...]
        ]:
        r"""
        Gets secondary divisions.

        ..  note:: Deprecated. Preprocess divisions by hand instead.

        Secondary divisions impose a cyclic split operation on divisions.

        ..  container:: example

            Here's a talea equal to two thirty-second notes repeating
            indefinitely. Output equals four divisions of 12 thirty-second
            notes each:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[2],
            ...         denominator=32,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                >>

        ..  container:: example

            Here's the same talea with secondary divisions set to split the
            divisions every 17 thirty-second notes. The rhythm_maker makes six
            divisions with durations equal, respectively, to 12, 5, 7, 10, 2
            and 12 thirty-second notes.

            Note that ``12 + 5 = 17`` and ``7 + 10 = 17``:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[2],
            ...         denominator=32,
            ...         ),
            ...     split_divisions_by_counts=[17],
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'32
                        ~
                        ]
                        c'32
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                >>

            Additional divisions created when using
            ``split_divisions_by_counts`` are subject to
            ``extra_counts_per_division`` just like other divisions.

        ..  container:: example

            This example adds one extra thirty-second note to every other
            division. The durations of the divisions remain the same as in the
            previous example. But now every other division is tupletted:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[2],
            ...         denominator=32,
            ...         ),
            ...     split_divisions_by_counts=[17],
            ...     extra_counts_per_division=[0, 1],
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            [
                            c'16
                            c'16
                            c'32
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 10/11 {
                            c'32
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/13 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'32
                            ]
                        }
                    }
                >>

        """
        return self._split_divisions_by_counts

    @property
    def state(self) -> abjad.OrderedDict:
        r"""
        Gets state dictionary.

        ..  container:: example

            Consumes 4 divisions and 31 counts:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, 1, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[4],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'16
                            c'4
                            c'8.
                            ~
                        }
                        c'16
                        c'4
                        c'8.
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 4),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 8),
                    ('talea_weight_consumed', 31),
                    ]
                )

            Advances 4 divisions and 31 counts; then consumes another 4
            divisions and 31 counts:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions, previous_state=state)
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            c'4
                            c'8
                            ~
                        }
                        \times 4/5 {
                            c'8
                            c'4
                            c'4
                        }
                        c'4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                        }
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 8),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 16),
                    ('talea_weight_consumed', 63),
                    ]
                )

            Advances 8 divisions and 62 counts; then consumes 4 divisions and
            31 counts:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions, previous_state=state)
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'16
                            c'4
                            c'8.
                            ~
                        }
                        c'16
                        c'4
                        c'8.
                        ~
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            c'4
                            c'8
                            ~
                        }
                        \times 4/5 {
                            c'8
                            c'4
                            c'4
                        }
                    }
                >>

            >>> state = rhythm_maker.state
            >>> abjad.f(state)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 12),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 24),
                    ('talea_weight_consumed', 96),
                    ]
                )


        """
        return super(TaleaRhythmMaker, self).state


    @property
    def tag(self) -> typing.Optional[str]:
        r"""
        Gets tag.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     tag='TALEA_RHYTHM_MAKER',
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     extra_counts_per_division=[0, 1],
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> abjad.f(lilypond_file[abjad.Score], strict=30)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text %! TALEA_RHYTHM_MAKER
                    \times 1/1 {          %! TALEA_RHYTHM_MAKER
                        c'16              %! TALEA_RHYTHM_MAKER
                        [                 %! TALEA_RHYTHM_MAKER
                        c'8               %! TALEA_RHYTHM_MAKER
                        c'8.              %! TALEA_RHYTHM_MAKER
                        ]                 %! TALEA_RHYTHM_MAKER
                    }                     %! TALEA_RHYTHM_MAKER
                    \times 8/9 {          %! TALEA_RHYTHM_MAKER
                        c'4               %! TALEA_RHYTHM_MAKER
                        c'16              %! TALEA_RHYTHM_MAKER
                        [                 %! TALEA_RHYTHM_MAKER
                        c'8               %! TALEA_RHYTHM_MAKER
                        c'8               %! TALEA_RHYTHM_MAKER
                        ~
                        ]                 %! TALEA_RHYTHM_MAKER
                    }                     %! TALEA_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! TALEA_RHYTHM_MAKER
                    \times 1/1 {          %! TALEA_RHYTHM_MAKER
                        c'16              %! TALEA_RHYTHM_MAKER
                        c'4               %! TALEA_RHYTHM_MAKER
                        c'16              %! TALEA_RHYTHM_MAKER
                    }                     %! TALEA_RHYTHM_MAKER
                    \times 8/9 {          %! TALEA_RHYTHM_MAKER
                        c'8               %! TALEA_RHYTHM_MAKER
                        [                 %! TALEA_RHYTHM_MAKER
                        c'8.              %! TALEA_RHYTHM_MAKER
                        ]                 %! TALEA_RHYTHM_MAKER
                        c'4               %! TALEA_RHYTHM_MAKER
                    }                     %! TALEA_RHYTHM_MAKER
                }
            >>

        """
        return super().tag

    @property
    def talea(self) -> typing.Optional[Talea]:
        r"""
        Gets talea.

        ..  container:: example

            No talea:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker()

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4.
                        c'4.
                        c'4.
                        c'4.
                    }
                >>

        ..  container:: example

            Working with ``preamble``.

            Preamble less than total duration:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[8, -4, 8],
            ...         denominator=32,
            ...         preamble=[1, 1, 1, 1],
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'32
                        [
                        c'32
                        c'32
                        c'32
                        ]
                        c'4
                        r8
                        c'4
                        c'8
                        ~
                        c'8
                        r8
                        c'8
                        ~
                        c'8
                        c'4
                        r8
                    }
                >>

            Preamble more than total duration; ignores counts:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[8, -4, 8],
            ...         denominator=32,
            ...         preamble=[32, 32, 32, 32],
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'4.
                        ~
                        c'2
                        ~
                        c'8
                        c'4
                        ~
                        c'2
                    }
                >>

        ..  container:: example

            Working with ``end_counts``.

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[8, -4, 8],
            ...         denominator=32,
            ...         end_counts=[1, 1, 1, 1],
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        r8
                        c'4
                        c'4
                        r8
                        c'4
                        c'4
                        r8
                        c'32
                        [
                        c'32
                        c'32
                        c'32
                        ]
                    }
                >>

        ..  container:: example

            REGRESSION. End counts leave 5-durated tie in tact:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[6],
            ...         denominator=16,
            ...         end_counts=[1],
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4.
                        c'4
                        ~
                        c'16
                        [
                        c'16
                        ]
                    }
                >>

        """
        return self._talea

    @property
    def tie_specifier(self) -> typing.Optional[TieSpecifier]:
        r"""
        Gets tie specifier.

        ..  container:: example

            Does not tie across divisions:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, 3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                    }
                >>

        ..  container:: example

            Ties across divisions:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, 3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ~
                        ]
                        c'8.
                        [
                        c'8.
                        ~
                        ]
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ~
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                    }
                >>

        ..  container:: example

            Patterns ties across divisions:

            >>> pattern = abjad.Pattern(
            ...     indices=[0],
            ...     period=2,
            ...     )
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, 3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=pattern,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ~
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ~
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                    }
                >>

        ..  container:: example

            Uses repeat ties:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, 3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         repeat_ties=True,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        c'16
                        \repeatTie
                        [
                        c'8.
                        ]
                        c'8.
                        \repeatTie
                        [
                        c'8.
                        ]
                        c'4
                        \repeatTie
                        c'16
                        \repeatTie
                        [
                        c'8.
                        ]
                        c'8.
                        \repeatTie
                        [
                        c'8.
                        ]
                    }
                >>

        ..  container:: example

            Ties consecutive notes:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, -3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_consecutive_notes=True,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'16
                        r8.
                        c'8.
                        ~
                        [
                        c'8.
                        ~
                        ]
                        c'4
                        ~
                        c'16
                        r8.
                        c'8.
                        ~
                        [
                        c'8.
                        ]
                    }
                >>

        """
        return super(TaleaRhythmMaker, self).tie_specifier

    @property
    def tie_split_notes(self) -> typing.Optional[bool]:
        r"""
        Is true when talea rhythm-maker should tie split notes.

        ..  todo:: Add examples.

        """
        return self._tie_split_notes

    @property
    def tuplet_specifier(self) -> typing.Optional[TupletSpecifier]:
        r"""
        Gets tuplet specifier.

        ..  container:: example

            Working with ``denominator``.

            Reduces terms in tuplet ratio to relative primes when no tuplet
            specifier is given:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[1, 1, 2, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            [
                            c'8
                            c'8.
                            c'16
                            ~
                            ]
                        }
                        \times 8/9 {
                            c'8.
                            [
                            c'16
                            c'8
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ~
                            ]
                        }
                        \times 4/5 {
                            c'8
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ]
                        }
                    }
                >>

            REGRESSION. Spells tuplet denominator in terms of duration when
            denominator is given as a duration:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[1, 1, 2, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         denominator=(1, 16),
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            [
                            c'8
                            c'8.
                            c'16
                            ~
                            ]
                        }
                        \times 8/9 {
                            c'8.
                            [
                            c'16
                            c'8
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/8 {
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ~
                            ]
                        }
                        \times 8/10 {
                            c'8
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Working with ``diminution``.
            
            Makes diminished tuplets when ``diminution`` is true (or when no
            tuplet specifier is given):

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, -1],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     )

            >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
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
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            Makes augmented tuplets when ``diminution`` is set to false:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, -1],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         diminution=False,
            ...         extract_trivial=True,
            ...         ),
            ...     )

            >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
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
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Working with ``trivialize``.

            Leaves trivializable tuplets as-is when no tuplet specifier is
            given. The tuplets in measures 2 and 4 can be written as trivial
            tuplets, but they are not:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, 4],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, 6, 6],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \times 2/3 {
                            c'4.
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \times 2/3 {
                            c'4.
                            c'4.
                        }
                    }
                >>

            Rewrites trivializable tuplets as trivial (1:1) tuplets when
            ``trivialize`` is true:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, 4],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, 6, 6],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         trivialize=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'4
                        }
                    }
                >>

            REGRESSION #907a. Rewrites trivializable tuplets even when
            tuplets contain multiple ties:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, 4],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, 6, 6],
            ...         denominator=16,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         trivialize=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'4
                        }
                    }
                >>

            REGRESSION #907b. Rewrites trivializable tuplets even when
            tuplets contain very long ties:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[0, 4],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, 6, 6],
            ...         denominator=16,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         tie_consecutive_notes=True,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         trivialize=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            ~
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            ~
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            ~
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            ~
                            c'4
                        }
                    }
                >>

        ..  container:: example

            Working with ``rewrite_rest_filled``.

            Makes rest-filled tuplets when ``rewrite_rest_filled`` is false (or
            when no tuplet specifier is given):

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[1, 0],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, -6, -6],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'8.
                            [
                            c'8.
                            ]
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r4
                            r16
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            r8.
                            c'8.
                            [
                            c'16
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            r4.
                        }
                    }
                >>

            Rewrites rest-filled tuplets when ``rewrite_rest_filled`` is true:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[1, 0],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, -6, -6],
            ...         denominator=16,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_rest_filled=True,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
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
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'8.
                            [
                            c'8.
                            ]
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r2
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            r8.
                            c'8.
                            [
                            c'16
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            r4.
                        }
                    }
                >>

        """
        return super(TaleaRhythmMaker, self).tuplet_specifier
