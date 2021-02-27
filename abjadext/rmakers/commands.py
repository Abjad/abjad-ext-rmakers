import typing

import abjad

from . import specifiers as _specifiers

### CLASSES ###


class Command:
    """
    Command baseclass.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Commands"

    __slots__ = ("_selector",)

    ### INITIALIZER ###

    def __init__(self, selector: abjad.Expression = None) -> None:
        if isinstance(selector, str):
            selector = eval(selector)
            assert isinstance(selector, abjad.Expression)
        self._selector = selector

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls command on ``voice``.
        """
        pass

    def __eq__(self, argument) -> bool:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __hash__(self) -> int:
        """
        Delegates to storage format manager.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC PROPERTIES ###

    @property
    def selector(self) -> typing.Optional[abjad.Expression]:
        """
        Gets selector.
        """
        return self._selector


class BeamCommand(Command):
    """
    Beam command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_beam_lone_notes", "_beam_rests", "_stemlet_length")

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.Expression = None,
        *,
        beam_lone_notes: bool = None,
        beam_rests: bool = None,
        stemlet_length: abjad.Number = None,
    ) -> None:
        super().__init__(selector)
        if beam_lone_notes is not None:
            beam_lone_notes = bool(beam_lone_notes)
        self._beam_lone_notes = beam_lone_notes
        if beam_rests is not None:
            beam_rests = bool(beam_rests)
        self._beam_rests = beam_rests
        if stemlet_length is not None:
            assert isinstance(stemlet_length, (int, float))
        self._stemlet_length = stemlet_length

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls beam command on ``voice``.
        """
        selection = voice
        if self.selector is not None:
            selections = self.selector(selection)
        else:
            selections = [selection]
        for selection in selections:
            unbeam()(selection)
            leaves = abjad.select(selection).leaves()
            abjad.beam(
                leaves,
                beam_lone_notes=self.beam_lone_notes,
                beam_rests=self.beam_rests,
                stemlet_length=self.stemlet_length,
                tag=tag,
            )

    ### PUBLIC PROPERTIES ###

    @property
    def beam_lone_notes(self) -> typing.Optional[bool]:
        """
        Is true when command beams lone notes.
        """
        return self._beam_lone_notes

    @property
    def beam_rests(self) -> typing.Optional[bool]:
        r"""
        Is true when beams include rests.
        """
        return self._beam_rests

    @property
    def stemlet_length(self) -> typing.Optional[typing.Union[int, float]]:
        r"""
        Gets stemlet length.
        """
        return self._stemlet_length


class BeamGroupsCommand(Command):
    """
    Beam groups command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_beam_lone_notes", "_beam_rests", "_stemlet_length", "_tag")

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.Expression = None,
        *,
        beam_lone_notes: bool = None,
        beam_rests: bool = None,
        stemlet_length: abjad.Number = None,
        tag: abjad.Tag = None,
    ) -> None:
        super().__init__(selector)
        if beam_lone_notes is not None:
            beam_lone_notes = bool(beam_lone_notes)
        self._beam_lone_notes = beam_lone_notes
        if beam_rests is not None:
            beam_rests = bool(beam_rests)
        self._beam_rests = beam_rests
        if stemlet_length is not None:
            assert isinstance(stemlet_length, (int, float))
        self._stemlet_length = stemlet_length
        if tag is not None:
            assert isinstance(tag, abjad.Tag), repr(tag)
        self._tag = tag

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls beam groups command on ``voice``.
        """
        components: typing.List[abjad.Component] = []
        if not isinstance(voice, abjad.Voice):
            selections = voice
            if self.selector is not None:
                selections = self.selector(selections)
        else:
            assert self.selector is not None
            selections = self.selector(voice)
        unbeam()(selections)
        durations = []
        for selection in selections:
            duration = abjad.get.duration(selection)
            durations.append(duration)
        for selection in selections:
            if isinstance(selection, abjad.Selection):
                components.extend(selection)
            elif isinstance(selection, abjad.Tuplet):
                components.append(selection)
            else:
                raise TypeError(selection)
        leaves = abjad.select(components).leaves()
        parts = []
        if tag is not None:
            parts.append(str(tag))
        if self.tag is not None:
            parts.append(str(self.tag))
        string = ":".join(parts)
        tag = abjad.Tag(string)
        abjad.beam(
            leaves,
            beam_lone_notes=self.beam_lone_notes,
            beam_rests=self.beam_rests,
            durations=durations,
            span_beam_count=1,
            stemlet_length=self.stemlet_length,
            tag=tag,
        )

    ### PUBLIC PROPERTIES ###

    @property
    def beam_lone_notes(self) -> typing.Optional[bool]:
        """
        Is true when command beams lone notes.
        """
        return self._beam_lone_notes

    @property
    def beam_rests(self) -> typing.Optional[bool]:
        r"""
        Is true when beams include rests.
        """
        return self._beam_rests

    @property
    def stemlet_length(self) -> typing.Optional[typing.Union[int, float]]:
        r"""
        Gets stemlet length.
        """
        return self._stemlet_length

    @property
    def tag(self) -> typing.Optional[abjad.Tag]:
        """
        Gets tag.
        """
        return self._tag


class CacheStateCommand(Command):
    """
    Cache state command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### INITIALIZER ###

    def __init__(self) -> None:
        pass


class DenominatorCommand(Command):
    """
    Denominator command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_denominator",)

    ### INITIALIZER ###

    def __init__(
        self,
        denominator: typing.Union[int, abjad.DurationTyping] = None,
        selector: abjad.Expression = None,
    ) -> None:
        super().__init__(selector)
        if isinstance(denominator, tuple):
            denominator = abjad.Duration(denominator)
        if denominator is not None:
            prototype = (int, abjad.Duration)
            assert isinstance(denominator, prototype), repr(denominator)
        self._denominator = denominator

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls denominator command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        denominator = self.denominator
        if isinstance(denominator, tuple):
            denominator = abjad.Duration(denominator)
        for tuplet in abjad.select(selection).tuplets():
            if isinstance(denominator, abjad.Duration):
                unit_duration = denominator
                assert unit_duration.numerator == 1
                duration = abjad.get.duration(tuplet)
                denominator_ = unit_duration.denominator
                nonreduced_fraction = duration.with_denominator(denominator_)
                tuplet.denominator = nonreduced_fraction.numerator
            elif abjad.math.is_positive_integer(denominator):
                tuplet.denominator = denominator
            else:
                message = f"invalid preferred denominator: {denominator!r}."
                raise Exception(message)

    ### PUBLIC PROPERTIES ###

    @property
    def denominator(self) -> typing.Union[int, abjad.Duration, None]:
        r"""
        Gets preferred denominator.
        """
        return self._denominator


class DurationBracketCommand(Command):
    """
    Duration bracket command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls duration bracket command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            duration_ = abjad.get.duration(tuplet)
            notes = abjad.LeafMaker()([0], [duration_])
            string = abjad.illustrators.selection_to_score_markup_string(notes)
            markup = abjad.Markup(
                rf"\markup \scale #'(0.75 . 0.75) {string}",
                literal=True,
            )
            abjad.override(tuplet).TupletNumber.text = markup


