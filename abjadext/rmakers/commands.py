import abjad
import collections
import typing


### CLASSES ###


class Command(object):
    """
    Command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_selector",)

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(self, selector: abjad.SelectorTyping = None) -> None:
        if isinstance(selector, str):
            selector = eval(selector)
            assert isinstance(selector, abjad.Expression)
        self._selector = selector

    ### SPECIAL METHODS ###

    def __call__(self, staff, *, tag: str = None) -> None:
        """
        Calls command on ``staff``.
        """
        pass

    def __eq__(self, argument) -> bool:
        """
        Is true when initialization values of command equal
        initialization values of ``argument``.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __format__(self, format_specification="") -> str:
        """
        Formats command.
        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __hash__(self) -> int:
        """
        Hashes command.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __repr__(self) -> str:
        """
        Gets interpreter representation of command.
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

    __slots__ = (
        "_beam_divisions_together",
        "_beam_lone_notes",
        "_beam_rests",
        "_selector",
        "_stemlet_length",
        "_use_feather_beams",
    )

    #    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        beam_divisions_together: bool = None,
        beam_lone_notes: bool = None,
        beam_rests: bool = None,
        selector: abjad.SelectorTyping = None,
        stemlet_length: abjad.Number = None,
        use_feather_beams: bool = None,
    ) -> None:
        super().__init__(selector)
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
        #        if isinstance(selector, str):
        #            selector = eval(selector)
        #            assert isinstance(selector, abjad.Expression)
        #        self._selector = selector
        if stemlet_length is not None:
            assert isinstance(stemlet_length, (int, float))
        self._stemlet_length = stemlet_length
        if use_feather_beams is not None:
            use_feather_beams = bool(use_feather_beams)
        self._use_feather_beams = use_feather_beams

    ### SPECIAL METHODS ###

    def __call__(self, staff, tag: str = None) -> None:
        """
        Calls beam command on ``selections``.
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

    #    def __format__(self, format_specification="") -> str:
    #        """
    #        Formats beam command.
    #
    #        ..  container:: example
    #
    #            >>> command = rmakers.BeamCommand(
    #            ...     selector=abjad.select().tuplets(),
    #            ...     )
    #            >>> abjad.f(command)
    #            abjadext.commands.BeamCommand(
    #                selector=abjad.select().tuplets(),
    #                )
    #
    #        """
    #        return abjad.StorageFormatManager(self).get_storage_format()
    #
    #    def __repr__(self) -> str:
    #        """
    #        Gets interpreter representation of beam command.
    #
    #        ..  container:: example
    #
    #            >>> rmakers.BeamCommand()
    #            BeamCommand()
    #
    #        """
    #        return abjad.StorageFormatManager(self).get_repr_format()

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
        Is true when command beams lone notes.
        """
        return self._beam_lone_notes

    @property
    def beam_rests(self) -> typing.Optional[bool]:
        r"""
        Is true when beams include rests.
        """
        return self._beam_rests

    #    @property
    #    def selector(self) -> typing.Optional[abjad.Expression]:
    #        """
    #        Gets selector.
    #        """
    #        return self._selector

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


class CacheStateCommand(Command):
    """
    Cache state command.
    """

    #    ### CLASS VARIABLES ###
    #
    #    _publish_storage_format = True

    ## INITIALIZER ###

    def __init__(self) -> None:
        pass


#    ### SPECIAL METHODS ###
#
#    def __format__(self, format_specification="") -> str:
#        """
#        Formats directive.
#
#        ..  container:: example
#
#            >>> command = rmakers.cache_state()
#            >>> abjad.f(command)
#            abjadext.commands.CacheStateCommand()
#
#        """
#        return abjad.StorageFormatManager(self).get_storage_format()
#
#    def __repr__(self) -> str:
#        """
#        Gets interpreter representation of directive.
#
#        ..  container:: example
#
#            >>> rmakers.cache_state()
#            CacheStateCommand()
#
#        """
#        return abjad.StorageFormatManager(self).get_repr_format()


class NoteCommand(Command):
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

    #    __slots__ = ("_selector",)
    #
    #    _publish_storage_format = True

    __slots__ = ()

    #    ### INITIALIZER ###
    #
    #    def __init__(self, selector: abjad.SelectorTyping) -> None:
    #        if isinstance(selector, str):
    #            selector = eval(selector)
    #            assert isinstance(selector, abjad.Expression)
    #        self._selector = selector

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


