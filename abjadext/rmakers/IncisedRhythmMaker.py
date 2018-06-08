import abjad
import typing
from .BeamSpecifier import BeamSpecifier
from .DurationSpecifier import DurationSpecifier
from .InciseSpecifier import InciseSpecifier
from .RhythmMaker import RhythmMaker
from .TaleaRhythmMaker import TaleaRhythmMaker
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier
from .typings import Mask


class IncisedRhythmMaker(RhythmMaker):
    r"""
    Incised rhythm-maker.

    >>> import abjadext

    ..  container:: example

        >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
        ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
        ...         prefix_talea=[-1],
        ...         prefix_counts=[0, 1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=16,
        ...         ),
        ...     )

        >>> divisions = 4 * [(5, 16)]
        >>> selections = rhythm_maker(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections,
        ...     divisions,
        ...     )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(lilypond_file[abjad.Staff])
            \new RhythmicStaff
            {
                {   % measure
                    \time 5/16
                    c'4
                    r16
                }   % measure
                {   % measure
                    r16
                    c'8.
                    r16
                }   % measure
                {   % measure
                    c'4
                    r16
                }   % measure
                {   % measure
                    r16
                    c'8.
                    r16
                }   % measure
            }

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Rhythm-makers'

    __slots__ = (
        '_extra_counts_per_division',
        '_incise_specifier',
        '_replace_rests_with_skips',
        '_split_divisions_by_counts',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        beam_specifier: BeamSpecifier = None,
        duration_specifier: DurationSpecifier = None,
        division_masks: typing.Sequence[Mask] = None,
        extra_counts_per_division: typing.Sequence[int] = None,
        incise_specifier: InciseSpecifier = None,
        logical_tie_masks: typing.Sequence[Mask] = None,
        replace_rests_with_skips: bool = None,
        split_divisions_by_counts: typing.Sequence[int] = None,
        tie_specifier: TieSpecifier = None,
        tuplet_specifier: TupletSpecifier = None,
        ) -> None:
        RhythmMaker.__init__(
            self,
            beam_specifier=beam_specifier,
            duration_specifier=duration_specifier,
            division_masks=division_masks,
            logical_tie_masks=logical_tie_masks,
            tie_specifier=tie_specifier,
            tuplet_specifier=tuplet_specifier,
            )
        prototype = (InciseSpecifier, type(None))
        assert isinstance(incise_specifier, prototype)
        self._incise_specifier = incise_specifier
        if extra_counts_per_division is not None:
            extra_counts_per_division = tuple(extra_counts_per_division)
        if split_divisions_by_counts is not None:
            split_divisions_by_counts = tuple(split_divisions_by_counts)
        assert (extra_counts_per_division is None or
            abjad.mathtools.all_are_nonnegative_integer_equivalent_numbers(
                extra_counts_per_division)), extra_counts_per_division
        assert (split_divisions_by_counts is None or
            abjad.mathtools.all_are_nonnegative_integer_equivalent_numbers(
                split_divisions_by_counts)), split_divisions_by_counts
        self._extra_counts_per_division = extra_counts_per_division
        self._replace_rests_with_skips = replace_rests_with_skips
        self._split_divisions_by_counts = split_divisions_by_counts

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.List[typing.Tuple[int, int]],
        previous_state: abjad.OrderedDict = None,
        ) -> typing.List[abjad.Selection]:
        """
        Calls incised rhythm-maker on ``divisions``.
        """
        return RhythmMaker.__call__(
            self,
            divisions,
            previous_state=previous_state,
            )

    ### PRIVATE METHODS ###

    def _get_incise_specifier(self):
        if self.incise_specifier is not None:
            return self.incise_specifier
        return InciseSpecifier()

    def _make_division_incised_numeric_map(
        self,
        divisions=None,
        prefix_talea=None,
        prefix_counts=None,
        suffix_talea=None,
        suffix_counts=None,
        extra_counts_per_division=None,
        ):
        numeric_map, prefix_talea_index, suffix_talea_index = [], 0, 0
        for pair_index, division in enumerate(divisions):
            prefix_length = prefix_counts[pair_index]
            suffix_length = suffix_counts[pair_index]
            start = prefix_talea_index
            stop = prefix_talea_index + prefix_length
            prefix = prefix_talea[start:stop]
            start = suffix_talea_index
            stop = suffix_talea_index + suffix_length
            suffix = suffix_talea[start:stop]
            prefix_talea_index += prefix_length
            suffix_talea_index += suffix_length
            prolation_addendum = extra_counts_per_division[pair_index]
            if isinstance(division, tuple):
                numerator = division[0] + (prolation_addendum % division[0])
            else:
                numerator = division.numerator + (
                    prolation_addendum % division.numerator)
            numeric_map_part = self._make_numeric_map_part(
                numerator, prefix, suffix)
            numeric_map.append(numeric_map_part)
        return numeric_map

    def _make_middle_of_numeric_map_part(self, middle):
        incise_specifier = self._get_incise_specifier()
        if incise_specifier.fill_with_notes:
            if not incise_specifier.outer_divisions_only:
                if 0 < middle:
                    if incise_specifier.body_ratio is not None:
                        shards = middle / incise_specifier.body_ratio
                        return tuple(shards)
                    else:
                        return (middle,)
                else:
                    return ()
            elif incise_specifier.outer_divisions_only:
                if 0 < middle:
                    return (middle,)
                else:
                    return ()
            else:
                message = 'must incise divisions or output.'
                raise Exception(message)
        else:
            if not incise_specifier.outer_divisions_only:
                if 0 < middle:
                    return (-abs(middle),)
                else:
                    return ()
            elif incise_specifier.outer_divisions_only:
                if 0 < middle:
                    return (-abs(middle),)
                else:
                    return ()
            else:
                raise Exception('must incise divisions or output.')

    def _make_music(self, divisions):
        input_divisions = divisions[:]
        input_ = self._prepare_input()
        prefix_talea = input_[0]
        prefix_counts = input_[1]
        suffix_talea = input_[2]
        suffix_counts = input_[3]
        extra_counts_per_division = input_[4]
        split_divisions_by_counts = input_[5]
        counts = {
            'prefix_talea': prefix_talea,
            'suffix_talea': suffix_talea,
            'extra_counts_per_division': extra_counts_per_division,
            'split_divisions_by_counts': split_divisions_by_counts,
            }
        if self.incise_specifier is not None:
            talea_denominator = self.incise_specifier.talea_denominator
        else:
            talea_denominator = None
        result = self._scale_counts(divisions, talea_denominator, counts)
        divisions = result['divisions']
        lcd = result['lcd']
        counts = result['counts']
        secondary_divisions = self._make_secondary_divisions(
            divisions,
            counts['split_divisions_by_counts'],
            )
        incise_specifier = self._get_incise_specifier()
        if not incise_specifier.outer_divisions_only:
            numeric_map = self._make_division_incised_numeric_map(
                secondary_divisions,
                counts['prefix_talea'],
                prefix_counts,
                counts['suffix_talea'],
                suffix_counts,
                counts['extra_counts_per_division'],
                )
        else:
            assert incise_specifier.outer_divisions_only
            numeric_map = self._make_output_incised_numeric_map(
                secondary_divisions,
                counts['prefix_talea'],
                prefix_counts,
                counts['suffix_talea'],
                suffix_counts,
                counts['extra_counts_per_division'],
                )
        result = []
        selections = self._numeric_map_to_leaf_selections(numeric_map, lcd)
        if not self.extra_counts_per_division:
            result.extend(selections)
        else:
            tuplets = self._make_tuplets(secondary_divisions, selections)
            result.extend(tuplets)
        if not self._all_are_tuplets_or_all_are_leaf_selections(result):
            message = 'should be tuplets or leaf selections: {!r}.'
            message = message.format(result)
            raise Exception(message)
        beam_specifier = self._get_beam_specifier()
        if beam_specifier.beam_divisions_together:
            beam = abjad.MultipartBeam()
            abjad.attach(beam, result)
        elif beam_specifier.beam_each_division:
            for x in result:
                beam = abjad.MultipartBeam()
                leaves = abjad.select(x).leaves()
                abjad.attach(beam, leaves)
        selections = [abjad.select(_) for _ in result]
        selections = self._apply_division_masks(selections)
        duration_specifier = self._get_duration_specifier()
        if duration_specifier.rewrite_meter:
            selections = duration_specifier._rewrite_meter_(
                selections,
                input_divisions,
                )
        return selections

    def _make_numeric_map_part(
        self,
        numerator,
        prefix,
        suffix,
        is_note_filled=True,
        ):
        prefix_weight = abjad.mathtools.weight(prefix)
        suffix_weight = abjad.mathtools.weight(suffix)
        middle = numerator - prefix_weight - suffix_weight
        if numerator < prefix_weight:
            weights = [numerator]
            prefix = abjad.sequence(prefix)
            prefix = prefix.split(weights, cyclic=False, overhang=False)[0]
        middle = self._make_middle_of_numeric_map_part(middle)
        suffix_space = numerator - prefix_weight
        if suffix_space <= 0:
            suffix = ()
        elif suffix_space < suffix_weight:
            weights = [suffix_space]
            suffix = abjad.sequence(suffix)
            suffix = suffix.split(weights, cyclic=False, overhang=False)[0]
        numeric_map_part = prefix + middle + suffix
        return [abjad.Duration(_) for _ in numeric_map_part]

    def _make_output_incised_numeric_map(
        self,
        divisions,
        prefix_talea,
        prefix_counts,
        suffix_talea,
        suffix_counts,
        extra_counts_per_division,
        ):
        numeric_map, prefix_talea_index, suffix_talea_index = [], 0, 0
        prefix_length, suffix_length = prefix_counts[0], suffix_counts[0]
        start = prefix_talea_index
        stop = prefix_talea_index + prefix_length
        prefix = prefix_talea[start:stop]
        start = suffix_talea_index
        stop = suffix_talea_index + suffix_length
        suffix = suffix_talea[start:stop]
        if len(divisions) == 1:
            prolation_addendum = extra_counts_per_division[0]
            if isinstance(divisions[0], abjad.NonreducedFraction):
                numerator = divisions[0].numerator
            else:
                numerator = divisions[0][0]
            numerator += (prolation_addendum % numerator)
            numeric_map_part = self._make_numeric_map_part(
                numerator, prefix, suffix)
            numeric_map.append(numeric_map_part)
        else:
            prolation_addendum = extra_counts_per_division[0]
            if isinstance(divisions[0], tuple):
                numerator = divisions[0][0]
            else:
                numerator = divisions[0].numerator
            numerator += (prolation_addendum % numerator)
            numeric_map_part = self._make_numeric_map_part(
                numerator, prefix, ())
            numeric_map.append(numeric_map_part)
            for i, division in enumerate(divisions[1:-1]):
                index = i + 1
                prolation_addendum = extra_counts_per_division[index]
                if isinstance(division, tuple):
                    numerator = division[0]
                else:
                    numerator = division.numerator
                numerator += (prolation_addendum % numerator)
                numeric_map_part = self._make_numeric_map_part(
                    numerator, (), ())
                numeric_map.append(numeric_map_part)
            try:
                index = i + 2
                prolation_addendum = extra_counts_per_division[index]
            except UnboundLocalError:
                index = 1 + 2
                prolation_addendum = extra_counts_per_division[index]
            if isinstance(divisions[-1], tuple):
                numerator = divisions[-1][0]
            else:
                numerator = divisions[-1].numerator
            numerator += (prolation_addendum % numerator)
            numeric_map_part = self._make_numeric_map_part(
                numerator, (), suffix)
            numeric_map.append(numeric_map_part)
        return numeric_map

    def _numeric_map_to_leaf_selections(self, numeric_map, lcd):
        selections = []
        specifier = self._get_duration_specifier()
        tie_specifier = self._get_tie_specifier()
        class_ = TaleaRhythmMaker
        for numeric_map_part in numeric_map:
            numeric_map_part = [
                _ for _ in numeric_map_part if _ != abjad.Duration(0)
                ]
            selection = class_._make_leaves_from_talea(
                numeric_map_part,
                lcd,
                forbidden_duration=specifier.forbidden_duration,
                decrease_monotonic=specifier.decrease_monotonic,
                spell_metrically=specifier.spell_metrically,
                repeat_ties=tie_specifier.repeat_ties,
                )
            if self.replace_rests_with_skips:
                new_components = []
                for component in selection:
                    if isinstance(component, abjad.Rest):
                        duration = abjad.inspect(component).get_duration()
                        skip = abjad.Skip(duration)
                        new_components.append(skip)
                    else:
                        new_components.append(component)
                selection = abjad.select(new_components)
            selections.append(selection)
        return selections

    def _prepare_input(self):
        #
        incise_specifier = self._get_incise_specifier()
        prefix_talea = incise_specifier.prefix_talea or ()
        prefix_talea = abjad.CyclicTuple(prefix_talea)
        #
        prefix_counts = incise_specifier.prefix_counts or (0,)
        prefix_counts = abjad.CyclicTuple(prefix_counts)
        #
        suffix_talea = incise_specifier.suffix_talea or ()
        suffix_talea = abjad.CyclicTuple(suffix_talea)
        #
        suffix_counts = incise_specifier.suffix_counts or (0,)
        suffix_counts = abjad.CyclicTuple(suffix_counts)
        #
        extra_counts_per_division = self.extra_counts_per_division or ()
        if extra_counts_per_division:
            extra_counts_per_division = abjad.CyclicTuple(
                extra_counts_per_division)
        else:
            extra_counts_per_division = abjad.CyclicTuple([0])
        #
        split_divisions_by_counts = self.split_divisions_by_counts or ()
        split_divisions_by_counts = abjad.CyclicTuple(
            split_divisions_by_counts)
        #
        return (
            prefix_talea,
            prefix_counts,
            suffix_talea,
            suffix_counts,
            extra_counts_per_division,
            split_divisions_by_counts,
            )

    ### PUBLIC PROPERTIES ###

    @property
    def division_masks(self) -> typing.Optional[abjad.PatternTuple]:
        r"""
        Gets division masks.

        ..  container:: example

            No division masks:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         talea_denominator=16,
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 4/8
                        r16
                        c'4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        r16
                        c'4
                        ~
                        c'16
                    }   % measure
                    {   % measure
                        \time 4/8
                        r16
                        c'4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        r16
                        c'4
                        ~
                        c'16
                    }   % measure
                }

        ..  container:: example

            Masks every other output division:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         talea_denominator=16,
            ...         ),
            ...     division_masks=[
            ...         abjad.Pattern(
            ...             indices=[0],
            ...             period=2,
            ...             ),
            ...         ],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 4/8
                        r2
                    }   % measure
                    {   % measure
                        \time 3/8
                        r16
                        c'4
                        ~
                        c'16
                    }   % measure
                    {   % measure
                        \time 4/8
                        r2
                    }   % measure
                    {   % measure
                        \time 3/8
                        r16
                        c'4
                        ~
                        c'16
                    }   % measure
                }

        """
        return super(IncisedRhythmMaker, self).division_masks

    @property
    def duration_specifier(self) -> typing.Optional[DurationSpecifier]:
        r"""
        Gets duration specifier.

        ..  container:: example

            Spells durations with the fewest number of glyphs:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'2..
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'2
                        ~
                        c'8
                        r8
                    }   % measure
                }

        ..  container:: example

            Forbids notes with written duration greater than or equal to
            ``1/2``:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_duration=(1, 2),
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'4
                        ~
                        c'4
                        ~
                        c'4.
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'4
                        ~
                        c'4
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'4
                        ~
                        c'4
                        ~
                        c'8
                        r8
                    }   % measure
                }

        ..  container:: example

            Spells all divisions metrically when ``spell_metrically`` is true:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         spell_metrically=True,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'4.
                        ~
                        c'4
                        ~
                        c'4
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'4.
                        ~
                        c'4
                        r8
                    }   % measure
                }

        ..  container:: example

            Spells only unassignable durations metrically when
            ``spell_metrically`` is ``'unassignable'``:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         spell_metrically='unassignable',
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'2..
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'4.
                        ~
                        c'4
                        r8
                    }   % measure
                }

        ..  container:: example

            Rewrites meter:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         rewrite_meter=True,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'2..
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'4.
                        ~
                        c'4
                        r8
                    }   % measure
                }

        Returns duration specifier or none.
        """
        return super(IncisedRhythmMaker, self).duration_specifier

    @property
    def extra_counts_per_division(self) -> typing.Optional[typing.List[int]]:
        """
        Gets extra counts per division.
        """
        if self._extra_counts_per_division:
            return list(self._extra_counts_per_division)
        return None

    @property
    def incise_specifier(self) -> typing.Optional[InciseSpecifier]:
        r"""
        Gets incise specifier.

        ..  container:: example

            Doesn't incise:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker()

            >>> divisions = [(5, 8), (5, 8), (5, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 5/8
                        c'2
                        ~
                        c'8
                    }   % measure
                    {   % measure
                        c'2
                        ~
                        c'8
                    }   % measure
                    {   % measure
                        c'2
                        ~
                        c'8
                    }   % measure
                }

        ..  container:: example

            Fills divisions with notes. Incises outer divisions only:

            >>> incise_specifier = abjadext.rmakers.InciseSpecifier(
            ...     prefix_talea=[-8, -7],
            ...     prefix_counts=[2],
            ...     suffix_talea=[-3],
            ...     suffix_counts=[4],
            ...     talea_denominator=32,
            ...     outer_divisions_only=True,
            ...     )
            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=incise_specifier,
            ...     )

            >>> divisions = [(5, 8), (5, 8), (5, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 5/8
                        r4
                        r8..
                        c'8
                        ~
                        [
                        c'32
                        ]
                    }   % measure
                    {   % measure
                        c'2
                        ~
                        c'8
                    }   % measure
                    {   % measure
                        c'4
                        r16.
                        r16.
                        r16.
                        r16.
                    }   % measure
                }

        ..  container:: example

            Fills divisions with rests. Incises outer divisions only:

            >>> incise_specifier = abjadext.rmakers.InciseSpecifier(
            ...     prefix_talea=[7, 8],
            ...     prefix_counts=[2],
            ...     suffix_talea=[3],
            ...     suffix_counts=[4],
            ...     talea_denominator=32,
            ...     fill_with_notes=False,
            ...     outer_divisions_only=True,
            ...     )
            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=incise_specifier,
            ...     )

            >>> divisions = [(5, 8), (5, 8), (5, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 5/8
                        c'8..
                        c'4
                        r8
                        r32
                    }   % measure
                    {   % measure
                        r2
                        r8
                    }   % measure
                    {   % measure
                        r4
                        c'16.
                        [
                        c'16.
                        c'16.
                        c'16.
                        ]
                    }   % measure
                }

        """
        return self._incise_specifier

    @property
    def logical_tie_masks(self) -> typing.Optional[abjad.PatternTuple]:
        r"""
        Gets logical tie masks.

        ..  container:: example

            No logical tie masks:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         outer_divisions_only=True,
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=16,
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 4/8
                        r16
                        c'4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'4.
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'4
                        ~
                        c'16
                        r16
                    }   % measure
                }

        ..  container:: example

            Silences every other logical tie:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         outer_divisions_only=True,
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=16,
            ...         ),
            ...     logical_tie_masks=[
            ...         abjadext.rmakers.silence([1], 2),
            ...         ],
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 4/8
                        r16
                        r4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'4.
                    }   % measure
                    {   % measure
                        \time 4/8
                        r2
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'4
                        ~
                        c'16
                        r16
                    }   % measure
                }

        """
        return super(IncisedRhythmMaker, self).logical_tie_masks

    @property
    def replace_rests_with_skips(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker should replace rests with skips.

        ..  container:: example

            Does not replace rests with skips:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         fill_with_notes=False,
            ...         prefix_talea=[1],
            ...         prefix_counts=[1],
            ...         talea_denominator=16,
            ...         ),
            ...     replace_rests_with_skips=False,
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 4/8
                        c'16
                        r4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'16
                        r4
                        r16
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'16
                        r4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'16
                        r4
                        r16
                    }   % measure
                }

        ..  container:: example

            Does replace rests with skips:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         fill_with_notes=False,
            ...         prefix_talea=[1],
            ...         prefix_counts=[1],
            ...         talea_denominator=16,
            ...         ),
            ...     replace_rests_with_skips=True,
            ...     )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 4/8
                        c'16
                        s4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'16
                        s4
                        s16
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'16
                        s4..
                    }   % measure
                    {   % measure
                        \time 3/8
                        c'16
                        s4
                        s16
                    }   % measure
                }

            Use in keyboard and other polyphonic selections where other voices
            provide rhythmic alignment.

        """
        return self._replace_rests_with_skips

    @property
    def split_divisions_by_counts(self) -> typing.Optional[typing.List[int]]:
        """
        Gets secondary divisions.
        """
        return self._split_divisions_by_counts

    @property
    def tie_specifier(self) -> typing.Optional[TieSpecifier]:
        r"""
        Gets tie specifier.

        ..  container:: example

            Does not tie across divisions:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'2..
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'2
                        ~
                        c'8
                        r8
                    }   % measure
                }

        ..  container:: example

            Ties across divisions:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'2..
                        ~
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                        ~
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'2
                        ~
                        c'8
                        r8
                    }   % measure
                }

        ..  container:: example

            Patterns ties across divisions:

            >>> pattern = abjad.Pattern(
            ...     indices=[0],
            ...     period=2,
            ...     )
            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=pattern,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'2..
                        ~
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'2
                        ~
                        c'8
                        r8
                    }   % measure
                }

        ..  container:: example

            Uses repeat ties:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         repeat_ties=True,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'2..
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                        \repeatTie
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'2
                        \repeatTie
                        c'8
                        \repeatTie
                        r8
                    }   % measure
                }

        ..  container:: example

            Strips all ties:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         strip_ties=True,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'2..
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'2
                        c'8
                        r8
                    }   % measure
                }

        ..  container:: example

            Spells durations metrically and then strips all ties:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         spell_metrically=True,
            ...         ),
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         strip_ties=True,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        r8
                        c'4.
                        c'4
                        c'4
                    }   % measure
                    {   % measure
                        \time 4/8
                        c'2
                    }   % measure
                    {   % measure
                        \time 6/8
                        c'4.
                        c'4
                        r8
                    }   % measure
                }

        """
        return super(IncisedRhythmMaker, self).tie_specifier

    @property
    def tuplet_specifier(self) -> typing.Optional[TupletSpecifier]:
        r"""
        Gets tuplet specifier.

        ..  container:: example

            Makes augmentations:

            >>> rhythm_maker = abjadext.rmakers.IncisedRhythmMaker(
            ...     extra_counts_per_division=[1],
            ...     incise_specifier=abjadext.rmakers.InciseSpecifier(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         diminution=False,
            ...         ),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 8/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 16/9 {
                            r16
                            c'2
                        }
                    }   % measure
                    {   % measure
                        \time 4/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 8/5 {
                            c'4
                            ~
                            c'16
                        }
                    }   % measure
                    {   % measure
                        \time 6/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/7 {
                            c'4.
                            r16
                        }
                    }   % measure
                }

        """
        return super(IncisedRhythmMaker, self).tuplet_specifier
