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