class WrittenDurationCommand(Command):
    """
    Written duration command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_duration",)

    ### INITIALIZER ###

    def __init__(
        self,
        duration: abjad.DurationTyping,
        *,
        selector: abjad.Expression = abjad.select().leaf(0),
    ) -> None:
        super().__init__(selector)
        duration_ = abjad.Duration(duration)
        self._duration = duration_

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls duration multiplier command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        leaves = abjad.select(selection).leaves()
        assert isinstance(leaves, abjad.Selection)
        for leaf in leaves:
            self._set_written_duration(leaf, self.duration)

    ### PRIVATE METHODS ###

    @staticmethod
    def _set_written_duration(leaf, written_duration):
        if written_duration is None:
            return
        old_duration = leaf.written_duration
        if written_duration == old_duration:
            return
        leaf.written_duration = written_duration
        multiplier = old_duration / written_duration
        leaf.multiplier = multiplier

    ### PUBLIC PROPERTIES ###

    @property
    def duration(self) -> typing.Optional[abjad.Duration]:
        """
        Gets written duration.
        """
        return self._duration


class ExtractTrivialCommand(Command):
    """
    Extract trivial command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls extract trivial command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        tuplets = abjad.select(selection).tuplets()
        for tuplet in tuplets:
            if tuplet.trivial():
                abjad.mutate.extract(tuplet)


class FeatherBeamCommand(Command):
    """
    Feather beam command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_beam_rests", "_selector", "_stemlet_length")

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.Expression = None,
        *,
        beam_rests: bool = None,
        stemlet_length: abjad.Number = None,
    ) -> None:
        super().__init__(selector)
        if beam_rests is not None:
            beam_rests = bool(beam_rests)
        self._beam_rests = beam_rests
        if stemlet_length is not None:
            assert isinstance(stemlet_length, (int, float))
        self._stemlet_length = stemlet_length

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls feather beam command.
        """
        selection = voice
        if self.selector is not None:
            selections = self.selector(selection)
        else:
            selections = [selection]
        for selection in selections:
            unbeam()(selection)
            leaves = abjad.select(selection).leaves()
            abjad.beam(
                leaves,
                beam_rests=self.beam_rests,
                stemlet_length=self.stemlet_length,
                tag=tag,
            )
        for selection in selections:
            first_leaf = abjad.select(selection).leaf(0)
            if self._is_accelerando(selection):
                abjad.override(first_leaf).Beam.grow_direction = abjad.Right
            elif self._is_ritardando(selection):
                abjad.override(first_leaf).Beam.grow_direction = abjad.Left

    ### PRIVATE METHODS ###

    @staticmethod
    def _is_accelerando(selection):
        first_leaf = abjad.select(selection).leaf(0)
        last_leaf = abjad.select(selection).leaf(-1)
        first_duration = abjad.get.duration(first_leaf)
        last_duration = abjad.get.duration(last_leaf)
        if last_duration < first_duration:
            return True
        return False

    @staticmethod
    def _is_ritardando(selection):
        first_leaf = abjad.select(selection).leaf(0)
        last_leaf = abjad.select(selection).leaf(-1)
        first_duration = abjad.get.duration(first_leaf)
        last_duration = abjad.get.duration(last_leaf)
        if first_duration < last_duration:
            return True
        return False

    ### PUBLIC PROPERTIES ###

    @property
    def beam_rests(self) -> typing.Optional[bool]:
        r"""
        Is true when feather beams include rests.
        """
        return self._beam_rests

    @property
    def stemlet_length(self) -> typing.Optional[typing.Union[int, float]]:
        r"""
        Gets stemlet length.
        """
        return self._stemlet_length


class ForceAugmentationCommand(Command):
    """
    Force augmentation command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls force augmentation command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            if not tuplet.augmentation():
                tuplet.toggle_prolation()


class ForceDiminutionCommand(Command):
    """
    Force diminution command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls force diminution command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            if not tuplet.diminution():
                tuplet.toggle_prolation()


class ForceFractionCommand(Command):
    """
    Force fraction command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls force fraction command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.force_fraction = True


class ForceNoteCommand(Command):
    r"""
    Note command.

    ..  container:: example

        Changes logical ties 1 and 2 to notes:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().leaves()),
        ...     rmakers.force_note(abjad.select().logical_ties()[1:3]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

    ..  container:: example

        Sustains logical ties -1 and -2 to notes:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().leaves()),
        ...     rmakers.force_note(abjad.select().logical_ties()[-2:]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    r4.
                    c'4..
                    c'4.
                }
            >>

    ..  container:: example

        Changes patterned selection of leaves to notes:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().leaves()),
        ...     rmakers.force_note(abjad.select().logical_ties()[1:-1]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

    ..  container:: example

        Changes patterned selection of leave to notes. Works inverted composite
        pattern:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().leaves()),
        ...     rmakers.force_note(abjad.select().logical_ties().get([0, -1])),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag=None):
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)

        # will need to restore for statal rhythm-makers:
        # logical_ties = abjad.select(selections).logical_ties()
        # logical_ties = list(logical_ties)
        # total_logical_ties = len(logical_ties)
        # previous_logical_ties_produced = self._previous_logical_ties_produced()
        # if self._previous_incomplete_last_note():
        #    previous_logical_ties_produced -= 1

        leaves = abjad.select(selection).leaves()
        for leaf in leaves:
            if isinstance(leaf, abjad.Note):
                continue
            note = abjad.Note("C4", leaf.written_duration, tag=tag)
            if leaf.multiplier is not None:
                note.multiplier = leaf.multiplier
            abjad.mutate.replace(leaf, [note])


