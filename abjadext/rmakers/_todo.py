# TODO: make this work again relatively soon
#            Only logical tie 12 is rested here:
#
#            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
#            >>> selections = command(divisions, previous_segment_stop_state=state)
#
#
#            >>> lilypond_file = rmakers.example(selections, divisions)
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> score = lilypond_file["Score"]
#                >>> string = abjad.lilypond(score)
#                >>> print(string)
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                    }
#                    \new RhythmicStaff
#                    {
#                        \tweak text #tuplet-number::calc-fraction-text
#                        \times 6/7 {
#                            c'16
#                            c'4
#                            c'8
#                            ~
#                        }
#                        \times 4/5 {
#                            c'8
#                            c'4
#                            c'4
#                        }
#                        r4
#                        c'8
#                        ~
#                        \times 8/9 {
#                            c'8
#                            c'4
#                            c'8.
#                        }
#                    }
#                >>
#
#            >>> command.state
#            dict(
#                [
#                    ('divisions_consumed', 8),
#                    ('incomplete_last_note', True),
#                    ('logical_ties_produced', 16),
#                    ('talea_weight_consumed', 63),
#                    ]
#                )
#
#        ..  container:: example
#
#            REGRESSION. Periodic rest commands also respect state.
#
#            >>> stack = rmakers.stack(
#            ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
#            ...     rmakers.force_rest(
#            ...         lambda _: abjad.select(_).logical_ties().get([3], 4),
#            ...     ),
#            ...     rmakers.beam(),
#            ...     rmakers.extract_trivial(),
#            ...     )
#
#            Incomplete last note is rested here:
#
#            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
#            >>> selections = stack(divisions)
#
#            >>> lilypond_file = rmakers.example(selections, divisions)
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> score = lilypond_file["Score"]
#                >>> string = abjad.lilypond(score)
#                >>> print(string)
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                    }
#                    \new RhythmicStaff
#                    {
#                        c'4
#                        c'8
#                        ~
#                        \times 8/9 {
#                            c'8
#                            c'4
#                            r8.
#                        }
#                        \tweak text #tuplet-number::calc-fraction-text
#                        \times 3/4 {
#                            r16
#                            c'4
#                            c'8.
#                            ~
#                        }
#                        c'16
#                        c'4
#                        r8.
#                    }
#                >>
#
#            >>> stack.maker.state
#            dict(
#                [
#                    ('divisions_consumed', 4),
#                    ('incomplete_last_note', True),
#                    ('logical_ties_produced', 8),
#                    ('talea_weight_consumed', 31),
#                    ]
#                )
#
#            Incomplete first note is rested here:
#
#            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
#            >>> selections = stack(divisions, previous_state=state)
#
#            >>> lilypond_file = rmakers.example(selections, divisions)
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> score = lilypond_file["Score"]
#                >>> string = abjad.lilypond(score)
#                >>> print(string)
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                    }
#                    \new RhythmicStaff
#                    {
#                        \tweak text #tuplet-number::calc-fraction-text
#                        \times 6/7 {
#                            r16
#                            c'4
#                            c'8
#                            ~
#                        }
#                        \times 4/5 {
#                            c'8
#                            c'4
#                            r4
#                        }
#                        c'4
#                        c'8
#                        ~
#                        \times 8/9 {
#                            c'8
#                            c'4
#                            r8.
#                        }
#                    }
#                >>
#
#            >>> stack.maker.state
#            dict(
#                [
#                    ('divisions_consumed', 8),
#                    ('incomplete_last_note', True),
#                    ('logical_ties_produced', 16),
#                    ('talea_weight_consumed', 63),
#                    ]
#                )


# TODO: allow statal GROUP_BY_MEASURE selector (or maybe tuplet selecctor) to work here:
#            Only tuplet 7 is rested here:
#
#            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
#            >>> selections = stack(divisions, previous_state=state)
#
#            >>> lilypond_file = rmakers.example(selections, divisions)
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> score = lilypond_file["Score"]
#                >>> string = abjad.lilypond(score)
#                >>> print(string)
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                    }
#                    \new RhythmicStaff
#                    {
#                        \tweak text #tuplet-number::calc-fraction-text
#                        \times 6/7 {
#                            c'16
#                            c'4
#                            c'8
#                            ~
#                        }
#                        \times 4/5 {
#                            c'8
#                            c'4
#                            c'4
#                        }
#                        c'4
#                        c'8
#                        r2
#                    }
#                >>
#
#            >>> stack.maker.state
#            dict(
#                [
#                    ('divisions_consumed', 8),
#                    ('incomplete_last_note', True),
#                    ('logical_ties_produced', 15),
#                    ('talea_weight_consumed', 63),
#                    ]
#                )


# TODO: allow statal GROUP_BY_MEASURE selector (or maybe tuplet selecctor) to work here:
#            Incomplete first note is rested here:
#
#            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
#            >>> selections = stack(divisions, previous_state=state)
#
#            >>> lilypond_file = rmakers.example(selections, divisions)
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> score = lilypond_file["Score"]
#                >>> string = abjad.lilypond(score)
#                >>> print(string)
#                \new Score
#                <<
#                    \new GlobalContext
#                    {
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                        \time 3/8
#                        s1 * 3/8
#                        \time 4/8
#                        s1 * 1/2
#                    }
#                    \new RhythmicStaff
#                    {
#                        \tweak text #tuplet-number::calc-fraction-text
#                        \times 6/7 {
#                            c'16
#                            c'4
#                            c'8
#                        }
#                        r2
#                        c'4
#                        c'8
#                        ~
#                        \times 8/9 {
#                            c'8
#                            c'4
#                            c'8.
#                        }
#                    }
#                >>
#
#            >>> stack.maker.state
#            dict(
#                [
#                    ('divisions_consumed', 8),
#                    ('incomplete_last_note', True),
#                    ('logical_ties_produced', 15),
#                    ('talea_weight_consumed', 63),
#                    ]
#                )


# TODO: integrate tests
#    @property
#    def preprocessor(self):
#        r"""
#        Gets division preprocessor.
#
#        ..  container:: example
#
#            >>> weights = [abjad.NonreducedFraction(3, 8)]
#            >>> divisions = []
#            >>> divisions = divisions.split(
#            ...     weights, cyclic=True, overhang=True,
#            ... )
#            >>> divisions = divisions.flatten(depth=-1)
#            >>> stack = rmakers.stack(rmakers.note(), preprocessor=divisions)
#            >>> divisions = [(4, 4), (4, 4)]
#            >>> selections = stack(divisions)
#
#            >>> lilypond_file = rmakers.example(selections, divisions)
#            >>> abjad.show(lilypond_file) # doctest: +SKIP
#
#            ..  docs::
#
#                >>> score = lilypond_file["Score"]
#                >>> string = abjad.lilypond(score)
#                >>> print(string)
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
