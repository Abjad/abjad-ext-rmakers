import abjad
from abjadext import rmakers


def test_Burnish_01():

    burnish_specifier = rmakers.Burnish(
        left_classes=[abjad.Rest],
        right_classes=[abjad.Rest],
        left_counts=[2],
        right_counts=[1],
    )

    talea = rmakers.Talea(counts=[1, 1, 2, 4], denominator=32)

    rhythm_maker = rmakers.TaleaRhythmMaker(
        rmakers.beam(),
        talea=talea,
        burnish_specifier=burnish_specifier,
        extra_counts_per_division=[0],
    )

    divisions = [(5, 16), (6, 16)]
    selections = rhythm_maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/16
                s1 * 5/16
                \time 6/16
                s1 * 3/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r32
                    r32
                    c'16
                    [
                    c'8
                    c'32
                    ]
                    r32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r16
                    r8
                    c'32
                    [
                    c'32
                    c'16
                    ]
                    r16
                }
            }
        >>
        """
    ), print(format(score))


def test_Burnish_02():

    burnish_specifier = rmakers.Burnish(
        left_classes=[0],
        middle_classes=[abjad.Rest],
        right_classes=[0],
        left_counts=[2],
        right_counts=[1],
    )

    talea = rmakers.Talea(counts=[1, 1, 2, 4], denominator=32)

    rhythm_maker = rmakers.TaleaRhythmMaker(
        rmakers.beam(),
        talea=talea,
        extra_counts_per_division=[0],
        burnish_specifier=burnish_specifier,
    )

    divisions = [(5, 16), (6, 16)]
    selections = rhythm_maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/16
                s1 * 5/16
                \time 6/16
                s1 * 3/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'32
                    [
                    c'32
                    ]
                    r16
                    r8
                    r32
                    c'32
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    c'16
                    [
                    c'8
                    ]
                    r32
                    r32
                    r16
                    c'16
                }
            }
        >>
        """
    ), print(format(score))


def test_Burnish_03():

    burnish_specifier = rmakers.Burnish(
        left_classes=[0],
        middle_classes=[abjad.Rest],
        right_classes=[0],
        left_counts=[2],
        right_counts=[1],
    )

    talea = rmakers.Talea(counts=[1, 1, 2, 4], denominator=32)

    rhythm_maker = rmakers.TaleaRhythmMaker(
        rmakers.beam(),
        talea=talea,
        extra_counts_per_division=[3],
        burnish_specifier=burnish_specifier,
    )

    divisions = [(5, 16), (6, 16)]
    selections = rhythm_maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/16
                s1 * 5/16
                \time 6/16
                s1 * 3/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 10/13 {
                    c'32
                    [
                    c'32
                    ]
                    r16
                    r8
                    r32
                    r32
                    r16
                    c'32
                    ~
                }
                \times 4/5 {
                    c'16.
                    [
                    c'32
                    ]
                    r32
                    r16
                    r8
                    r32
                    r32
                    c'16
                }
            }
        >>
        """
    ), print(format(score))


def test_Burnish_04():

    burnish_specifier = rmakers.Burnish(
        left_classes=[abjad.Rest],
        right_classes=[abjad.Rest],
        left_counts=[1],
        right_counts=[1],
    )

    talea = rmakers.Talea(counts=[1, 1, 2, 4], denominator=32)

    rhythm_maker = rmakers.TaleaRhythmMaker(
        rmakers.beam(),
        talea=talea,
        extra_counts_per_division=[0, 3],
        burnish_specifier=burnish_specifier,
    )

    divisions = [(5, 16), (6, 16)]
    selections = rhythm_maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 5/16
                s1 * 5/16
                \time 6/16
                s1 * 3/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r32
                    c'32
                    [
                    c'16
                    c'8
                    c'32
                    ]
                    r32
                }
                \times 4/5 {
                    r16
                    c'8
                    [
                    c'32
                    c'32
                    c'16
                    c'8
                    ]
                    r32
                }
            }
        >>
        """
    ), print(format(score))
