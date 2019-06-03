import typing
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask


MaskTyping = typing.Union[SilenceMask, SustainMask]

MasksTyping = typing.Union[MaskTyping, typing.Sequence[MaskTyping]]