class ForceRepeatTieCommand(Command):
    """
    Force repeat-tie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_threshold",)

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.Expression = None,
        *,
        threshold: typing.Union[
            bool, abjad.IntegerPair, abjad.DurationInequality
        ] = None,
    ) -> None:
        super().__init__(selector)
        threshold_ = threshold
        if isinstance(threshold, tuple) and len(threshold) == 2:
            threshold_ = abjad.DurationInequality(
                operator_string=">=", duration=threshold
            )
        if threshold_ is not None:
            assert isinstance(threshold_, (bool, abjad.DurationInequality))
        self._threshold = threshold_

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls force repeat-tie command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        if isinstance(self.threshold, abjad.DurationInequality):
            inequality = self.threshold
        elif self.threshold is True:
            inequality = abjad.DurationInequality(">=", 0)
        else:
            duration = abjad.Duration(self.threshold)
            inequality = abjad.DurationInequality(">=", duration)
        assert isinstance(inequality, abjad.DurationInequality)
        attach_repeat_ties = []
        for leaf in abjad.select(selection).leaves():
            if abjad.get.has_indicator(leaf, abjad.Tie):
                next_leaf = abjad.get.leaf(leaf, 1)
                if next_leaf is None:
                    continue
                if not isinstance(next_leaf, (abjad.Chord, abjad.Note)):
                    continue
                if abjad.get.has_indicator(next_leaf, abjad.RepeatTie):
                    continue
                duration = abjad.get.duration(leaf)
                if not inequality(duration):
                    continue
                attach_repeat_ties.append(next_leaf)
                abjad.detach(abjad.Tie, leaf)
        for leaf in attach_repeat_ties:
            repeat_tie = abjad.RepeatTie()
            abjad.attach(repeat_tie, leaf)

    ### PUBLIC PROPERTIES ###

    @property
    def threshold(self) -> typing.Union[bool, abjad.DurationInequality, None]:
        """
        Gets threshold.
        """
        return self._threshold


class ForceRestCommand(Command):
    r"""
    Rest command.

    ..  container:: example

        Changes logical ties 1 and 2 to rests:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().logical_ties()[1:3]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().logical_ties()[-2:]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().logical_ties()[1:-1]),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(
        ...         abjad.select().logical_ties().get([0, -1]),
        ...     ),
        ... )
        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, previous_logical_ties_produced=None, tag=None):
        selection = voice
        if self.selector is not None:
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
        leaves = abjad.select(selections).leaves()
        for leaf in leaves:
            rest = abjad.Rest(leaf.written_duration, tag=tag)
            if leaf.multiplier is not None:
                rest.multiplier = leaf.multiplier
            previous_leaf = abjad.get.leaf(leaf, -1)
            next_leaf = abjad.get.leaf(leaf, 1)
            abjad.mutate.replace(leaf, [rest])
            if previous_leaf is not None:
                abjad.detach(abjad.Tie, previous_leaf)
            abjad.detach(abjad.Tie, rest)
            abjad.detach(abjad.RepeatTie, rest)
            if next_leaf is not None:
                abjad.detach(abjad.RepeatTie, next_leaf)


class GraceContainerCommand(Command):
    """
    Grace container command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_beam_and_slash", "_class_", "_counts", "_talea")

    _classes = (abjad.BeforeGraceContainer, abjad.AfterGraceContainer)

    ### INITIALIZER ###

    def __init__(
        self,
        counts: abjad.IntegerSequence,
        selector: abjad.Expression = None,
        *,
        class_: typing.Type = abjad.BeforeGraceContainer,
        beam_and_slash: bool = None,
        talea: _specifiers.Talea = _specifiers.Talea([1], 8),
    ) -> None:
        super().__init__(selector)
        assert all(isinstance(_, int) for _ in counts), repr(counts)
        self._counts = tuple(counts)
        assert class_ in self._classes, repr(class_)
        self._class_ = class_
        if beam_and_slash is not None:
            beam_and_slash = bool(beam_and_slash)
        self._beam_and_slash = beam_and_slash
        assert isinstance(talea, _specifiers.Talea), repr(talea)
        self._talea = talea

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls grace container command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        leaves = abjad.select(selection).leaves(grace=False)
        counts = abjad.CyclicTuple(self.counts)
        maker = abjad.LeafMaker()
        start = 0
        for i, leaf in enumerate(leaves):
            count = counts[i]
            if not count:
                continue
            stop = start + count
            durations = self.talea[start:stop]
            notes = maker([0], durations)
            if self.beam_and_slash:
                abjad.beam(notes)
                literal = abjad.LilyPondLiteral(r"\slash")
                abjad.attach(literal, notes[0])
            container = self.class_(notes)
            abjad.attach(container, leaf)

    ### PUBLIC PROPERTIES ###

    @property
    def class_(self) -> typing.Type:
        """
        Gets class.
        """
        return self._class_

    @property
    def counts(self) -> typing.Tuple[int, ...]:
        """
        Gets counts.
        """
        return self._counts

    @property
    def beam_and_slash(self) -> typing.Optional[bool]:
        r"""
        Is true when command beams notes and attaches Nalesnik ``\slash``
        command to first note.
        """
        return self._beam_and_slash

    @property
    def talea(self) -> _specifiers.Talea:
        """
        Gets talea.
        """
        return self._talea


class InvisibleMusicCommand(Command):
    """
    Invisible music command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls invisible music command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        if tag is None:
            tag = abjad.Tag()
        tag_1 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COMMAND"))
        literal_1 = abjad.LilyPondLiteral(r"\abjad-invisible-music")
        tag_2 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COLORING"))
        literal_2 = abjad.LilyPondLiteral(r"\abjad-invisible-music-coloring")
        for leaf in abjad.select(selection).leaves():
            abjad.attach(literal_1, leaf, tag=tag_1, deactivate=True)
            abjad.attach(literal_2, leaf, tag=tag_2)


