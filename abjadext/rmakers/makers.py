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
        *commands, interpolations=interpolations, spelling=spelling, tag=tag
    )


def even_division(
    *commands: _commands.Command,
    denominator: typing.Union[str, int] = "from_counts",
    denominators: typing.Sequence[int] = [8],
    extra_counts: typing.Sequence[int] = None,
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
        extra_counts=extra_counts,
        spelling=spelling,
        tag=tag,
    )


def incised(
    *commands: _commands.Command,
    extra_counts: typing.Sequence[int] = None,
    incise: _specifiers.Incise = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> IncisedRhythmMaker:
    """
    Makes incised rhythm-maker
    """
    return IncisedRhythmMaker(
        *commands,
        extra_counts=extra_counts,
        incise=incise,
        spelling=spelling,
        tag=tag,
    )


def note(
    *commands: _commands.Command,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> NoteRhythmMaker:
    """
    Makes note rhythm-maker.
    """
    return NoteRhythmMaker(*commands, spelling=spelling, tag=tag)


def talea(
    counts,
    denominator,
    *commands: _commands.Command,
    end_counts: abjad.IntegerSequence = None,
    extra_counts: abjad.IntegerSequence = None,
    preamble=None,
    read_talea_once_only: bool = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> TaleaRhythmMaker:
    """
    Makes talea rhythm-maker.
    """
    return TaleaRhythmMaker(
        *commands,
        extra_counts=extra_counts,
        read_talea_once_only=read_talea_once_only,
        spelling=spelling,
        tag=tag,
        talea=_specifiers.Talea(
            counts=counts,
            denominator=denominator,
            end_counts=end_counts,
            preamble=preamble,
        ),
    )


def tuplet(
    *commands: _commands.Command,
    denominator: typing.Union[int, abjad.DurationTyping] = None,
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
        spelling=spelling,
        tag=tag,
        tuplet_ratios=tuplet_ratios,
    )
