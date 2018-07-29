"""
Tools for making rhythm.
"""
from .RhythmMaker import RhythmMaker
from .AccelerandoRhythmMaker import AccelerandoRhythmMaker
from .BeamSpecifier import BeamSpecifier
from .BurnishSpecifier import BurnishSpecifier
from .DurationSpecifier import DurationSpecifier
from .EvenDivisionRhythmMaker import EvenDivisionRhythmMaker
from .InciseSpecifier import InciseSpecifier
from .IncisedRhythmMaker import IncisedRhythmMaker
from .InterpolationSpecifier import InterpolationSpecifier
from .NoteRhythmMaker import NoteRhythmMaker
from .SilenceMask import SilenceMask
from .SustainMask import SustainMask
from .Talea import Talea
from .TaleaRhythmMaker import TaleaRhythmMaker
from .TieSpecifier import TieSpecifier
from .TupletRhythmMaker import TupletRhythmMaker
from .TupletSpecifier import TupletSpecifier
from .typings import *

silence = SilenceMask.silence
sustain = SustainMask.sustain
