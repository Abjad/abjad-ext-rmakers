import typing
from .BeamSpecifier import BeamSpecifier
from .CacheState import CacheState
from .RewriteMeterCommand import RewriteMeterCommand
from .SplitCommand import SplitCommand
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier
from .commands import SilenceMask
from .commands import SustainMask


MaskTyping = typing.Union[SilenceMask, SustainMask]

MasksTyping = typing.Union[MaskTyping, typing.Sequence[MaskTyping]]

SpecifierTyping = typing.Union[
    BeamSpecifier,
    CacheState,
    RewriteMeterCommand,
    SilenceMask,
    SplitCommand,
    SustainMask,
    TieSpecifier,
    TupletSpecifier,
]
