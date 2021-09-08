"""
Helpers.
"""
import abjad


def example(selection, time_signatures=None):
    """
    Makes example LilyPond file.
    """
    lilypond_file = abjad.illustrators.selection(selection, time_signatures)
    staff = lilypond_file[abjad.Score][0]
    staff.lilypond_type = "RhythmicStaff"
    abjad.override(staff).Clef.stencil = False
    return lilypond_file
