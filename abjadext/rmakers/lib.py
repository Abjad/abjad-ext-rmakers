import abjad


def attach_markup_struts(lilypond_file):
    """
    Workaround because LilyPond's multisystem cropping currently removes
    intersystem whitespace.
    """
    rhythmic_staff = lilypond_file[abjad.Score][-1]
    first_leaf = abjad.get.leaf(rhythmic_staff, 0)
    markup = abjad.Markup(r"\markup I", direction=abjad.Up, literal=True)
    abjad.attach(markup, first_leaf)
    abjad.tweak(markup).staff_padding = 11
    abjad.tweak(markup).transparent = "##t"
    duration = abjad.get.duration(rhythmic_staff)
    if abjad.Duration(6, 4) < duration:
        last_leaf = abjad.get.leaf(rhythmic_staff, -1)
        markup = abjad.Markup(r"\markup I", direction=abjad.Up, literal=True)
        abjad.attach(markup, last_leaf)
        abjad.tweak(markup).staff_padding = 18
        abjad.tweak(markup).transparent = "##t"
