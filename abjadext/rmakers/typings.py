import typing
from .BeamSpecifier import BeamSpecifier
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier


MaskTyping = typing.Union[SilenceMask, SustainMask]

MasksTyping = typing.Union[MaskTyping, typing.Sequence[MaskTyping]]

SpecifierTyping = typing.Union[
    BeamSpecifier, SilenceMask, SustainMask, TieSpecifier, TupletSpecifier
]
