import abjad
import typing
from . import commands as _commands
from . import specifiers as _specifiers
from .AccelerandoRhythmMaker import AccelerandoRhythmMaker
from .EvenDivisionRhythmMaker import EvenDivisionRhythmMaker
from .IncisedRhythmMaker import IncisedRhythmMaker
from .NoteRhythmMaker import NoteRhythmMaker
from .TaleaRhythmMaker import TaleaRhythmMaker
from .TupletRhythmMaker import TupletRhythmMaker


### FACTORY FUNCTIONS ###


def accelerando(
    *commands: _commands.Command,
    divisions: abjad.Expression = None,
    interpolations: typing.Union[
        _specifiers.Interpolation, typing.Sequence[_specifiers.Interpolation]
    ] = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> AccelerandoRhythmMaker:
    """
    Makes accelerando rhythm-maker.
    """
    return AccelerandoRhythmMaker(
        *commands,
        divisions=divisions,
        interpolations=interpolations,
        spelling=spelling,
        tag=tag,
    )


def even_division(
    *commands: _commands.Command,
    denominator: typing.Union[str, int] = "from_counts",
    denominators: typing.Sequence[int] = [8],
    divisions: abjad.Expression = None,
    extra_counts_per_division: typing.Sequence[int] = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> EvenDivisionRhythmMaker:
    """
    Makes even-division rhythm-maker.
    """
    return EvenDivisionRhythmMaker(
        *commands,
        denominator=denominator,
        denominators=denominators,
        divisions=divisions,
        extra_counts_per_division=extra_counts_per_division,
        spelling=spelling,
        tag=tag,
    )


def incised(
    *commands: _commands.Command,
    divisions: abjad.Expression = None,
    extra_counts_per_division: typing.Sequence[int] = None,
    incise: _specifiers.Incise = None,
    replace_rests_with_skips: bool = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> IncisedRhythmMaker:
    """
    Makes incised rhythm-maker
    """
    return IncisedRhythmMaker(
        *commands,
        divisions=divisions,
        extra_counts_per_division=extra_counts_per_division,
        incise=incise,
        replace_rests_with_skips=replace_rests_with_skips,
        spelling=spelling,
        tag=tag,
    )


def note() -> NoteRhythmMaker:
    """
    Makes note rhythm-maker.
    """
    return NoteRhythmMaker()


def talea(
    *commands: _commands.Command,
    curtail_ties: bool = None,
    divisions: abjad.Expression = None,
    extra_counts_per_division: abjad.IntegerSequence = None,
    read_talea_once_only: bool = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
    talea: _specifiers.Talea = _specifiers.Talea(counts=[1], denominator=16),
) -> TaleaRhythmMaker:
    """
    Makes talea rhythm-maker.
    """
    return TaleaRhythmMaker(
        *commands,
        curtail_ties=curtail_ties,
        divisions=divisions,
        extra_counts_per_division=extra_counts_per_division,
        read_talea_once_only=read_talea_once_only,
        spelling=spelling,
        tag=tag,
        talea=talea,
    )


def tuplet(
    *commands: _commands.Command,
    denominator: typing.Union[int, abjad.DurationTyping] = None,
    divisions: abjad.Expression = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
    tuplet_ratios: abjad.RatioSequenceTyping = None,
) -> TupletRhythmMaker:
    """
    Makes tuplet rhythm-maker.
    """
    return TupletRhythmMaker(
        *commands,
        denominator=denominator,
        divisions=divisions,
        spelling=spelling,
        tag=tag,
        tuplet_ratios=tuplet_ratios,
    )
