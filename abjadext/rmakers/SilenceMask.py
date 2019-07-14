import abjad
import typing


class SilenceMask(object):
    r"""
    Silence mask.

    ..  container:: example

        Changes logical ties 1 and 2 to rests:

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.SilenceMask(
        ...         selector=abjad.select().logical_ties()[1:3],
        ...     ),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
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
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'4..
                    r4.
                    r4..
                    c'4.
                }
            >>

    ..  container:: example

        Changes logical ties -1 and -2 to rests:

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.SilenceMask(
        ...         selector=abjad.select().logical_ties()[-2:]
        ...     ),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
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
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'4..
                    c'4.
                    r4..
                    r4.
                }
            >>

    ..  container:: example

        Changes patterned selection of logical ties to rests:

        >>> pattern_1 = abjad.index_all()
        >>> pattern_2 = abjad.index_first(1)
        >>> pattern_3 = abjad.index_last(1)
        >>> pattern = pattern_1 ^ pattern_2 ^ pattern_3
        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.SilenceMask(
        ...         selector=abjad.select().logical_ties()[pattern],
        ...     ),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
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
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'4..
                    r4.
                    r4..
                    c'4.
                }
            >>

    ..  container:: example

        Changes patterned selection of logical ties to rests. Works with
        inverted composite pattern:

        >>> pattern_1 = abjad.index_all()
        >>> pattern_2 = abjad.index_first(1)
        >>> pattern_3 = abjad.index_last(1)
        >>> pattern = pattern_1 ^ pattern_2 ^ pattern_3
        >>> pattern = ~pattern
        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.SilenceMask(
        ...         selector=abjad.select().logical_ties()[pattern],
        ...     ),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
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
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    r4..
                    c'4.
                    c'4..
                    r4.
                }
            >>

    """

    ### CLASS VARIABLES ###

    __slots__ = ("_selector", "_use_multimeasure_rests")

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.SelectorTyping,
        *,
        use_multimeasure_rests: bool = None,
    ) -> None:
        if isinstance(selector, str):
            selector = eval(selector)
            assert isinstance(selector, abjad.Expression)
        self._selector = selector
        if use_multimeasure_rests is not None:
            assert isinstance(use_multimeasure_rests, type(True))
        self._use_multimeasure_rests = use_multimeasure_rests

    ### SPECIAL METHODS ###

    def __call__(
        self, staff, *, previous_logical_ties_produced=None, tag=None
    ):
        if isinstance(staff, abjad.Staff):
            selection = staff["MusicVoice"]
        else:
            selection = staff

        selections = self.selector(
            selection, previous=previous_logical_ties_produced
        )
        # will need to restore for statal rhythm-makers:
        # logical_ties = abjad.select(selections).logical_ties()
        # logical_ties = list(logical_ties)
        # total_logical_ties = len(logical_ties)
        # previous_logical_ties_produced = self._previous_logical_ties_produced()
        # if self._previous_incomplete_last_note():
        #    previous_logical_ties_produced -= 1
        if self.use_multimeasure_rests is True:
            leaf_maker = abjad.LeafMaker(tag=tag, use_multimeasure_rests=True)
            for selection in selections:
                duration = abjad.inspect(selection).duration()
                new_selection = leaf_maker([None], [duration])
                abjad.mutate(selection).replace(new_selection)
        else:
            leaves = abjad.select(selections).leaves()
            for leaf in leaves:
                rest = abjad.Rest(leaf.written_duration, tag=tag)
                if leaf.multiplier is not None:
                    rest.multiplier = leaf.multiplier
                previous_leaf = abjad.inspect(leaf).leaf(-1)
                next_leaf = abjad.inspect(leaf).leaf(1)
                abjad.mutate(leaf).replace([rest])
                if previous_leaf is not None:
                    abjad.detach(abjad.TieIndicator, previous_leaf)
                abjad.detach(abjad.TieIndicator, rest)
                abjad.detach(abjad.RepeatTie, rest)
                if next_leaf is not None:
                    abjad.detach(abjad.RepeatTie, next_leaf)

    def __format__(self, format_specification="") -> str:
        """
        Formats silence mask.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    @property
    def selector(self) -> typing.Optional[abjad.Expression]:
        """
        Gets selector.
        """
        return self._selector

    @property
    def use_multimeasure_rests(self) -> typing.Optional[bool]:
        """
        Is true when silence mask uses multimeasure rests.
        """
        return self._use_multimeasure_rests
