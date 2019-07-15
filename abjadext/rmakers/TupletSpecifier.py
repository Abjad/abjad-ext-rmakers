import abjad
import copy
import typing


class TupletSpecifier(object):
    """
    Tuplet specifier.

    ..  container:: example

        >>> specifier = rmakers.TupletSpecifier()
        >>> abjad.f(specifier)
        abjadext.rmakers.TupletSpecifier()

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = (
        "_denominator",
        "_diminution",
        "_duration_bracket",
        "_extract_trivial",
        "_force_fraction",
        "_repeat_ties",
        "_rewrite_dots",
        "_rewrite_rest_filled",
        "_rewrite_sustained",
        "_selector",
        "_trivialize",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        denominator: typing.Union[int, abjad.DurationTyping] = None,
        diminution: bool = None,
        duration_bracket: bool = None,
        extract_trivial: bool = None,
        force_fraction: bool = None,
        repeat_ties: bool = None,
        rewrite_dots: bool = None,
        rewrite_rest_filled: bool = None,
        rewrite_sustained: bool = None,
        selector: abjad.SelectorTyping = None,
        trivialize: bool = None,
    ) -> None:
        if isinstance(denominator, tuple):
            denominator = abjad.Duration(denominator)
        if denominator is not None:
            prototype = (int, abjad.Duration)
            assert isinstance(denominator, prototype), repr(denominator)
        self._denominator = denominator
        if diminution is not None:
            diminution = bool(diminution)
        self._diminution = diminution
        if duration_bracket is not None:
            duration_bracket = bool(duration_bracket)
        self._duration_bracket = duration_bracket
        if extract_trivial is not None:
            extract_trivial = bool(extract_trivial)
        self._extract_trivial = extract_trivial
        if force_fraction is not None:
            force_fraction = bool(force_fraction)
        self._force_fraction = force_fraction
        if repeat_ties is not None:
            repeat_ties = bool(repeat_ties)
        self._repeat_ties = repeat_ties
        if rewrite_dots is not None:
            rewrite_dots = bool(rewrite_dots)
        self._rewrite_dots = rewrite_dots
        if rewrite_rest_filled is not None:
            rewrite_rest_fille = bool(rewrite_rest_filled)
        self._rewrite_rest_filled = rewrite_rest_filled
        if rewrite_sustained is not None:
            rewrite_rest_fille = bool(rewrite_sustained)
        self._rewrite_sustained = rewrite_sustained
        if isinstance(selector, str):
            selector = eval(selector)
            assert isinstance(selector, abjad.Expression)
        self._selector = selector
        if trivialize is not None:
            trivialize = bool(trivialize)
        self._trivialize = trivialize

    ### SPECIAL METHODS ###

    def __call__(self, staff, *, tag: str = None) -> None:
        """
        Calls tuplet specifier.
        """
        self._apply_denominator(staff)
        self._force_fraction_(staff)
        self._trivialize_(staff)
        # rewrite dots must follow trivialize:
        self._rewrite_dots_(staff)
        # rewrites must precede extract trivial:
        self._rewrite_sustained_(staff, tag=tag)

        self._rewrite_rest_filled_(staff, tag=tag)
        # extract trivial must follow the other operations:
        self._extract_trivial_(staff)

        # tentatively inserting duration bracket here:
        self._set_duration_bracket(staff)
        # toggle prolation must follow rewrite dots and extract trivial:
        self._toggle_prolation(staff)

    def __eq__(self, argument) -> bool:
        """
        Is true when initialization values of tuplet specifier equal
        initialization values of ``argument``.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __hash__(self) -> int:
        """
        Hashes tuplet specifier.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __format__(self, format_specification="") -> str:
        """
        Formats tuplet specifier.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _apply_denominator(self, staff):
        if not self.denominator:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        denominator = self.denominator
        if isinstance(denominator, tuple):
            denominator = abjad.Duration(denominator)
        for tuplet in abjad.select(selection).tuplets():
            if isinstance(denominator, abjad.Duration):
                unit_duration = denominator
                assert unit_duration.numerator == 1
                duration = abjad.inspect(tuplet).duration()
                denominator_ = unit_duration.denominator
                nonreduced_fraction = duration.with_denominator(denominator_)
                tuplet.denominator = nonreduced_fraction.numerator
            elif abjad.mathtools.is_positive_integer(denominator):
                tuplet.denominator = denominator
            else:
                message = f"invalid preferred denominator: {denominator!r}."
                raise Exception(message)

    def _extract_trivial_(self, staff):
        if not self.extract_trivial:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        tuplets = abjad.select(selection).tuplets()
        for tuplet in tuplets:
            if tuplet.trivial():
                abjad.mutate(tuplet).extract()

    def _force_fraction_(self, staff):
        if not self.force_fraction:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.force_fraction = True

    def _rewrite_dots_(self, staff):
        if not self.rewrite_dots:
            return None
        if self.selector is not None:
            selection = self.selector(staff)
        else:
            selection = abjad.select(staff)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.rewrite_dots()

    # TODO: pass in duration specifier
    def _rewrite_rest_filled_(self, staff, tag=None):
        if not self.rewrite_rest_filled:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        maker = abjad.LeafMaker(tag=tag)
        for tuplet in abjad.select(selection).tuplets():
            if not self.is_rest_filled_tuplet(tuplet):
                continue
            duration = abjad.inspect(tuplet).duration()
            rests = maker([None], [duration])
            abjad.mutate(tuplet[:]).replace(rests)
            tuplet.multiplier = abjad.Multiplier(1)

    # TODO: use this rewrite:
    #    # TODO: pass in duration specifier
    #    # TODO: pass in tie specifier
    #    def _rewrite_sustained_(self, staff, tag=None):
    #        if not self.rewrite_sustained:
    #            return None
    #        selection = staff["MusicVoice"][:]
    #        if self.selector is not None:
    #            selection = self.selector(selection)
    #        maker = abjad.LeafMaker(repeat_ties=self.repeat_ties, tag=tag)
    #        for tuplet in abjad.select(selection).tuplets():
    #            if not self.is_sustained_tuplet(tuplet):
    #                continue
    #            duration = abjad.inspect(tuplet).duration()
    #            leaves = abjad.select(tuplet).leaves()
    #            first_leaf = leaves[0]
    #            if abjad.inspect(first_leaf).has_indicator(abjad.RepeatTie):
    #                first_leaf_has_repeat_tie = True
    #            else:
    #                first_leaf_has_repeat_tie = False
    #            last_leaf = leaves[-1]
    #            if abjad.inspect(last_leaf).has_indicator(abjad.TieIndicator):
    #                last_leaf_has_tie = True
    #            else:
    #                last_leaf_has_tie = False
    #            notes = maker([0], [duration])
    #            abjad.mutate(tuplet[:]).replace(notes)
    #            tuplet.multiplier = abjad.Multiplier(1)
    #            if first_leaf_has_repeat_tie:
    #                abjad.attach(abjad.RepeatTie(), tuplet[0])
    #            if last_leaf_has_tie:
    #                abjad.attach(abjad.TieIndicator(), tuplet[-1])

    def _rewrite_sustained_(self, staff, tag=None):
        if not self.rewrite_sustained:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            if not self.is_sustained_tuplet(tuplet):
                continue
            duration = abjad.inspect(tuplet).duration()
            leaves = abjad.select(tuplet).leaves()
            last_leaf = leaves[-1]
            if abjad.inspect(last_leaf).has_indicator(abjad.TieIndicator):
                last_leaf_has_tie = True
            else:
                last_leaf_has_tie = False
            for leaf in leaves[1:]:
                tuplet.remove(leaf)
            assert len(tuplet) == 1, repr(tuplet)
            if not last_leaf_has_tie:
                abjad.detach(abjad.TieIndicator, tuplet[-1])
            tuplet[0]._set_duration(duration)
            tuplet.multiplier = abjad.Multiplier(1)

    def _set_duration_bracket(self, staff):
        if not self.duration_bracket:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            duration_ = abjad.inspect(tuplet).duration()
            markup = duration_.to_score_markup()
            markup = markup.scale((0.75, 0.75))
            abjad.override(tuplet).tuplet_number.text = markup

    def _toggle_prolation(self, staff):
        if self.diminution is None:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            if (self.diminution is True and not tuplet.diminution()) or (
                self.diminution is False and not tuplet.augmentation()
            ):
                tuplet.toggle_prolation()

    def _trivialize_(self, staff):
        if not self.trivialize:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.trivialize()

    ### PUBLIC PROPERTIES ###

    @property
    def denominator(self) -> typing.Union[int, abjad.Duration, None]:
        r"""
        Gets preferred denominator.

        ..  container:: example

            Tuplet numerators and denominators are reduced to numbers that are
            relatively prime when ``denominator`` is set to none. This
            means that ratios like ``6:4`` and ``10:8`` do not arise:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=None,
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> score = lilypond_file[abjad.Score]
            >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                \with
                {
                    \override TupletBracket.staff-padding = #4.5
                }
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            The preferred denominator of each tuplet is set in terms of a unit
            duration when ``denominator`` is set to a duration. The
            setting does not affect the first tuplet:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 16),
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> score = lilypond_file[abjad.Score]
            >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                \with
                {
                    \override TupletBracket.staff-padding = #4.5
                }
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator of each tuplet in terms 32nd notes.
            The setting affects all tuplets:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 32),
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> score = lilypond_file[abjad.Score]
            >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                \with
                {
                    \override TupletBracket.staff-padding = #4.5
                }
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 8/10 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                        \times 16/20 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator each tuplet in terms 64th notes. The
            setting affects all tuplets:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 64),
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> score = lilypond_file[abjad.Score]
            >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                \with
                {
                    \override TupletBracket.staff-padding = #4.5
                }
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 16/20 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 24/20 {
                            c'16
                            c'4
                        }
                        \times 32/40 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            The preferred denominator of each tuplet is set directly when
            ``denominator`` is set to a positive integer. This example
            sets the preferred denominator of each tuplet to ``8``. Setting
            does not affect the third tuplet:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=8,
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> score = lilypond_file[abjad.Score]
            >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                \with
                {
                    \override TupletBracket.staff-padding = #4.5
                }
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 8/10 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``12``. Setting
            affects all tuplets:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=12,
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> score = lilypond_file[abjad.Score]
            >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
            >>> moment = abjad.SchemeMoment((1, 28))
            >>> abjad.setting(score).proportional_notation_duration = moment
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                \with
                {
                    \override TupletBracket.staff-padding = #4.5
                    proportionalNotationDuration = #(ly:make-moment 1 28)
                }
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 12/15 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 12/15 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                        \times 12/15 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``13``. Setting
            does not affect any tuplet:

            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=13,
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     tuplet_ratios=[(1, 4)],
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> score = lilypond_file[abjad.Score]
            >>> abjad.override(score).tuplet_bracket.staff_padding = 4.5
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                \with
                {
                    \override TupletBracket.staff-padding = #4.5
                }
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }
                >>

        Set to duration, positive integer or none.
        """
        return self._denominator

    @property
    def diminution(self) -> typing.Optional[bool]:
        """
        Is true when tuplet spells as diminution.

        Is false when tuplet spells as augmentation.

        Is none when tuplet spelling does not force prolation.
        """
        return self._diminution

    @property
    def duration_bracket(self) -> typing.Optional[bool]:
        """
        Is true when tuplet overrides tuplet number text with note
        duration bracket giving tuplet duration.
        """
        return self._duration_bracket

    @property
    def extract_trivial(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker extracts trivial tuplets.

        ..  container:: example

            With selector:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         selector=abjad.select().tuplets()[-2:],
            ...     ),
            ... )

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
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                >>

        """
        return self._extract_trivial

    @property
    def force_fraction(self) -> typing.Optional[bool]:
        r"""
        Is true when tuplet forces tuplet number fraction formatting.

        ..  container:: example

            The ``default.ily`` stylesheet included in all Abjad API examples
            includes the following:
            
            ``\override TupletNumber.text = #tuplet-number::calc-fraction-text``

            This means that even simple tuplets format as explicit fractions:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8)]
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

            We can temporarily restore LilyPond's default tuplet numbering like
            this:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> staff = lilypond_file[abjad.Score]
            >>> string = 'tuplet-number::calc-denominator-text'
            >>> abjad.override(staff).tuplet_number.text = string
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                \with
                {
                    \override TupletNumber.text = #tuplet-number::calc-denominator-text
                }
                <<
                    \new GlobalContext
                    {
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

            Which then makes it possible to show that the force fraction
            property cancels LilyPond's default tuplet numbering once again:

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         force_fraction=True,
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> staff = lilypond_file[abjad.Score]
            >>> string = 'tuplet-number::calc-denominator-text'
            >>> abjad.override(staff).tuplet_number.text = string
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                \with
                {
                    \override TupletNumber.text = #tuplet-number::calc-denominator-text
                }
                <<
                    \new GlobalContext
                    {
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
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
        return self._force_fraction

    @property
    def repeat_ties(self) -> typing.Optional[bool]:
        """
        Is true when rewrite-sustained uses repeat ties.
        """
        return self._repeat_ties

    @property
    def rewrite_dots(self) -> typing.Optional[bool]:
        """
        Is true when tuplet rewrites dots.
        """
        return self._rewrite_dots

    @property
    def rewrite_rest_filled(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker rewrites rest-filled tuplets.

        ..  container:: example

            Does not rewrite rest-filled tuplets:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     extra_counts_per_division=[2, 1, 1, 1],
            ...     talea=rmakers.Talea(
            ...         counts=[-1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
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
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            r16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \times 4/5 {
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            r16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            r16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                    }
                >>

        ..  container:: example

            Rewrites rest-filled tuplets:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_rest_filled=True,
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     extra_counts_per_division=[2, 1, 1, 1],
            ...     talea=rmakers.Talea(
            ...         counts=[-1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
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
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r4
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r4
                            r16
                        }
                    }
                >>

            With selector:

            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_rest_filled=True,
            ...         selector=abjad.select().tuplets()[-2:],
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     extra_counts_per_division=[2, 1, 1, 1],
            ...     talea=rmakers.Talea(
            ...         counts=[-1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
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
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            r16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \times 4/5 {
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r4
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r4
                            r16
                        }
                    }
                >>

            Note that nonassignable divisions necessitate multiple rests
            even after rewriting.

        """
        return self._rewrite_rest_filled

    @property
    def rewrite_sustained(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker rewrites sustained tuplets.

        ..  container:: example

            Sustained tuplets generalize a class of rhythms composers are
            likely to rewrite:

            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=abjad.select().tuplets()[1:3].map(last_leaf),
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     extra_counts_per_division=[2, 1, 1, 1],
            ...     talea=rmakers.Talea(
            ...         counts=[6, 5, 5, 4, 1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
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
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \times 2/3 {
                            c'4.
                        }
                        \times 4/5 {
                            c'4
                            ~
                            c'16
                            ~
                        }
                        \times 4/5 {
                            c'4
                            ~
                            c'16
                            ~
                        }
                        \times 4/5 {
                            c'4
                            c'16
                        }
                    }
                >>

            The first three tuplets in the example above qualify as sustained:

                >>> staff = lilypond_file[abjad.Score]
                >>> for tuplet in abjad.select(staff).tuplets():
                ...     rmakers.TupletSpecifier.is_sustained_tuplet(tuplet)
                ...
                True
                True
                True
                False

            Tuplets 0 and 1 each contain only a single **tuplet-initial**
            attack. Tuplet 2 contains no attack at all. All three fill their
            duration completely.

            Tuplet 3 contains a **nonintial** attack that rearticulates the
            tuplet's duration midway through the course of the figure. Tuplet 3
            does not qualify as sustained.

        ..  container:: example

            Rewrite sustained tuplets like this:

            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.TupletSpecifier(
            ...         rewrite_sustained=True,
            ...         ),
            ...     rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=abjad.select().tuplets()[1:3].map(last_leaf),
            ...         ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     extra_counts_per_division=[2, 1, 1, 1],
            ...     talea=rmakers.Talea(
            ...         counts=[6, 5, 5, 4, 1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
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
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            ~
                        }
                        \times 4/5 {
                            c'4
                            c'16
                        }
                    }
                >>

        ..  container:: example

            Rewrite sustained tuplets -- and then extract the trivial tuplets
            that result -- like this:

            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.TaleaRhythmMaker(
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=abjad.select().tuplets()[1:3].map(last_leaf),
            ...         ),
            ...     rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         rewrite_sustained=True,
            ...         ),
            ...     extra_counts_per_division=[2, 1, 1, 1],
            ...     talea=rmakers.Talea(
            ...         counts=[6, 5, 5, 4, 1],
            ...         denominator=16,
            ...         ),
            ...     )

            >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
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
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                        \time 4/16
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        c'4
                        ~
                        c'4
                        ~
                        \times 4/5 {
                            c'4
                            c'16
                        }
                    }
                >>

        ..  container:: example

            With selector:

            >>> selector = abjad.select().notes()[:-1]
            >>> selector = abjad.select().tuplets().map(selector)
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=selector,
            ...     ),
            ...     rmakers.TupletSpecifier(
            ...         rewrite_sustained=True,
            ...         selector=abjad.select().tuplets()[-2:],
            ...     ),
            ...     rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
            ...     extra_counts_per_division=[1],
            ... )

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8)]
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
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/2 {
                            c'4
                        }
                    }
                >>

        """
        return self._rewrite_sustained

    @property
    def selector(self) -> typing.Optional[abjad.Expression]:
        """
        Gets selector.
        """
        return self._selector

    @property
    def trivialize(self) -> typing.Optional[bool]:
        """
        Is true when tuplet specifier trivializes trivializable tuplets.
        """
        return self._trivialize

    ### PUBLIC METHODS ###

    @staticmethod
    def is_rest_filled_tuplet(tuplet):
        """
        Is true when ``argument`` is rest-filled tuplet.
        """
        if not isinstance(tuplet, abjad.Tuplet):
            return False
        return all(isinstance(_, abjad.Rest) for _ in tuplet)

    @staticmethod
    def is_sustained_tuplet(argument):
        """
        Is true when ``argument`` is sustained tuplet.
        """
        if not isinstance(argument, abjad.Tuplet):
            return False
        lt_head_count = 0
        leaves = abjad.select(argument).leaves()
        for leaf in leaves:
            lt = abjad.inspect(leaf).logical_tie()
            if lt.head is leaf:
                lt_head_count += 1
        if lt_head_count == 0:
            return True
        lt = abjad.inspect(leaves[0]).logical_tie()
        if lt.head is leaves[0] and lt_head_count == 1:
            return True
        return False
