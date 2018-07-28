import abjad
import copy
import typing


class TupletSpecifier(abjad.AbjadValueObject):
    """
    Tuplet specifier.

    ..  container:: example

        >>> specifier = abjadext.rmakers.TupletSpecifier()
        >>> abjad.f(specifier)
        abjadext.rmakers.TupletSpecifier()

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Specifiers'

    __slots__ = (
        '_denominator',
        '_diminution',
        '_duration_bracket',
        '_extract_trivial',
        '_force_fraction',
        '_rewrite_dots',
        '_rewrite_rest_filled',
        '_rewrite_sustained',
        '_trivialize',
        )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        denominator: typing.Union[str, abjad.Duration, int] = None,
        diminution: bool = None,
        duration_bracket: bool = None,
        extract_trivial: bool = None,
        force_fraction: bool = None,
        rewrite_dots: bool = None,
        rewrite_rest_filled: bool = None,
        rewrite_sustained: bool = None,
        trivialize: bool = None,
        ) -> None:
        if isinstance(denominator, tuple):
            denominator = abjad.Duration(denominator)
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
        if rewrite_dots is not None:
            rewrite_dots = bool(rewrite_dots)
        self._rewrite_dots = rewrite_dots
        if rewrite_rest_filled is not None:
            rewrite_rest_fille = bool(rewrite_rest_filled)
        self._rewrite_rest_filled = rewrite_rest_filled
        if rewrite_sustained is not None:
            rewrite_rest_fille = bool(rewrite_sustained)
        self._rewrite_sustained = rewrite_sustained
        if trivialize is not None:
            trivialize = bool(trivialize)
        self._trivialize = trivialize

    ### SPECIAL METHODS ###

    def __call__(
        self,
        selections: typing.List[abjad.Selection],
        divisions: typing.List[abjad.NonreducedFraction],
        ) -> typing.List[abjad.Selection]:
        """
        Calls tuplet specifier.
        """
        self._apply_denominator(selections, divisions)
        self._force_fraction_(selections)
        self._trivialize_(selections)
        # rewrite dots must follow trivialize:
        self._rewrite_dots_(selections)
        # rewrites must precede extract trivial:
        selections = self._rewrite_sustained_(selections)
        selections = self._rewrite_rest_filled_(selections)
        # extract trivial must follow the other operations:
        selections = self._extract_trivial_(selections)
        # toggle prolation must follow rewrite dots and extract trivial:
        self._toggle_prolation(selections)
        return selections

    ### PRIVATE METHODS ###

    def _apply_denominator(self, selections, divisions):
        if not self.denominator:
            return
        tuplets = list(abjad.iterate(selections).components(abjad.Tuplet))
        if divisions is None:
            divisions = len(tuplets) * [None]
        else:
            for division in divisions:
                if not isinstance(division, abjad.NonreducedFraction):
                    raise Exception(f'must be division (not {division!r}).')
        assert len(selections) == len(divisions)
        assert len(tuplets) == len(divisions)
        denominator = self.denominator
        if isinstance(denominator, tuple):
            denominator = abjad.Duration(denominator)
        for tuplet, division in zip(tuplets, divisions):
            if denominator == 'divisions':
                tuplet.denominator = division.numerator
            elif isinstance(denominator, abjad.Duration):
                unit_duration = denominator
                assert unit_duration.numerator == 1
                duration = abjad.inspect(tuplet).duration()
                denominator_ = unit_duration.denominator
                nonreduced_fraction = duration.with_denominator(denominator_)
                tuplet.denominator = nonreduced_fraction.numerator
            elif abjad.mathtools.is_positive_integer(denominator):
                tuplet.denominator = denominator
            else:
                message = f'invalid preferred denominator: {denominator!r}.'
                raise Exception(message)

    def _extract_trivial_(self, selections):
        if not self.extract_trivial:
            return selections
        selections_ = []
        for selection in selections:
            selection_ = []
            for component in selection:
                if not (isinstance(component, abjad.Tuplet) and
                    component.trivial()):
                    selection_.append(component)
                    continue
                tuplet = component
                contents = abjad.mutate(tuplet).eject_contents()
                assert isinstance(contents, abjad.Selection)
                selection_.extend(contents)
            selection_ = abjad.select(selection_)
            selections_.append(selection_)
        return selections_

    def _force_fraction_(self, selections):
        if not self.force_fraction:
            return
        for tuplet in abjad.iterate(selections).components(abjad.Tuplet):
            tuplet.force_fraction = True

    @staticmethod
    def _is_rest_filled_tuplet(tuplet):
        if not isinstance(tuplet, abjad.Tuplet):
            return False
        return all(isinstance(_, abjad.Rest) for _ in tuplet)

    def _rewrite_dots_(self, selections):
        if not self.rewrite_dots:
            return
        for tuplet in abjad.iterate(selections).components(abjad.Tuplet):
            tuplet.rewrite_dots()

    def _rewrite_sustained_(self, selections):
        if not self.rewrite_sustained:
            return selections
        selections_ = []
        maker = abjad.LeafMaker()
        for selection in selections:
            selection_ = []
            for component in selection:
                if not self.is_sustained_tuplet(component):
                    selection_.append(component)
                    continue
                tuplet = component
                duration = abjad.inspect(tuplet).duration()
                leaves = abjad.select(tuplet).leaves()
                for leaf in leaves[1:]:
                    tuplet.remove(leaf)
                assert len(tuplet) == 1, repr(tuplet)
                tuplet[0]._set_duration(duration)
                tuplet.multiplier = abjad.Multiplier(1)
                selection_.append(tuplet)
            selection_ = abjad.select(selection_)
            selections_.append(selection_)
        return selections_

    def _rewrite_rest_filled_(self, selections):
        if not self.rewrite_rest_filled:
            return selections
        selections_ = []
        maker = abjad.LeafMaker()
        for selection in selections:
            selection_ = []
            for component in selection:
                if not self._is_rest_filled_tuplet(component):
                    selection_.append(component)
                    continue
                duration = abjad.inspect(component).duration()
                rests = maker([None], [duration])
                abjad.mutate(component[:]).replace(rests)
                component.multiplier = abjad.Multiplier(1)
                selection_.append(component)
            selection_ = abjad.select(selection_)
            selections_.append(selection_)
        return selections_

    def _toggle_prolation(self, selections):
        if self.diminution is None:
            return
        for tuplet in abjad.iterate(selections).components(abjad.Tuplet):
            if ((self.diminution is True and not tuplet.diminution()) or
                (self.diminution is False and not tuplet.augmentation())):
                tuplet.toggle_prolation()

    def _trivialize_(self, selections):
        if not self.trivialize:
            return
        for tuplet in abjad.iterate(selections).components(abjad.Tuplet):
            tuplet.trivialize()

    ### PUBLIC PROPERTIES ###

    @property
    def denominator(self) -> typing.Optional[
        typing.Union[str, abjad.Duration, int]
        ]:
        r"""
        Gets preferred denominator.

        ..  container:: example

            Tuplet numerators and denominators are reduced to numbers that are
            relatively prime when ``denominator`` is set to none. This
            means that ratios like ``6:4`` and ``10:8`` do not arise:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=None,
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 4/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            The preferred denominator of each tuplet is set to the numerator of
            the division that generates the tuplet when ``denominator``
            is set to the string ``'divisions'``. This means that the tuplet
            numerator and denominator are not necessarily relatively prime.
            This also means that ratios like ``6:4`` and ``10:8`` may arise:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator='divisions',
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 4/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            The preferred denominator of each tuplet is set in terms of a unit
            duration when ``denominator`` is set to a duration. The
            setting does not affect the first tuplet:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 16),
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 4/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            Sets the preferred denominator of each tuplet in terms 32nd notes.
            The setting affects all tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 32),
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 8/10 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 16/20 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            Sets the preferred denominator each tuplet in terms 64th notes. The
            setting affects all tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=(1, 64),
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \time 2/16
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 16/20 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 24/20 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 32/40 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            The preferred denominator of each tuplet is set directly when
            ``denominator`` is set to a positive integer. This example
            sets the preferred denominator of each tuplet to ``8``. Setting
            does not affect the third tuplet:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=8,
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \time 2/16
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 8/10 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``12``. Setting
            affects all tuplets:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=12,
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \time 2/16
                        \times 12/15 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 12/15 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 12/15 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``13``. Setting
            does not affect any tuplet:

            >>> rhythm_maker = abjadext.rmakers.TupletRhythmMaker(
            ...     tuplet_ratios=[(1, 4)],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_dots=True,
            ...         denominator=13,
            ...         ),
            ...     )

            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \time 2/16
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \time 4/16
                        \times 4/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 6/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \time 8/16
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }   % measure
                }

        Set to ``'divisions'``, duration, positive integer or none.
        """
        return self._denominator

    @property
    def diminution(self) -> typing.Optional[bool]:
        """
        Is true when tuplet should be spelled as diminution.

        Is false when tuplet should be spelled as augmentation.

        Is none when tuplet spelling does not force prolation.
        """
        return self._diminution

    @property
    def duration_bracket(self) -> typing.Optional[bool]:
        """
        Is true when tuplet should override tuplet number text with note
        duration bracket giving tuplet duration.
        """
        return self._duration_bracket

    @property
    def extract_trivial(self) -> typing.Optional[bool]:
        """
        Is true when rhythm-maker should extract trivial tuplets.
        """
        return self._extract_trivial

    @property
    def force_fraction(self) -> typing.Optional[bool]:
        r"""
        Is true when tuplet forces tuplet number fraction formatting.

        ..  container:: example

            The ``defaulti.ly`` stylesheet included in all Abjad API examples
            includes the following:
            
            ``\override TupletNumber.text = #tuplet-number::calc-fraction-text``

            This means that even simple tuplets format as explicit fractions:

            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 2/8
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }   % measure
                }

            We can temporarily restore LilyPond's default tuplet numbering like
            this:

            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     extra_counts_per_division=[1],
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> staff = lilypond_file[abjad.Staff]
            >>> string = 'tuplet-number::calc-denominator-text'
            >>> abjad.override(staff).tuplet_number.text = string
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                \with
                {
                    \override TupletNumber.text = #tuplet-number::calc-denominator-text
                }
                {
                    {   % measure
                        \time 2/8
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }   % measure
                }

            Which then makes it possible to show that the force fraction
            property cancels LilyPond's default tuplet numbering once again:

            >>> rhythm_maker = abjadext.rmakers.EvenDivisionRhythmMaker(
            ...     extra_counts_per_division=[1],
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         force_fraction=True,
            ...         ),
            ...     )

            >>> divisions = [(2, 8), (2, 8), (2, 8)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections,
            ...     divisions,
            ...     )
            >>> staff = lilypond_file[abjad.Staff]
            >>> string = 'tuplet-number::calc-denominator-text'
            >>> abjad.override(staff).tuplet_number.text = string
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                \with
                {
                    \override TupletNumber.text = #tuplet-number::calc-denominator-text
                }
                {
                    {   % measure
                        \time 2/8
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }   % measure
                }

        """
        return self._force_fraction

    @property
    def rewrite_dots(self) -> typing.Optional[bool]:
        """
        Is true when tuplet rewrites dots.
        """
        return self._rewrite_dots

    @property
    def rewrite_sustained(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker rewrites sustained tuplets.

        ..  container:: example

            Sustained tuplets generalize a class of rhythms composers are
            likely to rewrite:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[2, 1, 1, 1],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[6, 5, 5, 4, 1],
            ...         denominator=16,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=abjad.index([1, 2]),
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 4/16
                        \times 2/3 {
                            c'4.
                        }
                    }   % measure
                    {   % measure
                        \times 4/5 {
                            c'4
                            ~
                            c'16
                            ~
                        }
                    }   % measure
                    {   % measure
                        \times 4/5 {
                            c'4
                            ~
                            c'16
                            ~
                        }
                    }   % measure
                    {   % measure
                        \times 4/5 {
                            c'4
                            c'16
                        }
                    }   % measure
                }

            The first three tuplets in the example above qualify as sustained:

                >>> staff = lilypond_file[abjad.Staff]
                >>> for tuplet in abjad.iterate(staff).components(abjad.Tuplet):
                ...     abjadext.rmakers.TupletSpecifier.is_sustained_tuplet(tuplet)
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

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[2, 1, 1, 1],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[6, 5, 5, 4, 1],
            ...         denominator=16,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=abjad.index([1, 2]),
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         rewrite_sustained=True,
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 4/16
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            ~
                        }
                    }   % measure
                    {   % measure
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            ~
                        }
                    }   % measure
                    {   % measure
                        \times 4/5 {
                            c'4
                            c'16
                        }
                    }   % measure
                }

        ..  container:: example

            Rewrite sustained tuplets -- and then extract the trivial tuplets
            that result -- like this:

            >>> rhythm_maker = abjadext.rmakers.TaleaRhythmMaker(
            ...     extra_counts_per_division=[2, 1, 1, 1],
            ...     talea=abjadext.rmakers.Talea(
            ...         counts=[6, 5, 5, 4, 1],
            ...         denominator=16,
            ...         ),
            ...     tie_specifier=abjadext.rmakers.TieSpecifier(
            ...         tie_across_divisions=abjad.index([1, 2]),
            ...         ),
            ...     tuplet_specifier=abjadext.rmakers.TupletSpecifier(
            ...         extract_trivial=True,
            ...         rewrite_sustained=True,
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

                >>> abjad.f(lilypond_file[abjad.Staff])
                \new RhythmicStaff
                {
                    {   % measure
                        \time 4/16
                        c'4
                    }   % measure
                    {   % measure
                        c'4
                        ~
                    }   % measure
                    {   % measure
                        c'4
                        ~
                    }   % measure
                    {   % measure
                        \times 4/5 {
                            c'4
                            c'16
                        }
                    }   % measure
                }

        """
        return self._rewrite_sustained

    @property
    def rewrite_rest_filled(self) -> typing.Optional[bool]:
        """
        Is true when rhythm-maker rewrites rest-filled tuplets.
        """
        return self._rewrite_rest_filled

    @property
    def trivialize(self) -> typing.Optional[bool]:
        """
        Is true when trivializable tuplets should be trivialized.
        """
        return self._trivialize

    ### PUBLIC METHODS ###

    @staticmethod
    def is_sustained_tuplet(argument):
        r"""
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
