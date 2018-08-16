import abjad
import typing
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask


IntegerPair = typing.Tuple[int, int]

DurationTyping = typing.Union[IntegerPair, abjad.Duration]

Mask = typing.Union[SilenceMask, SustainMask]

MaskKeyword = typing.Union[Mask, typing.Sequence[Mask]]