#    def __format__(self, format_specification="") -> str:
#        """
#        Formats note command.
#        """
#        return abjad.StorageFormatManager(self).get_storage_format()
#
#    def __repr__(self) -> str:
#        """
#        Gets interpreter representation of note command.
#        """
#        return abjad.StorageFormatManager(self).get_repr_format()

#    ### PUBLIC PROPERTIES ###
#
#    @property
#    def selector(self) -> typing.Optional[abjad.Expression]:
#        """
#        Gets selector.
#        """
#        return self._selector


class RestCommand(Command):
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

    __slots__ = "_use_multimeasure_rests"

    #    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(
        self,
        selector: abjad.SelectorTyping,
        *,
        use_multimeasure_rests: bool = None,
    ) -> None:
        super().__init__(selector)
        #        if isinstance(selector, str):
        #            selector = eval(selector)
        #            assert isinstance(selector, abjad.Expression)
        #        self._selector = selector
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

    #    def __format__(self, format_specification="") -> str:
    #        """
    #        Formats rest command.
    #        """
    #        return abjad.StorageFormatManager(self).get_storage_format()
    #
    #    def __repr__(self) -> str:
    #        """
    #        Gets interpreter representation of rest command.
    #        """
    #        return abjad.StorageFormatManager(self).get_repr_format()
    #
    #    @property
    #    def selector(self) -> typing.Optional[abjad.Expression]:
    #        """
    #        Gets selector.
    #        """
    #        return self._selector

    ### PUBLIC PROPERTIES ###

    @property
    def use_multimeasure_rests(self) -> typing.Optional[bool]:
        """
        Is true when rest command uses multimeasure rests.
        """
        return self._use_multimeasure_rests


class RewriteMeterCommand(Command):
    """
    Rewrite meter command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_reference_meters", "_repeat_ties")

    #    _publish_storage_format = True

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

    #    def __format__(self, format_specification="") -> str:
    #        """
    #        Formats rewrite meter command.
    #
    #        ..  container:: example
    #
    #            >>> command = abjadext.rmakers.rewrite_meter()
    #            >>> abjad.f(command)
    #            abjadext.commands.RewriteMeterCommand()
    #
    #        """
    #        return abjad.StorageFormatManager(self).get_storage_format()
    #
    #    def __repr__(self) -> str:
    #        """
    #        Gets interpreter representation.
    #
    #        ..  container:: example
    #
    #            >>> abjadext.rmakers.rewrite_meter()
    #            RewriteMeterCommand()
    #
    #        """
    #        return abjad.StorageFormatManager(self).get_repr_format()

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


class SplitMeasuresCommand(Command):
    """
    Split measures command.
    """

    ### CLASS VARIABLES ###

    __slots__ = "_repeat_ties"

    #    _publish_storage_format = True

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

    #    def __format__(self, format_specification="") -> str:
    #        """
    #        Formats command.
    #
    #        ..  container:: example
    #
    #            >>> command = abjadext.rmakers.split_measures()
    #            >>> abjad.f(command)
    #            abjadext.commands.SplitMeasuresCommand()
    #
    #        """
    #        return abjad.StorageFormatManager(self).get_storage_format()
    #
    #    def __repr__(self) -> str:
    #        """
    #        Gets interpreter representation of command.
    #
    #        ..  container:: example
    #
    #            >>> abjadext.rmakers.split_measures()
    #            SplitMeasuresCommand()
    #
    #        """
    #        return abjad.StorageFormatManager(self).get_repr_format()

    #    ### PRIVATE METHODS ###
    #
    #    # TODO: activate tag
    #    def _call(self, music_voice, durations, *, tag=None):
    #        durations = [abjad.Duration(_) for _ in durations]
    #        total_duration = sum(durations)
    #        music_duration = abjad.inspect(music_voice).duration()
    #        if total_duration != music_duration:
    #            message = f"Total duration of splits is {total_duration!s}"
    #            message += f" but duration of music is {music_duration!s}:"
    #            message += f"\ndurations: {durations}."
    #            message += f"\nmusic voice: {music_voice[:]}."
    #            raise Exception(message)
    #        abjad.mutate(music_voice[:]).split(
    #            durations=durations, repeat_ties=self.repeat_ties
    #        )
    #        components = music_voice[:]
    #        component_durations = [abjad.inspect(_).duration() for _ in components]
    #        parts = abjad.sequence(component_durations)
    #        parts = parts.partition_by_weights(
    #            weights=durations, allow_part_weights=abjad.Exact
    #        )
    #        part_lengths = [len(_) for _ in parts]
    #        parts = abjad.sequence(components).partition_by_counts(
    #            counts=part_lengths, overhang=abjad.Exact
    #        )
    #        selections = [abjad.select(_) for _ in parts]
    #        return selections

    ### PUBLIC PROPERTIES ###

    @property
    def repeat_ties(self):
        """
        Is true when command uses repeat ties.
        """
        return self._repeat_ties


