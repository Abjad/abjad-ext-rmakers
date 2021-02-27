import math
import typing

import abjad

from . import specifiers as _specifiers

### CLASSES ###


class RhythmMaker:
    """
    Rhythm-maker baseclass.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = (
        "_already_cached_state",
        "_previous_state",
        "_spelling",
        "_state",
        "_tag",
    )

    ### INITIALIZER ###

    def __init__(
        self, *, spelling: _specifiers.Spelling = None, tag: abjad.Tag = None
    ) -> None:
        if spelling is not None:
            assert isinstance(spelling, _specifiers.Spelling)
        self._spelling = spelling
        self._already_cached_state = False
        self._previous_state = abjad.OrderedDict()
        self._state = abjad.OrderedDict()
        if tag is not None:
            assert isinstance(tag, abjad.Tag), repr(tag)
        self._tag = tag

    ### SPECIAL METHODS ###

    def __call__(
        self,
        divisions: typing.Sequence[abjad.IntegerPair],
        previous_state: abjad.OrderedDict = None,
    ) -> abjad.Selection:
        """
        Calls rhythm-maker.
        """
        self._previous_state = abjad.OrderedDict(previous_state)
        time_signatures = [abjad.TimeSignature(_) for _ in divisions]
        divisions = [abjad.NonreducedFraction(_) for _ in divisions]
        staff = self._make_staff(time_signatures)
        music = self._make_music(divisions)
        assert isinstance(music, list), repr(music)
        prototype = (abjad.Tuplet, abjad.Selection)
        for item in music:
            assert isinstance(item, prototype), repr(item)
        music_voice = staff["Rhythm_Maker_Music_Voice"]
        music_voice.extend(music)
        divisions_consumed = len(divisions)
        if self._already_cached_state is not True:
            self._cache_state(music_voice, divisions_consumed)
        self._validate_tuplets(music_voice)
        selection = music_voice[:]
        music_voice[:] = []
        return selection

    def __eq__(self, argument) -> bool:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager.compare_objects(self, argument)

    def __hash__(self) -> int:
        """
        Delegates to storage format manager.
        """
        hash_values = abjad.StorageFormatManager(self).get_hash_values()
        try:
            result = hash(hash_values)
        except TypeError:
            raise TypeError(f"unhashable type: {self}")
        return result

    def __repr__(self) -> str:
        """
        Delegates to storage format manager.
        """
        return abjad.StorageFormatManager(self).get_repr_format()

    ### PRIVATE METHODS ###

    def _cache_state(self, voice, divisions_consumed):
        previous_logical_ties_produced = self._previous_logical_ties_produced()
        logical_ties_produced = len(abjad.select(voice).logical_ties())
        logical_ties_produced += previous_logical_ties_produced
        if self._previous_incomplete_last_note():
            logical_ties_produced -= 1
        self.state["divisions_consumed"] = self.previous_state.get(
            "divisions_consumed", 0
        )
        self.state["divisions_consumed"] += divisions_consumed
        self.state["logical_ties_produced"] = logical_ties_produced
        items = self.state.items()
        state = abjad.OrderedDict(sorted(items))
        self._state = state

    def _call_commands(self, voice, divisions_consumed):
        pass

    def _get_spelling_specifier(self):
        if self.spelling is not None:
            return self.spelling
        return _specifiers.Spelling()

    def _get_format_specification(self):
        return abjad.FormatSpecification(self)

    @staticmethod
    def _make_leaves_from_talea(
        talea,
        talea_denominator,
        increase_monotonic=None,
        forbidden_note_duration=None,
        forbidden_rest_duration=None,
        tag: abjad.Tag = None,
    ):
        assert all(x != 0 for x in talea), repr(talea)
        result: typing.List[abjad.Leaf] = []
        leaf_maker = abjad.LeafMaker(
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            tag=tag,
        )
        pitches: typing.List[typing.Union[int, None]]
        for note_value in talea:
            if 0 < note_value:
                pitches = [0]
            else:
                pitches = [None]
            division = abjad.Duration(abs(note_value), talea_denominator)
            durations = [division]
            leaves = leaf_maker(pitches, durations)
            if (
                1 < len(leaves)
                and abjad.get.logical_tie(leaves[0]).is_trivial
                and not isinstance(leaves[0], abjad.Rest)
            ):
                abjad.tie(leaves)
            result.extend(leaves)
        result = abjad.select(result)
        return result

    def _make_music(self, divisions):
        return []

    @staticmethod
    def _make_staff(time_signatures):
        assert time_signatures, repr(time_signatures)
        staff = abjad.Staff(simultaneous=True)
        time_signature_voice = abjad.Voice(name="TimeSignatureVoice")
        for time_signature in time_signatures:
            duration = time_signature.pair
            skip = abjad.Skip(1, multiplier=duration)
            time_signature_voice.append(skip)
            abjad.attach(time_signature, skip, context="Staff")
        staff.append(time_signature_voice)
        staff.append(abjad.Voice(name="Rhythm_Maker_Music_Voice"))
        return staff

    def _make_tuplets(self, divisions, leaf_lists):
        assert len(divisions) == len(leaf_lists)
        tuplets = []
        for division, leaf_list in zip(divisions, leaf_lists):
            duration = abjad.Duration(division)
            tuplet = abjad.Tuplet.from_duration(duration, leaf_list, tag=self.tag)
            tuplets.append(tuplet)
        return tuplets

    def _previous_divisions_consumed(self):
        if not self.previous_state:
            return 0
        return self.previous_state.get("divisions_consumed", 0)

    def _previous_incomplete_last_note(self):
        if not self.previous_state:
            return False
        return self.previous_state.get("incomplete_last_note", False)

    def _previous_logical_ties_produced(self):
        if not self.previous_state:
            return 0
        return self.previous_state.get("logical_ties_produced", 0)

    def _scale_counts(self, divisions, talea_denominator, counts):
        talea_denominator = talea_denominator or 1
        scaled_divisions = divisions[:]
        dummy_division = (1, talea_denominator)
        scaled_divisions.append(dummy_division)
        scaled_divisions = abjad.Duration.durations_to_nonreduced_fractions(
            scaled_divisions
        )
        dummy_division = scaled_divisions.pop()
        lcd = dummy_division.denominator
        multiplier = lcd / talea_denominator
        assert abjad.math.is_integer_equivalent(multiplier)
        multiplier = int(multiplier)
        scaled_counts = {}
        for name, vector in counts.items():
            vector = [multiplier * _ for _ in vector]
            vector = abjad.CyclicTuple(vector)
            scaled_counts[name] = vector
        assert len(scaled_divisions) == len(divisions)
        assert len(scaled_counts) == len(counts)
        return abjad.OrderedDict(
            {"divisions": scaled_divisions, "lcd": lcd, "counts": scaled_counts}
        )

    def _validate_tuplets(self, selections):
        for tuplet in abjad.iterate(selections).components(abjad.Tuplet):
            assert abjad.Multiplier(tuplet.multiplier).normalized(), repr(tuplet)
            assert len(tuplet), repr(tuplet)

    ### PUBLIC PROPERTIES ###

    @property
    def previous_state(self) -> abjad.OrderedDict:
        """
        Gets previous state dictionary.
        """
        return self._previous_state

    @property
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        """
        Gets duration specifier.
        """
        return self._spelling

    @property
    def state(self) -> abjad.OrderedDict:
        """
        Gets state dictionary.
        """
        return self._state

    @property
    def tag(self) -> typing.Optional[abjad.Tag]:
        """
        Gets tag.
        """
        return self._tag


class AccelerandoRhythmMaker(RhythmMaker):
    r"""
    Accelerando rhythm-maker.

    ..  container:: example

        Makes accelerandi:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
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
            >>

    ..  container:: example

        Makes ritardandi:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 20), (1, 8), (1, 16)]),
        ...     rmakers.feather_beam(),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #left
                        c'16 * 5/8
                        [
                        c'16 * 43/64
                        c'16 * 51/64
                        c'16 * 65/64
                        c'16 * 85/64
                        c'16 * 25/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #left
                        c'16 * 5/8
                        [
                        c'16 * 43/64
                        c'16 * 51/64
                        c'16 * 65/64
                        c'16 * 85/64
                        c'16 * 25/16
                        ]
                    }
                    \revert TupletNumber.text
                }
            >>

    ..  container:: example

        REGRESSION. ``abjad.new()`` preserves commands:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.force_fraction()
        ... )

        >>> abjad.new(stack).commands
        [ForceFractionCommand()]

    ..  container:: example

        Sets duration bracket with no beams:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        c'16 * 63/32
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        c'16 * 117/64
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        c'16 * 63/32
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        c'16 * 117/64
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                    }
                    \revert TupletNumber.text
                }
            >>


    ..  container:: example

        Beams tuplets together without feathering:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.beam_groups(abjad.select().tuplets()),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 2
                        c'16 * 63/32
                        [
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 115/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 91/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 35/32
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 29/32
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 1
                        c'16 * 13/16
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        c'16 * 117/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 99/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 69/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 13/16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 1
                        c'16 * 47/64
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        c'16 * 63/32
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 115/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 91/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 35/32
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 29/32
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 1
                        c'16 * 13/16
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        c'16 * 117/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 99/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 69/64
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16 * 13/16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 0
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                }
            >>

        Leave feathering turned off here because LilyPond feathers conjoint
        beams poorly.

    ..  container:: example

        Ties across tuplets:

        >>> last_leaf = abjad.select().leaf(-1)
        >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.duration_bracket(),
        ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
        ...     rmakers.feather_beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ~
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ~
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ~
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
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
            >>

    ..  container:: example

        Ties across every other tuplet:

        >>> tuplets = abjad.select().tuplets().get([0], 2)
        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.duration_bracket(),
        ...     rmakers.tie(tuplets.map(last_leaf)),
        ...     rmakers.feather_beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ~
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ~
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
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
            >>

    ..  container:: example

        Forces rests at first and last leaves:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando(
        ...         [(1, 8), (1, 20), (1, 16)],
        ...         [(1, 20), (1, 8), (1, 16)],
        ...     ),
        ...     rmakers.force_rest(abjad.select().leaves().get([0, -1])),
        ...     rmakers.feather_beam(
        ...         beam_rests=True,
        ...         stemlet_length=0.75,
        ...     ),
        ...     rmakers.duration_bracket(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        \override Staff.Stem.stemlet-length = 0.75
                        r16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        \revert Staff.Stem.stemlet-length
                        c'16 * 13/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #left
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16 * 5/8
                        [
                        c'16 * 43/64
                        c'16 * 51/64
                        c'16 * 65/64
                        c'16 * 85/64
                        \revert Staff.Stem.stemlet-length
                        c'16 * 25/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        \revert Staff.Stem.stemlet-length
                        c'16 * 13/16
                        ]
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #left
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16 * 5/8
                        [
                        c'16 * 43/64
                        c'16 * 51/64
                        c'16 * 65/64
                        c'16 * 85/64
                        \revert Staff.Stem.stemlet-length
                        r16 * 25/16
                        ]
                    }
                    \revert TupletNumber.text
                }
            >>

    ..  container:: example

        Forces rests in every other tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
        ...     rmakers.force_rest(abjad.select().tuplets().get([1], 2)),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.extract_trivial(),
        ...     rmakers.duration_bracket(),
        ...     rmakers.feather_beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                    }
                    \revert TupletNumber.text
                    r4.
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                    }
                    \revert TupletNumber.text
                    r4.
                }
            >>

    Set interpolations' ``written_duration`` to ``1/16`` or less for multiple
    beams.
    """

    ### CLASS VARIABLES ###

    __slots__ = ("_exponent", "_interpolations")

    ### INITIALIZER ###

    def __init__(
        self,
        interpolations: typing.Union[
            _specifiers.Interpolation,
            typing.Sequence[_specifiers.Interpolation],
        ] = None,
        spelling: _specifiers.Spelling = None,
        tag: abjad.Tag = None,
    ) -> None:
        RhythmMaker.__init__(self, spelling=spelling, tag=tag)
        if isinstance(interpolations, _specifiers.Interpolation):
            interpolations = (interpolations,)
        if interpolations is not None:
            for interpolation in interpolations:
                if not isinstance(interpolation, _specifiers.Interpolation):
                    raise TypeError(interpolation)
            interpolations = tuple(interpolations)
        self._interpolations = interpolations

    ### PRIVATE METHODS ###

    @staticmethod
    def _fix_rounding_error(selection, total_duration, interpolation):
        selection_duration = abjad.get.duration(selection)
        if not selection_duration == total_duration:
            needed_duration = total_duration - abjad.get.duration(selection[:-1])
            multiplier = needed_duration / interpolation.written_duration
            selection[-1].multiplier = multiplier

    def _get_interpolations(self):
        specifiers_ = self.interpolations
        if specifiers_ is None:
            specifiers_ = abjad.CyclicTuple([_specifiers.Interpolation()])
        elif isinstance(specifiers_, _specifiers.Interpolation):
            specifiers_ = abjad.CyclicTuple([specifiers_])
        else:
            specifiers_ = abjad.CyclicTuple(specifiers_)
        string = "divisions_consumed"
        divisions_consumed = self.previous_state.get(string, 0)
        specifiers_ = abjad.sequence(specifiers_).rotate(n=-divisions_consumed)
        specifiers_ = abjad.CyclicTuple(specifiers_)
        return specifiers_

    @staticmethod
    def _interpolate_cosine(y1, y2, mu) -> float:
        """
        Performs cosine interpolation of ``y1`` and ``y2`` with ``mu``
        ``[0, 1]`` normalized.

        ..  container:: example

            >>> rmakers.AccelerandoRhythmMaker._interpolate_cosine(
            ...     y1=0,
            ...     y2=1,
            ...     mu=0.5,
            ...     )
            0.49999999999999994

        """
        mu2 = (1 - math.cos(mu * math.pi)) / 2
        return y1 * (1 - mu2) + y2 * mu2

    @staticmethod
    def _interpolate_divide(
        total_duration, start_duration, stop_duration, exponent="cosine"
    ) -> typing.Union[str, typing.List[float]]:
        """
        Divides ``total_duration`` into durations computed from interpolating
        between ``start_duration`` and ``stop_duration``.

        ..  container:: example

            >>> rmakers.AccelerandoRhythmMaker._interpolate_divide(
            ...     total_duration=10,
            ...     start_duration=1,
            ...     stop_duration=1,
            ...     exponent=1,
            ...     )
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
            >>> sum(_)
            10.0

            >>> rmakers.AccelerandoRhythmMaker._interpolate_divide(
            ...     total_duration=10,
            ...     start_duration=5,
            ...     stop_duration=1,
            ...     )
            [4.798..., 2.879..., 1.326..., 0.995...]
            >>> sum(_)
            10.0

        Set ``exponent`` to ``'cosine'`` for cosine interpolation.

        Set ``exponent`` to a numeric value for exponential interpolation with
        ``exponent`` as the exponent.

        Scales resulting durations so that their sum equals ``total_duration``
        exactly.
        """
        if total_duration <= 0:
            message = "Total duration must be positive."
            raise ValueError(message)
        if start_duration <= 0 or stop_duration <= 0:
            message = "Both 'start_duration' and 'stop_duration'"
            message += " must be positive."
            raise ValueError(message)
        if total_duration < (stop_duration + start_duration):
            return "too small"
        durations = []
        total_duration = float(total_duration)
        partial_sum = 0.0
        while partial_sum < total_duration:
            if exponent == "cosine":
                duration = AccelerandoRhythmMaker._interpolate_cosine(
                    start_duration, stop_duration, partial_sum / total_duration
                )
            else:
                duration = AccelerandoRhythmMaker._interpolate_exponential(
                    start_duration,
                    stop_duration,
                    partial_sum / total_duration,
                    exponent,
                )
            durations.append(duration)
            partial_sum += duration
        # scale result to fit total exaclty
        durations = [_ * total_duration / sum(durations) for _ in durations]
        return durations

    @staticmethod
    def _interpolate_divide_multiple(
        total_durations, reference_durations, exponent="cosine"
    ) -> typing.List[float]:
        """
        Interpolates ``reference_durations`` such that the sum of the
        resulting interpolated values equals the given ``total_durations``.

        ..  container:: example

            >>> class_ = rmakers.AccelerandoRhythmMaker
            >>> durations = class_._interpolate_divide_multiple(
            ...     total_durations=[100, 50],
            ...     reference_durations=[20, 10, 20],
            ...     )
            >>> for duration in durations:
            ...     duration
            19.448...
            18.520...
            16.227...
            13.715...
            11.748...
            10.487...
            9.8515...
            9.5130...
            10.421...
            13.073...
            16.991...

        The operation is the same as the interpolate_divide() method
        implemented on this class. But this function takes multiple
        total durations and multiple reference durations at one time.

        Precondition: ``len(totals_durations) == len(reference_durations)-1``.

        Set ``exponent`` to ``cosine`` for cosine interpolation. Set
        ``exponent`` to a number for exponential interpolation.
        """
        assert len(total_durations) == len(reference_durations) - 1
        durations = []
        for i in range(len(total_durations)):
            durations_ = AccelerandoRhythmMaker._interpolate_divide(
                total_durations[i],
                reference_durations[i],
                reference_durations[i + 1],
                exponent,
            )
            for duration_ in durations_:
                assert isinstance(duration_, float)
                durations.append(duration_)
        return durations

    @staticmethod
    def _interpolate_exponential(y1, y2, mu, exponent=1) -> float:
        """
        Interpolates between ``y1`` and ``y2`` at position ``mu``.

        ..  container:: example

            Exponents equal to 1 leave durations unscaled:

            >>> class_ = rmakers.AccelerandoRhythmMaker
            >>> for mu in (0, 0.25, 0.5, 0.75, 1):
            ...     class_._interpolate_exponential(100, 200, mu, exponent=1)
            ...
            100
            125.0
            150.0
            175.0
            200

            Exponents greater than 1 generate ritardandi:

            >>> class_ = rmakers.AccelerandoRhythmMaker
            >>> for mu in (0, 0.25, 0.5, 0.75, 1):
            ...     class_._interpolate_exponential(100, 200, mu, exponent=2)
            ...
            100
            106.25
            125.0
            156.25
            200

            Exponents less than 1 generate accelerandi:

            >>> class_ = rmakers.AccelerandoRhythmMaker
            >>> for mu in (0, 0.25, 0.5, 0.75, 1):
            ...     class_._interpolate_exponential(100, 200, mu, exponent=0.5)
            ...
            100.0
            150.0
            170.71067811865476
            186.60254037844388
            200.0

        """
        result = y1 * (1 - mu ** exponent) + y2 * mu ** exponent
        return result

    @classmethod
    def _make_accelerando(
        class_, total_duration, interpolations, index, *, tag: abjad.Tag = None
    ) -> abjad.Tuplet:
        """
        Makes notes with LilyPond multipliers equal to ``total_duration``.

        Total number of notes not specified: total duration is specified
        instead.

        Selects interpolation specifier at ``index`` in
        ``interpolations``.

        Computes duration multipliers interpolated from interpolation specifier
        start to stop.

        Sets note written durations according to interpolation specifier.
        multipliers.
        """
        total_duration = abjad.Duration(total_duration)
        interpolation = interpolations[index]
        durations = AccelerandoRhythmMaker._interpolate_divide(
            total_duration=total_duration,
            start_duration=interpolation.start_duration,
            stop_duration=interpolation.stop_duration,
        )
        if durations == "too small":
            maker = abjad.NoteMaker(tag=tag)
            notes = list(maker([0], [total_duration]))
            tuplet = abjad.Tuplet((1, 1), notes, tag=tag)
            selection = abjad.select([tuplet])
            return selection
        durations = class_._round_durations(durations, 2 ** 10)
        notes = []
        for i, duration in enumerate(durations):
            written_duration = interpolation.written_duration
            multiplier = duration / written_duration
            note = abjad.Note(0, written_duration, multiplier=multiplier, tag=tag)
            notes.append(note)
        selection = abjad.select(notes)
        class_._fix_rounding_error(selection, total_duration, interpolation)
        tuplet = abjad.Tuplet((1, 1), selection, tag=tag)
        return tuplet

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        tuplets = []
        interpolations = self._get_interpolations()
        for i, division in enumerate(divisions):
            tuplet = self._make_accelerando(division, interpolations, i, tag=self.tag)
            tuplets.append(tuplet)
        return tuplets

    @staticmethod
    def _round_durations(durations, denominator):
        durations_ = []
        for duration in durations:
            numerator = int(round(duration * denominator))
            duration_ = abjad.Duration(numerator, denominator)
            durations_.append(duration_)
        return durations_

    ### PUBLIC PROPERTIES ###

    @property
    def interpolations(
        self,
    ) -> typing.Optional[typing.List[_specifiers.Interpolation]]:
        r"""
        Gets interpolations.

        ..  container:: example

            Alternates accelerandi and ritardandi:

            >>> stack = rmakers.stack(
            ...     rmakers.accelerando(
            ...         [(1, 8), (1, 20), (1, 16)],
            ...         [(1, 20), (1, 8), (1, 16)],
            ...     ),
            ...     rmakers.feather_beam(),
            ...     rmakers.duration_bracket(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'2
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'4.
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            c'16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'2
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 63/32
                            [
                            c'16 * 115/64
                            c'16 * 91/64
                            c'16 * 35/32
                            c'16 * 29/32
                            c'16 * 13/16
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'4.
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #left
                            c'16 * 5/8
                            [
                            c'16 * 43/64
                            c'16 * 51/64
                            c'16 * 65/64
                            c'16 * 85/64
                            c'16 * 25/16
                            ]
                        }
                        \revert TupletNumber.text
                    }
                >>

        ..  container:: example

            Makes a single note in short division:

            >>> stack = rmakers.stack(
            ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
            ...     rmakers.feather_beam(),
            ...     rmakers.duration_bracket(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(5, 8), (3, 8), (1, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 3/8
                        s1 * 3/8
                        \time 1/8
                        s1 * 1/8
                    }
                    \new RhythmicStaff
                    {
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'2
                                        ~
                                        c'8
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
                            \once \override Beam.grow-direction = #right
                            c'16 * 61/32
                            [
                            c'16 * 115/64
                            c'16 * 49/32
                            c'16 * 5/4
                            c'16 * 33/32
                            c'16 * 57/64
                            c'16 * 13/16
                            c'16 * 25/32
                            ]
                        }
                        \revert TupletNumber.text
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'4.
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                        c'8
                    }
                >>

        """
        if self._interpolations is not None:
            return list(self._interpolations)
        return None

    @property
    def state(self) -> abjad.OrderedDict:
        r"""
        Gets state dictionary.

        ..  container:: example

            Consumes 3 divisions:

            >>> stack = rmakers.stack(
            ...     rmakers.accelerando(
            ...         [(1, 8), (1, 20), (1, 16)],
            ...         [(1, 20), (1, 8), (1, 16)],
            ...         ),
            ...     rmakers.feather_beam(),
            ...     rmakers.duration_bracket(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'4.
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'2
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'4.
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                >>

            >>> state = stack.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 3),
                    ('logical_ties_produced', 17),
                    ]
                )

            Advances 3 divisions; then consumes another 3 divisions:

            >>> divisions = [(4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions, previous_state=state)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                    }
                    \new RhythmicStaff
                    {
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'2
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'4.
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'2
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                >>

            >>> state = stack.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 6),
                    ('logical_ties_produced', 36),
                    ]
                )

            Advances 6 divisions; then consumes another 3 divisions:

            >>> divisions = [(3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions, previous_state=state)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'4.
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'2
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                            {
                                \new Score
                                \with
                                {
                                    \override SpacingSpanner.spacing-increment = 0.5
                                    proportionalNotationDuration = ##f
                                }
                                <<
                                    \new RhythmicStaff
                                    \with
                                    {
                                        \remove Time_signature_engraver
                                        \remove Staff_symbol_engraver
                                        \override Stem.direction = #up
                                        \override Stem.length = 5
                                        \override TupletBracket.bracket-visibility = ##t
                                        \override TupletBracket.direction = #up
                                        \override TupletBracket.minimum-length = 4
                                        \override TupletBracket.padding = 1.25
                                        \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                        \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                        \override TupletNumber.font-size = 0
                                        \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                        tupletFullLength = ##t
                                    }
                                    {
                                        c'4.
                                    }
                                >>
                                \layout {
                                    indent = 0
                                    ragged-right = ##t
                                }
                            }
                        \times 1/1 {
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
                >>

            >>> state = stack.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 9),
                    ('logical_ties_produced', 53),
                    ]
                )

        """
        return super().state

    @property
    def tag(self) -> typing.Optional[abjad.Tag]:
        r"""
        Gets tag.

        ..  container:: example

            Tags LilyPond output:

            >>> stack = rmakers.stack(
            ...     rmakers.accelerando([(1, 8), (1, 20), (1, 16)]),
            ...     rmakers.feather_beam(),
            ...     rmakers.duration_bracket(),
            ...     tag=abjad.Tag("ACCELERANDO_RHYTHM_MAKER"),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> string = abjad.lilypond(lilypond_file[abjad.Score], tags=True)
            >>> string = abjad.LilyPondFormatManager.align_tags(string, 30)
            >>> print(string)
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
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {          %! ACCELERANDO_RHYTHM_MAKER
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32      %! ACCELERANDO_RHYTHM_MAKER
                        [                 %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 115/64     %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 91/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 35/32      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 29/32      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16      %! ACCELERANDO_RHYTHM_MAKER
                        ]                 %! ACCELERANDO_RHYTHM_MAKER
                    }                     %! ACCELERANDO_RHYTHM_MAKER
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {          %! ACCELERANDO_RHYTHM_MAKER
                        \once \override Beam.grow-direction = #right
                        c'16 * 117/64     %! ACCELERANDO_RHYTHM_MAKER
                        [                 %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 99/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 69/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 47/64      %! ACCELERANDO_RHYTHM_MAKER
                        ]                 %! ACCELERANDO_RHYTHM_MAKER
                    }                     %! ACCELERANDO_RHYTHM_MAKER
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'2
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {          %! ACCELERANDO_RHYTHM_MAKER
                        \once \override Beam.grow-direction = #right
                        c'16 * 63/32      %! ACCELERANDO_RHYTHM_MAKER
                        [                 %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 115/64     %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 91/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 35/32      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 29/32      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16      %! ACCELERANDO_RHYTHM_MAKER
                        ]                 %! ACCELERANDO_RHYTHM_MAKER
                    }                     %! ACCELERANDO_RHYTHM_MAKER
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \new Score
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \new RhythmicStaff
                                \with
                                {
                                    \remove Time_signature_engraver
                                    \remove Staff_symbol_engraver
                                    \override Stem.direction = #up
                                    \override Stem.length = 5
                                    \override TupletBracket.bracket-visibility = ##t
                                    \override TupletBracket.direction = #up
                                    \override TupletBracket.minimum-length = 4
                                    \override TupletBracket.padding = 1.25
                                    \override TupletBracket.shorten-pair = #'(-1 . -1.5)
                                    \override TupletBracket.springs-and-rods = #ly:spanner::set-spacing-rods
                                    \override TupletNumber.font-size = 0
                                    \override TupletNumber.text = #tuplet-number::calc-fraction-text
                                    tupletFullLength = ##t
                                }
                                {
                                    c'4.
                                }
                            >>
                            \layout {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1 {          %! ACCELERANDO_RHYTHM_MAKER
                        \once \override Beam.grow-direction = #right
                        c'16 * 117/64     %! ACCELERANDO_RHYTHM_MAKER
                        [                 %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 99/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 69/64      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16      %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 47/64      %! ACCELERANDO_RHYTHM_MAKER
                        ]                 %! ACCELERANDO_RHYTHM_MAKER
                    }                     %! ACCELERANDO_RHYTHM_MAKER
                    \revert TupletNumber.text
                }
            >>

        """
        return super().tag


class EvenDivisionRhythmMaker(RhythmMaker):
    r"""
    Even division rhythm-maker.

    ..  container:: example

        Forces tuplet diminution:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[0, 0, 1]),
        ...     rmakers.force_diminution(),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(5, 16), (6, 16), (6, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 5/16
                    s1 * 5/16
                    \time 6/16
                    s1 * 3/8
                    \time 6/16
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/8 {
                        c'4
                        c'4
                    }
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        Forces tuplet augmentation:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[0, 0, 1]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ...     rmakers.force_augmentation(),
        ... )
        >>> divisions = [(5, 16), (6, 16), (6, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 5/16
                    s1 * 5/16
                    \time 6/16
                    s1 * 3/8
                    \time 6/16
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4 {
                        c'8
                        [
                        c'8
                        ]
                    }
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2 {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>


    ..  container:: example

        Ties nonlast tuplets:

        >>> last_leaf = abjad.select().leaf(-1)
        >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4 {
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4 {
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ~
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        (Equivalent to earlier tie-across-divisions pattern.)

    ..  container:: example

        Forces rest at every third logical tie:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.force_rest(
        ...         abjad.select().logical_ties().get([0], 3),
        ...     ),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4 {
                        r8
                        c'8
                        [
                        c'8
                        ]
                        r8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
                        c'8
                        [
                        c'8
                        ]
                        r8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4 {
                        c'8
                        [
                        c'8
                        ]
                        r8
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
                        c'8
                        r8
                        c'8
                    }
                }
            >>

        Forces rest at every fourth logical tie:

        >>> last_leaf = abjad.select().leaf(-1)
        >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
        ...     rmakers.force_rest(
        ...         abjad.select().logical_ties().get([3], 4),
        ...     ),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        r8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
                        r8
                        c'8
                        [
                        c'8
                        ~
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4 {
                        c'8
                        [
                        c'8
                        ]
                        r8
                        c'8
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        (Forcing rests at the fourth logical tie produces two rests.
        Forcing rests at the eighth logical tie produces only one rest.)

        Forces rest at leaf 0 of every tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8]),
        ...     rmakers.force_rest(
        ...         abjad.select().tuplets().map(abjad.select().leaf(0))
        ...     ),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
                        r8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4 {
                        r8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3 {
                        r8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4 {
                        r8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Forces rest and rewrites every other tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.force_rest(
        ...         abjad.select().tuplets().get([0], 2),
        ...     ),
        ...     rmakers.rewrite_rest_filled(),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                    r2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        (Equivalent to ealier silence pattern.)

    ..  container:: example

        Ties and rewrites every other tuplet:

        >>> tuplets = abjad.select().tuplets().get([0], 2)
        >>> nonlast_notes = abjad.select().notes()[:-1]
        >>> selector = tuplets.map(nonlast_notes)
        >>> stack = rmakers.stack(
        ...     rmakers.even_division([8], extra_counts=[1]),
        ...     rmakers.tie(selector),
        ...     rmakers.rewrite_sustained(),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                    c'2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        (Equivalent to earlier sustain pattern.)

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_denominator", "_denominators", "_extra_counts")

    ### INITIALIZER ###

    def __init__(
        self,
        denominator: typing.Union[str, int] = "from_counts",
        # TODO: make mandatory:
        denominators: typing.Sequence[int] = [8],
        extra_counts: typing.Sequence[int] = None,
        spelling: _specifiers.Spelling = None,
        tag: abjad.Tag = None,
    ) -> None:
        RhythmMaker.__init__(self, spelling=spelling, tag=tag)
        assert abjad.math.all_are_nonnegative_integer_powers_of_two(denominators), repr(
            denominators
        )
        denominators = tuple(denominators)
        self._denominators: typing.Tuple[int, ...] = denominators
        if extra_counts is not None:
            if not abjad.math.all_are_integer_equivalent(extra_counts):
                message = "must be integer sequence:\n"
                message += f"    {repr(extra_counts)}"
                raise Exception(message)
            extra_counts = [int(_) for _ in extra_counts]
            extra_counts = tuple(extra_counts)
        self._extra_counts = extra_counts
        extra_counts = extra_counts or (0,)
        self._denominator = denominator

    ### PRIVATE METHODS ###

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        tuplets = []
        divisions_consumed = self.previous_state.get("divisions_consumed", 0)
        divisions = [abjad.NonreducedFraction(_) for _ in divisions]
        denominators = abjad.sequence(self.denominators)
        denominators = denominators.rotate(-divisions_consumed)
        denominators = abjad.CyclicTuple(denominators)
        extra_counts_ = self.extra_counts or [0]
        extra_counts = abjad.sequence(extra_counts_)
        extra_counts = extra_counts.rotate(-divisions_consumed)
        extra_counts = abjad.CyclicTuple(extra_counts)
        for i, division in enumerate(divisions):
            if not abjad.math.is_positive_integer_power_of_two(division.denominator):
                message = "non-power-of-two divisions not implemented:"
                message += f" {division}."
                raise Exception(message)
            denominator_ = denominators[i]
            extra_count = extra_counts[i]
            basic_duration = abjad.Duration(1, denominator_)
            unprolated_note_count = None
            maker = abjad.NoteMaker(tag=self.tag)
            if division < 2 * basic_duration:
                notes = maker([0], [division])
            else:
                unprolated_note_count = division / basic_duration
                unprolated_note_count = int(unprolated_note_count)
                unprolated_note_count = unprolated_note_count or 1
                if 0 < extra_count:
                    modulus = unprolated_note_count
                    extra_count = extra_count % modulus
                elif extra_count < 0:
                    modulus = int(math.ceil(unprolated_note_count / 2.0))
                    extra_count = abs(extra_count) % modulus
                    extra_count *= -1
                note_count = unprolated_note_count + extra_count
                durations = note_count * [basic_duration]
                notes = maker([0], durations)
                assert all(
                    _.written_duration.denominator == denominator_ for _ in notes
                )
            tuplet_duration = abjad.Duration(division)
            tuplet = abjad.Tuplet.from_duration(tuplet_duration, notes, tag=self.tag)
            if self.denominator == "from_counts" and unprolated_note_count is not None:
                denominator = unprolated_note_count
                tuplet.denominator = denominator
            elif isinstance(self.denominator, int):
                tuplet.denominator = self.denominator
            tuplets.append(tuplet)
        assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
        return tuplets

    ### PUBLIC PROPERTIES ###

    @property
    def denominator(self) -> typing.Union[str, int]:
        r"""
        Gets preferred denominator.

        ..  container:: example

            No preferred denominator:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division([16], extra_counts=[4], denominator=None),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        \times 2/3 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 2/3 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            Expresses tuplet ratios in the usual way with numerator and
            denominator relatively prime.

        ..  container:: example

            Preferred denominator equal to 4:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division(
            ...         [16], extra_counts=[4], denominator=4
            ...     ),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        \times 4/6 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 4/6 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            Preferred denominator equal to 8:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division(
            ...         [16], extra_counts=[4], denominator=8
            ...     ),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        \times 8/12 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 8/12 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            Preferred denominator equal to 16:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division(
            ...         [16], extra_counts=[4], denominator=16
            ...     ),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        \times 16/24 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 16/24 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Preferred denominator taken from count of elements in tuplet:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division(
            ...         [16], extra_counts=[4], denominator="from_counts"
            ...     ),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        \times 8/12 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/10 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 8/12 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/10 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        """
        return self._denominator

    @property
    def denominators(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets denominators.

        ..  container:: example

            Fills tuplets with 16th notes and 8th notes, alternately:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division([16, 8]),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 16), (3, 8), (3, 4)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/16
                        s1 * 3/16
                        \time 3/8
                        s1 * 3/8
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                >>

        ..  container:: example

            Fills tuplets with 8th notes:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division([8]),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 16), (3, 8), (3, 4)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/16
                        s1 * 3/16
                        \time 3/8
                        s1 * 3/8
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'8.
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        c'8
                        c'8
                        ]
                    }
                >>

            (Fills tuplets less than twice the duration of an eighth note with
            a single attack.)

            Fills tuplets with quarter notes:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division([4]),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 16), (3, 8), (3, 4)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/16
                        s1 * 3/16
                        \time 3/8
                        s1 * 3/8
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'8.
                        c'4.
                        c'4
                        c'4
                        c'4
                    }
                >>

            (Fills tuplets less than twice the duration of a quarter note with
            a single attack.)

            Fills tuplets with half notes:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division([2]),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 16), (3, 8), (3, 4)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/16
                        s1 * 3/16
                        \time 3/8
                        s1 * 3/8
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'8.
                        c'4.
                        c'2.
                    }
                >>

            (Fills tuplets less than twice the duration of a half note with a
            single attack.)

        """
        if self._denominators:
            return list(self._denominators)
        return None

    @property
    def extra_counts(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets extra counts.

        ..  container:: example

            Adds extra counts to tuplets according to a pattern of three
            elements:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division([16], extra_counts=[0, 1, 2]),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/8 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            **Modular handling of positive values.** Denote by
            ``unprolated_note_count`` the number counts included in a tuplet
            when ``extra_counts`` is set to zero. Then extra
            counts equals ``extra_counts %
            unprolated_note_count`` when ``extra_counts`` is
            positive.

            This is likely to be intuitive; compare with the handling of
            negative values, below.

            For positive extra counts, the modulus of transformation of a
            tuplet with six notes is six:

            >>> import math
            >>> unprolated_note_count = 6
            >>> modulus = unprolated_note_count
            >>> extra_counts = list(range(12))
            >>> labels = []
            >>> for count in extra_counts:
            ...     modular_count = count % modulus
            ...     label = f"{count:3} becomes {modular_count:2}"
            ...     labels.append(label)

            Which produces the following pattern of changes:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division([16], extra_counts=extra_counts),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = 12 * [(6, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> staff = lilypond_file[abjad.Staff]
            >>> abjad.override(staff).TextScript.staff_padding = 7
            >>> groups = abjad.select(staff).leaves().group_by_measure()
            >>> for group, label in zip(groups, labels):
            ...     markup = abjad.Markup(label, direction=abjad.Up)
            ...     abjad.attach(markup, group[0])
            ...

            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    \with
                    {
                        \override TextScript.staff-padding = 7
                    }
                    {
                        c'16
                        ^ \markup { 0 becomes 0 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            ^ \markup { 1 becomes 1 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/8 {
                            c'16
                            ^ \markup { 2 becomes 2 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 6/9 {
                            c'16
                            ^ \markup { 3 becomes 3 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/10 {
                            c'16
                            ^ \markup { 4 becomes 4 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/11 {
                            c'16
                            ^ \markup { 5 becomes 5 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        ^ \markup { 6 becomes 0 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            ^ \markup { 7 becomes 1 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/8 {
                            c'16
                            ^ \markup { 8 becomes 2 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \times 6/9 {
                            c'16
                            ^ \markup { 9 becomes 3 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/10 {
                            c'16
                            ^ \markup { 10 becomes 4 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/11 {
                            c'16
                            ^ \markup { 11 becomes 5 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            This modular formula ensures that rhythm-maker ``denominators`` are
            always respected: a very large number of extra counts never causes
            a ``16``-denominated tuplet to result in 32nd- or 64th-note
            rhythms.

        ..  container:: example

            **Modular handling of negative values.** Denote by
            ``unprolated_note_count`` the number of counts included in a tuplet
            when ``extra_counts`` is set to zero. Further, let
            ``modulus = ceiling(unprolated_note_count / 2)``. Then extra counts
            equals ``-(abs(extra_counts) % modulus)`` when
            ``extra_counts`` is negative.

            For negative extra counts, the modulus of transformation of a
            tuplet with six notes is three:

            >>> import math
            >>> unprolated_note_count = 6
            >>> modulus = math.ceil(unprolated_note_count / 2)
            >>> extra_counts = [0, -1, -2, -3, -4, -5, -6, -7, -8]
            >>> labels = []
            >>> for count in extra_counts:
            ...     modular_count = -(abs(count) % modulus)
            ...     label = f"{count:3} becomes {modular_count:2}"
            ...     labels.append(label)

            Which produces the following pattern of changes:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division([16], extra_counts=extra_counts),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = 9 * [(6, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> staff = lilypond_file[abjad.Staff]
            >>> abjad.override(staff).TextScript.staff_padding = 8
            >>> groups = abjad.select(staff).leaves().group_by_measure()
            >>> for group, label in zip(groups, labels):
            ...     markup = abjad.Markup(label, direction=abjad.Up)
            ...     abjad.attach(markup, group[0])
            ...

            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                        \time 6/16
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    \with
                    {
                        \override TextScript.staff-padding = 8
                    }
                    {
                        c'16
                        ^ \markup { 0 becomes 0 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            ^ \markup { -1 becomes -1 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/4 {
                            c'16
                            ^ \markup { -2 becomes -2 }
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        ^ \markup { -3 becomes 0 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            ^ \markup { -4 becomes -1 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/4 {
                            c'16
                            ^ \markup { -5 becomes -2 }
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        ^ \markup { -6 becomes 0 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            ^ \markup { -7 becomes -1 }
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/4 {
                            c'16
                            ^ \markup { -8 becomes -2 }
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            This modular formula ensures that rhythm-maker ``denominators`` are
            always respected: a very small number of extra counts never causes
            a ``16``-denominated tuplet to result in 8th- or quarter-note
            rhythms.

        """
        if self._extra_counts:
            return list(self._extra_counts)
        return None

    @property
    def state(self) -> abjad.OrderedDict:
        r"""
        Gets state dictionary.

        ..  container:: example

            Fills divisions with 16th, 8th, quarter notes. Consumes 5:

            >>> stack = rmakers.stack(
            ...     rmakers.even_division([16, 8, 4], extra_counts=[0, 1]),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        \times 4/5 {
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
                >>

            >>> state = stack.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 5),
                    ('logical_ties_produced', 15),
                    ]
                )

            Advances 5 divisions; then consumes another 5 divisions:

            >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
            >>> selection = stack(divisions, previous_state=state)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        \time 2/8
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \times 2/3 {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        \times 4/5 {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            >>> state = stack.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 10),
                    ('logical_ties_produced', 29),
                    ]
                )

        """
        return super().state


class IncisedRhythmMaker(RhythmMaker):
    r"""
    Incised rhythm-maker.

    ..  container:: example

        Forces rest at every other tuplet:

        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=16,
        ...     ),
        ...     rmakers.force_rest(
        ...         abjad.select().logical_ties().get([1], 2),
        ...     ),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    r16
                    r4..
                    c'4.
                    r2
                    c'4
                    ~
                    c'16
                    r16
                }
            >>

    ..  container:: example

        Ties nonlast tuplets:

        >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         outer_divisions_only=True,
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...         ),
        ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 8/8
                    s1 * 1
                    \time 4/8
                    s1 * 1/2
                    \time 6/8
                    s1 * 3/4
                }
                \new RhythmicStaff
                {
                    r8
                    c'2..
                    ~
                    c'2
                    ~
                    c'2
                    ~
                    c'8
                    r8
                }
            >>

    ..  container:: example

        Repeat-ties nonfirst tuplets:

        >>> nonfirst_tuplets = abjad.select().tuplets()[1:]
        >>> first_leaf = abjad.select().leaf(0)
        >>> stack = rmakers.stack(
        ...     rmakers.incised(
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         outer_divisions_only=True,
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...         ),
        ...     rmakers.repeat_tie(nonfirst_tuplets.map(first_leaf)),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 8/8
                    s1 * 1
                    \time 4/8
                    s1 * 1/2
                    \time 6/8
                    s1 * 3/4
                }
                \new RhythmicStaff
                {
                    r8
                    c'2..
                    c'2
                    \repeatTie
                    c'2
                    \repeatTie
                    ~
                    c'8
                    r8
                }
            >>

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_extra_counts", "_incise")

    ### INITIALIZER ###

    def __init__(
        self,
        extra_counts: typing.Sequence[int] = None,
        incise: _specifiers.Incise = None,
        spelling: _specifiers.Spelling = None,
        tag: abjad.Tag = None,
    ) -> None:
        RhythmMaker.__init__(self, spelling=spelling, tag=tag)
        prototype = (_specifiers.Incise, type(None))
        assert isinstance(incise, prototype)
        self._incise = incise
        if extra_counts is not None:
            extra_counts = tuple(extra_counts)
        assert (
            extra_counts is None
            or abjad.math.all_are_nonnegative_integer_equivalent_numbers(extra_counts)
        ), extra_counts
        self._extra_counts = extra_counts

    ### PRIVATE METHODS ###

    def _get_incise_specifier(self):
        if self.incise is not None:
            return self.incise
        return _specifiers.Incise()

    def _make_division_incised_numeric_map(
        self,
        divisions=None,
        prefix_talea=None,
        prefix_counts=None,
        suffix_talea=None,
        suffix_counts=None,
        extra_counts=None,
    ):
        numeric_map, prefix_talea_index, suffix_talea_index = [], 0, 0
        for pair_index, division in enumerate(divisions):
            prefix_length = prefix_counts[pair_index]
            suffix_length = suffix_counts[pair_index]
            start = prefix_talea_index
            stop = prefix_talea_index + prefix_length
            prefix = prefix_talea[start:stop]
            start = suffix_talea_index
            stop = suffix_talea_index + suffix_length
            suffix = suffix_talea[start:stop]
            prefix_talea_index += prefix_length
            suffix_talea_index += suffix_length
            prolation_addendum = extra_counts[pair_index]
            if isinstance(division, tuple):
                numerator = division[0] + (prolation_addendum % division[0])
            else:
                numerator = division.numerator + (
                    prolation_addendum % division.numerator
                )
            numeric_map_part = self._make_numeric_map_part(numerator, prefix, suffix)
            numeric_map.append(numeric_map_part)
        return numeric_map

    def _make_middle_of_numeric_map_part(self, middle):
        incise = self._get_incise_specifier()
        if not (incise.fill_with_rests):
            if not incise.outer_divisions_only:
                if 0 < middle:
                    if incise.body_ratio is not None:
                        shards = middle / incise.body_ratio
                        return tuple(shards)
                    else:
                        return (middle,)
                else:
                    return ()
            elif incise.outer_divisions_only:
                if 0 < middle:
                    return (middle,)
                else:
                    return ()
            else:
                raise Exception("must incise divisions or output.")
        else:
            if not incise.outer_divisions_only:
                if 0 < middle:
                    return (-abs(middle),)
                else:
                    return ()
            elif incise.outer_divisions_only:
                if 0 < middle:
                    return (-abs(middle),)
                else:
                    return ()
            else:
                raise Exception("must incise divisions or output.")

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        input_ = self._prepare_input()
        prefix_talea = input_[0]
        prefix_counts = input_[1]
        suffix_talea = input_[2]
        suffix_counts = input_[3]
        extra_counts = input_[4]
        counts = {
            "prefix_talea": prefix_talea,
            "suffix_talea": suffix_talea,
            "extra_counts": extra_counts,
        }
        if self.incise is not None:
            talea_denominator = self.incise.talea_denominator
        else:
            talea_denominator = None
        result = self._scale_counts(divisions, talea_denominator, counts)
        divisions = result["divisions"]
        lcd = result["lcd"]
        counts = result["counts"]
        incise = self._get_incise_specifier()
        if not incise.outer_divisions_only:
            numeric_map = self._make_division_incised_numeric_map(
                divisions,
                counts["prefix_talea"],
                prefix_counts,
                counts["suffix_talea"],
                suffix_counts,
                counts["extra_counts"],
            )
        else:
            assert incise.outer_divisions_only
            numeric_map = self._make_output_incised_numeric_map(
                divisions,
                counts["prefix_talea"],
                prefix_counts,
                counts["suffix_talea"],
                suffix_counts,
                counts["extra_counts"],
            )
        selections = self._numeric_map_to_leaf_selections(numeric_map, lcd)
        tuplets = self._make_tuplets(divisions, selections)
        assert all(isinstance(_, abjad.Tuplet) for _ in tuplets)
        return tuplets

    def _make_numeric_map_part(self, numerator, prefix, suffix, is_note_filled=True):
        prefix_weight = abjad.math.weight(prefix)
        suffix_weight = abjad.math.weight(suffix)
        middle = numerator - prefix_weight - suffix_weight
        if numerator < prefix_weight:
            weights = [numerator]
            prefix = abjad.sequence(prefix)
            prefix = prefix.split(weights, cyclic=False, overhang=False)[0]
        middle = self._make_middle_of_numeric_map_part(middle)
        suffix_space = numerator - prefix_weight
        if suffix_space <= 0:
            suffix = ()
        elif suffix_space < suffix_weight:
            weights = [suffix_space]
            suffix = abjad.sequence(suffix)
            suffix = suffix.split(weights, cyclic=False, overhang=False)[0]
        numeric_map_part = prefix + middle + suffix
        return [abjad.Duration(_) for _ in numeric_map_part]

    def _make_output_incised_numeric_map(
        self,
        divisions,
        prefix_talea,
        prefix_counts,
        suffix_talea,
        suffix_counts,
        extra_counts,
    ):
        numeric_map, prefix_talea_index, suffix_talea_index = [], 0, 0
        prefix_length, suffix_length = prefix_counts[0], suffix_counts[0]
        start = prefix_talea_index
        stop = prefix_talea_index + prefix_length
        prefix = prefix_talea[start:stop]
        start = suffix_talea_index
        stop = suffix_talea_index + suffix_length
        suffix = suffix_talea[start:stop]
        if len(divisions) == 1:
            prolation_addendum = extra_counts[0]
            if isinstance(divisions[0], abjad.NonreducedFraction):
                numerator = divisions[0].numerator
            else:
                numerator = divisions[0][0]
            numerator += prolation_addendum % numerator
            numeric_map_part = self._make_numeric_map_part(numerator, prefix, suffix)
            numeric_map.append(numeric_map_part)
        else:
            prolation_addendum = extra_counts[0]
            if isinstance(divisions[0], tuple):
                numerator = divisions[0][0]
            else:
                numerator = divisions[0].numerator
            numerator += prolation_addendum % numerator
            numeric_map_part = self._make_numeric_map_part(numerator, prefix, ())
            numeric_map.append(numeric_map_part)
            for i, division in enumerate(divisions[1:-1]):
                index = i + 1
                prolation_addendum = extra_counts[index]
                if isinstance(division, tuple):
                    numerator = division[0]
                else:
                    numerator = division.numerator
                numerator += prolation_addendum % numerator
                numeric_map_part = self._make_numeric_map_part(numerator, (), ())
                numeric_map.append(numeric_map_part)
            try:
                index = i + 2
                prolation_addendum = extra_counts[index]
            except UnboundLocalError:
                index = 1 + 2
                prolation_addendum = extra_counts[index]
            if isinstance(divisions[-1], tuple):
                numerator = divisions[-1][0]
            else:
                numerator = divisions[-1].numerator
            numerator += prolation_addendum % numerator
            numeric_map_part = self._make_numeric_map_part(numerator, (), suffix)
            numeric_map.append(numeric_map_part)
        return numeric_map

    def _numeric_map_to_leaf_selections(self, numeric_map, lcd):
        selections = []
        specifier = self._get_spelling_specifier()
        for numeric_map_part in numeric_map:
            numeric_map_part = [_ for _ in numeric_map_part if _ != abjad.Duration(0)]
            selection = self._make_leaves_from_talea(
                numeric_map_part,
                lcd,
                forbidden_note_duration=specifier.forbidden_note_duration,
                forbidden_rest_duration=specifier.forbidden_rest_duration,
                increase_monotonic=specifier.increase_monotonic,
                tag=self.tag,
            )
            selections.append(selection)
        return selections

    def _prepare_input(self):
        #
        incise = self._get_incise_specifier()
        prefix_talea = incise.prefix_talea or ()
        prefix_talea = abjad.CyclicTuple(prefix_talea)
        #
        prefix_counts = incise.prefix_counts or (0,)
        prefix_counts = abjad.CyclicTuple(prefix_counts)
        #
        suffix_talea = incise.suffix_talea or ()
        suffix_talea = abjad.CyclicTuple(suffix_talea)
        #
        suffix_counts = incise.suffix_counts or (0,)
        suffix_counts = abjad.CyclicTuple(suffix_counts)
        #
        extra_counts = self.extra_counts or ()
        if extra_counts:
            extra_counts = abjad.CyclicTuple(extra_counts)
        else:
            extra_counts = abjad.CyclicTuple([0])
        #
        return (
            prefix_talea,
            prefix_counts,
            suffix_talea,
            suffix_counts,
            extra_counts,
        )

    ### PUBLIC PROPERTIES ###

    @property
    def extra_counts(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets extra counts.

        ..  container:: example

            Add one extra count per tuplet:

            >>> stack = rmakers.stack(
            ...     rmakers.incised(
            ...         extra_counts=[1],
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.force_augmentation(),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 16/9 {
                            r16
                            c'2
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 8/5 {
                            c'4
                            ~
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/7 {
                            c'4.
                            r16
                        }
                    }
                >>

        """
        if self._extra_counts:
            return list(self._extra_counts)
        return None

    @property
    def incise(self) -> typing.Optional[_specifiers.Incise]:
        r"""
        Gets incise specifier.


        ..  container:: example

            >>> stack = rmakers.stack(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[0, 1],
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=16,
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = 4 * [(5, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        r16
                        r16
                        c'8.
                        r16
                        c'4
                        r16
                        r16
                        c'8.
                        r16
                    }
                >>

        ..  container:: example

            Fills divisions with notes. Incises outer divisions only:

            >>> stack = rmakers.stack(
            ...     rmakers.incised(
            ...         prefix_talea=[-8, -7],
            ...         prefix_counts=[2],
            ...         suffix_talea=[-3],
            ...         suffix_counts=[4],
            ...         talea_denominator=32,
            ...         outer_divisions_only=True,
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(5, 8), (5, 8), (5, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        r4
                        r8..
                        c'8
                        ~
                        [
                        c'32
                        ]
                        c'2
                        ~
                        c'8
                        c'4
                        r16.
                        r16.
                        r16.
                        r16.
                    }
                >>

        ..  container:: example

            Fills divisions with rests. Incises outer divisions only:

            >>> stack = rmakers.stack(
            ...     rmakers.incised(
            ...         prefix_talea=[7, 8],
            ...         prefix_counts=[2],
            ...         suffix_talea=[3],
            ...         suffix_counts=[4],
            ...         talea_denominator=32,
            ...         fill_with_rests=True,
            ...         outer_divisions_only=True,
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(5, 8), (5, 8), (5, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        c'8..
                        c'4
                        r8
                        r32
                        r2
                        r8
                        r4
                        c'16.
                        [
                        c'16.
                        c'16.
                        c'16.
                        ]
                    }
                >>

        """
        return self._incise

    @property
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        r"""
        Gets duration specifier.

        ..  container:: example

            Spells durations with the fewest number of glyphs:

            >>> stack = rmakers.stack(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        r8
                        c'2..
                        c'2
                        c'2
                        ~
                        c'8
                        r8
                    }
                >>

        ..  container:: example

            Forbids notes with written duration greater than or equal to
            ``1/2``:

            >>> stack = rmakers.stack(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         spelling=rmakers.Spelling(forbidden_note_duration=(1, 2)),
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        r8
                        c'4
                        ~
                        c'4
                        ~
                        c'4.
                        c'4
                        ~
                        c'4
                        c'4
                        ~
                        c'4
                        ~
                        c'8
                        r8
                    }
                >>

        ..  container:: example

            Rewrites meter:

            >>> stack = rmakers.stack(
            ...     rmakers.incised(
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     rmakers.rewrite_meter(),
            ... )
            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 8/8
                        s1 * 1
                        \time 4/8
                        s1 * 1/2
                        \time 6/8
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        r8
                        c'2..
                        c'2
                        c'4.
                        ~
                        c'4
                        r8
                    }
                >>

        """
        return super().spelling

    @property
    def tag(self) -> typing.Optional[abjad.Tag]:
        r"""
        Gets tag.

        ..  container:: example

            Makes augmentations:

            >>> stack = rmakers.stack(
            ...     rmakers.incised(
            ...         extra_counts=[1],
            ...         prefix_talea=[-1],
            ...         prefix_counts=[1],
            ...         outer_divisions_only=True,
            ...         suffix_talea=[-1],
            ...         suffix_counts=[1],
            ...         talea_denominator=8,
            ...         ),
            ...     rmakers.force_augmentation(),
            ...     rmakers.beam(),
            ...     tag=abjad.Tag("INCISED_RHYTHM_MAKER"),
            ... )
            >>> divisions = [(8, 8), (4, 8), (6, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> string = abjad.lilypond(lilypond_file[abjad.Score], tags=True)
            >>> string = abjad.LilyPondFormatManager.align_tags(string, 40)
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 8/8
                    s1 * 1
                    \time 4/8
                    s1 * 1/2
                    \time 6/8
                    s1 * 3/4
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text %! INCISED_RHYTHM_MAKER
                    \times 16/9 {                   %! INCISED_RHYTHM_MAKER
                        r16                         %! INCISED_RHYTHM_MAKER
                        c'2                         %! INCISED_RHYTHM_MAKER
                    }                               %! INCISED_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! INCISED_RHYTHM_MAKER
                    \times 8/5 {                    %! INCISED_RHYTHM_MAKER
                        c'4                         %! INCISED_RHYTHM_MAKER
                        ~
                        c'16                        %! INCISED_RHYTHM_MAKER
                    }                               %! INCISED_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! INCISED_RHYTHM_MAKER
                    \times 12/7 {                   %! INCISED_RHYTHM_MAKER
                        c'4.                        %! INCISED_RHYTHM_MAKER
                        r16                         %! INCISED_RHYTHM_MAKER
                    }                               %! INCISED_RHYTHM_MAKER
                }
            >>

        """
        return super().tag


class MultipliedDurationRhythmMaker(RhythmMaker):
    r"""
    Multiplied-duration rhythm-maker.

    ..  container:: example

        >>> rhythm_maker = rmakers.multiplied_duration()
        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> selections = rhythm_maker(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selections, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/4
                    s1 * 1/4
                    \time 3/16
                    s1 * 3/16
                    \time 5/8
                    s1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    s1 * 1/3
                }
                \new RhythmicStaff
                {
                    c'1 * 1/4
                    c'1 * 3/16
                    c'1 * 5/8
                    c'1 * 1/3
                }
            >>

    ..  container:: example

        >>> rhythm_maker = rmakers.multiplied_duration()
        >>> string = abjad.storage(rhythm_maker)
        >>> print(string)
        rmakers.MultipliedDurationRhythmMaker(
            prototype=abjad.Note,
            duration=abjad.Duration(1, 1),
            )

    """

    ### CLASS VARIABLES ###

    __slots__ = ("_duration", "_prototype")

    _prototypes = (abjad.MultimeasureRest, abjad.Note, abjad.Rest, abjad.Skip)

    ### INITIALIZER ###

    def __init__(
        self,
        prototype: typing.Type = abjad.Note,
        *,
        duration: abjad.DurationTyping = (1, 1),
        tag: abjad.Tag = None,
    ) -> None:
        RhythmMaker.__init__(self, tag=tag)
        if prototype not in self._prototypes:
            message = "must be note, (multimeasure) rest, skip:\n"
            message += f"   {repr(prototype)}"
            raise Exception(message)
        self._prototype = prototype
        duration = abjad.Duration(duration)
        self._duration = duration

    ### PRIVATE METHODS ###

    def _make_music(self, divisions) -> typing.List[abjad.Selection]:
        component: typing.Union[abjad.MultimeasureRest, abjad.Skip]
        components = []
        for division in divisions:
            assert isinstance(division, abjad.NonreducedFraction)
            multiplier = division / self.duration
            if self.prototype is abjad.Note:
                component = self.prototype(
                    "c'", self.duration, multiplier=multiplier, tag=self.tag
                )
            else:
                component = self.prototype(
                    self.duration, multiplier=multiplier, tag=self.tag
                )
            components.append(component)
        selection = abjad.select(components)
        return [selection]

    ### PUBLIC PROPERTIES ###

    @property
    def duration(self) -> abjad.Duration:
        r"""
        Gets (written) duration.

        ..  container:: example

            Makes multiplied-duration whole notes when ``duration`` is unset:

            >>> rhythm_maker = rmakers.multiplied_duration()
            >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/4
                        s1 * 1/4
                        \time 3/16
                        s1 * 3/16
                        \time 5/8
                        s1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        s1 * 1/3
                    }
                    \new RhythmicStaff
                    {
                        c'1 * 1/4
                        c'1 * 3/16
                        c'1 * 5/8
                        c'1 * 1/3
                    }
                >>

            Makes multiplied-duration half notes when ``duration=(1, 2)``:

            >>> rhythm_maker = rmakers.multiplied_duration(duration=(1, 2))
            >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/4
                        s1 * 1/4
                        \time 3/16
                        s1 * 3/16
                        \time 5/8
                        s1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        s1 * 1/3
                    }
                    \new RhythmicStaff
                    {
                        c'2 * 2/4
                        c'2 * 6/16
                        c'2 * 10/8
                        c'2 * 2/3
                    }
                >>

            Makes multiplied-duration quarter notes when ``duration=(1, 4)``:

            >>> rhythm_maker = rmakers.multiplied_duration(duration=(1, 4))
            >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/4
                        s1 * 1/4
                        \time 3/16
                        s1 * 3/16
                        \time 5/8
                        s1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        s1 * 1/3
                    }
                    \new RhythmicStaff
                    {
                        c'4 * 4/4
                        c'4 * 12/16
                        c'4 * 20/8
                        c'4 * 4/3
                    }
                >>

        """
        return self._duration

    @property
    def prototype(self) -> typing.Type:
        r"""
        Gets prototype.

        ..  container:: example

            Makes multiplied-duration notes when ``prototype`` is unset:

            >>> rhythm_maker = rmakers.multiplied_duration()
            >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/4
                        s1 * 1/4
                        \time 3/16
                        s1 * 3/16
                        \time 5/8
                        s1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        s1 * 1/3
                    }
                    \new RhythmicStaff
                    {
                        c'1 * 1/4
                        c'1 * 3/16
                        c'1 * 5/8
                        c'1 * 1/3
                    }
                >>

        ..  container:: example

            Makes multiplied-duration rests when ``prototype=abjad.Rest``:

            >>> rhythm_maker = rmakers.multiplied_duration(abjad.Rest)
            >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/4
                        s1 * 1/4
                        \time 3/16
                        s1 * 3/16
                        \time 5/8
                        s1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        s1 * 1/3
                    }
                    \new RhythmicStaff
                    {
                        r1 * 1/4
                        r1 * 3/16
                        r1 * 5/8
                        r1 * 1/3
                    }
                >>

        ..  container:: example

            Makes multiplied-duration multimeasures rests when
            ``prototype=abjad.MultimeasureRest``:

            >>> rhythm_maker = rmakers.multiplied_duration(
            ...     abjad.MultimeasureRest
            ... )
            >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/4
                        s1 * 1/4
                        \time 3/16
                        s1 * 3/16
                        \time 5/8
                        s1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        s1 * 1/3
                    }
                    \new RhythmicStaff
                    {
                        R1 * 1/4
                        R1 * 3/16
                        R1 * 5/8
                        R1 * 1/3
                    }
                >>

        ..  container:: example

            Makes multiplied-duration skips when ``prototype=abjad.Skip``:

            >>> rhythm_maker = rmakers.multiplied_duration(abjad.Skip)
            >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
            >>> selections = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selections, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/4
                        s1 * 1/4
                        \time 3/16
                        s1 * 3/16
                        \time 5/8
                        s1 * 5/8
                        #(ly:expect-warning "strange time signature found")
                        \time 1/3
                        s1 * 1/3
                    }
                    \new RhythmicStaff
                    {
                        s1 * 1/4
                        s1 * 3/16
                        s1 * 5/8
                        s1 * 1/3
                    }
                >>

        """
        return self._prototype


class NoteRhythmMaker(RhythmMaker):
    r"""
    Note rhtyhm-maker.

    ..  container:: example

        Silences every other logical tie:

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(
        ...         abjad.select().logical_ties().get([0], 2),
        ...     ),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select()),
        ... )

        >>> divisions = [(4, 8), (3, 8), (4, 8), (5, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(
        ...         abjad.select().logical_ties().get([0], 2)[1:-1],
        ...     ),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8), (2, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.beam(abjad.select().logical_ties(pitched=True)),
        ... )
        >>> divisions = [(5, 32), (5, 32)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.beam_groups(abjad.select().logical_ties()),
        ... )
        >>> divisions = [(5, 32), (5, 32)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.NoteRhythmMaker()
        >>> divisions = [(5, 32), (5, 32)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.NoteRhythmMaker()

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.tie(nonlast_lts.map(last_leaf)),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.tie(lts.map(last_leaf)),
        ... )
        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.untie(),
        ... )
        >>> divisions = [(7, 16), (1, 4), (5, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.NoteRhythmMaker()
        >>> divisions = [(5, 14), (3, 7)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \times 8/14 {
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_augmentation(),
        ... )
        >>> divisions = [(5, 14), (3, 7)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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
                    \times 16/14 {
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().logical_ties()[0]),
        ... )
        >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(abjad.select().logical_ties()[:2]),
        ... )
        >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

        >>> stack = rmakers.stack(
        ...     rmakers.note(),
        ...     rmakers.force_rest(
        ...         abjad.select().logical_ties().get([0, -1])
        ...     ),
        ... )
        >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
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

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ()

    ### INITIALIZER ###

    def __init__(
        self, spelling: _specifiers.Spelling = None, tag: abjad.Tag = None
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
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        r"""
        Gets duration specifier.

        ..  container:: example

            Spells durations with the fewest number of glyphs:

            >>> rhythm_maker = rmakers.NoteRhythmMaker()
            >>> divisions = [(5, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
            ... )
            >>> divisions = [(5, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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

            >>> stack = rmakers.stack(
            ...     rmakers.note(),
            ...     rmakers.rewrite_meter(),
            ... )
            >>> divisions = [(3, 4), (6, 16), (9, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
    def tag(self) -> typing.Optional[abjad.Tag]:
        r"""
        Gets tag.

        ..  container:: example

            >>> rhythm_maker = rmakers.NoteRhythmMaker(
            ...     tag=abjad.Tag("NOTE_RHYTHM_MAKER"),
            ... )
            >>> divisions = [(5, 8), (3, 8)]
            >>> selection = rhythm_maker(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> string = abjad.lilypond(lilypond_file[abjad.Score], tags=True)
            >>> print(string)
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


class TaleaRhythmMaker(RhythmMaker):
    r"""
        Talea rhythm-maker.

        ..  container:: example

            Repeats talea of 1/16, 2/16, 3/16, 4/16:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        c'8.
                        c'8
                        ]
                    }
                >>

        ..  container:: example

            Silences first and last logical ties:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([0, -1]),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        r8
                    }
                >>

        ..  container:: example

            Silences all logical ties. Then sustains first and last logical
            ties:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.force_rest(abjad.select().logical_ties()),
            ...     rmakers.force_note(
            ...         abjad.select().logical_ties().get([0, -1]),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        r8
                        r8.
                        r4
                        r16
                        r8
                        r16
                        r8
                        r4
                        r16
                        r8
                        r8.
                        c'8
                    }
                >>

        ..  container:: example

            REGRESSION. Nonperiodic rest commands respect state.

            Only logical ties 0 and 2 are rested here:

            >>> command = rmakers.stack(
            ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
            ...     rmakers.force_rest(
            ...         abjad.select().logical_ties().get([0, 2, 12]),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = command(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        r4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            r4
                            c'8.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'16
                            c'4
                            c'8.
                            ~
                        }
                        c'16
                        c'4
                        c'8.
                    }
                >>

            >>> state = command.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 4),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 8),
                    ('talea_weight_consumed', 31),
                    ]
                )

    # TODO: make this work again relatively soon
    #            Only logical tie 12 is rested here:
    #
    #            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
    #            >>> selection = command(divisions, previous_segment_stop_state=state)
    #            >>> lilypond_file = abjad.LilyPondFile.rhythm(
    #            ...     selection, divisions
    #            ... )
    #            >>> abjad.show(lilypond_file) # doctest: +SKIP
    #
    #            ..  docs::
    #
    #                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
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
    #            >>> state = command.state
    #            >>> string = abjad.storage(state)
    #            >>> print(string)
    #            abjad.OrderedDict(
    #                [
    #                    ('divisions_consumed', 8),
    #                    ('incomplete_last_note', True),
    #                    ('logical_ties_produced', 16),
    #                    ('talea_weight_consumed', 63),
    #                    ]
    #                )

    #        ..  container:: example
    #
    #            REGRESSION. Periodic rest commands also respect state.
    #
    #            >>> stack = rmakers.stack(
    #            ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
    #            ...     rmakers.force_rest(
    #            ...         abjad.select().logical_ties().get([3], 4),
    #            ...     ),
    #            ...     rmakers.beam(),
    #            ...     rmakers.extract_trivial(),
    #            ...     )
    #
    #            Incomplete last note is rested here:
    #
    #            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
    #            >>> selection = stack(divisions)
    #            >>> lilypond_file = abjad.LilyPondFile.rhythm(
    #            ...     selection, divisions
    #            ... )
    #            >>> abjad.show(lilypond_file) # doctest: +SKIP
    #
    #            ..  docs::
    #
    #                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
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
    #            >>> state = stack.maker.state
    #            >>> string = abjad.storage(state)
    #            >>> print(string)
    #            abjad.OrderedDict(
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
    #            >>> selection = stack(divisions, previous_state=state)
    #            >>> lilypond_file = abjad.LilyPondFile.rhythm(
    #            ...     selection, divisions
    #            ... )
    #            >>> abjad.show(lilypond_file) # doctest: +SKIP
    #
    #            ..  docs::
    #
    #                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
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
    #            >>> state = stack.maker.state
    #            >>> string = abjad.storage(state)
    #            >>> print(string)
    #            abjad.OrderedDict(
    #                [
    #                    ('divisions_consumed', 8),
    #                    ('incomplete_last_note', True),
    #                    ('logical_ties_produced', 16),
    #                    ('talea_weight_consumed', 63),
    #                    ]
    #                )

        ..  container:: example

            REGRESSION. Spells tuplet denominator in terms of duration when
            denominator is given as a duration:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[1, 1, 2, 2]),
            ...     rmakers.denominator((1, 16)),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            [
                            c'8
                            c'8.
                            c'16
                            ~
                            ]
                        }
                        \times 8/9 {
                            c'8.
                            [
                            c'16
                            c'8
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/8 {
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ~
                            ]
                        }
                        \times 8/10 {
                            c'8
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Beams each division:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1], 16),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                >>

        ..  container:: example

            Beams tuplets together:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1], 16),
            ...     rmakers.beam_groups(abjad.select().tuplets()),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 2
                        c'16
                        [
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 1
                        c'16
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 1
                        c'16
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 1
                        c'16
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 2
                        c'16
                        \set stemLeftBeamCount = 2
                        \set stemRightBeamCount = 0
                        c'16
                        ]
                    }
                >>

        ..  container:: example

            Beams nothing:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1], 16),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                        c'16
                    }
                >>

        ..  container:: example

            Does not beam rests:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 1, 1, -1], 16),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                        c'16
                        [
                        c'16
                        ]
                        c'16
                        r16
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                        c'16
                        [
                        c'16
                        ]
                        c'16
                        r16
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                        c'16
                        [
                        c'16
                        c'16
                        ]
                        r16
                    }
                >>

        ..  container:: example

            Does beam rests:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 1, 1, -1], 16),
            ...     rmakers.beam(beam_rests=True),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        r16
                        c'16
                        c'16
                        ]
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        r16
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        c'16
                        c'16
                        r16
                        ]
                    }
                >>

        ..  container:: example

            Beams rests with stemlets:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 1, 1, -1], 16),
            ...     rmakers.beam(
            ...         beam_rests=True,
            ...         stemlet_length=0.75,
            ...         ),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        \revert Staff.Stem.stemlet-length
                        c'16
                        ]
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        r16
                        c'16
                        \revert Staff.Stem.stemlet-length
                        c'16
                        ]
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        r16
                        c'16
                        c'16
                        c'16
                        \revert Staff.Stem.stemlet-length
                        r16
                        ]
                        \override Staff.Stem.stemlet-length = 0.75
                        c'16
                        [
                        c'16
                        c'16
                        r16
                        c'16
                        c'16
                        c'16
                        \revert Staff.Stem.stemlet-length
                        r16
                        ]
                    }
                >>

        ..  container:: example

            Does not tie across divisions:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([5, 3, 3, 3], 16),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                    }
                >>

        ..  container:: example

            Ties across divisions:

            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> stack = rmakers.stack(
            ...     rmakers.talea([5, 3, 3, 3], 16),
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ~
                        ]
                        c'8.
                        [
                        c'8.
                        ~
                        ]
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ~
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                    }
                >>

        ..  container:: example

            Ties across every other tuplet:

            >>> tuplets = abjad.select().tuplets().get([0], 2)
            >>> last_leaf = abjad.select().leaf(-1)
            >>> stack = rmakers.stack(
            ...     rmakers.talea([5, 3, 3, 3], 16),
            ...     rmakers.tie(tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ~
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ~
                        ]
                        c'8.
                        [
                        c'8.
                        ]
                    }
                >>

        ..  container:: example

            TIE-CONSECUTIVE-NOTES RECIPE:

            >>> nonlast_notes = abjad.select().notes()[:-1]
            >>> selector = abjad.select().runs()
            >>> selector = selector.map(nonlast_notes)
            >>> stack = rmakers.stack(
            ...     rmakers.talea([5, -3, 3, 3], 16),
            ...     rmakers.untie(selector),
            ...     rmakers.tie(selector),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
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
                        c'4
                        ~
                        c'16
                        r8.
                        c'8.
                        ~
                        [
                        c'8.
                        ~
                        ]
                        c'4
                        ~
                        c'16
                        r8.
                        c'8.
                        ~
                        [
                        c'8.
                        ]
                    }
                >>

        ..  container:: example

            REGRESSION. Commands survive new:

            >>> command = rmakers.stack(
            ...     rmakers.talea([5, -3, 3, 3], 16),
            ...     rmakers.extract_trivial(),
            ...     )
            >>> new_command = abjad.new(command)
            >>> string = abjad.storage(command)
            >>> print(string)
            rmakers.Stack(
                rmakers.TaleaRhythmMaker(
                    talea=rmakers.Talea(
                        [5, -3, 3, 3],
                        16
                        ),
                    ),
                ExtractTrivialCommand()
                )

            >>> command == new_command
            True

        ..  container:: example

            Working with ``denominator``.

            Reduces terms in tuplet ratio to relative primes when no tuplet
            command is given:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[1, 1, 2, 2]),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            [
                            c'8
                            c'8.
                            c'16
                            ~
                            ]
                        }
                        \times 8/9 {
                            c'8.
                            [
                            c'16
                            c'8
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ~
                            ]
                        }
                        \times 4/5 {
                            c'8
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ]
                        }
                    }
                >>

            REGRESSION. Spells tuplet denominator in terms of duration when
            denominator is given as a duration:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[1, 1, 2, 2]),
            ...     rmakers.denominator((1, 16)),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            [
                            c'8
                            c'8.
                            c'16
                            ~
                            ]
                        }
                        \times 8/9 {
                            c'8.
                            [
                            c'16
                            c'8
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/8 {
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ~
                            ]
                        }
                        \times 8/10 {
                            c'8
                            c'4
                            c'16
                            [
                            c'8
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Working with ``diminution``.

            Makes diminished tuplets when ``diminution`` is true (or when no
            tuplet command is given):

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1], 16, extra_counts=[0, -1]),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

            Makes augmented tuplets when ``diminution`` is set to false:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1], 16, extra_counts=[0, -1]),
            ...     rmakers.beam(),
            ...     rmakers.force_augmentation(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                        \time 1/4
                        s1 * 1/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 4/3 {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Working with ``trivialize``.

            Leaves trivializable tuplets as-is when no tuplet command is
            given. The tuplets in measures 2 and 4 can be written as trivial
            tuplets, but they are not:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([3, 3, 6, 6], 16, extra_counts=[0, 4]),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \times 2/3 {
                            c'4.
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \times 2/3 {
                            c'4.
                            c'4.
                        }
                    }
                >>

            Rewrites trivializable tuplets as trivial (1:1) tuplets when
            ``trivialize`` is true:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([3, 3, 6, 6], 16, extra_counts=[0, 4]),
            ...     rmakers.trivialize(),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'4
                        }
                    }
                >>

            REGRESSION #907a. Rewrites trivializable tuplets even when
            tuplets contain multiple ties:

            >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
            >>> last_leaf = abjad.select().leaf(-1)
            >>> stack = rmakers.stack(
            ...     rmakers.talea([3, 3, 6, 6], 16, extra_counts=[0, 4]),
            ...     rmakers.trivialize(),
            ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'4
                        }
                    }
                >>

            REGRESSION #907b. Rewrites trivializable tuplets even when
            tuplets contain very long ties:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([3, 3, 6, 6], 16, extra_counts=[0, 4]),
            ...     rmakers.trivialize(),
            ...     rmakers.tie(abjad.select().notes()[:-1]),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            ~
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            ~
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            ~
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            ~
                            c'4
                        }
                    }
                >>

        ..  container:: example

            Working with ``rewrite_rest_filled``.

            Makes rest-filled tuplets when ``rewrite_rest_filled`` is false (or
            when no tuplet command is given):

            >>> stack = rmakers.stack(
            ...     rmakers.talea([3, 3, -6, -6], 16, extra_counts=[1, 0]),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'8.
                            [
                            c'8.
                            ]
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r4
                            r16
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            r8.
                            c'8.
                            [
                            c'16
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            r4.
                        }
                    }
                >>

            Rewrites rest-filled tuplets when ``rewrite_rest_filled`` is true:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([3, 3, -6, -6], 16, extra_counts=[1, 0]),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_rest_filled(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'8.
                            [
                            c'8.
                            ]
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            r2
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            r8.
                            c'8.
                            [
                            c'16
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8
                            r4.
                        }
                    }
                >>

        ..  container:: example

            No rest commands:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        c'8.
                        c'8
                        ]
                    }
                >>

        ..  container:: example

            Silences every other output division:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.force_rest(
            ...         abjad.select().tuplets().get([1], 2),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_rest_filled(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        r2
                        c'8
                        c'4
                        r2
                    }
                >>

        ..  container:: example

            Sustains every other output division:

            >>> selector = abjad.select().tuplets().get([1], 2)
            >>> nonlast_notes = abjad.select().notes()[:-1]
            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.tie(selector.map(nonlast_notes)),
            ...     rmakers.rewrite_sustained(selector),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'2
                        ~
                        c'8
                        c'4
                        c'2
                    }
                >>

        ..  container:: example

            REGRESSION. Nonperiodic rest commands respect state.

            TODO: change TUPLET selector to GROUP_BY_MEASURE selector and allow
            to be statal with divisions_produced. Possibly also allow tuplet
            selectors to be statal by tallying tuplet_produced in state
            metadata.

            Only tuplets 0 and 2 are rested here:

            >>> selector = abjad.select().tuplets().get([0, 2, 7])
            >>> stack = rmakers.stack(
            ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
            ...     rmakers.force_rest(selector),
            ...     rmakers.rewrite_rest_filled(),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        r4.
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                        }
                        r4.
                        c'16
                        c'4
                        c'8.
                    }
                >>

            >>> state = stack.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 4),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 8),
                    ('talea_weight_consumed', 31),
                    ]
                )

    # TODO: allow statal GROUP_BY_MEASURE selector (or maybe tuplet selecctor) to work here:
    #            Only tuplet 7 is rested here:
    #
    #            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
    #            >>> selection = stack(divisions, previous_state=state)
    #            >>> lilypond_file = abjad.LilyPondFile.rhythm(
    #            ...     selection, divisions
    #            ... )
    #            >>> abjad.show(lilypond_file) # doctest: +SKIP
    #
    #            ..  docs::
    #
    #                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
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
    #            >>> state = stack.maker.state
    #            >>> string = abjad.storage(state)
    #            >>> print(string)
    #            abjad.OrderedDict(
    #                [
    #                    ('divisions_consumed', 8),
    #                    ('incomplete_last_note', True),
    #                    ('logical_ties_produced', 15),
    #                    ('talea_weight_consumed', 63),
    #                    ]
    #                )

        ..  container:: example

            REGRESSION. Periodic rest commands also respect state.

            >>> selector = abjad.select().tuplets().get([2], 3)
            >>> stack = rmakers.stack(
            ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
            ...     rmakers.force_rest(selector),
            ...     rmakers.rewrite_rest_filled(),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                        }
                        r4.
                        c'16
                        c'4
                        c'8.
                    }
                >>

            >>> state = stack.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 4),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 8),
                    ('talea_weight_consumed', 31),
                    ]
                )

    # TODO: allow statal GROUP_BY_MEASURE selector (or maybe tuplet selecctor) to work here:
    #            Incomplete first note is rested here:
    #
    #            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
    #            >>> selection = stack(divisions, previous_state=state)
    #            >>> lilypond_file = abjad.LilyPondFile.rhythm(
    #            ...     selection, divisions
    #            ... )
    #            >>> abjad.show(lilypond_file) # doctest: +SKIP
    #
    #            ..  docs::
    #
    #                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
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
    #            >>> state = stack.maker.state
    #            >>> string = abjad.storage(state)
    #            >>> print(string)
    #            abjad.OrderedDict(
    #                [
    #                    ('divisions_consumed', 8),
    #                    ('incomplete_last_note', True),
    #                    ('logical_ties_produced', 15),
    #                    ('talea_weight_consumed', 63),
    #                    ]
    #                )

        ..  container:: example

            Forces the first leaf and the last two leaves to be rests:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.force_rest(
            ...         abjad.select().leaves().get([0, -2, -1])
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        ]
                        r8.
                        r8
                    }
                >>

        ..  container:: example

            Forces rest at last leaf of every tuplet:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.force_rest(
            ...         abjad.select().tuplets().map(abjad.select().leaf(0))
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        r4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        r8
                        c'4
                        r16
                        c'8
                        [
                        c'8.
                        c'8
                        ]
                    }
                >>

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_extra_counts", "_read_talea_once_only", "_talea")

    ### INITIALIZER ###

    def __init__(
        self,
        extra_counts: abjad.IntegerSequence = None,
        read_talea_once_only: bool = None,
        spelling: _specifiers.Spelling = None,
        tag: abjad.Tag = None,
        talea: _specifiers.Talea = _specifiers.Talea(counts=[1], denominator=16),
    ) -> None:
        RhythmMaker.__init__(self, spelling=spelling, tag=tag)
        if talea is not None:
            assert isinstance(talea, _specifiers.Talea), repr(talea)
        self._talea = talea
        if extra_counts is not None:
            assert abjad.math.all_are_integer_equivalent_numbers(extra_counts)
        self._extra_counts = extra_counts
        if read_talea_once_only is not None:
            read_talea_once_only = bool(read_talea_once_only)
        self._read_talea_once_only = read_talea_once_only

    ### PRIVATE METHODS ###

    def _apply_ties_to_split_notes(
        self, tuplets, unscaled_end_counts, unscaled_preamble, unscaled_talea
    ):
        leaves = abjad.select(tuplets).leaves()
        written_durations = [leaf.written_duration for leaf in leaves]
        written_durations = abjad.sequence(written_durations)
        total_duration = written_durations.weight()
        preamble_weights = []
        if unscaled_preamble:
            preamble_weights = []
            for numerator in unscaled_preamble:
                pair = (numerator, self.talea.denominator)
                duration = abjad.Duration(*pair)
                weight = abs(duration)
                preamble_weights.append(weight)
        preamble_duration = sum(preamble_weights)
        if total_duration <= preamble_duration:
            preamble_parts = written_durations.partition_by_weights(
                weights=preamble_weights,
                allow_part_weights=abjad.More,
                cyclic=True,
                overhang=True,
            )
            talea_parts = []
        else:
            assert preamble_duration < total_duration
            preamble_parts = written_durations.partition_by_weights(
                weights=preamble_weights,
                allow_part_weights=abjad.Exact,
                cyclic=False,
                overhang=False,
            )
            talea_weights = []
            for numerator in unscaled_talea:
                pair = (numerator, self.talea.denominator)
                weight = abs(abjad.Duration(*pair))
                talea_weights.append(weight)
            preamble_length = len(preamble_parts.flatten())
            talea_written_durations = written_durations[preamble_length:]
            talea_parts = talea_written_durations.partition_by_weights(
                weights=talea_weights,
                allow_part_weights=abjad.More,
                cyclic=True,
                overhang=True,
            )
        parts = preamble_parts + talea_parts
        part_durations = parts.flatten()
        assert part_durations == abjad.sequence(written_durations)
        counts = [len(part) for part in parts]
        parts = abjad.sequence(leaves).partition_by_counts(counts)
        for i, part in enumerate(parts):
            if any(isinstance(_, abjad.Rest) for _ in part):
                continue
            if len(part) == 1:
                continue
            abjad.tie(part)
        # TODO: this will need to be generalized and better tested:
        if unscaled_end_counts:
            total = len(unscaled_end_counts)
            end_leaves = leaves[-total:]
            for leaf in reversed(end_leaves):
                previous_leaf = abjad.get.leaf(leaf, -1)
                if previous_leaf is not None:
                    abjad.detach(abjad.Tie, previous_leaf)

    def _get_talea(self):
        if self.talea is not None:
            return self.talea
        return _specifiers.Talea()

    def _make_leaf_lists(self, numeric_map, talea_denominator):
        leaf_lists = []
        specifier = self._get_spelling_specifier()
        for map_division in numeric_map:
            leaf_list = self._make_leaves_from_talea(
                map_division,
                talea_denominator,
                increase_monotonic=specifier.increase_monotonic,
                forbidden_note_duration=specifier.forbidden_note_duration,
                forbidden_rest_duration=specifier.forbidden_rest_duration,
                tag=self.tag,
            )
            leaf_lists.append(leaf_list)
        return leaf_lists

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        input_ = self._prepare_input()
        end_counts = input_["end_counts"]
        preamble = input_["preamble"]
        talea = input_["talea"]
        advanced_talea = _specifiers.Talea(
            counts=talea,
            denominator=self.talea.denominator,
            end_counts=end_counts,
            preamble=preamble,
        )
        extra_counts = input_["extra_counts"]
        unscaled_end_counts = tuple(end_counts)
        unscaled_preamble = tuple(preamble)
        unscaled_talea = tuple(talea)
        counts = {
            "end_counts": end_counts,
            "extra_counts": extra_counts,
            "preamble": preamble,
            "talea": talea,
        }
        talea_denominator = None
        if self.talea is not None:
            talea_denominator = self.talea.denominator
        result = self._scale_counts(divisions, talea_denominator, counts)
        divisions = result["divisions"]
        lcd = result["lcd"]
        counts = result["counts"]
        preamble = counts["preamble"]
        if counts["talea"]:
            numeric_map, expanded_talea = self._make_numeric_map(
                divisions,
                counts["preamble"],
                counts["talea"],
                counts["extra_counts"],
                counts["end_counts"],
            )
            if expanded_talea is not None:
                unscaled_talea = expanded_talea
            talea_weight_consumed = sum(_.weight() for _ in numeric_map)
            leaf_lists = self._make_leaf_lists(numeric_map, lcd)
            if not counts["extra_counts"]:
                tuplets = [abjad.Tuplet(1, _) for _ in leaf_lists]
            else:
                tuplets = self._make_tuplets(divisions, leaf_lists)
        else:
            talea_weight_consumed = 0
            leaf_maker = abjad.LeafMaker(tag=self.tag)
            selections = []
            for division in divisions:
                selection = leaf_maker([0], [division])
                selections.append(selection)
            tuplets = self._make_tuplets(divisions, selections)
        if counts["talea"]:
            self._apply_ties_to_split_notes(
                tuplets, unscaled_end_counts, unscaled_preamble, unscaled_talea
            )
        for tuplet in abjad.iterate(tuplets).components(abjad.Tuplet):
            tuplet.normalize_multiplier()
        if "+" in talea or "-" in talea:
            pass
        elif talea_weight_consumed not in advanced_talea:
            last_leaf = abjad.get.leaf(tuplets, -1)
            if isinstance(last_leaf, abjad.Note):
                self.state["incomplete_last_note"] = True
        string = "talea_weight_consumed"
        self.state[string] = self.previous_state.get(string, 0)
        self.state[string] += talea_weight_consumed
        return tuplets

    def _make_numeric_map(self, divisions, preamble, talea, extra_counts, end_counts):
        assert all(isinstance(_, int) for _ in end_counts), repr(end_counts)
        assert all(isinstance(_, int) for _ in preamble), repr(preamble)
        for count in talea:
            assert isinstance(count, int) or count in "+-", repr(talea)
        if "+" in talea or "-" in talea:
            assert not preamble, repr(preamble)
        prolated_divisions = self._make_prolated_divisions(divisions, extra_counts)
        prolated_divisions = [abjad.NonreducedFraction(_) for _ in prolated_divisions]
        if not preamble and not talea:
            return prolated_divisions, None
        prolated_numerators = [_.numerator for _ in prolated_divisions]
        expanded_talea = None
        if "-" in talea or "+" in talea:
            total_weight = sum(prolated_numerators)
            talea_ = list(talea)
            if "-" in talea:
                index = talea_.index("-")
            else:
                index = talea_.index("+")
            talea_[index] = 0
            explicit_weight = sum([abs(_) for _ in talea_])
            implicit_weight = total_weight - explicit_weight
            if "-" in talea:
                implicit_weight *= -1
            talea_[index] = implicit_weight
            expanded_talea = tuple(talea_)
            talea = abjad.CyclicTuple(expanded_talea)
        result = self._split_talea_extended_to_weights(
            preamble, talea, prolated_numerators
        )
        if end_counts:
            end_counts = abjad.sequence(end_counts)
            end_weight = end_counts.weight()
            division_weights = [_.weight() for _ in result]
            counts = result.flatten()
            counts_weight = counts.weight()
            assert end_weight <= counts_weight, repr(end_counts)
            left = counts_weight - end_weight
            right = end_weight
            counts = counts.split([left, right])
            counts = counts[0] + end_counts
            assert counts.weight() == counts_weight
            result = counts.partition_by_weights(division_weights)
        for sequence in result:
            assert all(isinstance(_, int) for _ in sequence), repr(sequence)
        return result, expanded_talea

    def _make_prolated_divisions(self, divisions, extra_counts):
        prolated_divisions = []
        for i, division in enumerate(divisions):
            if not extra_counts:
                prolated_divisions.append(division)
                continue
            prolation_addendum = extra_counts[i]
            try:
                numerator = division.numerator
            except AttributeError:
                numerator = division[0]
            if 0 <= prolation_addendum:
                prolation_addendum %= numerator
            else:
                # NOTE: do not remove the following (nonfunctional) if-else;
                #       preserved for backwards compatability.
                use_old_extra_counts_logic = False
                if use_old_extra_counts_logic:
                    prolation_addendum %= numerator
                else:
                    prolation_addendum %= -numerator
            if isinstance(division, tuple):
                numerator, denominator = division
            else:
                numerator, denominator = division.pair
            prolated_division = (numerator + prolation_addendum, denominator)
            prolated_divisions.append(prolated_division)
        return prolated_divisions

    def _prepare_input(self):
        talea_weight_consumed = self.previous_state.get("talea_weight_consumed", 0)
        if self.talea is None:
            end_counts = ()
            preamble = ()
            talea = ()
        else:
            talea = self.talea.advance(talea_weight_consumed)
            end_counts = talea.end_counts or ()
            preamble = talea.preamble or ()
            talea = talea.counts or ()
        talea = abjad.CyclicTuple(talea)
        extra_counts = self.extra_counts or ()
        extra_counts = abjad.sequence(extra_counts)
        divisions_consumed = self.previous_state.get("divisions_consumed", 0)
        extra_counts = extra_counts.rotate(-divisions_consumed)
        extra_counts = abjad.CyclicTuple(extra_counts)
        return {
            "end_counts": end_counts,
            "extra_counts": extra_counts,
            "preamble": preamble,
            "talea": talea,
        }

    def _split_talea_extended_to_weights(self, preamble, talea, weights):
        assert abjad.math.all_are_positive_integers(weights)
        preamble_weight = abjad.math.weight(preamble)
        talea_weight = abjad.math.weight(talea)
        weight = abjad.math.weight(weights)
        if self.read_talea_once_only and preamble_weight + talea_weight < weight:
            message = f"{preamble!s} + {talea!s} is too short"
            message += f" to read {weights} once."
            raise Exception(message)
        if weight <= preamble_weight:
            talea = abjad.sequence(preamble)
            talea = talea.truncate(weight=weight)
        else:
            weight -= preamble_weight
            talea = abjad.sequence(talea).repeat_to_weight(weight)
            talea = preamble + talea
        talea = talea.split(weights, cyclic=True)
        return talea

    ### PUBLIC PROPERTIES ###

    @property
    def spelling(self) -> typing.Optional[_specifiers.Spelling]:
        r"""
        Gets duration specifier.

        Several duration specifier configurations are available.

        ..  container:: example

            Spells nonassignable durations with monontonically decreasing
            durations:

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [5],
            ...         16,
            ...         spelling=rmakers.Spelling(increase_monotonic=False),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(5, 8), (5, 8), (5, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                        c'4
                        ~
                        c'16
                    }
                >>

        ..  container:: example

            Spells nonassignable durations with monontonically increasing
            durations:

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [5], 16,
            ...         spelling=rmakers.Spelling(increase_monotonic=True),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(5, 8), (5, 8), (5, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                        \time 5/8
                        s1 * 5/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                        c'16
                        ~
                        c'4
                    }
                >>

        ..  container:: example

            Forbids no durations:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 1, 1, 1, 4, 4], 16),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 4), (3, 4)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        c'4
                        c'4
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        ]
                        c'4
                        c'4
                    }
                >>

        ..  container:: example

            Forbids durations equal to ``1/4`` or greater:

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [1, 1, 1, 1, 4, 4], 16,
            ...         spelling=rmakers.Spelling(forbidden_note_duration=(1, 4)),
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 4), (3, 4)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'8
                        ~
                        c'8
                        c'8
                        ~
                        c'8
                        ]
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'8
                        ~
                        c'8
                        c'8
                        ~
                        c'8
                        ]
                    }
                >>

            Rewrites forbidden durations with smaller durations tied together.

        ..  container:: example

            Rewrites meter:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([5, 4], 16),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     rmakers.rewrite_meter(),
            ... )
            >>> divisions = [(3, 4), (3, 4), (3, 4)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
                        \time 3/4
                        s1 * 3/4
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
                        c'8
                        [
                        c'8
                        ~
                        ]
                        c'8.
                        [
                        c'16
                        ~
                        ]
                        c'8.
                        [
                        c'16
                        ~
                        ]
                        c'4
                        c'4
                    }
                >>

        """
        return super().spelling

    @property
    def extra_counts(self) -> typing.Optional[typing.List[int]]:
        r"""
        Gets extra counts.

        ..  container:: example

            No extra counts:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ~
                        ]
                        c'8
                        c'4
                        c'16
                        [
                        c'8
                        c'8.
                        c'8
                        ]
                    }
                >>

        ..  container:: example

            Adds one extra count to every other division:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[0, 1]),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            [
                            c'8
                            c'8.
                            ]
                        }
                        \times 8/9 {
                            c'4
                            c'16
                            [
                            c'8
                            c'8
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            c'4
                            c'16
                        }
                        \times 8/9 {
                            c'8
                            [
                            c'8.
                            ]
                            c'4
                        }
                    }
                >>

        ..  container:: example

            Adds two extra counts to every other division:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[0, 2]),
            ...     rmakers.beam(),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            [
                            c'8
                            c'8.
                            ]
                        }
                        \times 4/5 {
                            c'4
                            c'16
                            [
                            c'8
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            c'16
                            [
                            c'16
                            ~
                            ]
                        }
                        \times 4/5 {
                            c'16
                            [
                            c'8.
                            ]
                            c'4
                            c'16
                            [
                            c'16
                            ]
                        }
                    }
                >>

            The duration of each added count equals the duration
            of each count in the rhythm-maker's input talea.

        ..  container:: example

            Removes one count from every other division:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[0, -1]),
            ...     rmakers.beam(),
            ...     )

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'16
                            [
                            c'8
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 8/7 {
                            c'4
                            c'16
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8.
                            ~
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 8/7 {
                            c'16
                            [
                            c'16
                            c'8
                            c'8.
                            ]
                        }
                    }
                >>

        """
        if self._extra_counts:
            return list(self._extra_counts)
        else:
            return None

    @property
    def read_talea_once_only(self) -> typing.Optional[bool]:
        r"""
        Is true when rhythm-maker reads talea once only.

        ..  container:: example

            Reads talea cyclically:

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ...     )

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ...     )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        c'4
                        c'16
                        [
                        c'16
                        ~
                        ]
                        c'16
                        [
                        c'8.
                        c'8
                        ~
                        ]
                        c'8
                        [
                        c'16
                        c'8
                        c'16
                        ]
                    }
                >>

        ..  container:: example

            Reads talea once only:

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [1, 2, 3, 4],
            ...         16,
            ...         read_talea_once_only=True,
            ...     ),
            ...     rmakers.beam(),
            ... )

            Calling stack on these divisions raises an exception because talea
            is too short to read once only:

            >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
            >>> stack(divisions)
            Traceback (most recent call last):
                ...
            Exception: () + (1, 2, 3, 4) is too short to read [6, 6, 6, 6] once.

        Set to true to ensure talea is long enough to cover all divisions
        without repeating.

        Provides way of using talea noncyclically when, for example,
        interpolating from short durations to long durations.
        """
        return self._read_talea_once_only

    @property
    def state(self) -> abjad.OrderedDict:
        r"""
        Gets state dictionary.

        ..  container:: example

            Consumes 4 divisions and 31 counts:

            >>> command = rmakers.stack(
            ...     rmakers.talea([4], 16, extra_counts=[0, 1, 2]),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = command(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'16
                            c'4
                            c'8.
                            ~
                        }
                        c'16
                        c'4
                        c'8.
                    }
                >>

            >>> state = command.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 4),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 8),
                    ('talea_weight_consumed', 31),
                    ]
                )

            Advances 4 divisions and 31 counts; then consumes another 4
            divisions and 31 counts:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = command(divisions, previous_state=state)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            c'4
                            c'8
                            ~
                        }
                        \times 4/5 {
                            c'8
                            c'4
                            c'4
                        }
                        c'4
                        c'8
                        ~
                        \times 8/9 {
                            c'8
                            c'4
                            c'8.
                        }
                    }
                >>

            >>> state = command.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 8),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 16),
                    ('talea_weight_consumed', 63),
                    ]
                )

            Advances 8 divisions and 62 counts; then consumes 4 divisions and
            31 counts:

            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = command(divisions, previous_state=state)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'16
                            c'4
                            c'8.
                            ~
                        }
                        c'16
                        c'4
                        c'8.
                        ~
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/7 {
                            c'16
                            c'4
                            c'8
                            ~
                        }
                        \times 4/5 {
                            c'8
                            c'4
                            c'4
                        }
                    }
                >>

            >>> state = command.maker.state
            >>> string = abjad.storage(state)
            >>> print(string)
            abjad.OrderedDict(
                [
                    ('divisions_consumed', 12),
                    ('incomplete_last_note', True),
                    ('logical_ties_produced', 24),
                    ('talea_weight_consumed', 96),
                    ]
                )


        """
        return super().state

    @property
    def tag(self) -> typing.Optional[abjad.Tag]:
        r"""
        Gets tag.

        ..  container:: example

            >>> stack = rmakers.stack(
            ...     rmakers.talea([1, 2, 3, 4], 16, extra_counts=[0, 1]),
            ...     rmakers.beam(),
            ...     tag=abjad.Tag("TALEA_RHYTHM_MAKER"),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> string = abjad.lilypond(lilypond_file[abjad.Score], tags=True)
            >>> string = abjad.LilyPondFormatManager.align_tags(string, 30)
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text %! TALEA_RHYTHM_MAKER
                    \times 1/1 {          %! TALEA_RHYTHM_MAKER
                        c'16              %! TALEA_RHYTHM_MAKER
                        [                 %! TALEA_RHYTHM_MAKER
                        c'8               %! TALEA_RHYTHM_MAKER
                        c'8.              %! TALEA_RHYTHM_MAKER
                        ]                 %! TALEA_RHYTHM_MAKER
                    }                     %! TALEA_RHYTHM_MAKER
                    \times 8/9 {          %! TALEA_RHYTHM_MAKER
                        c'4               %! TALEA_RHYTHM_MAKER
                        c'16              %! TALEA_RHYTHM_MAKER
                        [                 %! TALEA_RHYTHM_MAKER
                        c'8               %! TALEA_RHYTHM_MAKER
                        c'8               %! TALEA_RHYTHM_MAKER
                        ~
                        ]                 %! TALEA_RHYTHM_MAKER
                    }                     %! TALEA_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! TALEA_RHYTHM_MAKER
                    \times 1/1 {          %! TALEA_RHYTHM_MAKER
                        c'16              %! TALEA_RHYTHM_MAKER
                        c'4               %! TALEA_RHYTHM_MAKER
                        c'16              %! TALEA_RHYTHM_MAKER
                    }                     %! TALEA_RHYTHM_MAKER
                    \times 8/9 {          %! TALEA_RHYTHM_MAKER
                        c'8               %! TALEA_RHYTHM_MAKER
                        [                 %! TALEA_RHYTHM_MAKER
                        c'8.              %! TALEA_RHYTHM_MAKER
                        ]                 %! TALEA_RHYTHM_MAKER
                        c'4               %! TALEA_RHYTHM_MAKER
                    }                     %! TALEA_RHYTHM_MAKER
                }
            >>

        """
        return super().tag

    @property
    def talea(self) -> _specifiers.Talea:
        r"""
        Gets talea.

        ..  container:: example

            Working with ``preamble``.

            Preamble less than total duration:

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [8, -4, 8],
            ...         32,
            ...         preamble=[1, 1, 1, 1],
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'32
                        [
                        c'32
                        c'32
                        c'32
                        ]
                        c'4
                        r8
                        c'4
                        c'8
                        ~
                        c'8
                        r8
                        c'8
                        ~
                        c'8
                        c'4
                        r8
                    }
                >>

            Preamble more than total duration; ignores counts:

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [8, -4, 8],
            ...         32,
            ...         preamble=[32, 32, 32, 32],
            ...         ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'4.
                        ~
                        c'2
                        ~
                        c'8
                        c'4
                        ~
                        c'2
                    }
                >>

        ..  container:: example

            Working with ``end_counts``.

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [8, -4, 8],
            ...         32,
            ...         end_counts=[1, 1, 1, 1],
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 4/8
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        c'4
                        r8
                        c'4
                        c'4
                        r8
                        c'4
                        c'4
                        r8
                        c'32
                        [
                        c'32
                        c'32
                        c'32
                        ]
                    }
                >>

        ..  container:: example

            REGRESSION. End counts leave 5-durated tie in tact:

            >>> stack = rmakers.stack(
            ...     rmakers.talea(
            ...         [6],
            ...         16,
            ...         end_counts=[1],
            ...     ),
            ...     rmakers.beam(),
            ...     rmakers.extract_trivial(),
            ... )
            >>> divisions = [(3, 8), (3, 8)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 3/8
                        s1 * 3/8
                        \time 3/8
                        s1 * 3/8
                    }
                    \new RhythmicStaff
                    {
                        c'4.
                        c'4
                        ~
                        c'16
                        [
                        c'16
                        ]
                    }
                >>

        """
        return self._talea


