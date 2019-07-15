import typing
from .TupletSpecifier import TupletSpecifier
from .commands import BeamCommand
from .commands import CacheStateCommand
from .commands import NoteCommand
from .commands import RestCommand
from .commands import RewriteMeterCommand
from .commands import SplitCommand
from .commands import TieCommand


MaskTyping = typing.Union[RestCommand, NoteCommand]

MasksTyping = typing.Union[MaskTyping, typing.Sequence[MaskTyping]]

SpecifierTyping = typing.Union[
    BeamCommand,
    CacheStateCommand,
    RewriteMeterCommand,
    RestCommand,
    SplitCommand,
    NoteCommand,
    TieCommand,
    TupletSpecifier,
]
