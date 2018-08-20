import abjad
from abjadext import rmakers


def test_TaleaRhythmMaker_tie_split_notes_01():

    talea = rmakers.Talea(
        counts=[5],
        denominator=16,
        )
    rhythm_maker = rmakers.TaleaRhythmMaker(
        talea=talea,
        )

    divisions = [(2, 8), (2, 8), (2, 8), (2, 8)]
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
                \time 2/8
                s1 * 1/4
                \time 2/8
                s1 * 1/4
                \time 2/8
                s1 * 1/4
                \time 2/8
                s1 * 1/4
            }
            \new RhythmicStaff
            {
                c'4
                ~
                c'16
                [
                c'8.
                ~
                ]
                c'8
                [
                c'8
                ~
                ]
                c'8.
                [
                c'16
                ]
            }
        >>
        """
        ), print(format(score))

    assert abjad.inspect(score).is_wellformed()


def test_TaleaRhythmMaker_tie_split_notes_02():

    talea = rmakers.Talea(
        counts=[5],
        denominator=16,
        )
    rhythm_maker = rmakers.TaleaRhythmMaker(
        talea=talea,
        )

    divisions = [(3, 16), (5, 8), (4, 8), (7, 16)]
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
                \time 3/16
                s1 * 3/16
                \time 5/8
                s1 * 5/8
                \time 4/8
                s1 * 1/2
                \time 7/16
                s1 * 7/16
            }
            \new RhythmicStaff
            {
                c'8.
                ~
                c'8
                c'4
                ~
                c'16
                [
                c'8.
                ~
                ]
                c'8
                c'4
                ~
                c'16
                [
                c'16
                ~
                ]
                c'4
                c'8.
            }
        >>
        """
        ), print(format(score))

    assert abjad.inspect(score).is_wellformed()
