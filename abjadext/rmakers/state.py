r"""
Examples that show how to work with rmakers in a statal way.

..  container:: example

    Using ``rmakers.accelerando()`` with the ``previous_state`` keyword.

    ..  container:: example

        Consumes 3 durations:

        >>> def make_statal_accelerandi(pairs, previous_state=None):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     if previous_state is None:
        ...         previous_state = {}
        ...     state = {}
        ...     tuplets = rmakers.accelerando(
        ...         durations,
        ...         [(1, 8), (1, 20), (1, 16)], [(1, 20), (1, 8), (1, 16)],
        ...         previous_state=previous_state,
        ...         state=state,
        ...     )
        ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file_["Voice"]
        ...     rmakers.duration_bracket(voice)
        ...     rmakers.feather_beam(voice)
        ...     return lilypond_file_, state

        >>> pairs = [(3, 8), (4, 8), (3, 8)]
        >>> lilypond_file, state = make_statal_accelerandi(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                    }
                }
            }

        >>> state
        {'durations_consumed': 3, 'logical_ties_produced': 17}

        Advances 3 durations; then consumes another 3 durations:

        >>> pairs = [(4, 8), (3, 8), (4, 8)]
        >>> lilypond_file, state = make_statal_accelerandi(pairs, previous_state=state)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                    }
                }
            }

        >>> state
        {'durations_consumed': 6, 'logical_ties_produced': 36}

        Advances 6 durations; then consumes another 3 durations:

        >>> pairs = [(3, 8), (4, 8), (3, 8)]
        >>> lilypond_file, state = make_statal_accelerandi(pairs, previous_state=state)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
                            \once \override Beam.grow-direction = #left
                            c'16 * 3/4
                            [
                            c'16 * 25/32
                            c'16 * 7/8
                            c'16 * 65/64
                            c'16 * 79/64
                            c'16 * 49/32
                            c'16 * 29/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
                            \once \override Beam.grow-direction = #right
                            c'16 * 117/64
                            [
                            c'16 * 99/64
                            c'16 * 69/64
                            c'16 * 13/16
                            c'16 * 47/64
                            ]
                        }
                        \revert TupletNumber.text
                    }
                }
            }

        >>> state
        {'durations_consumed': 9, 'logical_ties_produced': 53}

..  container:: example

    Using ``rmakers.even_division()`` with the ``previous_state`` keyword.

    Fills durations with 16th, 8th, quarter notes. Consumes 5 durations:

    >>> def make_lilypond_file(pairs, *, previous_state=None):
    ...     time_signatures = rmakers.time_signatures(pairs)
    ...     durations = [abjad.Duration(_) for _ in time_signatures]
    ...     state = {}
    ...     tuplets = rmakers.even_division(
    ...         durations, [16, 8, 4], extra_counts=[0, 1],
    ...         previous_state=previous_state, state=state
    ...     )
    ...     lilypond_file_ = rmakers.example(tuplets, time_signatures)
    ...     voice = lilypond_file_["Voice"]
    ...     rmakers.beam(voice)
    ...     rmakers.extract_trivial(voice)
    ...     return lilypond_file_, state

    >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
    >>> lilypond_file, state = make_lilypond_file(pairs)
    >>> abjad.show(lilypond_file) # doctest: +SKIP

    ..  docs::

        >>> score = lilypond_file["Score"]
        >>> string = abjad.lilypond(score)
        >>> print(string)
        \context Score = "Score"
        {
            \context RhythmicStaff = "Staff"
            \with
            {
                \override Clef.stencil = ##f
            }
            {
                \context Voice = "Voice"
                {
                    \time 2/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tuplet 3/2
                    {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    c'4
                    \tuplet 5/4
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    c'8
                    [
                    c'8
                    ]
                }
            }
        }

    >>> state
    {'durations_consumed': 5, 'logical_ties_produced': 15}

    Advances 5 durations; then consumes another 5 durations:

    >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
    >>> lilypond_file, state = make_lilypond_file(pairs, previous_state=state)
    >>> abjad.show(lilypond_file) # doctest: +SKIP

    ..  docs::

        >>> score = lilypond_file["Score"]
        >>> string = abjad.lilypond(score)
        >>> print(string)
        \context Score = "Score"
        {
            \context RhythmicStaff = "Staff"
            \with
            {
                \override Clef.stencil = ##f
            }
            {
                \context Voice = "Voice"
                {
                    \time 2/8
                    c'4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tuplet 3/2
                    {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    c'4
                    \tuplet 5/4
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            }
        }

    >>> state
    {'durations_consumed': 10, 'logical_ties_produced': 29}

..  container:: example

    Using ``rmakers.talea()`` with the ``previous_state`` keyword.

    >>> def make_lilypond_file(pairs, *, previous_state=None):
    ...     time_signatures = rmakers.time_signatures(pairs)
    ...     durations = [abjad.Duration(_) for _ in time_signatures]
    ...     state = {}
    ...     tuplets = rmakers.talea(
    ...         durations, [4], 16, extra_counts=[0, 1, 2],
    ...         previous_state=previous_state,
    ...         state=state,
    ...     )
    ...     container = abjad.Container(tuplets)
    ...     rmakers.beam(container)
    ...     rmakers.extract_trivial(container)
    ...     components = abjad.mutate.eject_contents(container)
    ...     lilypond_file = rmakers.example(components, time_signatures)
    ...     return lilypond_file, state

    ..  container:: example

        **#1.** This call consumes 4 durations and 31 counts, as shown in
        output ``state``:

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file, state = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \time 3/8
                        c'4
                        c'8
                        ~
                        \tuplet 9/8
                        {
                            \time 4/8
                            c'8
                            c'4
                            c'8.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'16
                            c'4
                            c'8.
                            ~
                        }
                        \time 4/8
                        c'16
                        c'4
                        c'8.
                    }
                }
            }

        >>> for item in state.items():
        ...     item
        ('durations_consumed', 4)
        ('incomplete_last_note', True)
        ('logical_ties_produced', 8)
        ('talea_weight_consumed', 31)

    ..  container:: example

        **#2.** This call advances 4 durations and 31 counts, as read from
        ``previous_state``. The function then consumes another 4 durations
        and 32 counts. This equals 8 durations and 63 counts consumed so far,
        as shown in output ``state``:

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file, state = make_lilypond_file(pairs, previous_state=state)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/6
                        {
                            \time 3/8
                            c'16
                            c'4
                            c'8
                            ~
                        }
                        \tuplet 5/4
                        {
                            \time 4/8
                            c'8
                            c'4
                            c'4
                        }
                        \time 3/8
                        c'4
                        c'8
                        ~
                        \tuplet 9/8
                        {
                            \time 4/8
                            c'8
                            c'4
                            c'8.
                        }
                    }
                }
            }

        >>> for item in state.items():
        ...     item
        ('durations_consumed', 8)
        ('incomplete_last_note', True)
        ('logical_ties_produced', 16)
        ('talea_weight_consumed', 63)

    ..  container:: example

        **#3.** This call advances 8 durations and 63 counts, as read from
        ``previous_state``. The function then consumes another 4 durations
        and 33 counts. This equals 12 durations and 96 counts consumed so far,
        as shown in output ``state``:

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file, state = make_lilypond_file(pairs, previous_state=state)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'16
                            c'4
                            c'8.
                            ~
                        }
                        \time 4/8
                        c'16
                        c'4
                        c'8.
                        ~
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/6
                        {
                            \time 3/8
                            c'16
                            c'4
                            c'8
                            ~
                        }
                        \tuplet 5/4
                        {
                            \time 4/8
                            c'8
                            c'4
                            c'4
                        }
                    }
                }
            }

        >>> for item in state.items():
        ...     item
        ('durations_consumed', 12)
        ('logical_ties_produced', 24)
        ('talea_weight_consumed', 96)

"""


def sphinx():
    """
    Makes Sphinx read this module.
    """
    pass