class TieCommand(Command):
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

    #    _publish_storage_format = True

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
        super().__init__(selector)
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

    #        if isinstance(selector, str):
    #            selector = eval(selector)
    #            assert isinstance(selector, abjad.Expression)
    #        self._selector = selector

    ### SPECIAL METHODS ###

    def __call__(self, staff, *, tag: str = None) -> None:
        """
        Calls tie command on ``staff``.
        """
        assert isinstance(staff, abjad.Staff), repr(staff)
        self._attach_repeat_ties_(staff)
        self._attach_ties_(staff)
        self._detach_ties_(staff)
        self._detach_repeat_ties_(staff)
        self._configure_repeat_ties(staff)

    #    def __eq__(self, argument) -> bool:
    #        """
    #        Is true when initialization values of tie command equal
    #        initialization values of ``argument``.
    #        """
    #        return abjad.StorageFormatManager.compare_objects(self, argument)
    #
    #    def __format__(self, format_specification="") -> str:
    #        """
    #        Formats tie command.
    #        """
    #        return abjad.StorageFormatManager(self).get_storage_format()
    #
    #    def __hash__(self) -> int:
    #        """
    #        Hashes tie command.
    #        """
    #        hash_values = abjad.StorageFormatManager(self).get_hash_values()
    #        try:
    #            result = hash(hash_values)
    #        except TypeError:
    #            raise TypeError(f"unhashable type: {self}")
    #        return result
    #
    #    def __repr__(self) -> str:
    #        """
    #        Gets interpreter representation of tie command.
    #        """
    #        return abjad.StorageFormatManager(self).get_repr_format()

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
            ...     rmakers.repeat_tie(selector),
            ...     rmakers.beam(abjad.select().tuplets()),
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
            ...     rmakers.repeat_tie(selector),
            ...     rmakers.beam(abjad.select().tuplets()),
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
            ...     rmakers.tie(abjad.select().notes()[5:15]),
            ...     rmakers.beam(abjad.select().tuplets()),
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
            ...     rmakers.tie(selector),
            ...     rmakers.beam(abjad.select().tuplets()),
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
            ...     rmakers.tie(selector),
            ...     rmakers.beam(abjad.select().tuplets()),
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
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
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
            ...     rmakers.untie(selector),
            ...     rmakers.tie(selector),
            ...     rmakers.beam(abjad.select().tuplets()),
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
            ...     rmakers.tie(selector),
            ...     rmakers.beam(abjad.select().tuplets()),
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
        """
        return self._detach_repeat_ties

    @property
    def detach_ties(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker detaches ties.
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


#    @property
#    def selector(self) -> typing.Optional[abjad.Expression]:
#        """
#        Gets selector.
#        """
#        return self._selector


class TupletCommand(Command):
    """
    Tuplet command.

    ..  container:: example

        >>> command = rmakers.TupletCommand()
        >>> abjad.f(command)
        abjadext.commands.TupletCommand()

    """

    ### CLASS VARIABLES ###

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

    #    _publish_storage_format = True

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
        super().__init__(selector)
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
        #        if isinstance(selector, str):
        #            selector = eval(selector)
        #            assert isinstance(selector, abjad.Expression)
        #        self._selector = selector
        if trivialize is not None:
            trivialize = bool(trivialize)
        self._trivialize = trivialize

    ### SPECIAL METHODS ###

    def __call__(self, staff, *, tag: str = None) -> None:
        """
        Calls tuplet command.
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

    #    def __eq__(self, argument) -> bool:
    #        """
    #        Is true when initialization values of tuplet command equal
    #        initialization values of ``argument``.
    #        """
    #        return abjad.StorageFormatManager.compare_objects(self, argument)
    #
    #    def __hash__(self) -> int:
    #        """
    #        Hashes tuplet command.
    #        """
    #        hash_values = abjad.StorageFormatManager(self).get_hash_values()
    #        try:
    #            result = hash(hash_values)
    #        except TypeError:
    #            raise TypeError(f"unhashable type: {self}")
    #        return result
    #
    #    def __format__(self, format_specification="") -> str:
    #        """
    #        Formats tuplet command.
    #        """
    #        return abjad.StorageFormatManager(self).get_storage_format()
    #
    #    def __repr__(self) -> str:
    #        """
    #        Gets interpreter representation.
    #        """
    #        return abjad.StorageFormatManager(self).get_repr_format()

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
        """
        return self._extract_trivial

    @property
    def force_fraction(self) -> typing.Optional[bool]:
        r"""
        Is true when tuplet forces tuplet number fraction formatting.
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
        """
        return self._rewrite_rest_filled

    @property
    def rewrite_sustained(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker rewrites sustained tuplets.
        """
        return self._rewrite_sustained

    #    @property
    #    def selector(self) -> typing.Optional[abjad.Expression]:
    #        """
    #        Gets selector.
    #        """
    #        return self._selector

    @property
    def trivialize(self) -> typing.Optional[bool]:
        """
        Is true when tuplet command trivializes trivializable tuplets.
        """
        return self._trivialize

    ### PUBLIC METHODS ###

    # TODO: move to abjad.Tuplet
    @staticmethod
    def is_rest_filled_tuplet(tuplet):
        """
        Is true when ``argument`` is rest-filled tuplet.
        """
        if not isinstance(tuplet, abjad.Tuplet):
            return False
        return all(isinstance(_, abjad.Rest) for _ in tuplet)

    # TODO: move to abjad.Tuplet
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