class OnBeatGraceContainerCommand(Command):
    """
    On-beat grace container command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_counts", "_grace_leaf_duration", "_talea")

    ### INITIALIZER ###

    def __init__(
        self,
        counts: abjad.IntegerSequence,
        selector: abjad.Expression = None,
        *,
        leaf_duration: abjad.DurationTyping = None,
        talea: _specifiers.Talea = _specifiers.Talea([1], 8),
    ) -> None:
        super().__init__(selector)
        assert all(isinstance(_, int) for _ in counts), repr(counts)
        self._counts = tuple(counts)
        if leaf_duration is not None:
            leaf_duration = abjad.Duration(leaf_duration)
        self._grace_leaf_duration = leaf_duration
        assert isinstance(talea, _specifiers.Talea), repr(talea)
        self._talea = talea

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls on-beat grace container command.
        """
        selections = voice
        if self.selector is not None:
            selections = self.selector(selections)
        counts = abjad.CyclicTuple(self.counts)
        maker = abjad.LeafMaker()
        start = 0
        for i, selection in enumerate(selections):
            count = counts[i]
            if not count:
                continue
            stop = start + count
            durations = self.talea[start:stop]
            notes = maker([0], durations)
            abjad.on_beat_grace_container(
                notes,
                selection,
                anchor_voice_number=2,
                grace_voice_number=1,
                leaf_duration=self.leaf_duration,
            )

    ### PUBLIC PROPERTIES ###

    @property
    def counts(self) -> typing.Tuple[int, ...]:
        """
        Gets counts.
        """
        return self._counts

    @property
    def leaf_duration(self) -> typing.Optional[abjad.Duration]:
        """
        Gets grace leaf duration.
        """
        return self._grace_leaf_duration

    @property
    def talea(self) -> _specifiers.Talea:
        """
        Gets talea.
        """
        return self._talea


class ReduceMultiplierCommand(Command):
    """
    Reduce multiplier command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls reduce multiplier command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.multiplier = abjad.Multiplier(tuplet.multiplier)


class RepeatTieCommand(Command):
    """
    Repeat-tie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls tie command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for note in abjad.select(selection).notes():
            tie = abjad.RepeatTie()
            abjad.attach(tie, note, tag=tag)


class RewriteDotsCommand(Command):
    """
    Rewrite dots command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls rewrite dots command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.rewrite_dots()


class RewriteMeterCommand(Command):
    """
    Rewrite meter command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_boundary_depth", "_reference_meters")

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        boundary_depth: int = None,
        reference_meters: typing.Sequence[abjad.Meter] = None,
    ) -> None:
        if boundary_depth is not None:
            assert isinstance(boundary_depth, int)
        self._boundary_depth = boundary_depth
        reference_meters_ = None
        if reference_meters is not None:
            if not all(isinstance(_, abjad.Meter) for _ in reference_meters):
                message = "must be sequence of meters:\n"
                message += f"   {repr(reference_meters)}"
                raise Exception(message)
            reference_meters_ = tuple(reference_meters)
        self._reference_meters = reference_meters_

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls rewrite meter command.
        """
        assert isinstance(voice, abjad.Voice), repr(voice)
        staff = abjad.get.parentage(voice).parent
        assert isinstance(staff, abjad.Staff), repr(staff)
        time_signature_voice = staff["TimeSignatureVoice"]
        assert isinstance(time_signature_voice, abjad.Voice)
        meters, preferred_meters = [], []
        for skip in time_signature_voice:
            time_signature = abjad.get.indicator(skip, abjad.TimeSignature)
            meter = abjad.Meter(time_signature)
            meters.append(meter)
        durations = [abjad.Duration(_) for _ in meters]
        reference_meters = self.reference_meters or ()
        command = SplitMeasuresCommand()
        command(voice, durations=durations)
        selections = abjad.select(voice[:]).group_by_measure()
        for meter, selection in zip(meters, selections):
            for reference_meter in reference_meters:
                if str(reference_meter) == str(meter):
                    meter = reference_meter
                    break

            preferred_meters.append(meter)
            nontupletted_leaves = []
            for leaf in abjad.iterate(selection).leaves():
                if not abjad.get.parentage(leaf).count(abjad.Tuplet):
                    nontupletted_leaves.append(leaf)
            unbeam()(nontupletted_leaves)
            abjad.Meter.rewrite_meter(
                selection,
                meter,
                boundary_depth=self.boundary_depth,
                rewrite_tuplets=False,
            )
        selections = abjad.select(voice[:]).group_by_measure()
        for meter, selection in zip(preferred_meters, selections):
            leaves = abjad.select(selection).leaves(grace=False)
            beat_durations = []
            beat_offsets = meter.depthwise_offset_inventory[1]
            for start, stop in abjad.sequence(beat_offsets).nwise():
                beat_duration = stop - start
                beat_durations.append(beat_duration)
            beamable_groups = self._make_beamable_groups(leaves, beat_durations)
            for beamable_group in beamable_groups:
                if not beamable_group:
                    continue
                abjad.beam(
                    beamable_group,
                    beam_rests=False,
                    tag=abjad.Tag("rmakers.RewriteMeterCommand.__call__"),
                )

    ### PRIVATE METHODS ###

    @staticmethod
    def _make_beamable_groups(components, durations):
        music_duration = abjad.get.duration(components)
        if music_duration != sum(durations):
            message = f"music duration {music_duration} does not equal"
            message += f" total duration {sum(durations)}:\n"
            message += f"   {components}\n"
            message += f"   {durations}"
            raise Exception(message)
        component_to_timespan = []
        start_offset = abjad.Offset(0)
        for component in components:
            duration = abjad.get.duration(component)
            stop_offset = start_offset + duration
            timespan = abjad.Timespan(start_offset, stop_offset)
            pair = (component, timespan)
            component_to_timespan.append(pair)
            start_offset = stop_offset
        group_to_target_duration = []
        start_offset = abjad.Offset(0)
        for target_duration in durations:
            stop_offset = start_offset + target_duration
            group_timespan = abjad.Timespan(start_offset, stop_offset)
            start_offset = stop_offset
            group = []
            for component, component_timespan in component_to_timespan:
                if component_timespan.happens_during_timespan(group_timespan):
                    group.append(component)
            selection = abjad.select(group)
            pair = (selection, target_duration)
            group_to_target_duration.append(pair)
        beamable_groups = []
        for group, target_duration in group_to_target_duration:
            group_duration = abjad.get.duration(group)
            assert group_duration <= target_duration
            if group_duration == target_duration:
                beamable_groups.append(group)
            else:
                beamable_groups.append(abjad.select([]))
        return beamable_groups

    ### PUBLIC PROPERTIES ###

    @property
    def boundary_depth(self) -> typing.Optional[int]:
        """
        Gets boundary depth.
        """
        return self._boundary_depth

    @property
    def reference_meters(
        self,
    ) -> typing.Optional[typing.Tuple[abjad.Meter, ...]]:
        """
        Gets reference meters.
        """
        return self._reference_meters


class RewriteRestFilledCommand(Command):
    """
    Rewrite rest-filled command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_spelling",)

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.Expression = None,
        *,
        spelling: _specifiers.Spelling = None,
    ) -> None:
        super().__init__(selector)
        if spelling is not None:
            assert isinstance(spelling, _specifiers.Spelling)
        self._spelling = spelling

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls rewrite rest-filled command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        if self.spelling is not None:
            increase_monotonic = self.spelling.increase_monotonic
            forbidden_note_duration = self.spelling.forbidden_note_duration
            forbidden_rest_duration = self.spelling.forbidden_rest_duration
        else:
            increase_monotonic = None
            forbidden_note_duration = None
            forbidden_rest_duration = None
        maker = abjad.LeafMaker(
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            tag=tag,
        )
        for tuplet in abjad.select(selection).tuplets():
            if not tuplet.rest_filled():
                continue
            duration = abjad.get.duration(tuplet)
            rests = maker([None], [duration])
            abjad.mutate.replace(tuplet[:], rests)
            tuplet.multiplier = abjad.Multiplier(1)

    ### PUBLIC PROPERTIES ###

    @property
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        """
        Gets spelling specifier.
        """
        return self._spelling


