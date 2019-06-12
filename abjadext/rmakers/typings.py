import typing
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask
from .TupletSpecifier import TupletSpecifier


MaskTyping = typing.Union[SilenceMask, SustainMask]

MasksTyping = typing.Union[MaskTyping, typing.Sequence[MaskTyping]]

SpecifierTyping = typing.Union[SilenceMask, SustainMask, TupletSpecifier]
