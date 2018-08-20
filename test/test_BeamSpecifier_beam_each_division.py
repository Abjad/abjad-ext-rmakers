import abjad
from abjadext import rmakers


def test_BeamSpecifier_beam_each_division_01():
    """
    Beam each cell with a multipart beam spanner.
    """

    talea = rmakers.Talea(
        counts=[1, 1, 1, -1, 2, 2],
        denominator=32,
        )

    rhythm_maker = rmakers.TaleaRhythmMaker(
        talea=talea,
        extra_counts_per_division=[3, 4],
        )

    divisions = [(2, 16), (5, 16)]
    selections = rhythm_maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(
        selections,
        divisions,
        )

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 2/16
                s1 * 1/8
                \time 5/16
                s1 * 5/16
            }
            \new RhythmicStaff
            {
                \times 4/7 {
                    c'32
                    [
                    c'32
                    c'32
                    ]
                    r32
                    c'16
                    [
                    c'32
                    ~
                    ]
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 5/7 {
                    c'32
                    [
                    c'32
                    c'32
                    c'32
                    ]
                    r32
                    c'16
                    [
                    c'16
                    c'32
                    c'32
                    c'32
                    ]
                    r32
                    c'32
                }
            }
        >>
        """
        ), print(format(score))