class RewriteSustainedCommand(Command):
    """
    Rewrite sustained command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls rewrite sustained command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            if not abjad.get.sustained(tuplet):
                continue
            duration = abjad.get.duration(tuplet)
            leaves = abjad.select(tuplet).leaves()
            last_leaf = leaves[-1]
            if abjad.get.has_indicator(last_leaf, abjad.Tie):
                last_leaf_has_tie = True
            else:
                last_leaf_has_tie = False
            for leaf in leaves[1:]:
                tuplet.remove(leaf)
            assert len(tuplet) == 1, repr(tuplet)
            if not last_leaf_has_tie:
                abjad.detach(abjad.Tie, tuplet[-1])
            abjad.mutate._set_leaf_duration(tuplet[0], duration)
            tuplet.multiplier = abjad.Multiplier(1)


class SplitMeasuresCommand(Command):
    """
    Split measures command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(
        self,
        voice,
        *,
        durations: typing.Sequence[abjad.DurationTyping] = None,
        tag: abjad.Tag = None,
    ) -> None:
        """
        Calls split measures command.
        """
        if durations is None:
            # TODO: implement abjad.get() method for measure durations
            staff = abjad.get.parentage(voice).parent
            assert isinstance(staff, abjad.Staff)
            voice_ = staff["TimeSignatureVoice"]
            durations = [abjad.get.duration(_) for _ in voice_]
        total_duration = sum(durations)
        music_duration = abjad.get.duration(voice)
        if total_duration != music_duration:
            message = f"Total duration of splits is {total_duration!s}"
            message += f" but duration of music is {music_duration!s}:"
            message += f"\ndurations: {durations}."
            message += f"\nvoice: {voice[:]}."
            raise Exception(message)
        abjad.mutate.split(voice[:], durations=durations)


class TieCommand(Command):
    """
    Tie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls tie command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for note in abjad.select(selection).notes():
            tie = abjad.Tie()
            abjad.attach(tie, note, tag=tag)


class TremoloContainerCommand(Command):
    """
    Tremolo container command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_count",)

    ### INITIALIZER ###

    def __init__(self, count: int, selector: abjad.Expression = None) -> None:
        super().__init__(selector)
        assert isinstance(count, int), repr(count)
        assert 0 < count, repr(count)
        self._count = count

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls tremolo container command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for note in abjad.select(selection).notes():
            container_duration = note.written_duration
            note_duration = container_duration / (2 * self.count)
            left_note = abjad.Note("c'", note_duration)
            right_note = abjad.Note("c'", note_duration)
            container = abjad.TremoloContainer(
                self.count, [left_note, right_note], tag=tag
            )
            abjad.mutate.replace(note, container)

    ### PUBLIC PROPERTIES ###

    @property
    def count(self) -> int:
        """
        Gets count.
        """
        return self._count


class TrivializeCommand(Command):
    """
    Trivialize command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls trivialize command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for tuplet in abjad.select(selection).tuplets():
            tuplet.trivialize()


class UnbeamCommand(Command):
    """
    Unbeam command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls unbeam command.
        """
        selection = voice
        if self.selector is not None:
            selections = self.selector(selection)
        else:
            selections = selection
        leaves = abjad.select(selections).leaves()
        for leaf in leaves:
            abjad.detach(abjad.BeamCount, leaf)
            abjad.detach(abjad.StartBeam, leaf)
            abjad.detach(abjad.StopBeam, leaf)


class UntieCommand(Command):
    """
    Untie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, voice, *, tag: abjad.Tag = None) -> None:
        """
        Calls untie command.
        """
        selection = voice
        if self.selector is not None:
            selection = self.selector(selection)
        for leaf in abjad.select(selection).leaves():
            abjad.detach(abjad.Tie, leaf)
            abjad.detach(abjad.RepeatTie, leaf)


### FACTORY FUNCTIONS ###


