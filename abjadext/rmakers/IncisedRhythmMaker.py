import abjad
import typing
from . import commands as _commands
from . import specifiers as _specifiers
from .RhythmMaker import RhythmMaker


class IncisedRhythmMaker(RhythmMaker):
    r"""
    Incised rhythm-maker.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_extra_counts", "_incise")

    ### INITIALIZER ###

    def __init__(
        self,
        *commands: _commands.Command,
        extra_counts: typing.Sequence[int] = None,
        incise: _specifiers.Incise = None,
        spelling: _specifiers.Spelling = None,
        tag: str = None,
    ) -> None:
        RhythmMaker.__init__(self, *commands, spelling=spelling, tag=tag)
        prototype = (_specifiers.Incise, type(None))
        assert isinstance(incise, prototype)
        self._incise = incise
        if extra_counts is not None:
            extra_counts = tuple(extra_counts)
        assert (
            extra_counts is None
            or abjad.mathtools.all_are_nonnegative_integer_equivalent_numbers(
                extra_counts
            )
        ), extra_counts
        self._extra_counts = extra_counts

    ### PRIVATE METHODS ###

    def _get_incise_specifier(self):
        if self.incise is not None:
            return self.incise
        return _specifiers.Incise()

    def _make_division_incised_numeric_map(
        self,
        divisions=None,
        prefix_talea=None,
        prefix_counts=None,
        suffix_talea=None,
        suffix_counts=None,
        extra_counts=None,
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
            prolation_addendum = extra_counts[pair_index]
            if isinstance(division, tuple):
                numerator = division[0] + (prolation_addendum % division[0])
            else:
                numerator = division.numerator + (
                    prolation_addendum % division.numerator
                )
            numeric_map_part = self._make_numeric_map_part(
                numerator, prefix, suffix
            )
            numeric_map.append(numeric_map_part)
        return numeric_map

    def _make_middle_of_numeric_map_part(self, middle):
        incise = self._get_incise_specifier()
        if not (incise.fill_with_rests):
            if not incise.outer_divisions_only:
                if 0 < middle:
                    if incise.body_ratio is not None:
                        shards = middle / incise.body_ratio
                        return tuple(shards)
                    else:
                        return (middle,)
                else:
                    return ()
            elif incise.outer_divisions_only:
                if 0 < middle:
                    return (middle,)
                else:
                    return ()
            else:
                raise Exception("must incise divisions or output.")
        else:
            if not incise.outer_divisions_only:
                if 0 < middle:
                    return (-abs(middle),)
                else:
                    return ()
            elif incise.outer_divisions_only:
                if 0 < middle:
                    return (-abs(middle),)
                else:
                    return ()
            else:
                raise Exception("must incise divisions or output.")

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        input_ = self._prepare_input()
        prefix_talea = input_[0]
        prefix_counts = input_[1]
        suffix_talea = input_[2]
        suffix_counts = input_[3]
        extra_counts = input_[4]
        counts = {
            "prefix_talea": prefix_talea,
            "suffix_talea": suffix_talea,
            "extra_counts": extra_counts,
        }
        if self.incise is not None:
            talea_denominator = self.incise.talea_denominator
        else:
            talea_denominator = None
        result = self._scale_counts(divisions, talea_denominator, counts)
        divisions = result["divisions"]
        lcd = result["lcd"]
        counts = result["counts"]
        incise = self._get_incise_specifier()
        if not incise.outer_divisions_only:
            numeric_map = self._make_division_incised_numeric_map(
                divisions,
                counts["prefix_talea"],
                prefix_counts,
                counts["suffix_talea"],
                suffix_counts,
                counts["extra_counts"],
            )
        else:
            assert incise.outer_divisions_only
            numeric_map = self._make_output_incised_numeric_map(
                divisions,
                counts["prefix_talea"],
                prefix_counts,
                counts["suffix_talea"],
                suffix_counts,
                counts["extra_counts"],
            )
        selections = self._numeric_map_to_leaf_selections(numeric_map, lcd)
        tuplets = self._make_tuplets(divisions, selections)
        assert all(isinstance(_, abjad.Tuplet) for _ in tuplets)
        return tuplets

    def _make_numeric_map_part(
        self, numerator, prefix, suffix, is_note_filled=True
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
        extra_counts,
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
            prolation_addendum = extra_counts[0]
            if isinstance(divisions[0], abjad.NonreducedFraction):
                numerator = divisions[0].numerator
            else:
                numerator = divisions[0][0]
            numerator += prolation_addendum % numerator
            numeric_map_part = self._make_numeric_map_part(
                numerator, prefix, suffix
            )
            numeric_map.append(numeric_map_part)
        else:
            prolation_addendum = extra_counts[0]
            if isinstance(divisions[0], tuple):
                numerator = divisions[0][0]
            else:
                numerator = divisions[0].numerator
            numerator += prolation_addendum % numerator
            numeric_map_part = self._make_numeric_map_part(
                numerator, prefix, ()
            )
            numeric_map.append(numeric_map_part)
            for i, division in enumerate(divisions[1:-1]):
                index = i + 1
                prolation_addendum = extra_counts[index]
                if isinstance(division, tuple):
                    numerator = division[0]
                else:
                    numerator = division.numerator
                numerator += prolation_addendum % numerator
                numeric_map_part = self._make_numeric_map_part(
                    numerator, (), ()
                )
                numeric_map.append(numeric_map_part)
            try:
                index = i + 2
                prolation_addendum = extra_counts[index]
            except UnboundLocalError:
                index = 1 + 2
                prolation_addendum = extra_counts[index]
            if isinstance(divisions[-1], tuple):
                numerator = divisions[-1][0]
            else:
                numerator = divisions[-1].numerator
            numerator += prolation_addendum % numerator
            numeric_map_part = self._make_numeric_map_part(
                numerator, (), suffix
            )
            numeric_map.append(numeric_map_part)
        return numeric_map

    def _numeric_map_to_leaf_selections(self, numeric_map, lcd):
        selections = []
        specifier = self._get_spelling_specifier()
        for numeric_map_part in numeric_map:
            numeric_map_part = [
                _ for _ in numeric_map_part if _ != abjad.Duration(0)
            ]
            selection = self._make_leaves_from_talea(
                numeric_map_part,
                lcd,
                forbidden_note_duration=specifier.forbidden_note_duration,
                forbidden_rest_duration=specifier.forbidden_rest_duration,
                increase_monotonic=specifier.increase_monotonic,
                tag=self.tag,
            )
            selections.append(selection)
        return selections

    def _prepare_input(self):
        #
        incise = self._get_incise_specifier()
        prefix_talea = incise.prefix_talea or ()
        prefix_talea = abjad.CyclicTuple(prefix_talea)
        #
        prefix_counts = incise.prefix_counts or (0,)
        prefix_counts = abjad.CyclicTuple(prefix_counts)
        #
        suffix_talea = incise.suffix_talea or ()
        suffix_talea = abjad.CyclicTuple(suffix_talea)
        #
        suffix_counts = incise.suffix_counts or (0,)
        suffix_counts = abjad.CyclicTuple(suffix_counts)
        #
        extra_counts = self.extra_counts or ()
        if extra_counts:
            extra_counts = abjad.CyclicTuple(extra_counts)
        else:
            extra_counts = abjad.CyclicTuple([0])
        #
        return (
            prefix_talea,
            prefix_counts,
            suffix_talea,
            suffix_counts,
            extra_counts,
        )

    ### PUBLIC PROPERTIES ###

    @property
    def commands(self) -> typing.List[_commands.Command]:
        r"""
        Gets commands.

        ..  container:: example

            Forces rest at every other tuplet:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         outer_divisions_only=True,
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=16,
            ...     ),
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([1], 2),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )

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
                        r16
                        r4..
                        c'4.
                        r2
                        c'4
                        ~
                        c'16
                        r16
                    }
                >>

        ..  container:: example

            Ties nonlast tuplets:

            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
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
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        r8
                        c'2..
                        ~
                        c'2
                        ~
                        c'2
                        ~
                        c'8
                        r8
                    }
                >>

        ..  container:: example

            Repeat-ties nonfirst tuplets:

            >>> nonfirst_tuplets = abjad.select().tuplets()[1:]
            >>> first_leaf = abjad.select().leaf(0)
            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.repeat_tie(nonfirst_tuplets.map(first_leaf)),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
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
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        r8
                        c'2..
                        c'2
                        \repeatTie
                        c'2
                        \repeatTie
                        ~
                        c'8
                        r8
                    }
                >>

        """
        return super().commands

    @property
    def extra_counts(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets extra counts.
        
        ..  container:: example

            Add one extra count per tuplet:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         extra_counts=[1],
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.force_augmentation(),
            ...     rmakers.beam(),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
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
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 16/9 {
                            r16
                            c'2
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 8/5 {
                            c'4
                            ~
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/7 {
                            c'4.
                            r16
                        }
                    }
                >>

        """
        if self._extra_counts:
            return list(self._extra_counts)
        return None

    @property
    def incise(self) -> typing.Optional[_specifiers.Incise]:
        r"""
        Gets incise specifier.


        ..  container:: example

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[0, 1],
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=16,
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     )

            >>> divisions = 4 * [(5, 16)]
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
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        r16
                        r16
                        c'8.
                        r16
                        c'4
                        r16
                        r16
                        c'8.
                        r16
                    }
                >>

        ..  container:: example

            Fills divisions with notes. Incises outer divisions only:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         prefix_talea=[-8, -7],
            ...         prefix_counts=[2],
            ...         suffix_talea=[-3],
            ...         suffix_counts=[4],
            ...         talea_denominator=32,
            ...         outer_divisions_only=True,
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )

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
                        r4
                        r8..
                        c'8
                        ~
                        [
                        c'32
                        ]
                        c'2
                        ~
                        c'8
                        c'4
                        r16.
                        r16.
                        r16.
                        r16.
                    }
                >>

        ..  container:: example

            Fills divisions with rests. Incises outer divisions only:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         prefix_talea=[7, 8],
            ...         prefix_counts=[2],
            ...         suffix_talea=[3],
            ...         suffix_counts=[4],
            ...         talea_denominator=32,
            ...         fill_with_rests=True,
            ...         outer_divisions_only=True,
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )

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
                        c'8..
                        c'4
                        r8
                        r32
                        r2
                        r8
                        r4
                        c'16.
                        [
                        c'16.
                        c'16.
                        c'16.
                        ]
                    }
                >>

        """
        return self._incise

    @property
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        r"""
        Gets duration specifier.

        ..  container:: example

            Spells durations with the fewest number of glyphs:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
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
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        r8
                        c'2..
                        c'2
                        c'2
                        ~
                        c'8
                        r8
                    }
                >>

        ..  container:: example

            Forbids notes with written duration greater than or equal to
            ``1/2``:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         spelling=rmakers.Spelling(forbidden_note_duration=(1, 2)),
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
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
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        r8
                        c'4
                        ~
                        c'4
                        ~
                        c'4.
                        c'4
                        ~
                        c'4
                        c'4
                        ~
                        c'4
                        ~
                        c'8
                        r8
                    }
                >>

        ..  container:: example

            Rewrites meter:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     rmakers.rewrite_meter(),
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
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
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        r8
                        c'2..
                        c'2
                        c'4.
                        ~
                        c'4
                        r8
                    }
                >>

        """
        return super().spelling

    @property
    def tag(self) -> typing.Optional[str]:
        r"""
        Gets tag.

        ..  container:: example

            Makes augmentations:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.incised(
            ...         extra_counts=[1],
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.force_augmentation(),
            ...     rmakers.beam(),
            ...     tag='INCISED_RHYTHM_MAKER',
            ...     )

            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> abjad.f(lilypond_file[abjad.Score], strict=40)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 8/8
                    s1 * 1
                    \time 4/8
                    s1 * 1/2
                    \time 6/8
                    s1 * 3/4
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text %! INCISED_RHYTHM_MAKER
                    \times 16/9 {                   %! INCISED_RHYTHM_MAKER
                        r16                         %! INCISED_RHYTHM_MAKER
                        c'2                         %! INCISED_RHYTHM_MAKER
                    }                               %! INCISED_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! INCISED_RHYTHM_MAKER
                    \times 8/5 {                    %! INCISED_RHYTHM_MAKER
                        c'4                         %! INCISED_RHYTHM_MAKER
                        ~
                        c'16                        %! INCISED_RHYTHM_MAKER
                    }                               %! INCISED_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! INCISED_RHYTHM_MAKER
                    \times 12/7 {                   %! INCISED_RHYTHM_MAKER
                        c'4.                        %! INCISED_RHYTHM_MAKER
                        r16                         %! INCISED_RHYTHM_MAKER
                    }                               %! INCISED_RHYTHM_MAKER
                }
            >>

        """
        return super().tag
