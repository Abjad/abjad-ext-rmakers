"""
Helpers.
"""
import abjad


def example(selection, time_signatures=None, *, includes=None):
    """
    Makes example LilyPond file.
    """
    lilypond_file = abjad.illustrators.selection(
        selection,
        time_signatures,
    )
    includes = [rf'\include "{_}"' for _ in includes or []]
    lilypond_file.items[0:0] = includes
    staff = lilypond_file["Staff"]
    staff.lilypond_type = "RhythmicStaff"
    abjad.override(staff).Clef.stencil = False
    return lilypond_file
