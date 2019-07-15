import typing
from .TupletCommand import TupletCommand
from .commands import BeamCommand
from .commands import CacheStateCommand
from .commands import NoteCommand
from .commands import RestCommand
from .commands import RewriteMeterCommand
from .commands import SplitMeasuresCommand
from .commands import TieCommand


MaskTyping = typing.Union[RestCommand, NoteCommand]

MasksTyping = typing.Union[MaskTyping, typing.Sequence[MaskTyping]]

SpecifierTyping = typing.Union[
    BeamCommand,
    CacheStateCommand,
    RewriteMeterCommand,
    RestCommand,
    SplitMeasuresCommand,
    NoteCommand,
    TieCommand,
    TupletCommand,
]
