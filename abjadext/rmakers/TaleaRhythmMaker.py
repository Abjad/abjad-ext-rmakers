import abjad
import typing
from . import commands as _commands
from . import specifiers as _specifiers
from .RhythmMaker import RhythmMaker


class TaleaRhythmMaker(RhythmMaker):
    r"""
    Talea rhythm-maker.

    ..  container:: example

        Repeats talea of 1/16, 2/16, 3/16, 4/16:

        >>> rhythm_maker = rmakers.TaleaRhythmMaker(
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ...     talea=rmakers.Talea(
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

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_extra_counts", "_read_talea_once_only", "_talea")

    ### INITIALIZER ###

    def __init__(
        self,
        *commands: _commands.Command,
        extra_counts: abjad.IntegerSequence = None,
        preprocessor: abjad.Expression = None,
        read_talea_once_only: bool = None,
        spelling: _specifiers.Spelling = None,
        tag: str = None,
        talea: _specifiers.Talea = _specifiers.Talea(
            counts=[1], denominator=16
        ),
    ) -> None:
        RhythmMaker.__init__(
            self,
            *commands,
            preprocessor=preprocessor,
            spelling=spelling,
            tag=tag,
        )
        if talea is not None:
            assert isinstance(talea, _specifiers.Talea), repr(talea)
        self._talea = talea
        if extra_counts is not None:
            assert abjad.mathtools.all_are_integer_equivalent_numbers(
                extra_counts
            )
        self._extra_counts = extra_counts
        if read_talea_once_only is not None:
            read_talea_once_only = bool(read_talea_once_only)
        self._read_talea_once_only = read_talea_once_only

    ### SPECIAL METHODS ###

    def __format__(self, format_specification="") -> str:
        """
        Formats talea rhythm-maker.

        ..  container:: example

            REGRESSION. Commands appear in storage format:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
            ...         counts=[5, -3, 3, 3],
            ...         denominator=16,
            ...     ),
            ... )
            >>> abjad.f(rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                BeamCommand(selector=abjad.select().tuplets()),
                ExtractTrivialCommand(),
                talea=abjadext.specifiers.Talea(
                    counts=[5, -3, 3, 3],
                    denominator=16,
                    ),
                )

        """
        return super().__format__(format_specification=format_specification)

    ### PRIVATE METHODS ###

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
            if len(part) == 1:
                continue
            abjad.tie(part)
        # TODO: this will need to be generalized and better tested:
        if unscaled_end_counts:
            total = len(unscaled_end_counts)
            end_leaves = leaves[-total:]
            for leaf in reversed(end_leaves):
                previous_leaf = abjad.inspect(leaf).leaf(-1)
                if previous_leaf is not None:
                    abjad.detach(abjad.Tie, previous_leaf)

    def _get_talea(self):
        if self.talea is not None:
            return self.talea
        return Talea()

    def _make_leaf_lists(self, numeric_map, talea_denominator):
        leaf_lists = []
        specifier = self._get_spelling_specifier()
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

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        input_divisions = divisions[:]
        input_ = self._prepare_input()
        end_counts = input_["end_counts"]
        preamble = input_["preamble"]
        talea = input_["talea"]
        advanced_talea = _specifiers.Talea(
            counts=talea,
            denominator=self.talea.denominator,
            end_counts=end_counts,
            preamble=preamble,
        )
        extra_counts = input_["extra_counts"]
        unscaled_end_counts = tuple(end_counts)
        unscaled_preamble = tuple(preamble)
        unscaled_talea = tuple(talea)
        counts = {
            "end_counts": end_counts,
            "extra_counts": extra_counts,
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
                counts["extra_counts"],
                counts["end_counts"],
            )
            talea_weight_consumed = sum(_.weight() for _ in numeric_map)
            leaf_lists = self._make_leaf_lists(numeric_map, lcd)
            if not counts["extra_counts"]:
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
        self, divisions, preamble, talea, extra_counts, end_counts
    ):
        assert all(isinstance(_, int) for _ in end_counts), repr(end_counts)
        assert all(isinstance(_, int) for _ in preamble), repr(preamble)
        assert all(isinstance(_, int) for _ in talea), repr(talea)
        prolated_divisions = self._make_prolated_divisions(
            divisions, extra_counts
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
        return result

    def _make_prolated_divisions(self, divisions, extra_counts):
        prolated_divisions = []
        for i, division in enumerate(divisions):
            if not extra_counts:
                prolated_divisions.append(division)
                continue
            prolation_addendum = extra_counts[i]
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
        extra_counts = self.extra_counts or ()
        extra_counts = abjad.sequence(extra_counts)
        divisions_consumed = self.previous_state.get("divisions_consumed", 0)
        extra_counts = extra_counts.rotate(-divisions_consumed)
        extra_counts = abjad.CyclicTuple(extra_counts)
        return {
            "end_counts": end_counts,
            "extra_counts": extra_counts,
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
    def commands(self) -> typing.List[_commands.Command]:
        r"""
        Gets commands.

        ..  container:: example

            Silences first and last logical ties:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([0, -1]),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.force_rest(abjad.select().logical_ties()),
            ...     rmakers.force_note(
            ...         abjad.select().logical_ties().get([0, -1]),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            REGRESSION. Nonperiodic rest commands respect state.

            Only logical ties 0 and 2 are rested here:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([0, 2, 12]),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     extra_counts=[0, 1, 2],
            ...     talea=rmakers.Talea(
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

            Only logical tie 12 is rested here:

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
#            REGRESSION. Periodic rest commands also respect state.
#
#            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
#            ...     rmakers.force_rest(
#            ...         abjad.select().logical_ties().get([3], 4),
#            ...     ),
#            ...     rmakers.beam(),
#            ...     rmakers.extract_trivial(),
#            ...     extra_counts=[0, 1, 2],
#            ...     talea=rmakers.Talea(
#            ...         counts=[4],
#            ...         denominator=16,
#            ...         ),
#            ...     )
#
#            Incomplete last note is rested here:
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
#            Incomplete first note is rested here:
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.denominator((1, 16)),
            ...     rmakers.beam(),
            ...     extra_counts=[1, 1, 2, 2],
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            Beams tuplets together:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam_groups(abjad.select().tuplets()),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(beam_rests=True),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(
            ...         beam_rests=True,
            ...         stemlet_length=0.75,
            ...         ),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            Ties across every other tuplet:

            >>> tuplets = abjad.select().tuplets().get([0], 2)
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.tie(tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.untie(selector),
            ...     rmakers.tie(selector),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            REGRESSION. Commands survive new:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
            ...         counts=[5, -3, 3, 3],
            ...         denominator=16,
            ...         ),
            ...     )
            >>> new_rhythm_maker = abjad.new(rhythm_maker)
            >>> abjad.f(new_rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                ExtractTrivialCommand(),
                talea=abjadext.specifiers.Talea(
                    counts=[5, -3, 3, 3],
                    denominator=16,
                    ),
                )

            >>> rhythm_maker == new_rhythm_maker
            True

            REGRESSION. None eliminates commands when passed to new:

            >>> new_rhythm_maker = abjad.new(rhythm_maker, None)
            >>> abjad.f(new_rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                talea=abjadext.specifiers.Talea(
                    counts=[5, -3, 3, 3],
                    denominator=16,
                    ),
                )

            >>> new_rhythm_maker.commands
            []

            REGRESSION. New allows additional commands:

            >>> commands = rhythm_maker.commands[:]
            >>> command = rmakers.beam()
            >>> commands.insert(0, command)
            >>> new_rhythm_maker = abjad.new(rhythm_maker, *commands)
            >>> abjad.f(new_rhythm_maker)
            abjadext.rmakers.TaleaRhythmMaker(
                BeamCommand(selector=abjad.select().tuplets()),
                ExtractTrivialCommand(),
                talea=abjadext.specifiers.Talea(
                    counts=[5, -3, 3, 3],
                    denominator=16,
                    ),
                )

        ..  container:: example

            Working with ``denominator``.

            Reduces terms in tuplet ratio to relative primes when no tuplet
            command is given:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     extra_counts=[1, 1, 2, 2],
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.denominator((1, 16)),
            ...     rmakers.beam(),
            ...     extra_counts=[1, 1, 2, 2],
            ...     talea=rmakers.Talea(
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
            tuplet command is given):

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     extra_counts=[0, -1],
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.force_augmentation(),
            ...     rmakers.extract_trivial(),
            ...     extra_counts=[0, -1],
            ...     talea=rmakers.Talea(
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

            Leaves trivializable tuplets as-is when no tuplet command is
            given. The tuplets in measures 2 and 4 can be written as trivial
            tuplets, but they are not:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     extra_counts=[0, 4],
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.trivialize(),
            ...     rmakers.beam(),
            ...     extra_counts=[0, 4],
            ...     talea=rmakers.Talea(
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
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.trivialize(),
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     extra_counts=[0, 4],
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.trivialize(),
            ...     rmakers.tie(abjad.select().notes()[:-1]),
            ...     rmakers.beam(),
            ...     extra_counts=[0, 4],
            ...     talea=rmakers.Talea(
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
            when no tuplet command is given):

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     extra_counts=[1, 0],
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.rewrite_rest_filled(),
            ...     extra_counts=[1, 0],
            ...     talea=rmakers.Talea(
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

            No rest commands:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.force_rest(
            ...         abjad.select().tuplets().get([1], 2),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_rest_filled(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> selector = abjad.select().tuplets().get([1], 2)
            >>> nonlast_notes = abjad.select().notes()[:-1]
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.tie(selector.map(nonlast_notes)),
            ...     rmakers.rewrite_sustained(selector),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            REGRESSION. Nonperiodic rest commands respect state.

            Only divisions 0 and 2 are rested here:

            >>> selector = abjad.select().tuplets().get([0, 2, 7])
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.force_rest(selector),
            ...     rmakers.rewrite_rest_filled(selector),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     extra_counts=[0, 1, 2],
            ...     talea=rmakers.Talea(
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

# TODO: make statal division resting work again:
#            Only division 7 is rested here:
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

            REGRESSION. Periodic rest commands also respect state.

            >>> selector = abjad.select().tuplets().get([2], 3)
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.force_rest(selector),
            ...     rmakers.rewrite_rest_filled(selector),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     extra_counts=[0, 1, 2],
            ...     talea=rmakers.Talea(
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

# TODO: make statal division resting work again.
#            Incomplete first note is rested here:
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

        ..  container:: example

            Forces the first leaf and the last two leaves to be rests:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.force_rest(
            ...         abjad.select().leaves().get([0, -2, -1])
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            Forces rest at last leaf of every tuplet:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.force_rest(
            ...         abjad.select().tuplets().map(abjad.select().leaf(0))
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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
        return super().commands

    @property
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        r"""
        Gets duration specifier.

        Several duration specifier configurations are available.

        ..  container:: example

            Spells nonassignable durations with monontonically decreasing
            durations:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     spelling=rmakers.Spelling(increase_monotonic=False),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     spelling=rmakers.Spelling(increase_monotonic=True),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     spelling=rmakers.Spelling(forbidden_note_duration=(1, 4)),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     rmakers.rewrite_meter(),
            ...     talea=rmakers.Talea(
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
        return super().spelling

    @property
    def extra_counts(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets extra counts.

        ..  container:: example

            No extra counts:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     extra_counts=[0, 1],
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     extra_counts=[0, 2],
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     extra_counts=[0, -1],
            ...     talea=rmakers.Talea(
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
        if self._extra_counts:
            return list(self._extra_counts)
        else:
            return None

    @property
    def read_talea_once_only(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker reads talea once only.

        ..  container:: example

            Reads talea cyclically:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     read_talea_once_only=True,
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     extra_counts=[0, 1, 2],
            ...     talea=rmakers.Talea(
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
    def tag(self) -> typing.Optional[str]:
        r"""
        Gets tag.

        ..  container:: example

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     extra_counts=[0, 1],
            ...     tag='TALEA_RHYTHM_MAKER',
            ...     talea=rmakers.Talea(
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
    def talea(self) -> _specifiers.Talea:
        r"""
        Gets talea.

        ..  container:: example

            Default talea:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     talea=rmakers.Talea(
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
