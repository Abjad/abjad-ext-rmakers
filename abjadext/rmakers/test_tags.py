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
                \tweak text #tuplet-number::calc-fraction-text
                  %! INCISED_RHYTHM_MAKER
                \times 16/9
                  %! INCISED_RHYTHM_MAKER
                {
                    \time 8/8
                      %! INCISED_RHYTHM_MAKER
                    r16
                      %! INCISED_RHYTHM_MAKER
                    c'2
                  %! INCISED_RHYTHM_MAKER
                }
                  %! INCISED_RHYTHM_MAKER
                \tweak text #tuplet-number::calc-fraction-text
                  %! INCISED_RHYTHM_MAKER
                \times 8/5
                  %! INCISED_RHYTHM_MAKER
                {
                    \time 4/8
                      %! INCISED_RHYTHM_MAKER
                    c'4
                    ~
                      %! INCISED_RHYTHM_MAKER
                    c'16
                  %! INCISED_RHYTHM_MAKER
                }
                  %! INCISED_RHYTHM_MAKER
                \tweak text #tuplet-number::calc-fraction-text
                  %! INCISED_RHYTHM_MAKER
                \times 12/7
                  %! INCISED_RHYTHM_MAKER
                {
                    \time 6/8
                      %! INCISED_RHYTHM_MAKER
                    c'4.
                      %! INCISED_RHYTHM_MAKER
                    r16
                  %! INCISED_RHYTHM_MAKER
                }
            }
        >>
        """
    )
