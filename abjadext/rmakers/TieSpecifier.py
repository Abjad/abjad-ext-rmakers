import abjad
import collections
import itertools
import typing
from . import typings


class TieSpecifier(object):
    """
    Tie specifier.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Specifiers'

    __slots__ = (
        '_repeat_ties',
        '_strip_ties',
        '_tie_across_divisions',
        '_tie_consecutive_notes',
        '_tie_within_divisions',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        repeat_ties: typing.Union[
            bool,
            typings.IntegerPair,
            abjad.DurationInequality,
            ] = None,
        strip_ties: bool = None,
        tie_across_divisions: bool = None,
        tie_consecutive_notes: bool = None,
        tie_within_divisions: bool = None,
        ) -> None:
        repeat_ties_ = repeat_ties
        if isinstance(repeat_ties, tuple) and len(repeat_ties) == 2:
            repeat_ties_ = abjad.DurationInequality(
                operator_string='>=',
                duration=repeat_ties,
                )
        if repeat_ties_ is not None:
            assert isinstance(repeat_ties_, (bool, abjad.DurationInequality))
        self._repeat_ties = repeat_ties_
        if strip_ties is not None:
            strip_ties = bool(strip_ties)
        self._strip_ties = strip_ties
        prototype = (
            type(None),
            bool,
            collections.Sequence,
            abjad.Pattern,
            abjad.PatternTuple,
            )
        assert isinstance(tie_across_divisions, prototype)
        self._tie_across_divisions = tie_across_divisions
        if tie_consecutive_notes is not None:
            tie_consecutive_notes = bool(tie_consecutive_notes)
        self._tie_consecutive_notes = tie_consecutive_notes
        if self.tie_consecutive_notes and self.strip_ties:
            message = 'can not tie leaves and strip ties at same time.'
            raise Exception(message)
        if tie_within_divisions is not None:
            tie_within_divisions = bool(tie_within_divisions)
        self._tie_within_divisions = tie_within_divisions

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.List[abjad.NonreducedFraction],
        ) -> None:
        """
        Calls tie specifier on ``divisions``.
        """
        self._tie_within_divisions_(divisions)
        self._tie_across_divisions_(divisions)
        if self.tie_consecutive_notes:
            self._tie_consecutive_notes_(divisions)
        self._strip_ties_(divisions)
        self._configure_repeat_ties(divisions)

    def __eq__(self, argument) -> bool:
        """
        Is true when all initialization values of Abjad value object equal
        the initialization values of ``argument``.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __format__(self, format_specification='') -> str:
        """
        Formats Abjad object.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __hash__(self) -> int:
        """
        Hashes Abjad value object.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f'unhashable type: {self}')
        return result

    def __repr__(self) -> str:
        """
        Gets interpreter representation.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _configure_repeat_ties(self, divisions):
        if not self.repeat_ties:
            return
        temporary_container = abjad.Container(divisions)
        add_repeat_ties = []
        for leaf in abjad.iterate(divisions).leaves():
            if abjad.inspect(leaf).has_indicator(abjad.TieIndicator):
                next_leaf = abjad.inspect(leaf).leaf(1)
                if next_leaf is not None:
                    add_repeat_ties.append(next_leaf)
                abjad.detach(abjad.TieIndicator, leaf)
        for leaf in add_repeat_ties:
            repeat_tie = abjad.RepeatTie()
            abjad.attach(repeat_tie, leaf)
        temporary_container[:] = []

    def _get_format_specification(self):
        return abjad.FormatSpecification(client=self)

    def _strip_ties_(self, divisions):
        if not self.strip_ties:
            return
        for division in divisions:
            for leaf in abjad.iterate(division).leaves():
                abjad.detach(abjad.TieIndicator, leaf)
                abjad.detach(abjad.RepeatTie, leaf)

    def _tie_across_divisions_(self, divisions):
        if not self.tie_across_divisions:
            return
        if self.strip_ties:
            return
        if self.tie_consecutive_notes:
            return
        length = len(divisions)
        tie_across_divisions = self.tie_across_divisions
        if isinstance(tie_across_divisions, bool):
            tie_across_divisions = [tie_across_divisions]
        if not isinstance(tie_across_divisions, abjad.Pattern):
            tie_across_divisions = abjad.Pattern.from_vector(
                tie_across_divisions)
        pairs = abjad.sequence(divisions).nwise()
        rest_prototype = (abjad.Rest, abjad.MultimeasureRest)
        temporary_container = abjad.Container(divisions)
        for i, pair in enumerate(pairs):
            if not tie_across_divisions.matches_index(i, length):
                continue
            division_one, division_two = pair
            leaf_one = next(abjad.iterate(division_one).leaves(reverse=True))
            leaf_two = next(abjad.iterate(division_two).leaves())
            leaves = [leaf_one, leaf_two]
            if isinstance(leaf_one, rest_prototype):
                continue
            if isinstance(leaf_two, rest_prototype):
                continue
            pitched_prototype = (abjad.Note, abjad.Chord)
            if not all(isinstance(_, pitched_prototype) for _ in leaves):
                continue
            logical_tie_one = abjad.inspect(leaf_one).logical_tie()
            logical_tie_two = abjad.inspect(leaf_two).logical_tie()
            if logical_tie_one == logical_tie_two:
                continue
            combined_logical_tie = logical_tie_one + logical_tie_two
            pitch_set = abjad.PitchSet(combined_logical_tie)
            if 1 < len(pitch_set):
                continue
            for leaf in combined_logical_tie:
                abjad.detach(abjad.TieIndicator, leaf)
                abjad.detach(abjad.RepeatTie, leaf)
            abjad.tie(combined_logical_tie, repeat=self.repeat_ties)
        temporary_container[:] = []

    def _tie_consecutive_notes_(self, divisions):
        leaves = list(abjad.iterate(divisions).leaves())
        for leaf in leaves:
            abjad.detach(abjad.TieIndicator, leaf)
            abjad.detach(abjad.RepeatTie, leaf)
        pairs = itertools.groupby(leaves, lambda _: _.__class__)
        def _get_pitches(component):
            if isinstance(component, abjad.Note):
                return component.written_pitch
            elif isinstance(component, abjad.Chord):
                return component.written_pitches
            else:
                raise TypeError(component)
        for class_, group in pairs:
            group = list(group)
            if not isinstance(group[0], (abjad.Note, abjad.Chord)):
                continue
            subpairs = itertools.groupby(group, lambda _: _get_pitches(_))
            for pitches, subgroup in subpairs:
                subgroup = list(subgroup)
                if len(subgroup) == 1:
                    continue
                abjad.tie(subgroup)

    def _tie_within_divisions_(self, divisions):
        if not self.tie_within_divisions:
            return
        for division in divisions:
            self._tie_consecutive_notes_(division)

    ### PUBLIC PROPERTIES ###

    @property
    def repeat_ties(self) -> typing.Union[
        bool, abjad.DurationInequality, None,
        ]:
        r"""
        Is true when ties should format all notes in tie with LilyPond
        ``\repeatTie``.

        Is duration inequality when ties should format with LilyPond
        ``\repeatTie`` all notes that satisfy duration inequality.
        """
        return self._repeat_ties

    @property
    def strip_ties(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker strips ties.

        ..  container:: example

            Without ``strip_ties``:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(5, 2)],
            ...     )

            >>> divisions = [(4, 8), (4, 8), (4, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            c'4
                        }
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            c'4
                        }
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            c'4
                        }
                    }
                >>

            With ``strip_ties``:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(5, 2)],
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         strip_ties=True,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (4, 8), (4, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/7 {
                            c'2
                            c'8
                            c'4
                        }
                        \times 4/7 {
                            c'2
                            c'8
                            c'4
                        }
                        \times 4/7 {
                            c'2
                            c'8
                            c'4
                        }
                    }
                >>

        """
        return self._strip_ties

    @property
    def tie_across_divisions(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker ties across divisons.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(5, 2)],
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (4, 8), (4, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            c'4
                            ~
                        }
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            c'4
                            ~
                        }
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            c'4
                        }
                    }
                >>

        Set to true, false or to a boolean vector.
        """
        return self._tie_across_divisions

    @property
    def tie_consecutive_notes(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker should tie consecutive notes.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(5, 2)],
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_consecutive_notes=True,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (4, 8), (4, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            ~
                            c'4
                            ~
                        }
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            ~
                            c'4
                            ~
                        }
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            ~
                            c'4
                        }
                    }
                >>

        """
        return self._tie_consecutive_notes

    @property
    def tie_within_divisions(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker ties within divisions.

        ..  container:: example

            Ties within divisions:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(5, 2)],
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_within_divisions=True,
            ...         ),
            ...     )

            >>> divisions = [(4, 8), (4, 8), (4, 8)]
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
                        \time 4/8
                        s1 * 1/2
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            ~
                            c'4
                        }
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            ~
                            c'4
                        }
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                            ~
                            c'4
                        }
                    }
                >>

        """
        return self._tie_within_divisions
