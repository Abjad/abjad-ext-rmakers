import abjad
import typing


class SplitCommand(object):
    """
    Split mesures command.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    __slots__ = "_repeat_ties"

    _publish_storage_format = True

    ### INITIALIZER ###

    def __init__(self, *, repeat_ties=None) -> None:
        self._repeat_ties = repeat_ties

    ### SPECIAL METHODS ###

    def __call__(
        self,
        selections: typing.Sequence[abjad.Selection],
        durations: typing.Sequence[abjad.DurationTyping],
        *,
        tag: str = None,
    ) -> typing.List[abjad.Selection]:
        """
        Calls split command.
        """
        selections = self._call(
            selections=selections, durations=durations, tag=tag
        )
        return list(selections)

    def __format__(self, format_specification="") -> str:
        """
        Formats command.

        ..  container:: example

            >>> specifier = abjadext.rmakers.SplitCommand()
            >>> abjad.f(specifier)
            abjadext.rmakers.SplitCommand()

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of command.

        ..  container:: example

            >>> abjadext.rmakers.SplitCommand()
            SplitCommand()

        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    # TODO: activate tag
    def _call(self, selections, durations, *, tag=None):
        durations = [abjad.Duration(_) for _ in durations]
        selections = abjad.sequence(selections).flatten(depth=-1)
        total_duration = sum(durations)
        selection_duration = sum(
            abjad.inspect(_).duration() for _ in selections
        )
        if total_duration != selection_duration:
            message = f"Total duration of splits is {total_duration!s}"
            message += (
                f" but duration of selections is {selection_duration!s}:"
            )
            message += f"\ndurations: {durations}."
            message += f"\nselections: {selections}."
            raise Exception(message)
        voice = abjad.Voice(selections)
        abjad.mutate(voice[:]).split(
            durations=durations,
            tie_split_notes=True,
            repeat_ties=self.repeat_ties,
        )
        components = abjad.mutate(voice).eject_contents()
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
