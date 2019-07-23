import abjad
import typing
from . import commands as _commands
from . import specifiers as _specifiers
from .RhythmMaker import RhythmMaker


class NoteRhythmMaker(RhythmMaker):
    """
    Note rhtyhm-maker.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ()

    ### INITIALIZER ###

    def __init__(
        self, spelling: _specifiers.Spelling = None, tag: str = None
    ) -> None:
        RhythmMaker.__init__(self, spelling=spelling, tag=tag)

    ### PRIVATE METHODS ###

    def _make_music(self, divisions) -> typing.List[abjad.Selection]:
        selections = []
        spelling = self._get_spelling_specifier()
        leaf_maker = abjad.LeafMaker(
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=self.tag,
        )
        for division in divisions:
            selection = leaf_maker(pitches=0, durations=[division])
            selections.append(selection)
        return selections

    ### PUBLIC PROPERTIES ###

    @property
    def commands(self) -> typing.List[_commands.Command]:
        r"""
        Gets commands.

        ..  container:: example

            Silences every other logical tie:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([0], 2),
            ...     ),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        c'4.
                        r2
                        c'4.
                    }
                >>

        ..  container:: example

            Forces rest at every logical tie:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.force_rest(abjad.select()),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (5, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r4.
                        r2
                        r2
                        r8
                    }
                >>

        ..  container:: example

            Silences every other output division except for the first and last:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([0], 2)[1:-1],
            ...     ),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8), (2, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        c'4.
                        r2
                        c'4.
                        c'4
                    }
                >>

        ..  container:: example

            Beams each division:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.beam(abjad.select().logical_ties(pitched=True)),
            ...     )

            >>> divisions = [(5, 32), (5, 32)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/32
                        s1 * 5/32
                        \time 5/32
                        s1 * 5/32
                    }
                    \new RhythmicStaff
                    {
                        c'8
                        ~
                        [
                        c'32
                        ]
                        c'8
                        ~
                        [
                        c'32
                        ]
                    }
                >>

        ..  container:: example

            Beams divisions together:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.beam_groups(abjad.select().logical_ties()),
            ... )

            >>> divisions = [(5, 32), (5, 32)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/32
                        s1 * 5/32
                        \time 5/32
                        s1 * 5/32
                    }
                    \new RhythmicStaff
                    {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        c'8
                        ~
                        [
                        \set stemLeftBeamCount = 3
                        \set stemRightBeamCount = 1
                        c'32
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 1
                        c'8
                        ~
                        \set stemLeftBeamCount = 3
                        \set stemRightBeamCount = 0
                        c'32
                        ]
                    }
                >>

        ..  container:: example

            Makes no beams:

            >>> rhythm_maker = rmakers.NoteRhythmMaker()

            >>> divisions = [(5, 32), (5, 32)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/32
                        s1 * 5/32
                        \time 5/32
                        s1 * 5/32
                    }
                    \new RhythmicStaff
                    {
                        c'8
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                    }
                >>

        ..  container:: example

            Does not tie across divisions:

            >>> rhythm_maker = rmakers.NoteRhythmMaker()

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        c'4.
                        c'2
                        c'4.
                    }
                >>

        ..  container:: example

            Ties across divisions:

            >>> nonlast_lts = abjad.select().logical_ties()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.tie(nonlast_lts.map(last_leaf)),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        ~
                        c'4.
                        ~
                        c'2
                        ~
                        c'4.
                    }
                >>

        ..  container:: example

            Ties across every other logical tie:

            >>> lts = abjad.select().logical_ties().get([0], 2)
            >>> last_leaf = abjad.select().leaf(-1)
            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.tie(lts.map(last_leaf)),
            ... )

            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        ~
                        c'4.
                        c'2
                        ~
                        c'4.
                    }
                >>

        ..  container:: example

            Strips all ties:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.untie(),
            ... )

            >>> divisions = [(7, 16), (1, 4), (5, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 7/16
                        s1 * 7/16
                        \time 1/4
                        s1 * 1/4
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        c'4..
                        c'4
                        c'4
                        c'16
                    }
                >>

        ..  container:: example

            Spells tuplets as diminutions:

            >>> rhythm_maker = rmakers.NoteRhythmMaker()

            >>> divisions = [(5, 14), (3, 7)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 5/14
                        s1 * 5/14
                        #(ly:expect-warning "strange time signature found")
                        \time 3/7
                        s1 * 3/7
                    }
                    \new RhythmicStaff
                    {
                        \tweak edge-height #'(0.7 . 0)
                        \times 4/7 {
                            c'2
                            ~
                            c'8
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \times 4/7 {
                            c'2.
                        }
                    }
                >>

        ..  container:: example

            Spells tuplets as augmentations:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.force_augmentation(),
            ... )

            >>> divisions = [(5, 14), (3, 7)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 5/14
                        s1 * 5/14
                        #(ly:expect-warning "strange time signature found")
                        \time 3/7
                        s1 * 3/7
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tweak edge-height #'(0.7 . 0)
                        \times 8/7 {
                            c'4
                            ~
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tweak edge-height #'(0.7 . 0)
                        \times 8/7 {
                            c'4.
                        }
                    }
                >>

        ..  container:: example

            Forces rest in logical tie 0:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.force_rest(abjad.select().logical_ties()[0]),
            ...     )

            >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r8
                        c'4
                        c'4
                        c'2
                        ~
                        c'8
                    }
                >>

        ..  container:: example

            Forces rests in first two logical ties:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.force_rest(abjad.select().logical_ties()[:2]),
            ...     )

            >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r8
                        r4
                        c'4
                        c'2
                        ~
                        c'8
                    }
                >>

        ..  container:: example

            Forces rests in first and last logical ties:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([0, -1])
            ...     ),
            ... )

            >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 2/8
                        s1 * 1/4
                        \time 2/8
                        s1 * 1/4
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        r2
                        r8
                        c'4
                        c'4
                        r2
                        r8
                    }
                >>

        """
        return super().commands

    # TODO: port tests to rhythm command
    #    @property
    #    def preprocessor(self) -> typing.Optional[abjad.Expression]:
    #        r"""
    #        Gets division preprocessor.
    #
    #        ..  container:: example
    #
    #            >>> weights = [abjad.NonreducedFraction(3, 8)]
    #            >>> divisions = abjad.sequence().join()
    #            >>> divisions = divisions.split(
    #            ...     weights, cyclic=True, overhang=True,
    #            ...     )
    #            >>> divisions = divisions.flatten(depth=-1)
    #            >>> rhythm_maker = rmakers.rhythm(rmakers.note(), preprocessor=divisions)
    #
    #            >>> divisions = [(4, 4), (4, 4)]
    #            >>> selection = rhythm_maker(divisions)
    #            >>> lilypond_file = abjad.LilyPondFile.rhythm(
    #            ...     selection,
    #            ...     divisions,
    #            ...     )
    #            >>> abjad.show(lilypond_file) # doctest: +SKIP
    #
    #            ..  docs::
    #
    #                >>> abjad.f(lilypond_file[abjad.Score])
    #                \new Score
    #                <<
    #                    \new GlobalContext
    #                    {
    #                        \time 4/4
    #                        s1 * 1
    #                        \time 4/4
    #                        s1 * 1
    #                    }
    #                    \new RhythmicStaff
    #                    {
    #                        c'4.
    #                        c'4.
    #                        c'4.
    #                        c'4.
    #                        c'4.
    #                        c'8
    #                    }
    #                >>
    #
    #        """
    #        return super().preprocessor

    @property
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        r"""
        Gets duration specifier.

        ..  container:: example

            Spells durations with the fewest number of glyphs:

            >>> rhythm_maker = rmakers.NoteRhythmMaker()

            >>> divisions = [(5, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'2
                        ~
                        c'8
                        c'4.
                    }
                >>

        ..  container:: example

            Forbids notes with written duration greater than or equal to
            ``1/2``:

            >>> rhythm_maker = rmakers.NoteRhythmMaker(
            ...     spelling=rmakers.Spelling(forbidden_note_duration=(1, 2))
            ...     )

            >>> divisions = [(5, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'4
                        ~
                        c'8
                        c'4.
                    }
                >>

        ..  container:: example

            Rewrites meter:

            >>> rhythm_maker = rmakers.rhythm(
            ...     rmakers.note(),
            ...     rmakers.rewrite_meter(),
            ...     )

            >>> divisions = [(3, 4), (6, 16), (9, 16)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> abjad.f(lilypond_file[abjad.Score])
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/4
                        s1 * 3/4
                        \time 6/16
                        s1 * 3/8
                        \time 9/16
                        s1 * 9/16
                    }
                    \new RhythmicStaff
                    {
                        c'2.
                        c'4.
                        c'4.
                        ~
                        c'8.
                    }
                >>

        """
        return super().spelling

    @property
    def tag(self):
        r"""
        Gets tag.

        ..  container:: example

            >>> rhythm_maker = rmakers.NoteRhythmMaker(
            ...     tag='NOTE_RHYTHM_MAKER',
            ...     )

            >>> divisions = [(5, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection,
            ...     divisions,
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> abjad.f(lilypond_file[abjad.Score])
            \new Score
            <<
                \new GlobalContext
                {
                    \time 5/8
                    s1 * 5/8
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    c'2 %! NOTE_RHYTHM_MAKER
                    ~
                    c'8 %! NOTE_RHYTHM_MAKER
                    c'4. %! NOTE_RHYTHM_MAKER
                }
            >>

        """
        return super().tag
