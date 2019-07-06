import abjad
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier
from .BurnishSpecifier import BurnishSpecifier
from .DurationSpecifier import DurationSpecifier
from .RhythmMaker import RhythmMaker
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask
from .Talea import Talea
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier


class TaleaRhythmMaker(RhythmMaker):
    r"""
    Talea rhythm-maker.

    ..  container:: example

        Repeats talea of 1/16, 2/16, 3/16, 4/16:

        >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
        ...     abjadext.rmakers.BeamSpecifier(
        ...         selector=abjad.select().tuplets(),
        ...     ),
        ...     abjadext.rmakers.TupletSpecifier(
        ...         extract_trivial=True,
        ...     ),
        ...     talea=abjadext.rmakers.Talea(
        ...         counts=[1, 2, 3, 4],
        ...         denominator=16,
        ...         ),
        ...     )

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selection = rhythm_maker(divisions)
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

    __documentation_section__ = "Rhythm-makers"

    __slots__ = (
        "_burnish_specifier",
        "_curtail_ties",
        "_extra_counts_per_division",
        "_read_talea_once_only",
        "_talea",
    )

    ### INITIALIZER ###

    def __init__(
        self,
        *specifiers: typings.SpecifierTyping,
        burnish_specifier: BurnishSpecifier = None,
        curtail_ties: bool = None,
        divisions: abjad.Expression = None,
        duration_specifier: DurationSpecifier = None,
        extra_counts_per_division: abjad.IntegerSequence = None,
        read_talea_once_only: bool = None,
        tag: str = None,
        talea: Talea = Talea(counts=[1], denominator=16),
    ) -> None:
        RhythmMaker.__init__(
            self,
            *specifiers,
            divisions=divisions,
            duration_specifier=duration_specifier,
            tag=tag,
        )
        if talea is not None:
            assert isinstance(talea, Talea), repr(talea)
        self._talea = talea
        if burnish_specifier is not None:
            assert isinstance(burnish_specifier, BurnishSpecifier)
        self._burnish_specifier = burnish_specifier
        if curtail_ties is not None:
            curtail_ties = bool(curtail_ties)
        self._curtail_ties = curtail_ties
        if extra_counts_per_division is not None:
            assert abjad.mathtools.all_are_integer_equivalent_numbers(
                extra_counts_per_division
            )
        self._extra_counts_per_division = extra_counts_per_division
        if read_talea_once_only is not None:
            read_talea_once_only = bool(read_talea_once_only)
        self._read_talea_once_only = read_talea_once_only

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.Sequence[abjad.IntegerPair],
        previous_state: abjad.OrderedDict = None,
    ) -> abjad.Selection:
        """
        Calls talea rhythm-maker on ``divisions``.

        ..  container:: example

                >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
                ...     abjadext.rmakers.BeamSpecifier(
                ...         selector=abjad.select().tuplets(),
                ...     ),
                ...     talea=abjadext.rmakers.Talea(
                ...         counts=[1, 2, 3, 4],
                ...         denominator=16,
                ...         ),
                ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> for tuplet in selection:
            ...     tuplet
            Tuplet(Multiplier(1, 1), "c'16 c'8 c'8.")
            Tuplet(Multiplier(1, 1), "c'4 c'16 c'8 c'16")
            Tuplet(Multiplier(1, 1), "c'8 c'4")
            Tuplet(Multiplier(1, 1), "c'16 c'8 c'8. c'8")

        """
        return RhythmMaker.__call__(
            self, divisions, previous_state=previous_state
        )

    def __format__(self, format_specification="") -> str:
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

        ..  container:: example

            REGRESSION. Specifiers appear in storage format:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, -3, 3, 3],
            ...         denominator=16,
            ...     ),
            ... )
            >>> abjad.f(rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                BeamSpecifier(selector=abjad.select().tuplets()),
                TupletSpecifier(extract_trivial=True),
                talea=abjadext.rmakers.Talea(
                    counts=[5, -3, 3, 3],
                    denominator=16,
                    ),
                )

        """
        return super().__format__(format_specification=format_specification)

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

        """
        return super().__repr__()

    ### PRIVATE METHODS ###

    def _apply_burnish_specifier(self, divisions):
        burnish_specifier = self._get_burnish_specifier()
        return burnish_specifier(divisions)

    def _apply_ties_to_split_notes(
        self, tuplets, unscaled_end_counts, unscaled_preamble, unscaled_talea
    ):
        leaves = abjad.select(tuplets).leaves()
        written_durations = [leaf.written_duration for leaf in leaves]
        written_durations = abjad.sequence(written_durations)
        total_duration = written_durations.weight()
        preamble_weights = []
        if unscaled_preamble:
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
        for i, part in enumerate(parts):
            if any(isinstance(_, abjad.Rest) for _ in part):
                continue
            # part = abjad.select(part)
            if len(part) == 1:
                continue
            if self.curtail_ties:
                # this appears to be an ancient accidental constraint
                # induced by the way tie spanners used to attach:
                abjad.tie(part[-2:])
            else:
                abjad.tie(part)
        # TODO: this will need to be generalized and better tested:
        if unscaled_end_counts:
            total = len(unscaled_end_counts)
            end_leaves = leaves[-total:]
            for leaf in reversed(end_leaves):
                previous_leaf = abjad.inspect(leaf).leaf(-1)
                if previous_leaf is not None:
                    abjad.detach(abjad.TieIndicator, previous_leaf)

    def _get_burnish_specifier(self):
        if self.burnish_specifier is not None:
            return self.burnish_specifier
        return BurnishSpecifier()

    def _get_talea(self):
        if self.talea is not None:
            return self.talea
        return Talea()

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
            division = abjad.Duration(abs(note_value), talea_denominator)
            durations = [division]
            leaves = leaf_maker(pitches, durations)
            if (
                1 < len(leaves)
                and abjad.inspect(leaves[0]).logical_tie().is_trivial
                and not isinstance(leaves[0], abjad.Rest)
            ):
                abjad.tie(leaves, repeat=repeat_ties)
            result.extend(leaves)
        result = abjad.select(result)
        return result

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        input_divisions = divisions[:]
        input_ = self._prepare_input()
        end_counts = input_["end_counts"]
        preamble = input_["preamble"]
        talea = input_["talea"]
        advanced_talea = Talea(
            counts=talea,
            denominator=self.talea.denominator,
            end_counts=end_counts,
            preamble=preamble,
        )
        extra_counts_per_division = input_["extra_counts_per_division"]
        unscaled_end_counts = tuple(end_counts)
        unscaled_preamble = tuple(preamble)
        unscaled_talea = tuple(talea)
        counts = {
            "end_counts": end_counts,
            "extra_counts_per_division": extra_counts_per_division,
            "preamble": preamble,
            "talea": talea,
        }
        talea_denominator = None
        if self.talea is not None:
            talea_denominator = self.talea.denominator
        result = self._scale_counts(divisions, talea_denominator, counts)
        divisions = result["divisions"]
        lcd = result["lcd"]
        counts = result["counts"]
        preamble = counts["preamble"]
        if counts["talea"]:
            numeric_map = self._make_numeric_map(
                divisions,
                counts["preamble"],
                counts["talea"],
                counts["extra_counts_per_division"],
                counts["end_counts"],
            )
            talea_weight_consumed = sum(_.weight() for _ in numeric_map)
            leaf_lists = self._make_leaf_lists(numeric_map, lcd)
            if not counts["extra_counts_per_division"]:
                tuplets = [abjad.Tuplet(1, _) for _ in leaf_lists]
            else:
                tuplets = self._make_tuplets(divisions, leaf_lists)
        else:
            talea_weight_consumed = 0
            leaf_maker = abjad.LeafMaker(tag=self.tag)
            selections = []
            for division in divisions:
                selection = leaf_maker([0], [division])
                selections.append(selection)
            tuplets = self._make_tuplets(divisions, selections)
        if counts["talea"]:
            self._apply_ties_to_split_notes(
                tuplets, unscaled_end_counts, unscaled_preamble, unscaled_talea
            )
        if talea_weight_consumed not in advanced_talea:
            last_leaf = abjad.inspect(tuplets).leaf(-1)
            if isinstance(last_leaf, abjad.Note):
                self.state["incomplete_last_note"] = True
        string = "talea_weight_consumed"
        self.state[string] = self.previous_state.get(string, 0)
        self.state[string] += talea_weight_consumed
        return tuplets

    def _make_numeric_map(
        self, divisions, preamble, talea, extra_counts_per_division, end_counts
    ):
        assert all(isinstance(_, int) for _ in end_counts), repr(end_counts)
        assert all(isinstance(_, int) for _ in preamble), repr(preamble)
        assert all(isinstance(_, int) for _ in talea), repr(talea)
        prolated_divisions = self._make_prolated_divisions(
            divisions, extra_counts_per_division
        )
        prolated_divisions = [
            abjad.NonreducedFraction(_) for _ in prolated_divisions
        ]
        if not preamble and not talea:
            return prolated_divisions
        prolated_numerators = [_.numerator for _ in prolated_divisions]
        result = self._split_talea_extended_to_weights(
            preamble, talea, prolated_numerators
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
            prolated_division = (numerator + prolation_addendum, denominator)
            prolated_divisions.append(prolated_division)
        return prolated_divisions

    def _prepare_input(self):
        talea_weight_consumed = self.previous_state.get(
            "talea_weight_consumed", 0
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
        extra_counts_per_division = abjad.sequence(extra_counts_per_division)
        divisions_consumed = self.previous_state.get("divisions_consumed", 0)
        extra_counts_per_division = extra_counts_per_division.rotate(
            -divisions_consumed
        )
        extra_counts_per_division = abjad.CyclicTuple(
            extra_counts_per_division
        )
        return {
            "end_counts": end_counts,
            "extra_counts_per_division": extra_counts_per_division,
            "preamble": preamble,
            "talea": talea,
        }

    def _split_talea_extended_to_weights(self, preamble, talea, weights):
        assert abjad.mathtools.all_are_positive_integers(weights)
        preamble_weight = abjad.mathtools.weight(preamble)
        talea_weight = abjad.mathtools.weight(talea)
        weight = abjad.mathtools.weight(weights)
        if (
            self.read_talea_once_only
            and preamble_weight + talea_weight < weight
        ):
            message = f"{preamble!s} + {talea!s} is too short"
            message += f" to read {weights} once."
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
    def burnish_specifier(self) -> typing.Optional[BurnishSpecifier]:
        r"""
        Gets burnish specifier.

        ..  container:: example

            Forces the first leaf and the last two leaves to be rests:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[1],
            ...         right_classes=[abjad.Rest],
            ...         right_counts=[2],
            ...         outer_divisions_only=True,
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[1],
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
    def curtail_ties(self) -> typing.Optional[bool]:
        """
        Deprecated: included only for backwards compatibility.
        """
        return self._curtail_ties

    @property
    def duration_specifier(self) -> typing.Optional[DurationSpecifier]:
        r"""
        Gets duration specifier.

        Several duration specifier configurations are available.

        ..  container:: example

            Spells nonassignable durations with monontonically decreasing
            durations:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         increase_monotonic=False,
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (5, 8), (5, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         increase_monotonic=True,
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(5, 8), (5, 8), (5, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_note_duration=None,
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, 1, 4, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_note_duration=(1, 4),
            ...         ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, 1, 4, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4)]
            >>> selection = rhythm_maker(divisions)
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

            Rewrites meter:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.RewriteMeterCommand(),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 4), (3, 4), (3, 4)]
            >>> selection = rhythm_maker(divisions)
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
                        [ %! rmakers.RewriteMeterCommand.__call__
                        c'8.
                        ~
                        ] %! rmakers.RewriteMeterCommand.__call__
                        c'16
                        [ %! rmakers.RewriteMeterCommand.__call__
                        c'8.
                        ~
                        ] %! rmakers.RewriteMeterCommand.__call__
                        c'8
                        [ %! rmakers.RewriteMeterCommand.__call__
                        c'8
                        ~
                        ] %! rmakers.RewriteMeterCommand.__call__
                        c'8
                        [ %! rmakers.RewriteMeterCommand.__call__
                        c'8
                        ~
                        ] %! rmakers.RewriteMeterCommand.__call__
                        c'8.
                        [ %! rmakers.RewriteMeterCommand.__call__
                        c'16
                        ~
                        ] %! rmakers.RewriteMeterCommand.__call__
                        c'8.
                        [ %! rmakers.RewriteMeterCommand.__call__
                        c'16
                        ~
                        ] %! rmakers.RewriteMeterCommand.__call__
                        c'4
                        c'4
                    }
                >>

        """
        return super().duration_specifier

    @property
    def extra_counts_per_division(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets extra counts per division.

        ..  container:: example

            No extra counts per division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     extra_counts_per_division=[0, 1],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     extra_counts_per_division=[0, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     extra_counts_per_division=[0, -1],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
    def read_talea_once_only(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker reads talea once only.

        ..  container:: example

            Reads talea cyclically:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
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
    def state(self) -> abjad.OrderedDict:
        r"""
        Gets state dictionary.

        ..  container:: example

            Consumes 4 divisions and 31 counts:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     extra_counts_per_division=[0, 1, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            >>> selection = rhythm_maker(divisions, previous_state=state)
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
            >>> selection = rhythm_maker(divisions, previous_state=state)
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
        return super().state

    @property
    def specifiers(self) -> typing.List[typings.SpecifierTyping]:
        r"""
        Gets specifiers.

        ..  container:: example

            Silences first and last logical ties:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.SilenceMask(
            ...         selector=abjad.select().logical_ties()[abjad.index([0, -1])],
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...     ),
            ... )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
                        c'8.
                        ]
                        r8
                    }
                >>

        ..  container:: example

            Silences all logical ties. Then sustains first and last logical
            ties:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.SilenceMask(
            ...         selector=abjad.select().logical_ties()
            ...     ),
            ...     abjadext.rmakers.SustainMask(
            ...         selector=abjad.select().logical_ties()[abjad.index([0, -1])],
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...     ),
            ... )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
                        r8
                        r8.
                        r4
                        r16
                        r8
                        r16
                        r8
                        r4
                        r16
                        r8
                        r8.
                        c'8
                    }
                >>

        ..  container:: example

            REGRESSION. Nonperiodic logical tie masks respect state.

            Only logical ties 0 and 2 are masked here:

            >>> pattern = abjad.Pattern([0, 2, 12])
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.SilenceMask(
            ...         selector=abjad.select().logical_ties()[pattern]
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     extra_counts_per_division=[0, 1, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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

            TODO: restore statal logical tie masks:

            Only logical tie 12 is masked here:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions, previous_state=state)
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

#        ..  container:: example
#
#            REGRESSION. Periodic logical tie masks also respect state.
#
#            >>> pattern = abjad.Pattern([3], period=4)
#            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
#            ...     abjadext.rmakers.SilenceMask(
#            ...         selector=abjad.select().logical_ties()[pattern]
#            ...     ),
#            ...     abjadext.rmakers.BeamSpecifier(
#            ...         selector=abjad.select().tuplets(),
#            ...     ),
#            ...     abjadext.rmakers.TupletSpecifier(
#            ...         extract_trivial=True,
#            ...         ),
#            ...     extra_counts_per_division=[0, 1, 2],
#            ...     talea=abjadext.rmakers.Talea(
#            ...         counts=[4],
#            ...         denominator=16,
#            ...         ),
#            ...     )
#
#            Incomplete last note is masked here:
#
#            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
#            >>> selection = rhythm_maker(divisions)
#            >>> lilypond_file = abjad.LilyPondFile.rhythm(
#            ...     selection,
#            ...     divisions,
#            ...     )
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> abjad.f(lilypond_file[abjad.Score])
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                    }
#                    \new RhythmicStaff
#                    {
#                        c'4
#                        c'8
#                        ~
#                        \times 8/9 {
#                            c'8
#                            c'4
#                            r8.
#                        }
#                        \tweak text #tuplet-number::calc-fraction-text
#                        \times 3/4 {
#                            r16
#                            c'4
#                            c'8.
#                            ~
#                        }
#                        c'16
#                        c'4
#                        r8.
#                    }
#                >>
#
#            >>> state = rhythm_maker.state
#            >>> abjad.f(state)
#            abjad.OrderedDict(
#                [
#                    ('divisions_consumed', 4),
#                    ('incomplete_last_note', True),
#                    ('logical_ties_produced', 8),
#                    ('talea_weight_consumed', 31),
#                    ]
#                )
#
#            Incomplete first note is masked here:
#
#            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
#            >>> selection = rhythm_maker(divisions, previous_state=state)
#            >>> lilypond_file = abjad.LilyPondFile.rhythm(
#            ...     selection,
#            ...     divisions,
#            ...     )
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> abjad.f(lilypond_file[abjad.Score])
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                    }
#                    \new RhythmicStaff
#                    {
#                        \tweak text #tuplet-number::calc-fraction-text
#                        \times 6/7 {
#                            r16
#                            c'4
#                            c'8
#                            ~
#                        }
#                        \times 4/5 {
#                            c'8
#                            c'4
#                            r4
#                        }
#                        c'4
#                        c'8
#                        ~
#                        \times 8/9 {
#                            c'8
#                            c'4
#                            r8.
#                        }
#                    }
#                >>
#
#            >>> state = rhythm_maker.state
#            >>> abjad.f(state)
#            abjad.OrderedDict(
#                [
#                    ('divisions_consumed', 8),
#                    ('incomplete_last_note', True),
#                    ('logical_ties_produced', 16),
#                    ('talea_weight_consumed', 63),
#                    ]
#                )

        ..  container:: example

            REGRESSION. Spells tuplet denominator in terms of duration when
            denominator is given as a duration:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         denominator=(1, 16),
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     extra_counts_per_division=[1, 1, 2, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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

            Beams each division:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=True,
            ...         selector=abjad.select().tuplets(),
            ...         ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, -1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_rests=True,
            ...         selector=abjad.select().tuplets(),
            ...         ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, -1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_rests=True,
            ...         selector=abjad.select().tuplets(),
            ...         stemlet_length=0.75,
            ...         ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 1, 1, -1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        \revert Staff.Stem.stemlet-length
                        c'16
                        ]
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        r16
                        c'16
                        \revert Staff.Stem.stemlet-length
                        c'16
                        ]
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        \revert Staff.Stem.stemlet-length
                        r16
                        ]
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        c'16
                        c'16
                        \revert Staff.Stem.stemlet-length
                        r16
                        ]
                    }
                >>

        ..  container:: example

            Does not tie across divisions:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, 3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
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

            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=nonlast_tuplets.map(last_leaf),
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, 3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
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

            >>> pattern = abjad.Pattern([0], period=2)
            >>> tuplets = abjad.select().tuplets()[pattern]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=tuplets.map(last_leaf),
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, 3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
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

            TIE-CONSECUTIVE-NOTES RECIPE:

            >>> nonlast_notes = abjad.select().notes()[:-1]
            >>> selector = abjad.select().runs()
            >>> selector = selector.map(nonlast_notes)
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         detach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets(),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, -3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
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

        ..  container:: example

            REGRESSION. Specifiers survive new:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[5, -3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     )
            >>> new_rhythm_maker = abjad.new(rhythm_maker)
            >>> abjad.f(new_rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                TupletSpecifier(extract_trivial=True),
                talea=abjadext.rmakers.Talea(
                    counts=[5, -3, 3, 3],
                    denominator=16,
                    ),
                )

            >>> rhythm_maker == new_rhythm_maker
            True

            REGRESSION. None eliminates specifiers when passed to new:

            >>> new_rhythm_maker = abjad.new(rhythm_maker, None)
            >>> abjad.f(new_rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                talea=abjadext.rmakers.Talea(
                    counts=[5, -3, 3, 3],
                    denominator=16,
                    ),
                )

            >>> new_rhythm_maker.specifiers
            []

            REGRESSION. New allows additional specifiers:

            >>> specifiers = rhythm_maker.specifiers[:]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     selector=abjad.select().tuplets(),
            ...     )
            >>> specifiers.insert(0, specifier)
            >>> new_rhythm_maker = abjad.new(rhythm_maker, *specifiers)
            >>> abjad.f(new_rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                BeamSpecifier(selector=abjad.select().tuplets()),
                TupletSpecifier(extract_trivial=True),
                talea=abjadext.rmakers.Talea(
                    counts=[5, -3, 3, 3],
                    denominator=16,
                    ),
                )

        ..  container:: example

            Working with ``denominator``.

            Reduces terms in tuplet ratio to relative primes when no tuplet
            specifier is given:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     extra_counts_per_division=[1, 1, 2, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.TupletSpecifier(
            ...         denominator=(1, 16),
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     extra_counts_per_division=[1, 1, 2, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     extra_counts_per_division=[0, -1],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         diminution=False,
            ...         extract_trivial=True,
            ...         ),
            ...     extra_counts_per_division=[0, -1],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     extra_counts_per_division=[0, 4],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, 6, 6],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.TupletSpecifier(
            ...         trivialize=True,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     extra_counts_per_division=[0, 4],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, 6, 6],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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

            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         trivialize=True,
            ...         ),
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=nonlast_tuplets.map(last_leaf),
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     extra_counts_per_division=[0, 4],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, 6, 6],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.TupletSpecifier(
            ...         trivialize=True,
            ...         ),
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=abjad.select().notes()[:-1],
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     extra_counts_per_division=[0, 4],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, 6, 6],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     extra_counts_per_division=[1, 0],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, -6, -6],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_rest_filled=True,
            ...         ),
            ...     extra_counts_per_division=[1, 0],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[3, 3, -6, -6],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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

        ..  container:: example

            No division masks:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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

            >>> pattern = abjad.Pattern([1], period=2)
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.SilenceMask(
            ...         selector=abjad.select().tuplets()[pattern]
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         rewrite_rest_filled=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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

            >>> pattern = abjad.Pattern([1], period=2)
            >>> selector = abjad.select().tuplets()[pattern]
            >>> nonlast_notes = abjad.select().notes()[:-1]
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=selector.map(nonlast_notes),
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_sustained=True,
            ...         selector=selector,
            ...     ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
                        ~
                        c'8
                        c'4
                        c'2
                    }
                >>

        ..  container:: example

            REGRESSION. Nonperiodic division masks respect state.

            Only divisions 0 and 2 are masked here:

            >>> pattern = abjad.Pattern([0, 2, 7])
            >>> selector = abjad.select().tuplets()[pattern]
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.SilenceMask(
            ...         selector=selector,
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_rest_filled=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     extra_counts_per_division=[0, 1, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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

# TODO: make statal division masking work again:
#            Only division 7 is masked here:
#
#            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
#            >>> selection = rhythm_maker(divisions, previous_state=state)
#            >>> lilypond_file = abjad.LilyPondFile.rhythm(
#            ...     selection,
#            ...     divisions,
#            ...     )
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> abjad.f(lilypond_file[abjad.Score])
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                    }
#                    \new RhythmicStaff
#                    {
#                        \tweak text #tuplet-number::calc-fraction-text
#                        \times 6/7 {
#                            c'16
#                            c'4
#                            c'8
#                            ~
#                        }
#                        \times 4/5 {
#                            c'8
#                            c'4
#                            c'4
#                        }
#                        c'4
#                        c'8
#                        r2
#                    }
#                >>
#
#            >>> state = rhythm_maker.state
#            >>> abjad.f(state)
#            abjad.OrderedDict(
#                [
#                    ('divisions_consumed', 8),
#                    ('incomplete_last_note', True),
#                    ('logical_ties_produced', 15),
#                    ('talea_weight_consumed', 63),
#                    ]
#                )

        ..  container:: example

            REGRESSION. Periodic division masks also respect state.

            >>> pattern = abjad.Pattern([2], period=3)
            >>> selector = abjad.select().tuplets()[pattern]
            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.SilenceMask(
            ...         selector=selector,
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         rewrite_rest_filled=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         ),
            ...     extra_counts_per_division=[0, 1, 2],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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

# TODO: make statal division masking work again:
#            Incomplete first note is masked here:
#
#            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
#            >>> selection = rhythm_maker(divisions, previous_state=state)
#            >>> lilypond_file = abjad.LilyPondFile.rhythm(
#            ...     selection,
#            ...     divisions,
#            ...     )
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> abjad.f(lilypond_file[abjad.Score])
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                    }
#                    \new RhythmicStaff
#                    {
#                        \tweak text #tuplet-number::calc-fraction-text
#                        \times 6/7 {
#                            c'16
#                            c'4
#                            c'8
#                        }
#                        r2
#                        c'4
#                        c'8
#                        ~
#                        \times 8/9 {
#                            c'8
#                            c'4
#                            c'8.
#                        }
#                    }
#                >>
#
#            >>> state = rhythm_maker.state
#            >>> abjad.f(state)
#            abjad.OrderedDict(
#                [
#                    ('divisions_consumed', 8),
#                    ('incomplete_last_note', True),
#                    ('logical_ties_produced', 15),
#                    ('talea_weight_consumed', 63),
#                    ]
#                )

        """
        return super().specifiers

    @property
    def tag(self) -> typing.Optional[str]:
        r"""
        Gets tag.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     extra_counts_per_division=[0, 1],
            ...     tag='TALEA_RHYTHM_MAKER',
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[1, 2, 3, 4],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
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
    def talea(self) -> Talea:
        r"""
        Gets talea.

        ..  container:: example

            Default talea:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ... )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
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
                    }
                >>

        ..  container:: example

            Working with ``preamble``.

            Preamble less than total duration:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[8, -4, 8],
            ...         denominator=32,
            ...         preamble=[1, 1, 1, 1],
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[8, -4, 8],
            ...         denominator=32,
            ...         preamble=[32, 32, 32, 32],
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[8, -4, 8],
            ...         denominator=32,
            ...         end_counts=[1, 1, 1, 1],
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = rhythm_maker(divisions)
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
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().tuplets()
            ...     ),
            ...     abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...     ),
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[6],
            ...         denominator=16,
            ...         end_counts=[1],
            ...         ),
            ...     )

            >>> divisions = [(3, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
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