def after_grace_container(
    counts: abjad.IntegerSequence,
    selector: abjad.Expression = None,
    *,
    beam_and_slash: bool = None,
    talea: _specifiers.Talea = _specifiers.Talea([1], 8),
) -> GraceContainerCommand:
    r"""
    Makes after-grace container command.

    ..  container:: example

        Single after-graces with slurs applied manually:

        >>> selector = abjad.select().note(-1)
        >>> selector = abjad.select().tuplets().map(selector)
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4], extra_counts=[2]),
        ...     rmakers.after_grace_container([1], selector),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> staff = lilypond_file[abjad.Staff]
        >>> containers = abjad.select().components(abjad.AfterGraceContainer)
        >>> selector = containers.map(abjad.select().with_next_leaf())
        >>> result = [abjad.slur(_) for _ in selector(staff)]
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            c'8
                            (
                        }
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        )
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            c'8
                            )
                            (
                        }
                    }
                }
            >>

    ..  container:: example

        Multiple after-graces with ``beam_and_slash=True`` and with slurs
        applied manually:

        >>> selector = abjad.select().note(-1)
        >>> selector = abjad.select().tuplets().map(selector)
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4], extra_counts=[2]),
        ...     rmakers.after_grace_container(
        ...         [2, 4], selector, beam_and_slash=True,
        ...     ),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> staff = lilypond_file[abjad.Staff]
        >>> containers = abjad.select().components(abjad.AfterGraceContainer)
        >>> selector = containers.map(abjad.select().with_next_leaf())
        >>> result = [abjad.slur(_) for _ in selector(staff)]
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        )
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            )
                            ]
                        }
                    }
                }
            >>

    """
    return GraceContainerCommand(
        counts,
        selector,
        beam_and_slash=beam_and_slash,
        class_=abjad.AfterGraceContainer,
        talea=talea,
    )


def beam(
    selector: abjad.Expression = abjad.select()
    .tuplets()
    .map(abjad.select().leaves(grace=False)),
    *,
    beam_lone_notes: bool = None,
    beam_rests: bool = None,
    stemlet_length: abjad.Number = None,
) -> BeamCommand:
    """
    Makes beam command.
    """
    return BeamCommand(
        selector,
        beam_rests=beam_rests,
        beam_lone_notes=beam_lone_notes,
        stemlet_length=stemlet_length,
    )


def beam_groups(
    selector: typing.Optional[abjad.Expression] = abjad.select()
    .tuplets(level=-1)
    .map(abjad.select().leaves(grace=False)),
    *,
    beam_lone_notes: bool = None,
    beam_rests: bool = None,
    stemlet_length: abjad.Number = None,
    tag: abjad.Tag = None,
) -> BeamGroupsCommand:
    """
    Makes beam-groups command.
    """
    return BeamGroupsCommand(
        selector,
        beam_lone_notes=beam_lone_notes,
        beam_rests=beam_rests,
        stemlet_length=stemlet_length,
        tag=tag,
    )


def before_grace_container(
    counts: abjad.IntegerSequence,
    selector: abjad.Expression = None,
    *,
    talea: _specifiers.Talea = _specifiers.Talea([1], 8),
) -> GraceContainerCommand:
    r"""
    Makes grace container command.

    ..  container:: example

        >>> selector = abjad.select().notes().exclude([0, -1])
        >>> selector = abjad.select().tuplets().map(selector)
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4], extra_counts=[2]),
        ...     rmakers.before_grace_container([2, 4], selector),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> staff = lilypond_file[abjad.Staff]
        >>> containers = abjad.select().components(abjad.BeforeGraceContainer)
        >>> result = [abjad.beam(_) for _ in containers(staff)]
        >>> selector = containers.map(abjad.select().with_next_leaf())
        >>> result = [abjad.slur(_) for _ in selector(staff)]
        >>> slash = abjad.LilyPondLiteral(r"\slash")
        >>> result = [abjad.attach(slash, _[0]) for _ in containers(staff)]
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                        c'4
                        )
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        )
                        c'4
                    }
                }
            >>

    """
    return GraceContainerCommand(counts, selector, talea=talea)


def cache_state() -> CacheStateCommand:
    """
    Makes cache state command.
    """
    return CacheStateCommand()


def denominator(
    denominator: typing.Union[int, abjad.DurationTyping],
    selector: abjad.Expression = abjad.select().tuplets(),
) -> DenominatorCommand:
    r"""
    Makes tuplet denominator command.

    ..  container:: example

        Tuplet numerators and denominators are reduced to numbers that are
        relatively prime when ``denominator`` is set to none. This
        means that ratios like ``6:4`` and ``10:8`` do not arise:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = 4.5
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

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 16)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = 4.5
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

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 32)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = 4.5
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

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator((1, 64)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = 4.5
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

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(8),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = 4.5
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

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(12),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.setting(score).proportionalNotationDuration = "#(ly:make-moment 1 28)"
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = 4.5
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

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 4)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.denominator(13),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> score = lilypond_file[abjad.Score]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            \with
            {
                \override TupletBracket.staff-padding = 4.5
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

    """
    return DenominatorCommand(denominator, selector)


def duration_bracket(
    selector: abjad.Expression = None,
) -> DurationBracketCommand:
    """
    Makes duration bracket command.
    """
    return DurationBracketCommand(selector)


