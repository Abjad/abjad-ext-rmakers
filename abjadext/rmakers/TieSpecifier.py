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

    __documentation_section__ = "Specifiers"

    __slots__ = (
        "_attach_repeat_ties",
        "_attach_ties",
        "_detach_repeat_ties",
        "_detach_ties",
        "_repeat_ties",
        "_selector",
        "_tie_across_divisions",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        attach_repeat_ties: bool = None,
        attach_ties: bool = None,
        detach_repeat_ties: bool = None,
        detach_ties: bool = None,
        repeat_ties: typing.Union[
            bool, abjad.IntegerPair, abjad.DurationInequality
        ] = None,
        selector: abjad.SelectorTyping = None,
        tie_across_divisions: typing.Union[bool, abjad.IntegerSequence] = None,
    ) -> None:
        if attach_repeat_ties is not None:
            attach_repeat_ties = bool(attach_repeat_ties)
        self._attach_repeat_ties = attach_repeat_ties
        if attach_ties is not None:
            attach_ties = bool(attach_ties)
        self._attach_ties = attach_ties
        if detach_repeat_ties is not None:
            detach_repeat_ties = bool(detach_repeat_ties)
        self._detach_repeat_ties = detach_repeat_ties
        if detach_ties is not None:
            detach_ties = bool(detach_ties)
        self._detach_ties = detach_ties
        repeat_ties_ = repeat_ties
        if isinstance(repeat_ties, tuple) and len(repeat_ties) == 2:
            repeat_ties_ = abjad.DurationInequality(
                operator_string=">=", duration=repeat_ties
            )
        if repeat_ties_ is not None:
            assert isinstance(repeat_ties_, (bool, abjad.DurationInequality))
        self._repeat_ties = repeat_ties_
        if isinstance(selector, str):
            selector = eval(selector)
            assert isinstance(selector, abjad.Expression)
        self._selector = selector
        prototype = (
            type(None),
            bool,
            collections.Sequence,
            abjad.Pattern,
            abjad.PatternTuple,
        )
        assert isinstance(tie_across_divisions, prototype)
        self._tie_across_divisions = tie_across_divisions

    ### SPECIAL METHODS ###

    def __call__(self, staff, *, tag: str = None) -> None:
        """
        Calls tie specifier on ``selections``.
        """
        assert isinstance(staff, abjad.Staff), repr(staff)
        #        time_signature_voice = staff["TimeSignatureVoice"]
        #        durations = [abjad.inspect(_).duration() for _ in time_signature_voice]
        #        music_voice = staff["MusicVoice"]
        #        selections = music_voice[:].partition_by_durations(durations)
        #        selections = list(selections)
        self._attach_repeat_ties_(staff)
        self._attach_ties_(staff)
        self._detach_ties_(staff)
        self._detach_repeat_ties_(staff)
        self._tie_across_divisions_(staff)
        self._configure_repeat_ties(staff)

    def __eq__(self, argument) -> bool:
        """
        Is true when all initialization values of Abjad value object equal
        the initialization values of ``argument``.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __format__(self, format_specification="") -> str:
        """
        Formats tie specifier.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __hash__(self) -> int:
        """
        Hashes tie specifier.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __repr__(self) -> str:
        """
        Gets interpreter representation of tie specifier.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _attach_repeat_ties_(self, staff, tag: str = None):
        from .RhythmMaker import RhythmMaker

        if not self.attach_repeat_ties:
            return
        selections = RhythmMaker._select_by_measure(staff)
        selection_ = selections
        if self.selector is not None:
            selection_ = self.selector(selections)
        for note in abjad.select(selection_).notes():
            tie = abjad.RepeatTie()
            abjad.attach(tie, note, tag=tag)

    def _attach_ties_(self, staff, tag: str = None):
        from .RhythmMaker import RhythmMaker

        if not self.attach_ties:
            return
        selections = RhythmMaker._select_by_measure(staff)
        selection_ = selections
        if self.selector is not None:
            selection_ = self.selector(selections)
        for note in abjad.select(selection_).notes():
            tie = abjad.TieIndicator()
            abjad.attach(tie, note, tag=tag)

    def _detach_repeat_ties_(self, staff, tag: str = None):
        from .RhythmMaker import RhythmMaker

        if not self.detach_repeat_ties:
            return
        selections = RhythmMaker._select_by_measure(staff)
        selection_ = selections
        if self.selector is not None:
            selection_ = self.selector(selections)
        for note in abjad.select(selection_).notes():
            abjad.detach(abjad.RepeatTie, note)

    def _detach_ties_(self, staff, tag: str = None):
        from .RhythmMaker import RhythmMaker

        if not self.detach_ties:
            return
        selections = RhythmMaker._select_by_measure(staff)
        selection_ = selections
        if self.selector is not None:
            selection_ = self.selector(selections)
        for note in abjad.select(selection_).notes():
            abjad.detach(abjad.TieIndicator, note)

    def _configure_repeat_ties(self, staff):
        from .RhythmMaker import RhythmMaker

        if not self.repeat_ties:
            return
        selections = RhythmMaker._select_by_measure(staff)
        add_repeat_ties = []
        for leaf in abjad.iterate(selections).leaves():
            if abjad.inspect(leaf).has_indicator(abjad.TieIndicator):
                next_leaf = abjad.inspect(leaf).leaf(1)
                if next_leaf is not None:
                    add_repeat_ties.append(next_leaf)
                abjad.detach(abjad.TieIndicator, leaf)
        for leaf in add_repeat_ties:
            repeat_tie = abjad.RepeatTie()
            abjad.attach(repeat_tie, leaf)

    def _tie_across_divisions_(self, staff):
        from .RhythmMaker import RhythmMaker

        if not self.tie_across_divisions:
            return
        selections = RhythmMaker._select_by_measure(staff)
        length = len(selections)
        tie_across_divisions = self.tie_across_divisions
        if isinstance(tie_across_divisions, bool):
            tie_across_divisions = [tie_across_divisions]
        if not isinstance(tie_across_divisions, abjad.Pattern):
            tie_across_divisions = abjad.Pattern.from_vector(
                tie_across_divisions
            )
        pairs = abjad.sequence(selections).nwise()
        rest_prototype = (abjad.Rest, abjad.MultimeasureRest)
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

    ### PUBLIC PROPERTIES ###

    @property
    def attach_repeat_ties(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker attaches repeat-ties to notes in selection.

        ..  container:: example

            TIE-ACROSS-DIVISIONS RECIPE. Attaches repeat-ties to first note in
            nonfirst tuplets:

            >>> selector = abjad.select().tuplets()[1:]
            >>> selector = selector.map(abjad.select().note(0))
            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_repeat_ties=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

            With pattern:

            >>> pattern = abjad.Pattern([1], period=2)
            >>> selector = abjad.select().tuplets()[pattern]
            >>> selector = selector.map(abjad.select().note(0))
            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_repeat_ties=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        """
        return self._attach_repeat_ties

    @property
    def attach_ties(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker attaches ties to notes in selection.

        ..  container:: example

            TIE-CONSECUTIVE-NOTES RECIPE. Attaches ties notes in selection:

            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=abjad.select().notes()[5:15],
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            TIE-ACROSS-DIVISIONS RECIPE. Attaches ties to last note in nonlast
            tuplets:

            >>> selector = abjad.select().tuplets()[:-1]
            >>> selector = selector.map(abjad.select().note(-1))
            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

            With pattern:

            >>> pattern = abjad.Pattern([0], period=2)
            >>> selector = abjad.select().tuplets()[pattern]
            >>> selector = selector.map(abjad.select().note(-1))
            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            TIE-WITHIN-DIVISIONS RECIPE:

            >>> selector = abjad.select().tuplets()
            >>> nonlast_notes = abjad.select().notes()[:-1]
            >>> selector = selector.map(nonlast_notes)
            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         detach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                    }
                >>

            With pattern:

            >>> pattern = abjad.Pattern([0], period=2)
            >>> selector = abjad.select().tuplets()[pattern]
            >>> selector = selector.map(abjad.select().notes()[:-1])
            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        """
        return self._attach_ties

    @property
    def detach_repeat_ties(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker detaches repeat ties.

        ..  container:: example

            Attaches repeat-ties to nonfirst notes; then detaches ties from
            select notes:

            >>> pattern = abjad.Pattern([0], period=4)
            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_repeat_ties=True,
            ...         selector=abjad.select().notes()[1:],
            ...         ),
            ...     abjadext.rmakers.TieSpecifier(
            ...         detach_repeat_ties=True,
            ...         selector=abjad.select().notes()[pattern],
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            \repeatTie
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            \repeatTie
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            \repeatTie
                            c'8
                            \repeatTie
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            \repeatTie
                            ]
                        }
                        \times 2/3 {
                            c'8
                            \repeatTie
                            [
                            c'8
                            c'8
                            \repeatTie
                            ]
                        }
                    }
                >>

        """
        return self._detach_repeat_ties

    @property
    def detach_ties(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker detaches ties.

        ..  container:: example

            Attaches ties to nonlast notes; then detaches ties from select
            notes:

            >>> pattern = abjad.Pattern([0], period=4)
            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=abjad.select().notes()[:-1],
            ...         ),
            ...     abjadext.rmakers.TieSpecifier(
            ...         detach_ties=True,
            ...         selector=abjad.select().notes()[pattern],
            ...         ),
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_each_division=True,
            ...     ),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            ~
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            ~
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            ~
                            c'8
                            ~
                            ]
                        }
                        \times 2/3 {
                            c'8
                            ~
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                >>

        """
        return self._detach_ties

    @property
    def repeat_ties(
        self
    ) -> typing.Union[bool, abjad.DurationInequality, None]:
        r"""
        Is true when all notes format with LilyPond ``\repeatTie``.

        Is duration inequality only those notes that satisfy duration
        inequality formath with LilyPond ``\repeatTie``.
        """
        return self._repeat_ties

    @property
    def selector(self) -> typing.Optional[abjad.Expression]:
        """
        Gets selector.
        """
        return self._selector

    @property
    def tie_across_divisions(
        self
    ) -> typing.Union[bool, abjad.IntegerSequence, None]:
        r"""
        Is true when rhythm-maker ties across divisons.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=True,
            ...         ),
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
