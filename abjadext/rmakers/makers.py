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
    *interpolations, spelling: _specifiers.Spelling = None, tag: str = None
) -> AccelerandoRhythmMaker:
    """
    Makes accelerando rhythm-maker.
    """
    interpolations_ = []
    for interpolation in interpolations:
        interpolation_ = _specifiers.Interpolation(*interpolation)
        interpolations_.append(interpolation_)
    return AccelerandoRhythmMaker(
        interpolations=interpolations_, spelling=spelling, tag=tag
    )


def even_division(
    denominators: typing.Sequence[int],
    *,
    denominator: typing.Union[str, int] = "from_counts",
    extra_counts: typing.Sequence[int] = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> EvenDivisionRhythmMaker:
    """
    Makes even-division rhythm-maker.
    """
    return EvenDivisionRhythmMaker(
        denominator=denominator,
        denominators=denominators,
        extra_counts=extra_counts,
        spelling=spelling,
        tag=tag,
    )


def incised(
    extra_counts: typing.Sequence[int] = None,
    body_ratio: abjad.RatioTyping = None,
    fill_with_rests: bool = None,
    outer_divisions_only: bool = None,
    prefix_talea: typing.Sequence[int] = None,
    prefix_counts: typing.Sequence[int] = None,
    suffix_talea: typing.Sequence[int] = None,
    suffix_counts: typing.Sequence[int] = None,
    talea_denominator: int = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> IncisedRhythmMaker:
    """
    Makes incised rhythm-maker
    """
    return IncisedRhythmMaker(
        extra_counts=extra_counts,
        incise=_specifiers.Incise(
            body_ratio=body_ratio,
            fill_with_rests=fill_with_rests,
            outer_divisions_only=outer_divisions_only,
            prefix_talea=prefix_talea,
            prefix_counts=prefix_counts,
            suffix_talea=suffix_talea,
            suffix_counts=suffix_counts,
            talea_denominator=talea_denominator,
        ),
        spelling=spelling,
        tag=tag,
    )


def note(
    spelling: _specifiers.Spelling = None, tag: str = None
) -> NoteRhythmMaker:
    """
    Makes note rhythm-maker.
    """
    return NoteRhythmMaker(spelling=spelling, tag=tag)


def talea(
    counts,
    denominator,
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
    tuplet_ratios: abjad.RatioSequenceTyping,
    # TODO: remove in favor of dedicated denominator control commands:
    denominator: typing.Union[int, abjad.DurationTyping] = None,
    spelling: _specifiers.Spelling = None,
    tag: str = None,
) -> TupletRhythmMaker:
    """
    Makes tuplet rhythm-maker.
    """
    return TupletRhythmMaker(
        denominator=denominator,
        spelling=spelling,
        tag=tag,
        tuplet_ratios=tuplet_ratios,
    )
