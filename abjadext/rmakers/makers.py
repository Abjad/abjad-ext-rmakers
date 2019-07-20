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
    preprocessor: abjad.Expression = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> AccelerandoRhythmMaker:
    """
    Makes accelerando rhythm-maker.
    """
    return AccelerandoRhythmMaker(
        *commands,
        preprocessor=preprocessor,
        interpolations=interpolations,
        spelling=spelling,
        tag=tag,
    )


def even_division(
    *commands: _commands.Command,
    denominator: typing.Union[str, int] = "from_counts",
    denominators: typing.Sequence[int] = [8],
    extra_counts: typing.Sequence[int] = None,
    preprocessor: abjad.Expression = None,
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
        preprocessor=preprocessor,
        extra_counts=extra_counts,
        spelling=spelling,
        tag=tag,
    )


def incised(
    *commands: _commands.Command,
    extra_counts: typing.Sequence[int] = None,
    incise: _specifiers.Incise = None,
    preprocessor: abjad.Expression = None,
    replace_rests_with_skips: bool = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> IncisedRhythmMaker:
    """
    Makes incised rhythm-maker
    """
    return IncisedRhythmMaker(
        *commands,
        preprocessor=preprocessor,
        extra_counts=extra_counts,
        incise=incise,
        replace_rests_with_skips=replace_rests_with_skips,
        spelling=spelling,
        tag=tag,
    )


def note(preprocessor: abjad.Expression = None,) -> NoteRhythmMaker:
    """
    Makes note rhythm-maker.
    """
    return NoteRhythmMaker()


def talea(
    *commands: _commands.Command,
    curtail_ties: bool = None,
    extra_counts: abjad.IntegerSequence = None,
    preprocessor: abjad.Expression = None,
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
        preprocessor=preprocessor,
        extra_counts=extra_counts,
        read_talea_once_only=read_talea_once_only,
        spelling=spelling,
        tag=tag,
        talea=talea,
    )


def tuplet(
    *commands: _commands.Command,
    denominator: typing.Union[int, abjad.DurationTyping] = None,
    preprocessor: abjad.Expression = None,
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
        preprocessor=preprocessor,
        spelling=spelling,
        tag=tag,
        tuplet_ratios=tuplet_ratios,
    )