class UntieCommand(Command):
    """
    Untie command.
    """

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __call__(self, staff, *, tag: str = None) -> None:
        """
        Calls untie command on ``staff``.
        """
        assert isinstance(staff, abjad.Staff), repr(staff)
        selection = staff["MusicVoice"]
        if self.selector is not None:
            selection = self.selector(selection)
        for leaf in abjad.select(selection).leaves():
            abjad.detach(abjad.TieIndicator, leaf)
            abjad.detach(abjad.RepeatTie, leaf)


### FACTORY FUNCTIONS ###


def beam(
    selector: abjad.SelectorTyping = abjad.select().tuplets(),
    *,
    beam_lone_notes: bool = None,
    beam_rests: bool = None,
    stemlet_length=None,
) -> BeamCommand:
    """
    Makes beam command.
    """
    return BeamCommand(
        selector=selector,
        beam_lone_notes=beam_lone_notes,
        beam_rests=beam_rests,
        stemlet_length=stemlet_length,
    )


def cache_state() -> CacheStateCommand:
    """
    Makes cache state command.
    """
    return CacheStateCommand()


def denominator(
    denominator: typing.Union[int, abjad.DurationTyping],
    *,
    selector: abjad.SelectorTyping = abjad.select().tuplets(),
) -> TupletCommand:
    r"""
    Makes tuplet command.

    ..  container:: example

        Tuplet numerators and denominators are reduced to numbers that are
        relatively prime when ``denominator`` is set to none. This
        means that ratios like ``6:4`` and ``10:8`` do not arise:

        >>> rhythm_maker = rmakers.TupletRhythmMaker(
        ...     rmakers.rewrite_tuplet_dots(),
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.rewrite_tuplet_dots(),
        ...     rmakers.denominator((1, 16)),
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.rewrite_tuplet_dots(),
        ...     rmakers.denominator((1, 32)),
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.rewrite_tuplet_dots(),
        ...     rmakers.denominator((1, 64)),
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.rewrite_tuplet_dots(),
        ...     rmakers.denominator(8),
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.rewrite_tuplet_dots(),
        ...     rmakers.denominator(12),
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.rewrite_tuplet_dots(),
        ...     rmakers.denominator(13),
        ...     rmakers.beam(abjad.select().tuplets()),
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

    """
    return TupletCommand(denominator=denominator, selector=selector)


