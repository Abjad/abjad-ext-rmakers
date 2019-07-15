import abjad
import typing


class BeamSpecifier(object):
    """
    Beam specifier.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

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

            >>> specifier = rmakers.BeamSpecifier(
            ...     selector=abjad.select().tuplets(),
            ...     )
            >>> abjad.f(specifier)
            abjadext.rmakers.BeamSpecifier(
                selector=abjad.select().tuplets(),
                )

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of beam specifier.

        ..  container:: example

            >>> rmakers.BeamSpecifier()
            BeamSpecifier()

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
