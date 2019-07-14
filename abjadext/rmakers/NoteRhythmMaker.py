import abjad
import typing
from . import typings
from .BeamSpecifier import BeamSpecifier
from .BurnishSpecifier import BurnishSpecifier
from .DurationSpecifier import DurationSpecifier
from .RhythmMaker import RhythmMaker
from .TieSpecifier import TieSpecifier
from .TupletSpecifier import TupletSpecifier
from .commands import RestCommand


class NoteRhythmMaker(RhythmMaker):
    r"""
    Note rhythm-maker.

    ..  container:: example

        Makes notes equal to the duration of input divisions. Adds ties where
        necessary:

        >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

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

    Usage follows the two-step configure-once / call-repeatedly pattern shown
    here.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_burnish_specifier",)

    ### INITIALIZER ###

    def __init__(
        self,
        *specifiers: typings.SpecifierTyping,
        burnish_specifier: BurnishSpecifier = None,
        divisions: abjad.Expression = None,
        duration_specifier: DurationSpecifier = None,
        tag: str = None,
    ) -> None:
        RhythmMaker.__init__(
            self,
            *specifiers,
            divisions=divisions,
            duration_specifier=duration_specifier,
            tag=tag,
        )
        if burnish_specifier is not None:
            assert isinstance(burnish_specifier, BurnishSpecifier)
        self._burnish_specifier = burnish_specifier

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.Sequence[abjad.IntegerPair],
        previous_state: abjad.OrderedDict = None,
    ) -> abjad.Selection:
        """
        Calls note rhythm-maker on ``divisions``.

        ..  container:: example

            Calls rhythm-maker on divisions:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()
            >>> divisions = [(5, 8), (3, 8)]
            >>> rhythm_maker(divisions)
            Selection([Note("c'2"), Note("c'8"), Note("c'4.")])

        """
        return RhythmMaker.__call__(
            self, divisions, previous_state=previous_state
        )

    def __format__(self, format_specification="") -> str:
        """
        Formats note rhythm-maker.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()
            >>> abjad.f(rhythm_maker)
            abjadext.rmakers.NoteRhythmMaker()

        """
        return super().__format__(format_specification=format_specification)

    def __repr__(self) -> str:
        """
        Gets interpreter representation.

        ..  container:: example

            >>> abjadext.rmakers.NoteRhythmMaker()
            NoteRhythmMaker()

        """
        return super().__repr__()

    ### PRIVATE METHODS ###

    def _apply_burnish_specifier(self, selections):
        if self.burnish_specifier is None:
            return selections
        elif self.burnish_specifier.outer_divisions_only:
            selections = self._burnish_outer_divisions(selections)
        else:
            selections = self._burnish_each_division(selections)
        return selections

    def _burnish_each_division(self, selections):
        message = "NoteRhythmMaker does not yet implement"
        message += " burnishing each division."
        raise NotImplementedError(message)

    def _burnish_outer_divisions(self, selections):
        left_classes = self.burnish_specifier.left_classes
        left_counts = self.burnish_specifier.left_counts
        right_classes = self.burnish_specifier.right_classes
        right_counts = self.burnish_specifier.right_counts
        if left_counts:
            assert len(left_counts) == 1, repr(left_counts)
            left_count = left_counts[0]
        else:
            left_count = 0
        if right_counts:
            assert len(right_counts) == 1, repr(right_counts)
            right_count = right_counts[0]
        else:
            right_count = 0
        if left_count + right_count <= len(selections):
            middle_count = len(selections) - (left_count + right_count)
        elif left_count <= len(selections):
            right_count = len(selections) - left_count
            middle_count = 0
        else:
            left_count = len(selections)
            right_count = 0
            middle_count = 0
        assert left_count + middle_count + right_count == len(selections)
        new_selections = []
        left_classes = abjad.CyclicTuple(left_classes)
        for i, selection in enumerate(selections[:left_count]):
            target_class = left_classes[i]
            new_selection = self._cast_selection(selection, target_class)
            new_selections.append(new_selection)
        if right_count:
            for selection in selections[left_count:-right_count]:
                new_selections.append(selection)
            right_classes = abjad.CyclicTuple(right_classes)
            for i, selection in enumerate(selections[-right_count:]):
                target_class = right_classes[i]
                new_selection = self._cast_selection(selection, target_class)
                new_selections.append(new_selection)
        else:
            for selection in selections[left_count:]:
                new_selections.append(selection)
        return new_selections

    def _cast_selection(self, selection, target_class):
        new_selection = []
        for leaf in selection:
            new_leaf = target_class(leaf, tag=self.tag)
            if not isinstance(new_leaf, (abjad.Chord, abjad.Note)):
                abjad.detach(abjad.TieIndicator, new_leaf)
                abjad.detach(abjad.RepeatTie, new_leaf)
            new_selection.append(new_leaf)
        new_selection = abjad.select(new_selection)
        return new_selection

    def _make_music(self, divisions) -> typing.List[abjad.Selection]:
        selections = []
        duration_specifier = self._get_duration_specifier()
        leaf_maker = abjad.LeafMaker(
            increase_monotonic=duration_specifier.increase_monotonic,
            forbidden_note_duration=duration_specifier.forbidden_note_duration,
            forbidden_rest_duration=duration_specifier.forbidden_rest_duration,
            tag=self.tag,
        )
        for division in divisions:
            selection = leaf_maker(pitches=0, durations=[division])
            selections.append(selection)
        selections = self._apply_burnish_specifier(selections)
        return selections

    ### PUBLIC PROPERTIES ###

    @property
    def burnish_specifier(self) -> typing.Optional[BurnishSpecifier]:
        r"""
        Gets burnish specifier.

        ..  container:: example

            Burnishes nothing:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

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
                        c'2
                        ~
                        c'8
                        c'4
                        c'4
                        c'2
                        ~
                        c'8
                    }
                >>

        ..  container:: example

            Forces leaves of first division to be rests:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[1],
            ...         outer_divisions_only=True,
            ...         ),
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

            Forces leaves of first two divisions to be rests:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[2],
            ...         outer_divisions_only=True,
            ...         ),
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

            Forces leaves of first and last divisions to rests:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     burnish_specifier=abjadext.rmakers.BurnishSpecifier(
            ...         left_classes=[abjad.Rest],
            ...         left_counts=[1],
            ...         right_classes=[abjad.Rest],
            ...         right_counts=[1],
            ...         outer_divisions_only=True,
            ...         ),
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
                        r2
                        r8
                    }
                >>

        ..  note:: Currently only works when ``outer_divisions_only`` is true.

        """
        return self._burnish_specifier

    @property
    def divisions(self) -> typing.Optional[abjad.Expression]:
        r"""
        Gets division expressions.

        ..  container:: example

            >>> weights = [abjad.NonreducedFraction(3, 8)]
            >>> divisions = abjad.sequence().join()
            >>> divisions = divisions.split(
            ...     weights, cyclic=True, overhang=True,
            ...     )
            >>> divisions = divisions.flatten(depth=-1)
            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     divisions=divisions,
            ... )

            >>> divisions = [(4, 4), (4, 4)]
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
                        \time 4/4
                        s1 * 1
                        \time 4/4
                        s1 * 1
                    }
                    \new RhythmicStaff
                    {
                        c'4.
                        c'4.
                        c'4.
                        c'4.
                        c'4.
                        c'8
                    }
                >>

        """
        return super().divisions

    @property
    def duration_specifier(self) -> typing.Optional[DurationSpecifier]:
        r"""
        Gets duration specifier.

        ..  container:: example

            Spells durations with the fewest number of glyphs:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

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

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     duration_specifier=abjadext.rmakers.DurationSpecifier(
            ...         forbidden_note_duration=(1, 2),
            ...         ),
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

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.RewriteMeterCommand(),
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
        return super().duration_specifier

    @property
    def specifiers(self) -> typing.List[typings.SpecifierTyping]:
        r"""
        Gets specifiers.

        ..  container:: example

            Silences every other logical tie:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.rest(
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

            Silences all leaves:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.rest(abjad.select()),
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
                        r4.
                        r2
                        r4.
                    }
                >>

        ..  container:: example

            Silences every other division:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.rest(
            ...         abjad.select().logical_ties().get([0], 2),
            ...     )
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

            Silences every output division:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...    abjadext.rmakers.rest(abjad.select().logical_ties()),
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
                        r4.
                        r2
                        r4.
                    }
                >>

        ..  container:: example

            Silences every output division and uses multimeasure rests:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...    abjadext.rmakers.rest(
            ...         abjad.select().logical_ties(), 
            ...         use_multimeasure_rests=True,
            ...     ),
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
                        R1 * 1/2
                        R1 * 3/8
                        R1 * 1/2
                        R1 * 5/8
                    }
                >>

        ..  container:: example

            Silences every other output division except for the first and last:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.rest(
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

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         selector=abjad.select().logical_ties(pitched=True),
            ...         ),
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

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(
            ...         beam_divisions_together=True,
            ...         selector=abjad.select().logical_ties(),
            ...         ),
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

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.BeamSpecifier(),
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
                        c'32
                        c'8
                        ~
                        c'32
                    }
                >>

        ..  container:: example

            Does not tie across divisions:

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

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
            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=nonlast_lts.map(last_leaf),
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
            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         attach_ties=True,
            ...         selector=lts.map(last_leaf),
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

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.TieSpecifier(
            ...         detach_ties=True,
            ...         selector=abjad.select().notes(),
            ...     ),
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

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker()

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

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
            ...     abjadext.rmakers.TupletSpecifier(
            ...         diminution=False,
            ...     ),
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

        """
        return super().specifiers

    @property
    def tag(self):
        r"""
        Gets tag.

        ..  container:: example

            >>> rhythm_maker = abjadext.rmakers.NoteRhythmMaker(
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
