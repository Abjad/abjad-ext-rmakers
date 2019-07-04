import abjad
import inspect
import typing


class SilenceMask(object):
    r"""
    Silence mask.

    ..  container:: example

        >>> pattern = abjad.index([0, 1, 7], 16)
        >>> mask = abjadext.rmakers.SilenceMask(pattern)

        >>> abjad.f(mask)
        abjadext.rmakers.SilenceMask(
            pattern=abjad.index([0, 1, 7], period=16),
            )

    ..  container:: example

        With composite pattern:

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

        With inverted composite pattern:

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

    __documentation_section__ = "Masks"

    __slots__ = (
        "_pattern",
        "_selector",
        "_template",
        "_use_multimeasure_rests",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        pattern: abjad.Pattern = None,
        *,
        selector: abjad.SelectorTyping = None,
        template: str = None,
        use_multimeasure_rests: bool = None,
    ) -> None:
        if pattern is not None and selector is not None:
            raise Exception("set only pattern or selector.")
        if pattern is None:
            pattern = abjad.index_all()
        assert isinstance(pattern, abjad.Pattern), repr(pattern)
        self._pattern = pattern
        if isinstance(selector, str):
            selector = eval(selector)
            assert isinstance(selector, abjad.Expression)
        self._selector = selector
        self._template = template
        if use_multimeasure_rests is not None:
            assert isinstance(use_multimeasure_rests, type(True))
        self._use_multimeasure_rests = use_multimeasure_rests

    ### SPECIAL METHODS ###

    def __call__(
        self, staff, *, previous_logical_ties_produced=None, tag=None
    ):
        if self.selector is None:
            raise Exception("call silence mask with selector.")
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
        Formats Abjad object.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __invert__(self) -> "SilenceMask":
        """
        Inverts pattern.
        """
        pattern = ~self.pattern
        inverted = pattern.inverted or None
        return SilenceMask.silence(pattern.indices, pattern.period, inverted)

    def __repr__(self) -> str:
        """
        Gets interpreter representation.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _get_format_specification(self):
        if self.template is None:
            return abjad.FormatSpecification(client=self)
        return abjad.FormatSpecification(
            client=self,
            repr_is_indented=False,
            storage_format_is_indented=False,
            storage_format_args_values=[self.template],
            storage_format_forced_override=self.template,
            storage_format_kwargs_names=(),
        )

    @staticmethod
    def _get_template(frame):
        try:
            frame_info = inspect.getframeinfo(frame)
            function_name = frame_info.function
            arguments = abjad.Expression._wrap_arguments(
                frame, static_class=SilenceMask
            )
            template = f"abjadext.rmakers.{function_name}({arguments})"
        finally:
            del frame
        return template

    ### PUBLIC PROPERTIES ###

    @property
    def pattern(self) -> abjad.Pattern:
        """
        Gets pattern.
        """
        return self._pattern

    @property
    def selector(self) -> typing.Optional[abjad.Expression]:
        """
        Gets selector.
        """
        return self._selector

    @property
    def template(self) -> typing.Optional[str]:
        """
        Gets template.
        """
        return self._template

    @property
    def use_multimeasure_rests(self) -> typing.Optional[bool]:
        """
        Is true when silence mask uses multimeasure rests.

        ..  container:: example

            Without multimeasure rests:

            >>> mask = abjadext.rmakers.SilenceMask(
            ...     abjad.index([0, 1, 7], 16),
            ...     use_multimeasure_rests=False,
            ...     )

            >>> mask.use_multimeasure_rests
            False

        ..  container:: example

            With multimeasure rests:

            >>> mask = abjadext.rmakers.SilenceMask(
            ...     abjad.index([0, 1, 7], 16),
            ...     use_multimeasure_rests=True,
            ...     )

            >>> mask.use_multimeasure_rests
            True

        """
        return self._use_multimeasure_rests

    ### PUBLIC METHODS ###

    @staticmethod
    def silence(
        indices: typing.Sequence[int],
        period: int = None,
        inverted: bool = None,
        use_multimeasure_rests: bool = None,
    ) -> "SilenceMask":
        r"""
        Makes silence mask that matches ``indices``.

        ..  container:: example

            Silences divisions 1 and 2:

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

            Silences divisions -1 and -2:

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


        """
        pattern = abjad.index(indices, period=period, inverted=inverted)
        template = SilenceMask._get_template(inspect.currentframe())
        return SilenceMask(
            pattern=pattern,
            template=template,
            use_multimeasure_rests=use_multimeasure_rests,
        )
