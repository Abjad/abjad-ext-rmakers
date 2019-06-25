import abjad
import typing


class BeamSpecifier(object):
    r"""
    Beam specifier.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = (
        "_beam_divisions_together",
        "_beam_each_division",
        "_beam_lone_notes",
        "_beam_rests",
        "_stemlet_length",
        "_use_feather_beams",
    )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        beam_each_division: bool = None,
        beam_divisions_together: bool = None,
        beam_lone_notes: bool = None,
        beam_rests: bool = None,
        stemlet_length: typing.Union[int, float] = None,
        use_feather_beams: bool = None,
    ) -> None:
        if beam_each_division is None:
            beam_each_division = bool(beam_each_division)
        self._beam_each_division = beam_each_division
        if beam_divisions_together is not None:
            beam_divisions_together = bool(beam_divisions_together)
        self._beam_divisions_together = beam_divisions_together
        if beam_lone_notes is not None:
            beam_lone_notes = bool(beam_lone_notes)
        self._beam_lone_notes = beam_lone_notes
        if beam_rests is not None:
            beam_rests = bool(beam_rests)
        self._beam_rests = beam_rests
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
        if isinstance(staff, abjad.Staff):
            time_signature_voice = staff["TimeSignatureVoice"]
            assert isinstance(time_signature_voice, abjad.Voice)
            durations = [
                abjad.inspect(_).duration() for _ in time_signature_voice
            ]
            music_voice = staff["MusicVoice"]
            selections = music_voice[:].partition_by_durations(durations)
            selections = list(selections)
        else:
            selections = staff
        self._detach_all_beams(selections)
        if self.beam_divisions_together:
            durations = []
            for selection in selections:
                duration = abjad.inspect(selection).duration()
                durations.append(duration)
            components: typing.List[abjad.Component] = []
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
        elif self.beam_each_division:
            for selection in selections:
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

            >>> specifier = abjadext.rmakers.BeamSpecifier(beam_each_division=True)
            >>> abjad.f(specifier)
            abjadext.rmakers.BeamSpecifier(
                beam_each_division=True,
                )

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of beam specifier.

        ..  container:: example

            >>> abjadext.rmakers.BeamSpecifier(beam_each_division=True)
            BeamSpecifier(beam_each_division=True)

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
        assert abjad.inspect(components).duration() == sum(durations)
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
    def beam_each_division(self) -> typing.Optional[bool]:
        r"""
        Is true when specifier beams each division.
        """
        return self._beam_each_division

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
