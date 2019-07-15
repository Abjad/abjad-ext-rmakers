import abjad
import collections
import typing
from . import typings


### CLASSES ###


class BeamCommand(object):
    """
    Beam command.
    """

    ### CLASS VARIABLES ###

    __slots__ = (
        "_beam_divisions_together",
        "_beam_lone_notes",
        "_beam_rests",
        "_selector",
        "_stemlet_length",
        "_use_feather_beams",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        beam_divisions_together: bool = None,
        beam_lone_notes: bool = None,
        beam_rests: bool = None,
        selector: abjad.SelectorTyping = None,
        stemlet_length: typing.Union[int, float] = None,
        use_feather_beams: bool = None,
    ) -> None:
        if beam_divisions_together is not None:
            beam_divisions_together = bool(beam_divisions_together)
        # if beam_divisions_together is True:
        #    assert selector is not None
        self._beam_divisions_together = beam_divisions_together
        if beam_lone_notes is not None:
            beam_lone_notes = bool(beam_lone_notes)
        self._beam_lone_notes = beam_lone_notes
        if beam_rests is not None:
            beam_rests = bool(beam_rests)
        self._beam_rests = beam_rests
        if isinstance(selector, str):
            selector = eval(selector)
            assert isinstance(selector, abjad.Expression)
        self._selector = selector
        if stemlet_length is not None:
            assert isinstance(stemlet_length, (int, float))
        self._stemlet_length = stemlet_length
        if use_feather_beams is not None:
            use_feather_beams = bool(use_feather_beams)
        self._use_feather_beams = use_feather_beams

    ### SPECIAL METHODS ###

    def __call__(self, staff, tag: str = None) -> None:
        """
        Calls beam specifier on ``selections``.
        """
        from .RhythmMaker import RhythmMaker

        components: typing.List[abjad.Component] = []
        if self.selector is not None:
            if isinstance(staff, abjad.Staff):
                selection = staff["MusicVoice"]
            else:
                selection = staff
            selections = self.selector(selection)
            #            print()
            #            for selection in selections:
            #                print("SSS", selection)
            if self.beam_divisions_together:
                self._detach_all_beams(selections)
                durations = []
                for selection in selections:
                    duration = abjad.inspect(selection).duration()
                    durations.append(duration)
                for selection in selections:
                    if isinstance(selection, abjad.Selection):
                        components.extend(selection)
                    elif isinstance(selection, abjad.Tuplet):
                        components.append(selection)
                    else:
                        raise TypeError(selection)
                leaves = abjad.select(components).leaves(
                    do_not_iterate_grace_containers=True
                )
                abjad.beam(
                    leaves,
                    beam_lone_notes=self.beam_lone_notes,
                    beam_rests=self.beam_rests,
                    durations=durations,
                    span_beam_count=1,
                    stemlet_length=self.stemlet_length,
                    tag=tag,
                )
            else:
                for selection in selections:
                    self._detach_all_beams(selection)
                    leaves = abjad.select(selection).leaves(
                        do_not_iterate_grace_containers=True
                    )
                    abjad.beam(
                        leaves,
                        beam_lone_notes=self.beam_lone_notes,
                        beam_rests=self.beam_rests,
                        stemlet_length=self.stemlet_length,
                        tag=tag,
                    )
        else:
            if isinstance(staff, abjad.Staff):
                selections = RhythmMaker._select_by_measure(staff)
            else:
                selections = staff
            self._detach_all_beams(selections)
            if self.beam_divisions_together:
                durations = []
                for selection in selections:
                    duration = abjad.inspect(selection).duration()
                    durations.append(duration)
                for selection in selections:
                    if isinstance(selection, abjad.Selection):
                        components.extend(selection)
                    elif isinstance(selection, abjad.Tuplet):
                        components.append(selection)
                    else:
                        raise TypeError(selection)
                leaves = abjad.select(components).leaves(
                    do_not_iterate_grace_containers=True
                )
                abjad.beam(
                    leaves,
                    beam_lone_notes=self.beam_lone_notes,
                    beam_rests=self.beam_rests,
                    durations=durations,
                    span_beam_count=1,
                    stemlet_length=self.stemlet_length,
                    tag=tag,
                )
        if self.use_feather_beams:
            for selection in selections:
                first_leaf = abjad.select(selection).leaf(0)
                if self._is_accelerando(selection):
                    abjad.override(
                        first_leaf
                    ).beam.grow_direction = abjad.Right
                elif self._is_ritardando(selection):
                    abjad.override(first_leaf).beam.grow_direction = abjad.Left

    def __format__(self, format_specification="") -> str:
        """
        Formats beam specifier.

        ..  container:: example

            >>> specifier = rmakers.BeamCommand(
            ...     selector=abjad.select().tuplets(),
            ...     )
            >>> abjad.f(specifier)
            abjadext.commands.BeamCommand(
                selector=abjad.select().tuplets(),
                )

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of beam specifier.

        ..  container:: example

            >>> rmakers.BeamCommand()
            BeamCommand()

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    @staticmethod
    def _detach_all_beams(divisions):
        leaves = abjad.select(divisions).leaves(
            do_not_iterate_grace_containers=True
        )
        for leaf in leaves:
            abjad.detach(abjad.BeamCount, leaf)
            abjad.detach(abjad.StartBeam, leaf)
            abjad.detach(abjad.StopBeam, leaf)

    @staticmethod
    def _make_beamable_groups(components, durations):
        music_duration = abjad.inspect(components).duration()
        if music_duration != sum(durations):
            message = f"music duration {music_duration} does not equal"
            message += f" total duration {sum(durations)}:\n"
            message += f"   {components}\n"
            message += f"   {durations}"
            raise Exception(message)
        component_to_timespan = []
        start_offset = abjad.Offset(0)
        for component in components:
            duration = abjad.inspect(component).duration()
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
            group_duration = abjad.inspect(group).duration()
            assert group_duration <= target_duration
            if group_duration == target_duration:
                beamable_groups.append(group)
            else:
                beamable_groups.append(abjad.select([]))
        return beamable_groups

    def _is_accelerando(self, selection):
        first_leaf = abjad.select(selection).leaf(0)
        last_leaf = abjad.select(selection).leaf(-1)
        first_duration = abjad.inspect(first_leaf).duration()
        last_duration = abjad.inspect(last_leaf).duration()
        if last_duration < first_duration:
            return True
        return False

    def _is_ritardando(self, selection):
        first_leaf = abjad.select(selection).leaf(0)
        last_leaf = abjad.select(selection).leaf(-1)
        first_duration = abjad.inspect(first_leaf).duration()
        last_duration = abjad.inspect(last_leaf).duration()
        if first_duration < last_duration:
            return True
        return False

    ### PUBLIC PROPERTIES ###

    @property
    def beam_divisions_together(self) -> typing.Optional[bool]:
        r"""
        Is true when divisions beam together.
        """
        return self._beam_divisions_together

    @property
    def beam_lone_notes(self) -> typing.Optional[bool]:
        """
        Is true when specifier beams lone notes.
        """
        return self._beam_lone_notes

    @property
    def beam_rests(self) -> typing.Optional[bool]:
        r"""
        Is true when beams include rests.
        """
        return self._beam_rests

    @property
    def selector(self) -> typing.Optional[abjad.Expression]:
        """
        Gets selector.
        """
        return self._selector

    @property
    def stemlet_length(self) -> typing.Optional[typing.Union[int, float]]:
        r"""
        Gets stemlet length.
        """
        return self._stemlet_length

    @property
    def use_feather_beams(self) -> typing.Optional[bool]:
        """
        Is true when multiple beams feather.
        """
        return self._use_feather_beams


class CacheStateCommand(object):
    """
    Cache state command.
    """

    ### CLASS VARIABLES ###

    _publish_storage_format = True

    ### SPECIAL METHODS ###

    def __format__(self, format_specification="") -> str:
        """
        Formats directive.

        ..  container:: example

            >>> specifier = rmakers.cache_state()
            >>> abjad.f(specifier)
            abjadext.commands.CacheStateCommand()

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of directive.

        ..  container:: example

            >>> rmakers.cache_state()
            CacheStateCommand()

        """
        return abjad.StorageFormatManager(self).get_repr_format()


class NoteCommand(object):
    r"""
    Note command.

    ..  container:: example

        Changes logical ties 1 and 2 to notes:

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.rest(abjad.select().leaves()),
        ...     abjadext.rmakers.note(abjad.select().logical_ties()[1:3]),
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

    ..  container:: example

        Sustains logical ties -1 and -2 to notes:

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.rest(abjad.select().leaves()),
        ...     abjadext.rmakers.note(abjad.select().logical_ties()[-2:]),
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
                    r4.
                    c'4..
                    c'4.
                }
            >>

    ..  container:: example

        Changes patterned selection of leaves to notes:

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.rest(abjad.select().leaves()),
        ...     abjadext.rmakers.note(abjad.select().logical_ties()[1:-1]),
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

    ..  container:: example

        Changes patterned selection of leave to notes. Works inverted composite
        pattern:

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.rest(abjad.select().leaves()),
        ...     abjadext.rmakers.note(
        ...         abjad.select().logical_ties().get([0, -1]),
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

    """

    ### CLASS VARIABLES ###

    __slots__ = ("_selector",)

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(self, selector: abjad.SelectorTyping) -> None:
        if isinstance(selector, str):
            selector = eval(selector)
            assert isinstance(selector, abjad.Expression)
        self._selector = selector

    ### SPECIAL METHODS ###

    def __call__(self, staff, tag=None):
        if isinstance(staff, abjad.Staff):
            selection = staff["MusicVoice"]
        else:
            selection = staff
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
            abjad.mutate(leaf).replace([note])

    def __format__(self, format_specification="") -> str:
        """
        Formats note command.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of note command.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC PROPERTIES ###

    @property
    def selector(self) -> typing.Optional[abjad.Expression]:
        """
        Gets selector.
        """
        return self._selector


class RestCommand(object):
    r"""
    Rest command.

    ..  container:: example

        Changes logical ties 1 and 2 to rests:

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.rest(abjad.select().logical_ties()[1:3]),
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
        ...     abjadext.rmakers.rest(abjad.select().logical_ties()[-2:]),
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

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.rest(abjad.select().logical_ties()[1:-1]),
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

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
        ...     abjadext.rmakers.rest(
        ...         abjad.select().logical_ties().get([0, -1]),
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
        Formats rest command.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of rest command.
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
        Is true when rest command uses multimeasure rests.
        """
        return self._use_multimeasure_rests


class RewriteMeterCommand(object):
    """
    Rewrite meter command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_reference_meters", "_repeat_ties")

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(self, *, reference_meters=None, repeat_ties=None) -> None:
        self._reference_meters = reference_meters
        self._repeat_ties = repeat_ties

    ### SPECIAL METHODS ###

    def __call__(
        self, staff, *, time_signatures=None, tag: str = None
    ) -> None:
        """
        Calls rewrite meter command.
        """
        from .RhythmMaker import RhythmMaker

        assert time_signatures is None, repr(time_signatures)
        time_signature_voice = staff["TimeSignatureVoice"]
        meters = []
        for skip in time_signature_voice:
            time_signature = abjad.inspect(skip).indicator(abjad.TimeSignature)
            meter = abjad.Meter(time_signature)
            meters.append(meter)
        durations = [abjad.Duration(_) for _ in meters]
        reference_meters = self.reference_meters or ()
        command = SplitMeasuresCommand(repeat_ties=self.repeat_ties)
        command(staff, time_signatures=meters)
        selections = RhythmMaker._select_by_measure(staff)
        for meter, selection in zip(meters, selections):
            for reference_meter in reference_meters:
                if str(reference_meter) == str(meter):
                    meter = reference_meter
                    break

            nontupletted_leaves = []
            for leaf in abjad.iterate(selection).leaves():
                if not abjad.inspect(leaf).parentage().count(abjad.Tuplet):
                    nontupletted_leaves.append(leaf)
            BeamCommand._detach_all_beams(nontupletted_leaves)
            abjad.mutate(selection).rewrite_meter(
                meter, rewrite_tuplets=False, repeat_ties=self.repeat_ties
            )
        selections = RhythmMaker._select_by_measure(staff)
        for meter, selection in zip(meters, selections):
            leaves = abjad.select(selection).leaves(
                do_not_iterate_grace_containers=True
            )
            beat_durations = []
            beat_offsets = meter.depthwise_offset_inventory[1]
            for start, stop in abjad.sequence(beat_offsets).nwise():
                beat_duration = stop - start
                beat_durations.append(beat_duration)
            beamable_groups = BeamCommand._make_beamable_groups(
                leaves, beat_durations
            )
            for beamable_group in beamable_groups:
                if not beamable_group:
                    continue
                abjad.beam(
                    beamable_group,
                    beam_rests=False,
                    tag="rmakers.RewriteMeterCommand.__call__",
                )

    def __format__(self, format_specification="") -> str:
        """
        Formats rewrite meter command.

        ..  container:: example

            >>> specifier = abjadext.rmakers.rewrite_meter()
            >>> abjad.f(specifier)
            abjadext.commands.RewriteMeterCommand()

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> abjadext.rmakers.rewrite_meter()
            RewriteMeterCommand()

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PUBLIC PROPERTIES ###

    @property
    def reference_meters(self):
        """
        Gets reference meters.
        """
        return self._reference_meters

    @property
    def repeat_ties(self):
        """
        Gets repeat ties.
        """
        return self._repeat_ties


class SplitMeasuresCommand(object):
    """
    Split measures command.
    """

    ### CLASS VARIABLES ###

    __slots__ = "_repeat_ties"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(self, *, repeat_ties=None) -> None:
        self._repeat_ties = repeat_ties

    ### SPECIAL METHODS ###

    def __call__(
        self, staff, *, time_signatures=None, tag: str = None
    ) -> None:
        """
        Calls split command.
        """
        music_voice = staff["MusicVoice"]
        if time_signatures is None:
            time_signature_voice = staff["TimeSignatureVoice"]
            durations = [
                abjad.inspect(_).duration() for _ in time_signature_voice
            ]
        else:
            durations = [abjad.Duration(_.pair) for _ in time_signatures]
        total_duration = sum(durations)
        music_duration = abjad.inspect(music_voice).duration()
        if total_duration != music_duration:
            message = f"Total duration of splits is {total_duration!s}"
            message += f" but duration of music is {music_duration!s}:"
            message += f"\ndurations: {durations}."
            message += f"\nmusic voice: {music_voice[:]}."
            raise Exception(message)
        abjad.mutate(music_voice[:]).split(
            durations=durations, repeat_ties=self.repeat_ties
        )

    def __format__(self, format_specification="") -> str:
        """
        Formats command.

        ..  container:: example

            >>> specifier = abjadext.rmakers.split_measures()
            >>> abjad.f(specifier)
            abjadext.commands.SplitMeasuresCommand()

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of command.

        ..  container:: example

            >>> abjadext.rmakers.split_measures()
            SplitMeasuresCommand()

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    # TODO: activate tag
    def _call(self, music_voice, durations, *, tag=None):
        durations = [abjad.Duration(_) for _ in durations]
        total_duration = sum(durations)
        music_duration = abjad.inspect(music_voice).duration()
        if total_duration != music_duration:
            message = f"Total duration of splits is {total_duration!s}"
            message += f" but duration of music is {music_duration!s}:"
            message += f"\ndurations: {durations}."
            message += f"\nmusic voice: {music_voice[:]}."
            raise Exception(message)
        abjad.mutate(music_voice[:]).split(
            durations=durations, repeat_ties=self.repeat_ties
        )
        components = music_voice[:]
        component_durations = [abjad.inspect(_).duration() for _ in components]
        parts = abjad.sequence(component_durations)
        parts = parts.partition_by_weights(
            weights=durations, allow_part_weights=abjad.Exact
        )
        part_lengths = [len(_) for _ in parts]
        parts = abjad.sequence(components).partition_by_counts(
            counts=part_lengths, overhang=abjad.Exact
        )
        selections = [abjad.select(_) for _ in parts]
        return selections

    ### PUBLIC PROPERTIES ###

    @property
    def repeat_ties(self):
        """
        Is true when command uses repeat ties.
        """
        return self._repeat_ties


class TieCommand(object):
    """
    Tie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = (
        "_attach_repeat_ties",
        "_attach_ties",
        "_detach_repeat_ties",
        "_detach_ties",
        "_repeat_ties",
        "_selector",
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

    ### SPECIAL METHODS ###

    def __call__(self, staff, *, tag: str = None) -> None:
        """
        Calls tie specifier on ``staff``.
        """
        assert isinstance(staff, abjad.Staff), repr(staff)
        self._attach_repeat_ties_(staff)
        self._attach_ties_(staff)
        self._detach_ties_(staff)
        self._detach_repeat_ties_(staff)
        self._configure_repeat_ties(staff)

    def __eq__(self, argument) -> bool:
        """
        Is true when initialization values of tie specifier equal
        initialization values of ``argument``.
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
        if not self.attach_repeat_ties:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for note in abjad.select(selection).notes():
            tie = abjad.RepeatTie()
            abjad.attach(tie, note, tag=tag)

    def _attach_ties_(self, staff, tag: str = None):
        if not self.attach_ties:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for note in abjad.select(selection).notes():
            tie = abjad.TieIndicator()
            abjad.attach(tie, note, tag=tag)

    def _detach_repeat_ties_(self, staff, tag: str = None):
        if not self.detach_repeat_ties:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for note in abjad.select(selection).notes():
            abjad.detach(abjad.RepeatTie, note)

    def _detach_ties_(self, staff, tag: str = None):
        if not self.detach_ties:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for note in abjad.select(selection).notes():
            abjad.detach(abjad.TieIndicator, note)

    def _configure_repeat_ties(self, staff):
        if not self.repeat_ties:
            return None
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        add_repeat_ties = []
        for leaf in abjad.select(selection).leaves():
            if abjad.inspect(leaf).has_indicator(abjad.TieIndicator):
                next_leaf = abjad.inspect(leaf).leaf(1)
                if next_leaf is None:
                    continue
                if not isinstance(next_leaf, (abjad.Chord, abjad.Note)):
                    continue
                if abjad.inspect(next_leaf).has_indicator(abjad.RepeatTie):
                    continue
                add_repeat_ties.append(next_leaf)
                abjad.detach(abjad.TieIndicator, leaf)
        for leaf in add_repeat_ties:
            repeat_tie = abjad.RepeatTie()
            abjad.attach(repeat_tie, leaf)

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
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieCommand(
            ...         attach_repeat_ties=True,
            ...         selector=selector,
            ...         ),
            ...     rmakers.BeamCommand(selector=abjad.select().tuplets()),
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

            >>> selector = abjad.select().tuplets().get([1], 2)
            >>> selector = selector.map(abjad.select().note(0))
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieCommand(
            ...         attach_repeat_ties=True,
            ...         selector=selector,
            ...         ),
            ...     rmakers.BeamCommand(selector=abjad.select().tuplets()),
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

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieCommand(
            ...         attach_ties=True,
            ...         selector=abjad.select().notes()[5:15],
            ...         ),
            ...     rmakers.BeamCommand(selector=abjad.select().tuplets()),
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
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieCommand(
            ...         attach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     rmakers.BeamCommand(selector=abjad.select().tuplets()),
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

            >>> selector = abjad.select().tuplets().get([0], 2)
            >>> selector = selector.map(abjad.select().note(-1))
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieCommand(
            ...         attach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     rmakers.BeamCommand(selector=abjad.select().tuplets()),
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

            TIE-ACROSS-DIVISIONS RECIPE:

            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.TupletRhythmMaker(
            ...     rmakers.TieCommand(
            ...         attach_ties=True,
            ...         selector=nonlast_tuplets.map(last_leaf),
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

        ..  container:: example

            TIE-WITHIN-DIVISIONS RECIPE:

            >>> selector = abjad.select().tuplets()
            >>> nonlast_notes = abjad.select().notes()[:-1]
            >>> selector = selector.map(nonlast_notes)
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieCommand(
            ...         detach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     rmakers.TieCommand(
            ...         attach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     rmakers.BeamCommand(selector=abjad.select().tuplets()),
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

            >>> selector = abjad.select().tuplets().get([0], 2)
            >>> selector = selector.map(abjad.select().notes()[:-1])
            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieCommand(
            ...         attach_ties=True,
            ...         selector=selector,
            ...         ),
            ...     rmakers.BeamCommand(selector=abjad.select().tuplets()),
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

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieCommand(
            ...         attach_repeat_ties=True,
            ...         selector=abjad.select().notes()[1:],
            ...         ),
            ...     rmakers.TieCommand(
            ...         detach_repeat_ties=True,
            ...         selector=abjad.select().notes().get([0], 4),
            ...         ),
            ...     rmakers.BeamCommand(selector=abjad.select().tuplets()),
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

            >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
            ...     rmakers.TieCommand(
            ...         attach_ties=True,
            ...         selector=abjad.select().notes()[:-1],
            ...         ),
            ...     rmakers.TieCommand(
            ...         detach_ties=True,
            ...         selector=abjad.select().notes().get([0], 4),
            ...         ),
            ...     rmakers.BeamCommand(selector=abjad.select().tuplets()),
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


### FACTORY FUNCTIONS ###


def cache_state() -> CacheStateCommand:
    """
    Makes cache state command.
    """
    return CacheStateCommand()


def note(selector: abjad.SelectorTyping,) -> NoteCommand:
    """
    Makes rest command.
    """
    return NoteCommand(selector)


def rest(
    selector: abjad.SelectorTyping, *, use_multimeasure_rests: bool = None
) -> RestCommand:
    """
    Makes rest command.
    """
    return RestCommand(selector, use_multimeasure_rests=use_multimeasure_rests)


def rewrite_meter(
    *, reference_meters=None, repeat_ties=None
) -> RewriteMeterCommand:
    """
    Makes rewrite meter command.
    """
    return RewriteMeterCommand(
        reference_meters=reference_meters, repeat_ties=repeat_ties
    )


def split_measures(*, repeat_ties=None) -> SplitMeasuresCommand:
    """
    Makes split measures command.
    """
    return SplitMeasuresCommand(repeat_ties=repeat_ties)
