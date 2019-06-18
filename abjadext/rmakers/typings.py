import typing
from .BeamSpecifier import BeamSpecifier
from .RewriteMeterCommand import RewriteMeterCommand
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier


MaskTyping = typing.Union[SilenceMask, SustainMask]

MasksTyping = typing.Union[MaskTyping, typing.Sequence[MaskTyping]]

SpecifierTyping = typing.Union[
    BeamSpecifier,
    RewriteMeterCommand,
    SilenceMask,
    SustainMask,
    TieSpecifier,
    TupletSpecifier,
]
