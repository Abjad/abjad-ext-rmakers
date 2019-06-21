import typing
from .BeamSpecifier import BeamSpecifier
from .CacheState import CacheState
from .RewriteMeterCommand import RewriteMeterCommand
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier


MaskTyping = typing.Union[SilenceMask, SustainMask]

MasksTyping = typing.Union[MaskTyping, typing.Sequence[MaskTyping]]

SpecifierTyping = typing.Union[
    BeamSpecifier,
    CacheState,
    RewriteMeterCommand,
    SilenceMask,
    SustainMask,
    TieSpecifier,
    TupletSpecifier,
]
