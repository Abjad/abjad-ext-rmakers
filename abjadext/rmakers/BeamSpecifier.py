import abjad
import typing


class BeamSpecifier(object):
    r"""
    Beam specifier.

    ..  container:: example

        Beams each division by default:

        >>> staff = abjad.Staff(name='RhythmicStaff')
        >>> staff.extend("c'8 c' c'16 c' c' c' c'8 c' c' c'")
        >>> abjad.setting(staff).auto_beaming = False
        >>> selections = [staff[:4], staff[4:]]
        >>> specifier = abjadext.rmakers.BeamSpecifier()
        >>> specifier(selections)
        >>> abjad.show(staff) # doctest: +SKIP

        ..  docs::

            >>> abjad.f(staff)
            \context Staff = "RhythmicStaff"
            \with
            {
                autoBeaming = ##f
            }
            {
                c'8
                [
                c'8
                c'16
                c'16
                ]
                c'16
                [
                c'16
                c'8
                c'8
                c'8
                c'8
                ]
            }

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Specifiers'

    __slots__ = (
        '_beam_divisions_together',
        '_beam_each_division',
        '_beam_lone_notes',
        '_beam_rests',
        '_stemlet_length',
        '_use_feather_beams',
        )

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        beam_each_division: bool = True,
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

    def __call__(self, selections, tag: str = None) -> None:
        """
        Calls beam specifier on ``selections``.
        """

        #_ll = abjad.select(selections).leaves()
        #print(selections, 'AAA1')
        #print(_ll, 'AAA2', len(_ll))

        self._detach_all_beams(selections)
        if self.beam_divisions_together:

            durations = []
            for selection in selections:
                duration = abjad.inspect(selection).duration()
                durations.append(duration)

#            beam = abjad.Beam(
#                beam_rests=self.beam_rests,
#                durations=durations,
#                span_beam_count=1,
#                stemlet_length=self.stemlet_length,
#                )

            components: typing.List[abjad.Component] = []
            for selection in selections:
                if isinstance(selection, abjad.Selection):
                    components.extend(selection)
                elif isinstance(selection, abjad.Tuplet):
                    components.append(selection)
                else:
                    raise TypeError(selection)
            # TODO: possibly do_not_iterate_grace_containers=True instead?
            leaves = abjad.select(components).leaves(grace_notes=False)
            #abjad.attach(beam, leaves, tag=tag)
            #print(leaves, 'AAA-together', len(leaves))
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
                # TODO: possibly do_not_iterate_grace_containers=True instead?
                leaves = abjad.select(selection).leaves(grace_notes=False)
#                beam = abjad.Beam(
#                    beam_rests=self.beam_rests,
#                    stemlet_length=self.stemlet_length,
#                    )
#                abjad.attach(beam, leaves, tag=tag)
#                # TODO:
                #print(leaves, 'AAA-each', len(leaves))
                abjad.beam(
                    leaves,
                    beam_lone_notes=self.beam_lone_notes,
                    beam_rests=self.beam_rests,
                    stemlet_length=self.stemlet_length,
                    tag=tag,
                    )

    def __format__(self, format_specification='') -> str:
        """
        Formats beam specifier.

        ..  container:: example

            >>> specifier = abjadext.rmakers.BeamSpecifier()
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

            >>> abjadext.rmakers.BeamSpecifier()
            BeamSpecifier(beam_each_division=True)

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    # TODO: possibly do_not_iterate_grace_containers=True instead?
    @staticmethod
    def _detach_all_beams(divisions, grace_notes=False):
        for leaf in abjad.iterate(divisions).leaves(grace_notes=grace_notes):
            abjad.detach(abjad.Beam, leaf)
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

    ### PUBLIC PROPERTIES ###

    @property
    def beam_divisions_together(self) -> typing.Optional[bool]:
        r"""
        Is true when divisions should beam together.

        ..  container:: example

            Does not beam divisions together:

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 c' c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier()
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    c'8
                    [
                    c'8
                    c'16
                    c'16
                    ]
                    c'16
                    [
                    c'16
                    c'8
                    c'8
                    c'8
                    c'8
                    ]
                }

        ..  container:: example

            Beams divisions together (but excludes rests):

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 r c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     beam_divisions_together=True,
            ...     beam_rests=False,
            ...     )
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    \set stemLeftBeamCount = 0
                    \set stemRightBeamCount = 1
                    c'8
                    [
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 1
                    c'8
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 1
                    c'16
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 1
                    c'16
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 0
                    c'8
                    ]
                    r8
                    \set stemLeftBeamCount = 0
                    \set stemRightBeamCount = 1
                    c'8
                    [
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 0
                    c'8
                    ]
                }

        ..  container:: example

            Beams divisions together (and includes rests):

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 r c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     beam_divisions_together=True,
            ...     beam_rests=True,
            ...     )
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    \set stemLeftBeamCount = 0
                    \set stemRightBeamCount = 1
                    c'8
                    [
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 1
                    c'8
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 1
                    c'16
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 2
                    c'16
                    \set stemLeftBeamCount = 2
                    \set stemRightBeamCount = 1
                    c'16
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 1
                    c'8
                    r8
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 1
                    c'8
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 0
                    c'8
                    ]
                }

        ..  container:: example

            Defaults to none:

            >>> specifier = abjadext.rmakers.BeamSpecifier()
            >>> specifier.beam_divisions_together is None
            True

        """
        return self._beam_divisions_together

    @property
    def beam_each_division(self) -> typing.Optional[bool]:
        r"""
        Is true when specifier beams each division.

        ..  container:: example

            Beams nothing:

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 c' c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     beam_each_division=False,
            ...     )
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    c'8
                    c'8
                    c'16
                    c'16
                    c'16
                    c'16
                    c'8
                    c'8
                    c'8
                    c'8
                }

        ..  container:: example

            Beams each division (but excludes rests):

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 r c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     beam_each_division=True,
            ...     beam_rests=False,
            ...     )
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    c'8
                    [
                    c'8
                    c'16
                    c'16
                    ]
                    c'16
                    [
                    c'16
                    c'8
                    ]
                    r8
                    c'8
                    [
                    c'8
                    ]
                }

        ..  container:: example

            Beams each division (and includes rests):

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 r c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     beam_each_division=True,
            ...     beam_rests=True,
            ...     )
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    c'8
                    [
                    c'8
                    c'16
                    c'16
                    ]
                    c'16
                    [
                    c'16
                    c'8
                    r8
                    c'8
                    c'8
                    ]
                }

        ..  container:: example

            Defaults to true:

            >>> specifier = abjadext.rmakers.BeamSpecifier()
            >>> specifier.beam_each_division
            True

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
        Is true when beams should include rests.

        ..  container:: example

            Does not beam rests:

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 r c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier()
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    c'8
                    [
                    c'8
                    c'16
                    c'16
                    ]
                    c'16
                    [
                    c'16
                    c'8
                    ]
                    r8
                    c'8
                    [
                    c'8
                    ]
                }

        ..  container:: example

            Beams rests:

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 r c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     beam_rests=True,
            ...     )
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    c'8
                    [
                    c'8
                    c'16
                    c'16
                    ]
                    c'16
                    [
                    c'16
                    c'8
                    r8
                    c'8
                    c'8
                    ]
                }

        ..  container:: example

            Beams skips:

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 s c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     beam_rests=True,
            ...     )
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    c'8
                    [
                    c'8
                    c'16
                    c'16
                    ]
                    c'16
                    [
                    c'16
                    c'8
                    s8
                    c'8
                    c'8
                    ]
                }

        ..  container:: example

            Defaults to none:

            >>> specifier = abjadext.rmakers.BeamSpecifier()
            >>> specifier.beam_rests is None
            True

        """
        return self._beam_rests

    @property
    def stemlet_length(self) -> typing.Optional[typing.Union[int, float]]:
        r"""
        Gets stemlet length.

        ..  container:: example

            Beams rests without stemlets:

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 r c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     beam_rests=True,
            ...     )
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    c'8
                    [
                    c'8
                    c'16
                    c'16
                    ]
                    c'16
                    [
                    c'16
                    c'8
                    r8
                    c'8
                    c'8
                    ]
                }

        ..  container:: example

            Beams rests with stemlets:

            >>> staff = abjad.Staff(name='RhythmicStaff')
            >>> staff.extend("c'8 c' c'16 c' c' c' c'8 r c' c'")
            >>> abjad.setting(staff).auto_beaming = False
            >>> selections = [staff[:4], staff[4:]]
            >>> specifier = abjadext.rmakers.BeamSpecifier(
            ...     beam_rests=True,
            ...     stemlet_length=2,
            ...     )
            >>> specifier(selections)
            >>> abjad.show(staff) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(staff)
                \context Staff = "RhythmicStaff"
                \with
                {
                    autoBeaming = ##f
                }
                {
                    \override Staff.Stem.stemlet-length = 2
                    c'8
                    [
                    c'8
                    c'16
                    \revert Staff.Stem.stemlet-length
                    c'16
                    ]
                    \override Staff.Stem.stemlet-length = 2
                    c'16
                    [
                    c'16
                    c'8
                    r8
                    c'8
                    \revert Staff.Stem.stemlet-length
                    c'8
                    ]
                }

        Stemlets appear only when ``beam_rests`` is set to true.

        ..  container:: example

            Defaults to none:

            >>> specifier = abjadext.rmakers.BeamSpecifier()
            >>> specifier.stemlet_length is None
            True

        """
        return self._stemlet_length

    @property
    def use_feather_beams(self) -> typing.Optional[bool]:
        """
        Is true when multiple beams should feather.

        ..  container:: example

            >>> specifier = abjadext.rmakers.BeamSpecifier()
            >>> specifier.use_feather_beams is None
            True

        """
        return self._use_feather_beams
