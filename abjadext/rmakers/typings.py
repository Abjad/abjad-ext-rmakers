import typing
from .BeamSpecifier import BeamSpecifier
from .CacheState import CacheState
from .RewriteMeterCommand import RewriteMeterCommand
from .SplitCommand import SplitCommand
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier
from .commands import RestCommand
from .commands import NoteCommand


MaskTyping = typing.Union[RestCommand, NoteCommand]

MasksTyping = typing.Union[MaskTyping, typing.Sequence[MaskTyping]]

SpecifierTyping = typing.Union[
    BeamSpecifier,
    CacheState,
    RewriteMeterCommand,
    RestCommand,
    SplitCommand,
    NoteCommand,
    TieSpecifier,
    TupletSpecifier,
]
