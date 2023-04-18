import abjad
from abjadext import rmakers


def test_01():
    """
    Tags work with rmakers.incised().
    """

    def make_rhythm(durations):
        tag = abjad.Tag("INCISED_RHYTHM_MAKER")
        tuplets = rmakers.incised(
            durations,
            extra_counts=[1],
            outer_tuplets_only=True,
            prefix_talea=[-1],
            prefix_counts=[1],
            suffix_talea=[-1],
            suffix_counts=[1],
            talea_denominator=8,
            tag=tag,
        )
        container = abjad.Container(tuplets)
        rmakers.force_augmentation(container)
        rmakers.beam(container, tag=tag)
        music = abjad.mutate.eject_contents(container)
        return music

    time_signatures = rmakers.time_signatures([(8, 8), (4, 8), (6, 8)])
    durations = [abjad.Duration(_) for _ in time_signatures]
    music = make_rhythm(durations)
    lilypond_file = rmakers.example(music, time_signatures)
    score = lilypond_file["Score"]
    string = abjad.lilypond(score, tags=True)

    assert string == abjad.string.normalize(
        r"""
        \context Score = "Score"
        <<
            \context RhythmicStaff = "Staff"
            \with
            {
                \override Clef.stencil = ##f
            }
            {
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                \tweak text #tuplet-number::calc-fraction-text
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                \times 16/9
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                {
                    \time 8/8
                      %! INCISED_RHYTHM_MAKER
                      %! rmakers.incised()
                    r16
                      %! INCISED_RHYTHM_MAKER
                      %! rmakers.incised()
                    c'2
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                }
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                \tweak text #tuplet-number::calc-fraction-text
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                \times 8/5
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                {
                    \time 4/8
                      %! INCISED_RHYTHM_MAKER
                      %! rmakers.incised()
                    c'4
                    ~
                      %! INCISED_RHYTHM_MAKER
                      %! rmakers.incised()
                    c'16
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                }
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                \tweak text #tuplet-number::calc-fraction-text
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                \times 12/7
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                {
                    \time 6/8
                      %! INCISED_RHYTHM_MAKER
                      %! rmakers.incised()
                    c'4.
                      %! INCISED_RHYTHM_MAKER
                      %! rmakers.incised()
                    r16
                  %! INCISED_RHYTHM_MAKER
                  %! rmakers.incised()
                }
            }
        >>
        """
    )


def test_tags_02():
    """
    Tags work with rmakers.talea().
    """

    def make_lilypond_file(pairs):
        time_signatures = rmakers.time_signatures(pairs)
        durations = [abjad.Duration(_) for _ in time_signatures]
        tag = abjad.Tag("TALEA_RHYTHM_MAKER")
        tuplets = rmakers.talea(
            durations, [1, 2, 3, 4], 16, extra_counts=[0, 1], tag=tag
        )
        container = abjad.Container(tuplets)
        rmakers.beam(container, tag=tag)
        components = abjad.mutate.eject_contents(container)
        lilypond_file = rmakers.example(components, time_signatures)
        return lilypond_file

    pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
    lilypond_file = make_lilypond_file(pairs)
    score = lilypond_file["Score"]
    string = abjad.lilypond(score, tags=True)

    assert string == abjad.string.normalize(
        r"""
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    \tweak text #tuplet-number::calc-fraction-text
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    \times 1/1
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    {
                        \time 3/8
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'16
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.beam()
                        [
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'8
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'8.
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.beam()
                        ]
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    }
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    \times 8/9
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    {
                        \time 4/8
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'4
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'16
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.beam()
                        [
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'8
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'8
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.beam()
                        ]
                        ~
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    }
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    \tweak text #tuplet-number::calc-fraction-text
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    \times 1/1
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    {
                        \time 3/8
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'16
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'4
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'16
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    }
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    \times 8/9
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    {
                        \time 4/8
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'8
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.beam()
                        [
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'8.
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.beam()
                        ]
                          %! TALEA_RHYTHM_MAKER
                          %! rmakers.talea()
                        c'4
                      %! TALEA_RHYTHM_MAKER
                      %! rmakers.talea()
                    }
                }
            >>
        """
    )