def extract_trivial(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> TupletCommand:
    r"""
    Makes tuplet command.

    ..  container:: example

        With selector:

        >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
        ...     rmakers.beam(abjad.select().tuplets()),
        ...     rmakers.extract_trivial(abjad.select().tuplets()[-2:]),
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
    return TupletCommand(extract_trivial=True, selector=selector)


def feather_beam(
    selector: abjad.SelectorTyping = abjad.select().tuplets(),
    *,
    beam_rests: bool = None,
    stemlet_length: abjad.Number = None,
) -> BeamCommand:
    """
    Makes tuplet command.
    """
    return BeamCommand(
        selector=selector,
        beam_rests=beam_rests,
        stemlet_length=stemlet_length,
        use_feather_beams=True,
    )


def force_augmentation(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> TupletCommand:
    r"""
    Makes tuplet command.

    ..  container:: example

        The ``default.ily`` stylesheet included in all Abjad API examples
        includes the following:
        
        ``\override TupletNumber.text = #tuplet-number::calc-fraction-text``

        This means that even simple tuplets format as explicit fractions:

        >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.force_fraction(),
        ...     rmakers.beam(abjad.select().tuplets()),
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
    return TupletCommand(diminution=False, selector=selector)


def force_diminution(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> TupletCommand:
    """
    Makes tuplet command.
    """
    return TupletCommand(diminution=True, selector=selector)


def force_fraction(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> TupletCommand:
    """
    Makes tuplet command.
    """
    return TupletCommand(force_fraction=True, selector=selector)


def note(selector: abjad.SelectorTyping,) -> NoteCommand:
    """
    Makes rest command.
    """
    return NoteCommand(selector)


def repeat_tie(selector: abjad.SelectorTyping = None) -> TieCommand:
    """
    Makes tie command.
    """
    return TieCommand(attach_repeat_ties=True, selector=selector)


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


def rewrite_rest_filled(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> TupletCommand:
    r"""
    Makes tuplet command.

    ..  container:: example

        Does not rewrite rest-filled tuplets:

        >>> rhythm_maker = rmakers.TaleaRhythmMaker(
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.rewrite_rest_filled(
        ...         abjad.select().tuplets()[-2:],
        ...         ),
        ...     rmakers.beam(abjad.select().tuplets()),
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
    return TupletCommand(rewrite_rest_filled=True, selector=selector)


def rewrite_sustained(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> TupletCommand:
    r"""
    Makes tuplet command.

    ..  container:: example

        Sustained tuplets generalize a class of rhythms composers are
        likely to rewrite:

        >>> last_leaf = abjad.select().leaf(-1)
        >>> rhythm_maker = rmakers.TaleaRhythmMaker(
        ...     rmakers.tie(abjad.select().tuplets()[1:3].map(last_leaf)),
        ...     rmakers.beam(abjad.select().tuplets()),
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
            ...     rmakers.TupletCommand.is_sustained_tuplet(tuplet)
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
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.tie(abjad.select().tuplets()[1:3].map(last_leaf)),
        ...     rmakers.beam(abjad.select().tuplets()),
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
        ...     rmakers.beam(abjad.select().tuplets()),
        ...     rmakers.tie(abjad.select().tuplets()[1:3].map(last_leaf)),
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.extract_trivial(),
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
        ...     rmakers.tie(selector),
        ...     rmakers.rewrite_sustained(
        ...         abjad.select().tuplets()[-2:],
        ...     ),
        ...     rmakers.beam(abjad.select().tuplets()),
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
    return TupletCommand(rewrite_sustained=True, selector=selector)


def rewrite_tuplet_dots(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> TupletCommand:
    """
    Makes tuplet command.
    """
    return TupletCommand(rewrite_dots=True, selector=selector)


def duration_bracket(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> TupletCommand:
    """
    Makes tuplet command.
    """
    return TupletCommand(selector=selector, duration_bracket=True)


def split_measures(*, repeat_ties=None) -> SplitMeasuresCommand:
    """
    Makes split measures command.
    """
    return SplitMeasuresCommand(repeat_ties=repeat_ties)


def tie(selector: abjad.SelectorTyping = None) -> TieCommand:
    """
    Makes tie command.
    """
    return TieCommand(attach_ties=True, selector=selector)


def to_repeat_tie(
    threshold=True, selector: abjad.SelectorTyping = None
) -> TieCommand:
    """
    Makes tie command.
    """
    return TieCommand(repeat_ties=threshold, selector=selector)


def trivialize(
    selector: abjad.SelectorTyping = abjad.select().tuplets()
) -> TupletCommand:
    """
    Makes tuplet command.
    """
    return TupletCommand(selector=selector, trivialize=True)


def untie(selector: abjad.SelectorTyping = None) -> UntieCommand:
    r"""
    Makes untie command.

    ..  container:: example

        Attaches ties to nonlast notes; then detaches ties from select
        notes:

        >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
        ...     rmakers.tie(abjad.select().notes()[:-1]),
        ...     rmakers.untie(abjad.select().notes().get([0], 4)),
        ...     rmakers.beam(abjad.select().tuplets()),
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

    ..  container:: example

        Attaches repeat-ties to nonfirst notes; then detaches ties from
        select notes:

        >>> rhythm_maker = rmakers.EvenDivisionRhythmMaker(
        ...     rmakers.repeat_tie(abjad.select().notes()[1:]),
        ...     rmakers.untie(abjad.select().notes().get([0], 4)),
        ...     rmakers.beam(abjad.select().tuplets()),
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
    return UntieCommand(selector=selector)