class TupletRhythmMaker(RhythmMaker):
    r"""
    Tuplet rhythm-maker.

    ..  container:: example

        Makes tuplets with ``3:2`` ratios:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, 2)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/2
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, -1), (3, 1)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/2
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'4
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'4.
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6 {
                        c'8.
                        r8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4 {
                        c'8.
                        [
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Beams each division:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1, 1, 1)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file)  # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 5/8
                    s1 * 5/8
                    \time 3/8
                    s1 * 3/8
                    \time 6/8
                    s1 * 3/4
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6 {
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'16.
                        [
                        c'16.
                        c'16.
                        c'16.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Beams each division:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1, 1, 1)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file)  # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 5/8
                    s1 * 5/8
                    \time 3/8
                    s1 * 3/8
                    \time 6/8
                    s1 * 3/4
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6 {
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'16.
                        [
                        c'16.
                        c'16.
                        c'16.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Beams tuplets together:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1, 2, 1, 1), (3, 1, 1)]),
        ...     rmakers.beam_groups(abjad.select().tuplets()),
        ... )
        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file)  # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 5/8
                    s1 * 5/8
                    \time 3/8
                    s1 * 3/8
                    \time 6/8
                    s1 * 3/4
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/9 {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        c'8.
                        [
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 0
                        c'8.
                        ]
                        c'4.
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        c'8.
                        [
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 0
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4.
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        c'8
                        [
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 1
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 1
                        c'8
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 0
                        c'8
                        ]
                        c'4
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        c'8
                        [
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 0
                        c'8
                        ]
                    }
                    \times 4/5 {
                        c'4.
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        c'8
                        [
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 0
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Beams nothing:

        >>> rhythm_maker = rmakers.tuplet([(1, 1, 2, 1, 1), (3, 1, 1)])
        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> selection = rhythm_maker(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file)  # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 5/8
                    s1 * 5/8
                    \time 3/8
                    s1 * 3/8
                    \time 6/8
                    s1 * 3/4
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/9 {
                        c'8.
                        c'8.
                        c'4.
                        c'8.
                        c'8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4.
                        c'8
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        c'8
                        c'4
                        c'8
                        c'8
                    }
                    \times 4/5 {
                        c'4.
                        c'8
                        c'8
                    }
                }
            >>

    ..  container:: example

        Ties nothing:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, -2, 1)]),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/2
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'16.
                        r8.
                        c'16.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8.
                        ]
                    }
                }
            >>

    ..  container:: example

        Ties across all divisions:

        >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, -2, 1)]),
        ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/2
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'16.
                        r8.
                        c'16.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8.
                        ]
                    }
                }
            >>

    ..  container:: example

        Ties across every other division:

        >>> tuplets = abjad.select().tuplets().get([0], 2)
        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, -2, 1)]),
        ...     rmakers.tie(tuplets.map(last_leaf)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/2
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'16.
                        r8.
                        c'16.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8.
                        ~
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6 {
                        c'16.
                        r8.
                        c'16.
                    }
                }
            >>

    ..  container:: example

        Makes diminished tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 1)]),
        ...     rmakers.force_diminution(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (4, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 2/3 {
                        c'4
                        c'8
                    }
                    \times 2/3 {
                        c'4
                        c'8
                    }
                    \times 2/3 {
                        c'2
                        c'4
                    }
                }
            >>

    ..  container:: example

        Makes augmented tuplets:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 1)]),
        ...     rmakers.force_augmentation(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (2, 8), (4, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 2/8
                    s1 * 1/4
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3 {
                        c'8
                        [
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3 {
                        c'8
                        [
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3 {
                        c'4
                        c'8
                    }
                }
            >>

    ..  container:: example

        Makes diminished tuplets and does not rewrite dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.force_diminution(),
        ... )
        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8..
                        [
                        c'8..
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes diminished tuplets and rewrites dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1)]),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.force_diminution(),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4 {
                        c'4
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 7/8 {
                        c'4
                        c'4
                    }
                }
            >>

    ..  container:: example

        Makes augmented tuplets and does not rewrite dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.force_augmentation(),
        ... )
        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8..
                        [
                        c'8..
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes augmented tuplets and rewrites dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ...     rmakers.force_augmentation(),
        ... )
        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 2/8
                    s1 * 1/4
                    \time 3/8
                    s1 * 3/8
                    \time 7/16
                    s1 * 7/16
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2 {
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 7/4 {
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Leaves trivializable tuplets as-is when ``trivialize`` is false:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, -2), (1,), (-2, 3), (1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.rewrite_dots(),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4.
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2 {
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        r4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2 {
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Rewrites trivializable tuplets when ``trivialize`` is true.
        Measures 2 and 4 contain trivial tuplets with 1:1 ratios. To remove
        these trivial tuplets, set ``extract_trivial`` as shown in the next
        example:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, -2), (1,), (-2, 3), (1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.trivialize(),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4.
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        r4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8.
                        [
                        c'8.
                        ]
                    }
                }
            >>

        REGRESSION: Ignores ``trivialize`` and respects ``rewrite_dots`` when
        both are true. Measures 2 and 4 are first rewritten as trivial but
        then supplied again with nontrivial prolation when removing dots.
        The result is that measures 2 and 4 carry nontrivial prolation with
        no dots:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(3, -2), (1,), (-2, 3), (1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.trivialize(),
        ...     rmakers.rewrite_dots(),
        ... )
        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                    \time 3/8
                    s1 * 3/8
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4.
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2 {
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        r4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2 {
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Leaves trivial tuplets as-is when ``extract_trivial`` is
        false:

        >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, 1)]),
        ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
        ...     rmakers.beam(),
        ... )
        >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 2/8
                    s1 * 1/4
                    \time 3/8
                    s1 * 3/8
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8
                        ~
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1 {
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Extracts trivial tuplets when ``extract_trivial`` is true.
        Measures 2 and 4 in the example below now contain only a flat list
        of notes:

        >>> nonlast_tuplets = abjad.select().tuplets()[:-1]
        >>> last_leaf = abjad.select().leaf(-1)
        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, 1)]),
        ...     rmakers.tie(nonlast_tuplets.map(last_leaf)),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 2/8
                    s1 * 1/4
                    \time 3/8
                    s1 * 3/8
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        c'4.
                        ~
                    }
                    c'8
                    [
                    c'8
                    ~
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        c'4.
                        ~
                    }
                    c'8
                    [
                    c'8
                    ]
                }
            >>

        .. note:: Flattening trivial tuplets makes it possible
            subsequently to rewrite the meter of the untupletted notes.

    ..  container:: example

        REGRESSION: Very long ties are preserved when ``extract_trivial``
        is true:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(2, 3), (1, 1)]),
        ...     rmakers.beam(),
        ...     rmakers.extract_trivial(),
        ...     rmakers.tie(abjad.select().notes()[:-1]),
        ... )
        >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 2/8
                    s1 * 1/4
                    \time 3/8
                    s1 * 3/8
                    \time 2/8
                    s1 * 1/4
                }
                \new RhythmicStaff
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        ~
                        c'4.
                        ~
                    }
                    c'8
                    [
                    ~
                    c'8
                    ]
                    ~
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5 {
                        c'4
                        ~
                        c'4.
                        ~
                    }
                    c'8
                    [
                    ~
                    c'8
                    ]
                }
            >>

    ..  container:: example

        No rest commands:

        >>> rhythm_maker = rmakers.tuplet([(4, 1)])
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selection = rhythm_maker(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'4.
                        c'16.
                    }
                    \times 4/5 {
                        c'2
                        c'8
                    }
                    \times 4/5 {
                        c'4.
                        c'16.
                    }
                    \times 4/5 {
                        c'2
                        c'8
                    }
                }
            >>

    ..  container:: example

        Masks every other output division:

        >>> stack = rmakers.stack(
        ...     rmakers.tuplet([(4, 1)]),
        ...     rmakers.force_rest(
        ...         abjad.select().tuplets().get([1], 2),
        ...     ),
        ...     rmakers.rewrite_rest_filled(
        ...         abjad.select().tuplets().get([1], 2),
        ...     ),
        ...     rmakers.extract_trivial(),
        ... )
        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> selection = stack(divisions)
        >>> lilypond_file = abjad.LilyPondFile.rhythm(
        ...     selection, divisions
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(lilypond_file[abjad.Score])
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 4/8
                    s1 * 1/2
                }
                \new RhythmicStaff
                {
                    \times 4/5 {
                        c'4.
                        c'16.
                    }
                    r2
                    \times 4/5 {
                        c'4.
                        c'16.
                    }
                    r2
                }
            >>

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Rhythm-makers"

    __slots__ = ("_denominator", "_tuplet_ratios")

    ### INITIALIZER ###

    def __init__(
        self,
        denominator: typing.Union[int, abjad.DurationTyping] = None,
        spelling: _specifiers.Spelling = None,
        tag: abjad.Tag = None,
        tuplet_ratios: abjad.RatioSequenceTyping = None,
    ) -> None:
        RhythmMaker.__init__(self, spelling=spelling, tag=tag)
        if denominator is not None:
            if isinstance(denominator, tuple):
                denominator = abjad.Duration(denominator)
            prototype = (abjad.Duration, int)
            assert denominator == "divisions" or isinstance(denominator, prototype)
        self._denominator = denominator
        tuplet_ratios_ = None
        if tuplet_ratios is not None:
            tuplet_ratios_ = tuple([abjad.Ratio(_) for _ in tuplet_ratios])
        self._tuplet_ratios = tuplet_ratios_

    ### PRIVATE METHODS ###

    def _make_music(self, divisions) -> typing.List[abjad.Tuplet]:
        tuplets = []
        tuplet_ratios = abjad.CyclicTuple(self.tuplet_ratios)
        for i, division in enumerate(divisions):
            ratio = tuplet_ratios[i]
            tuplet = abjad.makers.tuplet_from_duration_and_ratio(
                division, ratio, tag=self.tag
            )
            tuplets.append(tuplet)
        return tuplets

    ### PUBLIC PROPERTIES ###

    @property
    def denominator(
        self,
    ) -> typing.Optional[typing.Union[str, abjad.Duration, int]]:
        r"""
        Gets preferred denominator.

        ..  container:: example

            Tuplet numerators and denominators are reduced to numbers that are
            relatively prime when ``denominator`` is set to none. This
            means that ratios like ``6:4`` and ``10:8`` do not arise:

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(1, 4)]),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ... )
            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            The preferred denominator of each tuplet is set in terms of a unit
            duration when ``denominator`` is set to a duration. The
            setting does not affect the first tuplet:

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(1, 4)]),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator((1, 16)),
            ... )
            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator of each tuplet in terms 32nd notes.
            The setting affects all tuplets:

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(1, 4)]),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator((1, 32)),
            ... )
            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 8/10 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                        \times 16/20 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator each tuplet in terms 64th notes. The
            setting affects all tuplets:

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(1, 4)]),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator((1, 64)),
            ... )
            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 16/20 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 24/20 {
                            c'16
                            c'4
                        }
                        \times 32/40 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            The preferred denominator of each tuplet is set directly when
            ``denominator`` is set to a positive integer. This example
            sets the preferred denominator of each tuplet to ``8``. Setting
            does not affect the third tuplet:

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(1, 4)]),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator(8),
            ... )
            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 8/10 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 8/10 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 8/10 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``12``. Setting
            affects all tuplets:

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(1, 4)]),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator(12),
            ... )
            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 12/15 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 12/15 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 12/10 {
                            c'16
                            c'4
                        }
                        \times 12/15 {
                            c'8
                            c'2
                        }
                    }
                >>

        ..  container:: example

            Sets the preferred denominator of each tuplet to ``13``. Setting
            does not affect any tuplet:

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(1, 4)]),
            ...     rmakers.beam(),
            ...     rmakers.rewrite_dots(),
            ...     rmakers.denominator(13),
            ... )
            >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 2/16
                        s1 * 1/8
                        \time 4/16
                        s1 * 1/4
                        \time 6/16
                        s1 * 3/8
                        \time 8/16
                        s1 * 1/2
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'32
                            [
                            c'8
                            ]
                        }
                        \times 4/5 {
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 6/5 {
                            c'16
                            c'4
                        }
                        \times 4/5 {
                            c'8
                            c'2
                        }
                    }
                >>

        Set to duration, positive integer or none.
        """
        return self._denominator

    @property
    def tag(self) -> typing.Optional[abjad.Tag]:
        r"""
        Gets tag.

        ..  container:: example

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(3, 2)]),
            ...     rmakers.beam(),
            ...     tag=abjad.Tag("TUPLET_RHYTHM_MAKER"),
            ... )
            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            >>> string = abjad.lilypond(lilypond_file[abjad.Score], tags=True)
            >>> string = abjad.LilyPondFormatManager.align_tags(string, 30)
            >>> print(string)
            \new Score
            <<
                \new GlobalContext
                {
                    \time 1/2
                    s1 * 1/2
                    \time 3/8
                    s1 * 3/8
                    \time 5/16
                    s1 * 5/16
                    \time 5/16
                    s1 * 5/16
                }
                \new RhythmicStaff
                {
                    \times 4/5 {          %! TUPLET_RHYTHM_MAKER
                        c'4.              %! TUPLET_RHYTHM_MAKER
                        c'4               %! TUPLET_RHYTHM_MAKER
                    }                     %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! TUPLET_RHYTHM_MAKER
                    \times 3/5 {          %! TUPLET_RHYTHM_MAKER
                        c'4.              %! TUPLET_RHYTHM_MAKER
                        c'4               %! TUPLET_RHYTHM_MAKER
                    }                     %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! TUPLET_RHYTHM_MAKER
                    \times 1/1 {          %! TUPLET_RHYTHM_MAKER
                        c'8.              %! TUPLET_RHYTHM_MAKER
                        [                 %! TUPLET_RHYTHM_MAKER
                        c'8               %! TUPLET_RHYTHM_MAKER
                        ]                 %! TUPLET_RHYTHM_MAKER
                    }                     %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text %! TUPLET_RHYTHM_MAKER
                    \times 1/1 {          %! TUPLET_RHYTHM_MAKER
                        c'8.              %! TUPLET_RHYTHM_MAKER
                        [                 %! TUPLET_RHYTHM_MAKER
                        c'8               %! TUPLET_RHYTHM_MAKER
                        ]                 %! TUPLET_RHYTHM_MAKER
                    }                     %! TUPLET_RHYTHM_MAKER
                }
            >>

        """
        return super().tag

    @property
    def tuplet_ratios(self) -> typing.Optional[typing.List[abjad.Ratio]]:
        r"""
        Gets tuplet ratios.

        ..  container:: example

            Makes tuplets with ``3:2`` ratios:

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(3, 2)]),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/2
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \times 4/5 {
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5 {
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }
                >>

        ..  container:: example

            Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

            >>> stack = rmakers.stack(
            ...     rmakers.tuplet([(1, -1), (3, 1)]),
            ...     rmakers.beam(),
            ... )
            >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        \time 1/2
                        s1 * 1/2
                        \time 3/8
                        s1 * 3/8
                        \time 5/16
                        s1 * 5/16
                        \time 5/16
                        s1 * 5/16
                    }
                    \new RhythmicStaff
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/4 {
                            c'4.
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/6 {
                            c'8.
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 5/4 {
                            c'8.
                            [
                            c'16
                            ]
                        }
                    }
                >>

        ..  container:: example

            Makes length-1 tuplets:

            >>> stack = rmakers.stack(rmakers.tuplet([(1,)]))
            >>> divisions = [(1, 5), (1, 4), (1, 6), (7, 9)]
            >>> selection = stack(divisions)
            >>> lilypond_file = abjad.LilyPondFile.rhythm(
            ...     selection, divisions
            ... )
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(lilypond_file[abjad.Score])
                >>> print(string)
                \new Score
                <<
                    \new GlobalContext
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 1/5
                        s1 * 1/5
                        \time 1/4
                        s1 * 1/4
                        #(ly:expect-warning "strange time signature found")
                        \time 1/6
                        s1 * 1/6
                        #(ly:expect-warning "strange time signature found")
                        \time 7/9
                        s1 * 7/9
                    }
                    \new RhythmicStaff
                    {
                        \tweak edge-height #'(0.7 . 0)
                        \times 4/5 {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 1/1 {
                            c'4
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \times 2/3 {
                            c'4
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \times 8/9 {
                            c'2..
                        }
                    }
                >>

        """
        if self._tuplet_ratios:
            return list(self._tuplet_ratios)
        else:
            return None


### FACTORY FUNCTIONS ###


def accelerando(
    *interpolations,
    spelling: _specifiers.Spelling = None,
    tag: abjad.Tag = None,
) -> AccelerandoRhythmMaker:
    """
    Makes accelerando rhythm-maker.
    """
    interpolations_ = []
    for interpolation in interpolations:
        interpolation_ = _specifiers.Interpolation(*interpolation)
        interpolations_.append(interpolation_)
    return AccelerandoRhythmMaker(
        interpolations=interpolations_, spelling=spelling, tag=tag
    )


def even_division(
    denominators: typing.Sequence[int],
    *,
    denominator: typing.Union[str, int] = "from_counts",
    extra_counts: typing.Sequence[int] = None,
    spelling: _specifiers.Spelling = None,
    tag: abjad.Tag = None,
) -> EvenDivisionRhythmMaker:
    """
    Makes even-division rhythm-maker.
    """
    return EvenDivisionRhythmMaker(
        denominator=denominator,
        denominators=denominators,
        extra_counts=extra_counts,
        spelling=spelling,
        tag=tag,
    )


def incised(
    extra_counts: typing.Sequence[int] = None,
    body_ratio: abjad.RatioTyping = None,
    fill_with_rests: bool = None,
    outer_divisions_only: bool = None,
    prefix_talea: typing.Sequence[int] = None,
    prefix_counts: typing.Sequence[int] = None,
    suffix_talea: typing.Sequence[int] = None,
    suffix_counts: typing.Sequence[int] = None,
    talea_denominator: int = None,
    spelling: _specifiers.Spelling = None,
    tag: abjad.Tag = None,
) -> IncisedRhythmMaker:
    """
    Makes incised rhythm-maker
    """
    return IncisedRhythmMaker(
        extra_counts=extra_counts,
        incise=_specifiers.Incise(
            body_ratio=body_ratio,
            fill_with_rests=fill_with_rests,
            outer_divisions_only=outer_divisions_only,
            prefix_talea=prefix_talea,
            prefix_counts=prefix_counts,
            suffix_talea=suffix_talea,
            suffix_counts=suffix_counts,
            talea_denominator=talea_denominator,
        ),
        spelling=spelling,
        tag=tag,
    )


def multiplied_duration(
    prototype: typing.Type = abjad.Note,
    *,
    duration: abjad.DurationTyping = (1, 1),
    tag: abjad.Tag = None,
) -> MultipliedDurationRhythmMaker:
    """
    Makes multiplied-duration rhythm-maker.
    """
    return MultipliedDurationRhythmMaker(prototype, duration=duration, tag=tag)


def note(
    spelling: _specifiers.Spelling = None, tag: abjad.Tag = None
) -> NoteRhythmMaker:
    """
    Makes note rhythm-maker.
    """
    return NoteRhythmMaker(spelling=spelling, tag=tag)


def talea(
    counts,
    denominator,
    advance: int = None,
    end_counts: abjad.IntegerSequence = None,
    extra_counts: abjad.IntegerSequence = None,
    preamble=None,
    read_talea_once_only: bool = None,
    spelling: _specifiers.Spelling = None,
    tag: abjad.Tag = None,
) -> TaleaRhythmMaker:
    """
    Makes talea rhythm-maker.
    """
    talea = _specifiers.Talea(
        counts=counts,
        denominator=denominator,
        end_counts=end_counts,
        preamble=preamble,
    )
    if advance is not None:
        talea = talea.advance(advance)
    return TaleaRhythmMaker(
        extra_counts=extra_counts,
        read_talea_once_only=read_talea_once_only,
        spelling=spelling,
        tag=tag,
        talea=talea,
    )


def tuplet(
    tuplet_ratios: abjad.RatioSequenceTyping,
    # TODO: remove in favor of dedicated denominator control commands:
    denominator: typing.Union[int, abjad.DurationTyping] = None,
    spelling: _specifiers.Spelling = None,
    tag: abjad.Tag = None,
) -> TupletRhythmMaker:
    """
    Makes tuplet rhythm-maker.
    """
    return TupletRhythmMaker(
        denominator=denominator,
        spelling=spelling,
        tag=tag,
        tuplet_ratios=tuplet_ratios,
    )
