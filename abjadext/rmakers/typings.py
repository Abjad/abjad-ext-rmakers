import typing
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask


IntegerPair = typing.Tuple[int, int]

Mask = typing.Union[SilenceMask, SustainMask]