def extract_trivial(
    selector: abjad.Expression = None,
) -> ExtractTrivialCommand:
    r"""
    Makes extract trivial command.

    ..  container:: example

        With selector:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(abjad.select().tuplets()[-2:]),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
    return ExtractTrivialCommand(selector)


def feather_beam(
    selector: abjad.Expression = abjad.select()
    .tuplets()
    .map(abjad.select().leaves(grace=False)),
    *,
    beam_rests: bool = None,
    stemlet_length: abjad.Number = None,
) -> FeatherBeamCommand:
    """
    Makes feather beam command.
    """
    return FeatherBeamCommand(
        selector, beam_rests=beam_rests, stemlet_length=stemlet_length
    )


def force_augmentation(
    selector: abjad.Expression = None,
) -> ForceAugmentationCommand:
    r"""
    Makes force augmentation command.

    ..  container:: example

        The ``default.ily`` stylesheet included in all Abjad API examples
        includes the following:

        ``\override TupletNumber.text = #tuplet-number::calc-fraction-text``

        This means that even simple tuplets format as explicit fractions:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> staff = lilypond_file[abjad.Score]
        >>> string = '#tuplet-number::calc-denominator-text'
        >>> abjad.override(staff).TupletNumber.text = string
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.force_fraction(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> staff = lilypond_file[abjad.Score]
        >>> string = '#tuplet-number::calc-denominator-text'
        >>> abjad.override(staff).TupletNumber.text = string
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
    return ForceAugmentationCommand(selector)


def force_diminution(
    selector: abjad.Expression = None,
) -> ForceDiminutionCommand:
    """
    Makes force diminution command.
    """
    return ForceDiminutionCommand(selector)


def force_fraction(
    selector: abjad.Expression = None,
) -> ForceFractionCommand:
    """
    Makes force fraction command.
    """
    return ForceFractionCommand(selector)


def force_note(
    selector: abjad.Expression,
) -> ForceNoteCommand:
    """
    Makes force note command.
    """
    return ForceNoteCommand(selector)


def force_repeat_tie(
    threshold=True, selector: abjad.Expression = None
) -> ForceRepeatTieCommand:
    """
    Makes force repeat-ties command.
    """
    return ForceRepeatTieCommand(selector, threshold=threshold)


def force_rest(selector: abjad.Expression) -> ForceRestCommand:
    """
    Makes force rest command.
    """
    return ForceRestCommand(selector)


def invisible_music(selector: abjad.Expression) -> InvisibleMusicCommand:
    """
    Makes invisible music command.
    """
    return InvisibleMusicCommand(selector=selector)


def on_beat_grace_container(
    counts: abjad.IntegerSequence,
    selector: abjad.Expression = None,
    *,
    leaf_duration: abjad.DurationTyping = None,
    talea: _specifiers.Talea = _specifiers.Talea([1], 8),
) -> OnBeatGraceContainerCommand:
    r"""
    Makes on-beat grace container command.

    ..  container:: example

        >>> selector = abjad.select().notes().exclude([0, -1])
        >>> selector = abjad.select().tuplets().map(selector)
        >>> selector = selector.notes().map(abjad.select())
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4], extra_counts=[2]),
        ...     rmakers.on_beat_grace_container(
        ...         [2, 4], selector, leaf_duration=(1, 28)
        ...     ),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> music_voice = abjad.Voice(
        ...     selections, name="Rhythm_Maker_Music_Voice"
        ... )
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     abjad.select(music_voice), divisions, pitched_staff=False
        ... )
        >>> staff = lilypond_file[abjad.Staff]
        >>> abjad.override(staff).TupletBracket.direction = abjad.Up
        >>> abjad.override(staff).TupletBracket.staff_padding = 5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                \with
                {
                    \override TupletBracket.direction = #up
                    \override TupletBracket.staff-padding = 5
                }
                {
                    \context Voice = "Rhythm_Maker_Music_Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "Rhythm_Maker_Music_Voice"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "Rhythm_Maker_Music_Voice"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "Rhythm_Maker_Music_Voice"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            \oneVoice
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "Rhythm_Maker_Music_Voice"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "Rhythm_Maker_Music_Voice"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 10/21
                                    [
                                    (
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    c'8 * 10/21
                                    )
                                    ]
                                }
                                \context Voice = "Rhythm_Maker_Music_Voice"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                            \oneVoice
                            c'4
                        }
                    }
                }
            >>

    ..  container:: example

        >>> selector = abjad.select().logical_ties()
        >>> stack = rmakers.stack(
        ...     rmakers.talea([5], 16),
        ...     rmakers.extract_trivial(),
        ...     rmakers.on_beat_grace_container(
        ...         [6, 2], selector, leaf_duration=(1, 28)
        ...     ),
        ... )
        >>> divisions = [(3, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> music_voice = abjad.Voice(
        ...     selections, name="Rhythm_Maker_Music_Voice"
        ... )
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     abjad.select(music_voice), divisions, pitched_staff=False
        ... )
        >>> staff = lilypond_file[abjad.Staff]
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \context Voice = "Rhythm_Maker_Music_Voice"
                    {
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "Rhythm_Maker_Music_Voice"
                            {
                                \voiceTwo
                                c'4
                                ~
                                c'16
                            }
                        >>
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "Rhythm_Maker_Music_Voice"
                            {
                                \voiceTwo
                                c'4
                                ~
                                c'16
                            }
                        >>
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "Rhythm_Maker_Music_Voice"
                            {
                                \voiceTwo
                                c'8
                                ~
                                c'8.
                            }
                        >>
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "Rhythm_Maker_Music_Voice"
                            {
                                \voiceTwo
                                c'4
                                ~
                                c'16
                            }
                        >>
                        <<
                            \context Voice = "On_Beat_Grace_Container"
                            {
                                \set fontSize = #-3
                                \slash
                                \voiceOne
                                <
                                    \tweak font-size 0
                                    \tweak transparent ##t
                                    c'
                                >8 * 2/7
                                [
                                (
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                c'8 * 2/7
                                )
                                ]
                            }
                            \context Voice = "Rhythm_Maker_Music_Voice"
                            {
                                \voiceTwo
                                c'4
                            }
                        >>
                    }
                }
            >>

    """
    return OnBeatGraceContainerCommand(
        counts, selector, leaf_duration=leaf_duration, talea=talea
    )


def repeat_tie(selector: abjad.Expression = None) -> RepeatTieCommand:
    r"""
    Makes repeat-tie command.

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE. Attaches repeat-ties to first note in
        nonfirst tuplets:

        >>> selector = abjad.select().tuplets()[1:]
        >>> selector = selector.map(abjad.select().note(0))
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.repeat_tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> selector = abjad.select().tuplets().get([1], 2)
        >>> selector = selector.map(abjad.select().note(0))
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.repeat_tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
    return RepeatTieCommand(selector)


def reduce_multiplier(
    selector: abjad.Expression = None,
) -> ReduceMultiplierCommand:
    """
    Makes reduce multiplier command.
    """
    return ReduceMultiplierCommand(selector)


def rewrite_dots(selector: abjad.Expression = None) -> RewriteDotsCommand:
    """
    Makes rewrite dots command.
    """
    return RewriteDotsCommand(selector)


def rewrite_meter(
    *, boundary_depth: int = None, reference_meters=None
) -> RewriteMeterCommand:
    """
    Makes rewrite meter command.
    """
    return RewriteMeterCommand(
        boundary_depth=boundary_depth, reference_meters=reference_meters
    )


def rewrite_rest_filled(
    selector: abjad.Expression = None, spelling: _specifiers.Spelling = None
) -> RewriteRestFilledCommand:
    r"""
    Makes rewrite rest-filled command.

    ..  container:: example

        Does not rewrite rest-filled tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \times 4/5 {
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

        Rewrites rest-filled tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    r4
                    r4
                    r4
                    r16
                    r4
                    r16
                }
            >>

        With spelling specifier:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.rewrite_rest_filled(
        ...         spelling=rmakers.Spelling(increase_monotonic=True)
        ...     ),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    r4
                    r4
                    r16
                    r4
                    r16
                    r4
                }
            >>

        With selector:

        >>> stack = rmakers.stack(
        ...     rmakers.talea([-1], 16, extra_counts=[1]),
        ...     rmakers.rewrite_rest_filled(
        ...         abjad.select().tuplets()[-2:],
        ...     ),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \times 4/5 {
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
                    r4
                    r16
                    r4
                    r16
                }
            >>

        Note that nonassignable divisions necessitate multiple rests
        even after rewriting.

    """
    return RewriteRestFilledCommand(selector, spelling=spelling)


def rewrite_sustained(
    selector: abjad.Expression = abjad.select().tuplets(),
) -> RewriteSustainedCommand:
    r"""
    Makes tuplet command.

    ..  container:: example

        Sustained tuplets generalize a class of rhythms composers are
        likely to rewrite:

        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.talea([6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]),
        ...     rmakers.tie(abjad.select().tuplets()[1:3].map(last_leaf)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
            ...     abjad.get.sustained(tuplet)
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
        >>> stack = rmakers.stack(
        ...     rmakers.talea([6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]),
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.tie(abjad.select().tuplets()[1:3].map(last_leaf)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
        >>> stack = rmakers.stack(
        ...     rmakers.talea([6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]),
        ...     rmakers.beam(),
        ...     rmakers.tie(abjad.select().tuplets()[1:3].map(last_leaf)),
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(selector),
        ...     rmakers.rewrite_sustained(
        ...         abjad.select().tuplets()[-2:],
        ...     ),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
    return RewriteSustainedCommand(selector)


def split_measures() -> SplitMeasuresCommand:
    """
    Makes split measures command.
    """
    return SplitMeasuresCommand()


def tie(selector: abjad.Expression = None) -> TieCommand:
    r"""
    Makes tie command.

    ..  container:: example

        TIE-CONSECUTIVE-NOTES RECIPE. Attaches ties notes in selection:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(abjad.select().notes()[5:15]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> selector = abjad.select().tuplets().get([0], 2)
        >>> selector = selector.map(abjad.select().note(-1))
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        TIE-ACROSS-DIVISIONS RECIPE:

        >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(5, 2)]),
        ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
        ... )
        >>> divisions = [(4, 8), (4, 8), (4, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

    ..  container:: example

        TIE-WITHIN-DIVISIONS RECIPE:

        >>> selector = abjad.select().tuplets()
        >>> nonlast_notes = abjad.select().notes()[:-1]
        >>> selector = selector.map(nonlast_notes)
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.untie(selector),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> selector = abjad.select().tuplets().get([0], 2)
        >>> selector = selector.map(abjad.select().notes()[:-1])
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(selector),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
    return TieCommand(selector=selector)


def tremolo_container(
    count: int, selector: abjad.Expression = None
) -> TremoloContainerCommand:
    r"""
    Makes tremolo container command.

    ..  container:: example

        Repeats figures two times each:

        >>> selector = abjad.select().notes().get([0, -1])
        >>> selector = abjad.select().tuplets().map(selector)
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4]),
        ...     rmakers.tremolo_container(2, selector),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> selector = abjad.select().components(abjad.TremoloContainer)
        >>> result = [abjad.slur(_) for _ in selector(selections)]
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/4
                    s1 * 1
                    \time 3/4
                    s1 * 3/4
                }
                \new RhythmicStaff
                {
                    \repeat tremolo 2 {
                        c'16
                        (
                        c'16
                        )
                    }
                    c'4
                    c'4
                    \repeat tremolo 2 {
                        c'16
                        (
                        c'16
                        )
                    }
                    \repeat tremolo 2 {
                        c'16
                        (
                        c'16
                        )
                    }
                    c'4
                    \repeat tremolo 2 {
                        c'16
                        (
                        c'16
                        )
                    }
                }
            >>

        Repeats figures four times each:

        >>> selector = abjad.select().notes().get([0, -1])
        >>> selector = abjad.select().tuplets().map(selector)
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([4]),
        ...     rmakers.tremolo_container(4, selector),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 4), (3, 4)]
        >>> selections = stack(divisions)
        >>> selector = abjad.select().components(abjad.TremoloContainer)
        >>> result = [abjad.slur(_) for _ in selector(selections)]
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 4/4
                    s1 * 1
                    \time 3/4
                    s1 * 3/4
                }
                \new RhythmicStaff
                {
                    \repeat tremolo 4 {
                        c'32
                        (
                        c'32
                        )
                    }
                    c'4
                    c'4
                    \repeat tremolo 4 {
                        c'32
                        (
                        c'32
                        )
                    }
                    \repeat tremolo 4 {
                        c'32
                        (
                        c'32
                        )
                    }
                    c'4
                    \repeat tremolo 4 {
                        c'32
                        (
                        c'32
                        )
                    }
                }
            >>

    """
    return TremoloContainerCommand(count, selector=selector)


def trivialize(selector: abjad.Expression = None) -> TrivializeCommand:
    """
    Makes trivialize command.
    """
    return TrivializeCommand(selector)


def unbeam(
    selector: abjad.Expression = abjad.select().leaves(),
) -> UnbeamCommand:
    """
    Makes unbeam command.
    """
    return UnbeamCommand(selector)


def untie(selector: abjad.Expression = None) -> UntieCommand:
    r"""
    Makes untie command.

    ..  container:: example

        Attaches ties to nonlast notes; then detaches ties from select
        notes:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(abjad.select().notes()[:-1]),
        ...     rmakers.untie(abjad.select().notes().get([0], 4)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

    ..  container:: example

        Attaches repeat-ties to nonfirst notes; then detaches ties from
        select notes:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.repeat_tie(abjad.select().notes()[1:]),
        ...     rmakers.untie(abjad.select().notes().get([0], 4)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> selections = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
    return UntieCommand(selector=selector)


def written_duration(
    duration: abjad.DurationTyping,
    selector: abjad.Expression = abjad.select().leaves(),
) -> WrittenDurationCommand:
    """
    Makes written duration command.
    """
    return WrittenDurationCommand(duration, selector=selector)
