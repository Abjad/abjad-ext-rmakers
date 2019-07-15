import typing
from .BeamSpecifier import BeamSpecifier
from .CacheState import CacheState
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier
from .commands import NoteCommand
from .commands import RestCommand
from .commands import RewriteMeterCommand
from .commands import SplitCommand


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
