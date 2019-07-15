import typing
from .BeamCommand import BeamCommand
from .TieCommand import TieCommand
from .TupletSpecifier import TupletSpecifier
from .commands import CacheStateCommand
from .commands import NoteCommand
from .commands import RestCommand
from .commands import RewriteMeterCommand
from .commands import SplitCommand


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
