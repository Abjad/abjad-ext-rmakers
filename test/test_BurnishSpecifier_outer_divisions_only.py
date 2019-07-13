import abjad
import pytest
import sys
from abjadext import rmakers


def test_BurnishSpecifier_outer_divisions_only_01():

    burnish_specifier = rmakers.BurnishSpecifier(
        left_classes=[0],
        middle_classes=[-1],
        right_classes=[0],
        left_counts=[1],
        right_counts=[1],
        outer_divisions_only=True,
    )

    talea = rmakers.Talea(counts=[1], denominator=16)

    rhythm_maker = rmakers.TaleaRhythmMaker(
        talea=talea,
        burnish_specifier=burnish_specifier,
        extra_counts_per_division=[2],
    )

    divisions = [(3, 16), (3, 8)]
    selections = rhythm_maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 3/16
                s1 * 3/16
                \time 3/8
                s1 * 3/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 3/5 {
                    c'16
                    r16
                    r16
                    r16
                    r16
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 3/4 {
                    r16
                    r16
                    r16
                    r16
                    r16
                    r16
                    r16
                    c'16
                }
            }
        >>
        """
    ), print(format(score))


def test_BurnishSpecifier_outer_divisions_only_02():

    burnish_specifier = rmakers.BurnishSpecifier(
        left_classes=[-1],
        right_classes=[-1],
        left_counts=[1],
        right_counts=[1],
        outer_divisions_only=True,
    )

    talea = rmakers.Talea(counts=[1], denominator=4)

    rhythm_maker = rmakers.TaleaRhythmMaker(
        talea=talea,
        burnish_specifier=burnish_specifier,
        extra_counts_per_division=[2],
    )

    divisions = [(3, 16), (3, 8)]
    selections = rhythm_maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 3/16
                s1 * 3/16
                \time 3/8
                s1 * 3/8
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 3/5 {
                    r4
                    c'16
                    ~
                }
                \tweak text #tuplet-number::calc-fraction-text
                \times 3/4 {
                    c'8.
                    c'4
                    r16
                }
            }
        >>
        """
    ), print(format(score))


def test_BurnishSpecifier_outer_divisions_only_03():

    burnish_specifier = rmakers.BurnishSpecifier(
        left_classes=[-1],
        right_classes=[-1],
        left_counts=[1],
        right_counts=[2],
        outer_divisions_only=True,
    )

    talea = rmakers.Talea(counts=[1], denominator=8)

    rhythm_maker = rmakers.TaleaRhythmMaker(
        rmakers.BeamSpecifier(selector=abjad.select().tuplets()),
        talea=talea,
        burnish_specifier=burnish_specifier,
        extra_counts_per_division=[],
    )

    divisions = [(8, 8)]
    selections = rhythm_maker(divisions)
    lilypond_file = abjad.LilyPondFile.rhythm(selections, divisions)

    score = lilypond_file[abjad.Score]
    assert format(score) == abjad.String.normalize(
        r"""
        \new Score
        <<
            \new GlobalContext
            {
                \time 8/8
                s1 * 1
            }
            \new RhythmicStaff
            {
                \tweak text #tuplet-number::calc-fraction-text
                \times 1/1 {
                    r8
                    c'8
                    [
                    c'8
                    c'8
                    c'8
                    c'8
                    ]
                    r8
                    r8
                }
            }
        >>
        """
    ), print(format(score))
