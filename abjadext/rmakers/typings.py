import typing
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask


Mask = typing.Union[SilenceMask, SustainMask]
