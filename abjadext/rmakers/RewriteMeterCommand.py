import abjad
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier
from .SplitCommand import SplitCommand


class RewriteMeterCommand(object):
    """
    Rewrite meter command.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

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
        command = SplitCommand(repeat_ties=self.repeat_ties)
        command(staff, time_signatures=meters)
        selections = RhythmMaker._select_by_measure(staff)
        for meter, selection in zip(meters, selections):
            container = abjad.Container()
            abjad.mutate(selection).wrap(container)
            for reference_meter in reference_meters:
                if str(reference_meter) == str(meter):
                    meter = reference_meter
                    break

            nontupletted_leaves = []
            for leaf in abjad.iterate(container).leaves():
                if not abjad.inspect(leaf).parentage().count(abjad.Tuplet):
                    nontupletted_leaves.append(leaf)
            BeamSpecifier._detach_all_beams(nontupletted_leaves)
            abjad.mutate(container[:]).rewrite_meter(
                meter, rewrite_tuplets=False, repeat_ties=self.repeat_ties
            )
            leaves = abjad.select(container).leaves(
                do_not_iterate_grace_containers=True
            )
            beat_durations = []
            beat_offsets = meter.depthwise_offset_inventory[1]
            for start, stop in abjad.sequence(beat_offsets).nwise():
                beat_duration = stop - start
                beat_durations.append(beat_duration)
            beamable_groups = BeamSpecifier._make_beamable_groups(
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
        # making sure to copy first with [:] to avoid iterate-while-change:
        for container in staff["MusicVoice"][:]:
            for leaf in abjad.select(container).leaves():
                abjad.detach(abjad.TimeSignature, leaf)
            abjad.mutate(container).extract()

    def __format__(self, format_specification="") -> str:
        """
        Formats rewrite meter command.

        ..  container:: example

            >>> specifier = abjadext.rmakers.RewriteMeterCommand()
            >>> abjad.f(specifier)
            abjadext.rmakers.RewriteMeterCommand()

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> abjadext.rmakers.RewriteMeterCommand()
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
