"""
The rmakers functions.
"""

import inspect
import math
import typing

import abjad

from . import classes as _classes


def _function_name(frame):
    function_name = frame.f_code.co_name
    string = f"rmakers.{function_name}()"
    return abjad.Tag(string)


def _interpolate_cosine(y1, y2, mu) -> float:
    mu2 = (1 - math.cos(mu * math.pi)) / 2
    return y1 * (1 - mu2) + y2 * mu2


def _interpolate_divide_multiple(
    total_durations, reference_durations, exponent="cosine"
) -> list[float]:
    """
    Interpolates ``reference_durations`` such that the sum of the resulting
    interpolated values equals the given ``total_durations``.

    ..  container:: example

        >>> durations = rmakers.functions._interpolate_divide_multiple(
        ...     total_durations=[100, 50],
        ...     reference_durations=[20, 10, 20],
        ... )
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

    Precondition: ``len(totals_durations) == len(reference_durations)-1``.

    Set ``exponent`` to ``cosine`` for cosine interpolation. Set ``exponent`` to a
    number for exponential interpolation.
    """
    assert len(total_durations) == len(reference_durations) - 1
    durations = []
    for i in range(len(total_durations)):
        durations_ = _interpolate_divide(
            total_durations[i],
            reference_durations[i],
            reference_durations[i + 1],
            exponent,
        )
        for duration_ in durations_:
            assert isinstance(duration_, float)
            durations.append(duration_)
    return durations


def _interpolate_exponential(y1, y2, mu, exponent=1) -> float:
    """
    Interpolates between ``y1`` and ``y2`` at position ``mu``.

    ..  container:: example

        Exponents equal to 1 leave durations unscaled:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.functions._interpolate_exponential(100, 200, mu, exponent=1)
        ...
        100
        125.0
        150.0
        175.0
        200

        Exponents greater than 1 generate ritardandi:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.functions._interpolate_exponential(100, 200, mu, exponent=2)
        ...
        100
        106.25
        125.0
        156.25
        200

        Exponents less than 1 generate accelerandi:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.functions._interpolate_exponential(100, 200, mu, exponent=0.5)
        ...
        100.0
        150.0
        170.71067811865476
        186.60254037844388
        200.0

    """
    result = y1 * (1 - mu**exponent) + y2 * mu**exponent
    return result


def _interpolate_divide(
    total_duration, start_duration, stop_duration, exponent="cosine"
) -> str | list[float]:
    """
    Divides ``total_duration`` into durations computed from interpolating between
    ``start_duration`` and ``stop_duration``.

    ..  container:: example

        >>> rmakers.functions._interpolate_divide(
        ...     total_duration=10,
        ...     start_duration=1,
        ...     stop_duration=1,
        ...     exponent=1,
        ... )
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        >>> sum(_)
        10.0

        >>> rmakers.functions._interpolate_divide(
        ...     total_duration=10,
        ...     start_duration=5,
        ...     stop_duration=1,
        ... )
        [4.798..., 2.879..., 1.326..., 0.995...]
        >>> sum(_)
        10.0

    Set ``exponent`` to ``'cosine'`` for cosine interpolation.

    Set ``exponent`` to a numeric value for exponential interpolation with
    ``exponent`` as the exponent.

    Scales resulting durations so that their sum equals ``total_duration`` exactly.
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
            duration = _interpolate_cosine(
                start_duration, stop_duration, partial_sum / total_duration
            )
        else:
            duration = _interpolate_exponential(
                start_duration,
                stop_duration,
                partial_sum / total_duration,
                exponent,
            )
        durations.append(duration)
        partial_sum += duration
    durations = [_ * total_duration / sum(durations) for _ in durations]
    return durations


def _is_accelerando(argument):
    first_leaf = abjad.select.leaf(argument, 0)
    last_leaf = abjad.select.leaf(argument, -1)
    first_duration = abjad.get.duration(first_leaf)
    last_duration = abjad.get.duration(last_leaf)
    if last_duration < first_duration:
        return True
    return False


def _is_ritardando(argument):
    first_leaf = abjad.select.leaf(argument, 0)
    last_leaf = abjad.select.leaf(argument, -1)
    first_duration = abjad.get.duration(first_leaf)
    last_duration = abjad.get.duration(last_leaf)
    if first_duration < last_duration:
        return True
    return False


def _make_beamable_groups(components, durations):
    assert all(isinstance(_, abjad.Duration) for _ in durations)
    music_duration = abjad.get.duration(components)
    if music_duration != sum(durations):
        message = f"music duration {music_duration} does not equal"
        message += f" total duration {sum(durations)}:\n"
        message += f"   {components}\n"
        message += f"   {durations}"
        raise Exception(message)
    component_to_timespan = []
    start_offset = abjad.Offset(0)
    for component in components:
        duration = abjad.get.duration(component)
        stop_offset = start_offset + duration
        timespan = abjad.Timespan(start_offset, stop_offset)
        pair = (component, timespan)
        component_to_timespan.append(pair)
        start_offset = stop_offset
    group_to_target_duration = []
    start_offset = abjad.Offset(0)
    for target_duration in durations:
        stop_offset = start_offset + target_duration
        group_timespan = abjad.Timespan(start_offset, stop_offset)
        start_offset = stop_offset
        group = []
        for component, component_timespan in component_to_timespan:
            if component_timespan in group_timespan:
                group.append(component)
        pair = ([group], target_duration)
        group_to_target_duration.append(pair)
    beamable_groups = []
    for group, target_duration in group_to_target_duration:
        group_duration = abjad.get.duration(group)
        assert group_duration <= target_duration
        if group_duration == target_duration:
            beamable_groups.append(group)
        else:
            beamable_groups.append([])
    return beamable_groups


def _make_time_signature_staff(time_signatures):
    assert time_signatures, repr(time_signatures)
    staff = abjad.Staff(simultaneous=True)
    score = abjad.Score([staff], name="Score")
    time_signature_voice = abjad.Voice(name="TimeSignatureVoice")
    staff.append(time_signature_voice)
    staff.append(abjad.Voice(name="RhythmMaker.Music"))
    for time_signature in time_signatures:
        duration = time_signature.pair
        skip = abjad.Skip(1, multiplier=duration)
        time_signature_voice.append(skip)
        abjad.attach(time_signature, skip, context="Staff")
    return score


def _validate_tuplets(argument):
    for tuplet in abjad.iterate.components(argument, abjad.Tuplet):
        assert abjad.Duration(tuplet.multiplier).normalized(), repr(tuplet)
        assert len(tuplet), repr(tuplet)


def after_grace_container(
    argument: abjad.Component | typing.Sequence[abjad.Component],
    counts: typing.Sequence[int],
    *,
    beam: bool = False,
    slash: bool = False,
    tag: abjad.Tag | None = None,
    talea: _classes.Talea = _classes.Talea([1], 8),
) -> None:
    r"""
    Makes (and attaches) after-grace containers.

    ..  container:: example

        >>> def make_lilypond_file(pairs, *, beam=False, slash=False):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4], extra_counts=[2])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.after_grace_container(notes, [1, 4], beam=beam, slash=slash)
        ...     rmakers.extract_trivial(voice)
        ...     score = lilypond_file["Score"]
        ...     abjad.setting(score).autoBeaming = False
        ...     return lilypond_file

    ..  container:: example

        With ``beam=False`` and ``slash=False``:

        >>> pairs = [(3, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs, beam=False, slash=False)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
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
                        \tuplet 5/3
                        {
                            \time 3/4
                            c'4
                            c'4
                            c'4
                            c'4
                            \afterGrace
                            c'4
                            {
                                c'8
                            }
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            c'4
                            c'4
                            c'4
                            c'4
                            \afterGrace
                            c'4
                            {
                                c'8
                                c'8
                                c'8
                                c'8
                            }
                        }
                    }
                }
            }

    ..  container:: example

        With ``beam=True`` and ``slash=True``:

        >>> pairs = [(3, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs, beam=True, slash=True)
        >>> score = lilypond_file["Score"]
        >>> abjad.setting(score).autoBeaming = False
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
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
                        \tuplet 5/3
                        {
                            \time 3/4
                            c'4
                            c'4
                            c'4
                            c'4
                            \afterGrace
                            c'4
                            {
                                c'8
                            }
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            c'4
                            c'4
                            c'4
                            c'4
                            \afterGrace
                            c'4
                            {
                                \slash
                                c'8
                                [
                                c'8
                                c'8
                                c'8
                                ]
                            }
                        }
                    }
                }
            }

        When ``slash=True`` then ``beam`` must also be true.

        Leaves lone after-graces unslashed even when ``slash=True``.

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert all(isinstance(_, int) for _ in counts), repr(counts)
    if slash is True:
        assert beam is True, repr(beam)
    assert isinstance(talea, _classes.Talea), repr(talea)
    leaves = abjad.select.leaves(argument, grace=False)
    cyclic_counts = abjad.CyclicTuple(counts)
    start = 0
    for i, leaf in enumerate(leaves):
        count = cyclic_counts[i]
        if not count:
            continue
        stop = start + count
        durations = talea[start:stop]
        notes = abjad.makers.make_leaves([0], durations, tag=tag)
        container = abjad.AfterGraceContainer(notes, tag=tag)
        abjad.attach(container, leaf)
        if 1 < len(notes):
            if beam is True:
                abjad.beam(notes, tag=tag)
            if slash is True:
                literal = abjad.LilyPondLiteral(r"\slash", site="before")
                abjad.attach(literal, notes[0], tag=tag)


def attach_time_signatures(
    voice: abjad.Voice,
    time_signatures: list[abjad.TimeSignature],
) -> None:
    leaves = abjad.select.leaves(voice, grace=False)
    durations = [_.duration for _ in time_signatures]
    parts = abjad.select.partition_by_durations(leaves, durations)
    assert len(parts) == len(time_signatures)
    previous_time_signature = None
    for time_signature, part in zip(time_signatures, parts):
        assert isinstance(time_signature, abjad.TimeSignature)
        if time_signature != previous_time_signature:
            leaf = abjad.select.leaf(part, 0)
            abjad.detach(abjad.TimeSignature, leaf)
            abjad.attach(time_signature, leaf)
        previous_time_signature = time_signature


def beam(
    argument,
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    do_not_unbeam: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag | None = None,
) -> None:
    r"""
    Beams runs of notes in each component in ``argument``.

    ..  container:: example

        >>> def make_lilypond_file(pairs, beam_rests=False, stemlet_length=None):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1, 1, 1, -1], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(
        ...         voice, beam_rests=beam_rests, stemlet_length=stemlet_length
        ...     )
        ...     rmakers.swap_trivial(voice)
        ...     score = lilypond_file["Score"]
        ...     abjad.setting(score).autoBeaming = False
        ...     return lilypond_file

    ..  container:: example

        Beams runs of notes in each tuplet:

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        {
                            \time 3/8
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
                        }
                        {
                            \time 4/8
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
                        }
                        {
                            \time 3/8
                            c'16
                            r16
                            c'16
                            [
                            c'16
                            c'16
                            ]
                            r16
                        }
                        {
                            \time 4/8
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
                    }
                }
            }

    ..  container:: example

        Set ``beam_rests=True`` and ``stemlet_length=n`` to beam rests with
        stemlets of length ``n``:

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(
        ...     pairs, beam_rests=True, stemlet_length=0.75
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        {
                            \override RhythmicStaff.Stem.stemlet-length = 0.75
                            \time 3/8
                            c'16
                            [
                            c'16
                            c'16
                            r16
                            c'16
                            c'16
                            ]
                            \revert RhythmicStaff.Stem.stemlet-length
                        }
                        {
                            \override RhythmicStaff.Stem.stemlet-length = 0.75
                            \time 4/8
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
                            \revert RhythmicStaff.Stem.stemlet-length
                        }
                        {
                            \override RhythmicStaff.Stem.stemlet-length = 0.75
                            \time 3/8
                            c'16
                            [
                            r16
                            c'16
                            c'16
                            c'16
                            r16
                            ]
                            \revert RhythmicStaff.Stem.stemlet-length
                        }
                        {
                            \override RhythmicStaff.Stem.stemlet-length = 0.75
                            \time 4/8
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
                            \revert RhythmicStaff.Stem.stemlet-length
                        }
                    }
                }
            }

    ..  container:: example

        By default, ``rmakers.beam()`` unbeams input before applying new beams. All
        beams are lost in this example because ``rmakers.beam()`` finds no tuplets
        to beam:

        >>> staff = abjad.Staff(r"c'8 [ c'8 c'8 ] c'8 [ c'8 c'8 ] c'8 c'8")
        >>> abjad.setting(staff).autoBeaming = False
        >>> abjad.show(staff) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(staff)
            >>> print(string)
            \new Staff
            \with
            {
                autoBeaming = ##f
            }
            {
                c'8
                [
                c'8
                c'8
                ]
                c'8
                [
                c'8
                c'8
                ]
                c'8
                c'8
            }

        >>> rmakers.beam(staff)
        >>> abjad.show(staff) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(staff)
            >>> print(string)
            \new Staff
            \with
            {
                autoBeaming = ##f
            }
            {
                c'8
                c'8
                c'8
                c'8
                c'8
                c'8
                c'8
                c'8
            }

        Set ``do_not_unbeam=True`` to preserve existing beams:

        >>> staff = abjad.Staff(r"c'8 [ c'8 c'8 ] c'8 [ c'8 c'8 ] c'8 c'8")
        >>> abjad.setting(staff).autoBeaming = False
        >>> abjad.show(staff) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(staff)
            >>> print(string)
            \new Staff
            \with
            {
                autoBeaming = ##f
            }
            {
                c'8
                [
                c'8
                c'8
                ]
                c'8
                [
                c'8
                c'8
                ]
                c'8
                c'8
            }

        >>> rmakers.beam(staff, do_not_unbeam=True)
        >>> abjad.show(staff) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(staff)
            >>> print(string)
            \new Staff
            \with
            {
                autoBeaming = ##f
            }
            {
                c'8
                [
                c'8
                c'8
                ]
                c'8
                [
                c'8
                c'8
                ]
                c'8
                c'8
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    for item in argument:
        if not do_not_unbeam:
            unbeam(item)
        leaves = abjad.select.leaves(item)
        abjad.beam(
            leaves,
            beam_lone_notes=beam_lone_notes,
            beam_rests=beam_rests,
            stemlet_length=stemlet_length,
            tag=tag,
        )


def beam_groups(
    argument,
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag | None = None,
) -> None:
    r"""
    Beams groups in ``argument`` with single span beam.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam_groups(tuplets)
        ...     rmakers.swap_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        {
                            \set stemLeftBeamCount = 0
                            \set stemRightBeamCount = 2
                            \time 3/8
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
                        }
                        {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 2
                            \time 4/8
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
                        }
                        {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 2
                            \time 3/8
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
                        }
                        {
                            \set stemLeftBeamCount = 1
                            \set stemRightBeamCount = 2
                            \time 4/8
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
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    unbeam(argument)
    durations = [abjad.get.duration(_) for _ in argument]
    leaves = abjad.select.leaves(argument)
    abjad.beam(
        leaves,
        beam_lone_notes=beam_lone_notes,
        beam_rests=beam_rests,
        durations=durations,
        span_beam_count=1,
        stemlet_length=stemlet_length,
        tag=tag,
    )


def before_grace_container(
    argument: abjad.Component | typing.Sequence[abjad.Component],
    counts: typing.Sequence[int],
    *,
    beam: bool = False,
    slash: bool = False,
    slur: bool = False,
    talea: _classes.Talea = _classes.Talea([1], 8),
) -> None:
    r"""
    Makes (and attaches) before-grace containers.

    With ``beam=False``, ``slash=False``, ``slur=False`` (default):

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4], extra_counts=[2])
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     notes = [abjad.select.exclude(_, [0, -1]) for _ in notes]
        ...     rmakers.before_grace_container(notes, [1, 2, 3])
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> score = lilypond_file["Score"]
        >>> abjad.setting(score).autoBeaming = False
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
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
                        \tuplet 5/3
                        {
                            \time 3/4
                            c'4
                            \grace {
                                c'8
                            }
                            c'4
                            \grace {
                                c'8
                                c'8
                            }
                            c'4
                            \grace {
                                c'8
                                c'8
                                c'8
                            }
                            c'4
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        With ``beam=False``, ``slash=False``, ``slur=True``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4], extra_counts=[2])
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     notes = [abjad.select.exclude(_, [0, -1]) for _ in notes]
        ...     rmakers.before_grace_container(notes, [1, 2, 3], slur=True)
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> score = lilypond_file["Score"]
        >>> abjad.setting(score).autoBeaming = False
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
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
                        \tuplet 5/3
                        {
                            \time 3/4
                            c'4
                            \appoggiatura {
                                c'8
                            }
                            c'4
                            \appoggiatura {
                                c'8
                                c'8
                            }
                            c'4
                            \appoggiatura {
                                c'8
                                c'8
                                c'8
                            }
                            c'4
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        With ``beam=True``, ``slash=False``, ``slur=False``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4], extra_counts=[2])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     notes = [abjad.select.exclude(_, [0, -1]) for _ in notes]
        ...     rmakers.before_grace_container(notes, [1, 2, 3], beam=True)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> score = lilypond_file["Score"]
        >>> abjad.setting(score).autoBeaming = False
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
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
                        \tuplet 5/3
                        {
                            \time 3/4
                            c'4
                            \grace {
                                c'8
                            }
                            c'4
                            \grace {
                                c'8
                                [
                                c'8
                                ]
                            }
                            c'4
                            \grace {
                                c'8
                                [
                                c'8
                                c'8
                                ]
                            }
                            c'4
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        With ``beam=True``, ``slash=False``, ``slur=True``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4], extra_counts=[2])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     notes = [abjad.select.exclude(_, [0, -1]) for _ in notes]
        ...     rmakers.before_grace_container(notes, [1, 2, 3], beam=True, slur=True)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> score = lilypond_file["Score"]
        >>> abjad.setting(score).autoBeaming = False
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
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
                        \tuplet 5/3
                        {
                            \time 3/4
                            c'4
                            \appoggiatura {
                                c'8
                            }
                            c'4
                            \appoggiatura {
                                c'8
                                [
                                c'8
                                ]
                            }
                            c'4
                            \appoggiatura {
                                c'8
                                [
                                c'8
                                c'8
                                ]
                            }
                            c'4
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        With ``beam=True``, ``slash=True``, ``slur=False``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4], extra_counts=[2])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     notes = [abjad.select.exclude(_, [0, -1]) for _ in notes]
        ...     rmakers.before_grace_container(notes, [1, 2, 3], beam=True, slash=True)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> score = lilypond_file["Score"]
        >>> abjad.setting(score).autoBeaming = False
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
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
                        \tuplet 5/3
                        {
                            \time 3/4
                            c'4
                            \slashedGrace {
                                c'8
                            }
                            c'4
                            \slashedGrace {
                                \slash
                                c'8
                                [
                                c'8
                                ]
                            }
                            c'4
                            \slashedGrace {
                                \slash
                                c'8
                                [
                                c'8
                                c'8
                                ]
                            }
                            c'4
                            c'4
                        }
                    }
                }
            }

        (When ``slash=True`` then ``beam`` must also be true.)

    ..  container:: example

        With ``beam=True``, ``slash=True``, ``slur=True``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4], extra_counts=[2])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     notes = [abjad.select.exclude(_, [0, -1]) for _ in notes]
        ...     rmakers.before_grace_container(
        ...         notes, [1, 2, 3], beam=True, slash=True, slur=True
        ...     )
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> score = lilypond_file["Score"]
        >>> abjad.setting(score).autoBeaming = False
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                autoBeaming = ##f
            }
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
                        \tuplet 5/3
                        {
                            \time 3/4
                            c'4
                            \acciaccatura {
                                c'8
                            }
                            c'4
                            \acciaccatura {
                                \slash
                                c'8
                                [
                                c'8
                                ]
                            }
                            c'4
                            \acciaccatura {
                                \slash
                                c'8
                                [
                                c'8
                                c'8
                                ]
                            }
                            c'4
                            c'4
                        }
                    }
                }
            }

        (When ``slash=True`` then ``beam`` must also be true.)

    """
    assert all(isinstance(_, int) for _ in counts), repr(counts)
    if slash is True:
        assert beam is True, repr(beam)
    assert isinstance(talea, _classes.Talea), repr(talea)
    leaves = abjad.select.leaves(argument, grace=False)
    cyclic_counts = abjad.CyclicTuple(counts)
    start = 0
    for i, leaf in enumerate(leaves):
        count = cyclic_counts[i]
        if not count:
            continue
        stop = start + count
        durations = talea[start:stop]
        notes = abjad.makers.make_leaves([0], durations)
        if len(notes) == 1:
            if slash is False and slur is False:
                command = r"\grace"
            elif slash is False and slur is True:
                command = r"\appoggiatura"
            elif slash is True and slur is False:
                command = r"\slashedGrace"
            elif slash is True and slur is True:
                command = r"\acciaccatura"
            else:
                raise Exception
        elif 1 < len(notes):
            if slash is True:
                literal = abjad.LilyPondLiteral(r"\slash", site="before")
                abjad.attach(literal, notes[0])
            if slash is False and slur is False:
                command = r"\grace"
            elif slash is False and slur is True:
                command = r"\appoggiatura"
            elif slash is True and slur is False:
                command = r"\slashedGrace"
            elif slash is True and slur is True:
                command = r"\acciaccatura"
            else:
                raise Exception
        container = abjad.BeforeGraceContainer(notes, command=command)
        abjad.attach(container, leaf)
        if 1 < len(notes):
            if beam is True:
                abjad.beam(notes)


def denominator(argument, denominator: int | abjad.typings.Duration) -> None:
    r"""
    Sets tuplet ratio denominator of tuplets in ``argument``.

    ..  container:: example

        >>> def make_lilypond_file(pairs, denominator=None):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 4)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.beam(voice)
        ...     rmakers.force_fraction(voice)
        ...     if denominator is not None:
        ...         rmakers.denominator(voice, denominator)
        ...     score = lilypond_file["Score"]
        ...     abjad.override(score).TupletBracket.bracket_visibility = True
        ...     abjad.override(score).TupletBracket.staff_padding = 4.5
        ...     abjad.setting(score).tupletFullLength = True
        ...     return lilypond_file

    ..  container:: example

        By default, tuplet numerators and denominators are reduced to numbers
        that are relatively prime. This means that ratios like ``6:4`` and
        ``10:8`` do not arise:

        >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.staff-padding = 4.5
                tupletFullLength = ##t
            }
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
                        \tuplet 5/4
                        {
                            \time 2/16
                            c'32
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/4
                        {
                            \time 4/16
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/6
                        {
                            \time 6/16
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/4
                        {
                            \time 8/16
                            c'8
                            c'2
                        }
                    }
                }
            }

    ..  container:: example

        Spelling tuplet ratios in terms of a given duration.

        ..  container:: example

            **16th notes.** This attempts to set the denominator of each tuplet
            ratio in terms of sixteenth notes. Because the first tuplet is so
            short, its ratio must be read as "5 in the time of 4 thirty-second
            notes." But the ratios of the three longer tuplets can now be read
            as "x in the time of y sixteenth notes":

            >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, denominator=(1, 16))
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> score = lilypond_file["Score"]
                >>> string = abjad.lilypond(score)
                >>> print(string)
                \context Score = "Score"
                \with
                {
                    \override TupletBracket.bracket-visibility = ##t
                    \override TupletBracket.staff-padding = 4.5
                    tupletFullLength = ##t
                }
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
                            \tuplet 5/4
                            {
                                \time 2/16
                                c'32
                                [
                                c'8
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 5/4
                            {
                                \time 4/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 5/6
                            {
                                \time 6/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/8
                            {
                                \time 8/16
                                c'8
                                c'2
                            }
                        }
                    }
                }

        ..  container:: example

            **32nd notes.** This sets the denominator of each tuplet ratios in
            terms of thirty-second notes. All tuplet ratios can now be read as
            "x in the time of y thirty-second notes":

            >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, denominator=(1, 32))
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> score = lilypond_file["Score"]
                >>> string = abjad.lilypond(score)
                >>> print(string)
                \context Score = "Score"
                \with
                {
                    \override TupletBracket.bracket-visibility = ##t
                    \override TupletBracket.staff-padding = 4.5
                    tupletFullLength = ##t
                }
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
                            \tuplet 5/4
                            {
                                \time 2/16
                                c'32
                                [
                                c'8
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/8
                            {
                                \time 4/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/12
                            {
                                \time 6/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 20/16
                            {
                                \time 8/16
                                c'8
                                c'2
                            }
                        }
                    }
                }

        ..  container:: example

            **64th notes.** This sets the denominator of each tuplet ratios in
            terms of sixth-fourth notes. All tuplet ratios can now be read as
            "x in the time of y sixty-fourth notes":

            >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, (1, 64))
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(score)
                >>> print(string)
                \context Score = "Score"
                \with
                {
                    \override TupletBracket.bracket-visibility = ##t
                    \override TupletBracket.staff-padding = 4.5
                    tupletFullLength = ##t
                }
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
                            \tuplet 5/4
                            {
                                \time 2/16
                                c'32
                                [
                                c'8
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/8
                            {
                                \time 4/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/12
                            {
                                \time 6/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 20/16
                            {
                                \time 8/16
                                c'8
                                c'2
                            }
                        }
                    }
                }

    ..  container:: example

        Spelling tuplet ratios with a fixed denominator.

        ..  container:: example

            **Tuplet ratios spelled with denominator equal to 8.** The ratio of
            the third tuplet is left unchanged. But the ratios of the other
            tuplets can be spelled "x in the time of 8":

            >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, 8)
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(score)
                >>> print(string)
                \context Score = "Score"
                \with
                {
                    \override TupletBracket.bracket-visibility = ##t
                    \override TupletBracket.staff-padding = 4.5
                    tupletFullLength = ##t
                }
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
                            \tuplet 5/4
                            {
                                \time 2/16
                                c'32
                                [
                                c'8
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/8
                            {
                                \time 4/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/12
                            {
                                \time 6/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 20/16
                            {
                                \time 8/16
                                c'8
                                c'2
                            }
                        }
                    }
                }

        ..  container:: example

            **Tuplet ratios spelled with denominator equal to 12.** The ratios
            of all tuplets can be spelled "x in the time of 12":

            >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, 12)
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(score)
                >>> print(string)
                \context Score = "Score"
                \with
                {
                    \override TupletBracket.bracket-visibility = ##t
                    \override TupletBracket.staff-padding = 4.5
                    tupletFullLength = ##t
                }
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
                            \tuplet 5/4
                            {
                                \time 2/16
                                c'32
                                [
                                c'8
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/8
                            {
                                \time 4/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/12
                            {
                                \time 6/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 20/16
                            {
                                \time 8/16
                                c'8
                                c'2
                            }
                        }
                    }
                }

        ..  container:: example

            **Tuplet ratios spelled with denominator equal to 13.** No tuplet
            ratio can be spelled "x in the time of 13":

            >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, 13)
            >>> abjad.show(lilypond_file) # doctest: +SKIP

            ..  docs::

                >>> string = abjad.lilypond(score)
                >>> print(string)
                \context Score = "Score"
                \with
                {
                    \override TupletBracket.bracket-visibility = ##t
                    \override TupletBracket.staff-padding = 4.5
                    tupletFullLength = ##t
                }
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
                            \tuplet 5/4
                            {
                                \time 2/16
                                c'32
                                [
                                c'8
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/8
                            {
                                \time 4/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 10/12
                            {
                                \time 6/16
                                c'16
                                c'4
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 20/16
                            {
                                \time 8/16
                                c'8
                                c'2
                            }
                        }
                    }
                }

    """
    if isinstance(denominator, tuple):
        denominator = abjad.Duration(denominator)
    for tuplet in abjad.select.tuplets(argument):
        if isinstance(denominator, abjad.Duration):
            unit_duration = denominator
            assert unit_duration.numerator == 1
            duration = abjad.get.duration(tuplet)
            denominator_ = unit_duration.denominator
            pair = abjad.duration.with_denominator(duration, denominator_)
            tuplet.denominator = pair[0]
        elif abjad.math.is_positive_integer(denominator):
            tuplet.denominator = denominator
        else:
            raise Exception(f"invalid preferred denominator: {denominator!r}.")


def duration_bracket(argument) -> None:
    """
    Applies duration bracket to tuplets in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        duration_ = abjad.get.duration(tuplet)
        components = abjad.makers.make_leaves([0], [duration_])
        if all(isinstance(_, abjad.Note) for _ in components):
            durations = [abjad.get.duration(_) for _ in components]
            strings = [_.lilypond_duration_string for _ in durations]
            strings = [rf"\rhythm {{ {_} }}" for _ in strings]
            string = " + ".join(strings)
            if "+" in string:
                string = f"{{ {string} }}"
        else:
            string = abjad.illustrators.components_to_score_markup_string(components)
        string = rf"\markup \scale #'(0.75 . 0.75) {string}"
        abjad.override(tuplet).TupletNumber.text = string


def example(
    components: typing.Sequence[abjad.Component],
    time_signatures: typing.Sequence[abjad.TimeSignature],
    *,
    includes: typing.Sequence[str] = (),
) -> abjad.LilyPondFile:
    """
    Makes example LilyPond file.

    Function is a documentation helper.
    """
    assert all(isinstance(_, abjad.Component) for _ in components), repr(components)
    assert time_signatures is not None
    assert all(isinstance(_, abjad.TimeSignature) for _ in time_signatures), repr(
        time_signatures
    )
    assert all(isinstance(_, str) for _ in includes), repr(includes)
    lilypond_file = abjad.illustrators.components(components, time_signatures)
    includes = [rf'\include "{_}"' for _ in includes]
    lilypond_file.items[0:0] = includes
    staff = lilypond_file["Staff"]
    staff.lilypond_type = "RhythmicStaff"
    abjad.override(staff).Clef.stencil = False
    return lilypond_file


def extract_rest_filled(argument) -> None:
    """
    Extracts rest-filled tuplets from ``argument``.
    """
    tuplets = abjad.select.tuplets(argument)
    for tuplet in tuplets:
        if tuplet.rest_filled():
            abjad.mutate.extract(tuplet)


def extract_trivial(argument) -> None:
    r"""
    Extracts trivial tuplets from ``argument``.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     tuplets = abjad.select.tuplets(voice)[-2:]
        ...     rmakers.extract_trivial(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/3
                        {
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            }

    """
    tuplets = abjad.select.tuplets(argument)
    for tuplet in tuplets:
        if tuplet.trivial():
            abjad.mutate.extract(tuplet)


def feather_beam(
    argument,
    *,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag | None = None,
) -> None:
    r"""
    Feather-beams leaves in ``argument``.

    ..  container:: example

        >>> def make_lilypond_file():
        ...     voice = abjad.Voice("c'16 d' r f' g'8")
        ...     leaves = abjad.select.leaves(voice)
        ...     rmakers.feather_beam([leaves], beam_rests=True, stemlet_length=1)
        ...     staff = abjad.Staff([voice])
        ...     score = abjad.Score([staff], name="Score")
        ...     lilypond_file = abjad.LilyPondFile([score])
        ...     return lilypond_file

        >>> lilypond_file = make_lilypond_file()
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \new Staff
                {
                    \new Voice
                    {
                        \override Staff.Stem.stemlet-length = 1
                        \once \override Beam.grow-direction = #left
                        c'16
                        [
                        d'16
                        r16
                        f'16
                        g'8
                        ]
                        \revert Staff.Stem.stemlet-length
                    }
                }
            >>

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    for item in argument:
        unbeam(item)
        leaves = abjad.select.leaves(item)
        abjad.beam(
            leaves,
            beam_rests=beam_rests,
            stemlet_length=stemlet_length,
            tag=tag,
        )
    for item in argument:
        first_leaf = abjad.select.leaf(item, 0)
        if _is_accelerando(item):
            abjad.override(first_leaf).Beam.grow_direction = abjad.RIGHT
        elif _is_ritardando(item):
            abjad.override(first_leaf).Beam.grow_direction = abjad.LEFT


def force_augmentation(argument) -> None:
    r"""
    Spells tuplets in ``argument`` as augmentations.

    ..  container:: example

        >>> def make_lilypond_file(pairs, force_augmentation=False):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.force_fraction(voice)
        ...     rmakers.beam(voice)
        ...     if force_augmentation is True:
        ...         rmakers.force_augmentation(voice)
        ...     score = lilypond_file["Score"]
        ...     abjad.override(score).TupletBracket.bracket_visibility = True
        ...     abjad.override(score).TupletBracket.staff_padding = 4.5
        ...     abjad.setting(score).tupletFullLength = True
        ...     return lilypond_file

    ..  container:: example

        Without forced augmentation:

        >>> pairs = [(2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs, force_augmentation=False)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.staff-padding = 4.5
                tupletFullLength = ##t
            }
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        With forced augmentation:

        >>> pairs = [(2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs, force_augmentation=True)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.staff-padding = 4.5
                tupletFullLength = ##t
            }
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
                        \tuplet 3/4
                        {
                            \time 2/8
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                    }
                }
            }

    """
    for tuplet in abjad.select.tuplets(argument):
        if not tuplet.augmentation():
            tuplet.toggle_prolation()


def force_diminution(argument) -> None:
    r"""
    Spells tuplets in ``argument`` as diminutions.

    ..  container:: example

        >>> def make_lilypond_file(pairs, force_diminution=False):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1], 16, extra_counts=[0, -1])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.force_fraction(voice)
        ...     rmakers.beam(voice)
        ...     rmakers.swap_trivial(voice)
        ...     if force_diminution is True:
        ...         rmakers.force_diminution(voice)
        ...     score = lilypond_file["Score"]
        ...     abjad.override(score).TupletBracket.bracket_visibility = True
        ...     abjad.override(score).TupletBracket.staff_padding = 4.5
        ...     abjad.setting(score).tupletFullLength = True
        ...     return lilypond_file

    ..  container:: example

        Without forced diminution (default):

        >>> pairs = [(1, 4), (1, 4), (1, 4), (1, 4)]
        >>> lilypond_file = make_lilypond_file(pairs, force_diminution=False)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.staff-padding = 4.5
                tupletFullLength = ##t
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        {
                            \time 1/4
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                        {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'16
                            [
                            c'16
                            c'16
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        With forced diminution (default):

        >>> pairs = [(1, 4), (1, 4), (1, 4), (1, 4)]
        >>> lilypond_file = make_lilypond_file(pairs, force_diminution=True)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.staff-padding = 4.5
                tupletFullLength = ##t
            }
            {
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \context Voice = "Voice"
                    {
                        {
                            \time 1/4
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        {
                            c'16
                            [
                            c'16
                            c'16
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    for tuplet in abjad.select.tuplets(argument):
        if not tuplet.diminution():
            tuplet.toggle_prolation()


def force_fraction(argument) -> None:
    """
    Sets ``force_fraction=True`` on tuplets in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        tuplet.force_fraction = True


def force_note(argument, *, tag: abjad.Tag | None = None) -> None:
    r"""
    Replaces leaves in ``argument`` with notes.

    Changes logical ties 1 and 2 to notes:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     rmakers.force_rest(components)
        ...     logical_ties = abjad.select.logical_ties(container)[1:3]
        ...     rmakers.force_note(logical_ties)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \time 7/16
                        r4..
                        \time 3/8
                        c'4.
                        \time 7/16
                        c'4..
                        \time 3/8
                        r4.
                    }
                }
            }

    ..  container:: example

        Changes leaves to notes with inverted composite pattern:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     leaves = abjad.select.leaves(container)
        ...     rmakers.force_rest(leaves)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     leaves = abjad.select.get(logical_ties, [0, -1])
        ...     rmakers.force_note(leaves)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \time 7/16
                        c'4..
                        \time 3/8
                        r4.
                        \time 7/16
                        r4..
                        \time 3/8
                        c'4.
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    leaves = abjad.select.leaves(argument)
    for leaf in leaves:
        if isinstance(leaf, abjad.Note):
            continue
        note = abjad.Note("C4", leaf.written_duration, tag=tag)
        if leaf.multiplier is not None:
            note.multiplier = leaf.multiplier
        abjad.mutate.replace(leaf, [note])


def force_repeat_tie(
    argument,
    *,
    tag: abjad.Tag | None = None,
    threshold: bool | tuple[int, int] | typing.Callable = True,
) -> None:
    r"""
    Replaces ties in ``argument`` with repeat-ties.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

    ..  container:: example

        Attaches tie to last note in each nonlast tuplet:

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Changes ties to repeat-ties:

        >>> rmakers.force_repeat_tie(lilypond_file["Score"])
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert isinstance(argument, abjad.Container), repr(argument)
    if callable(threshold):
        inequality = threshold
    elif threshold in (None, False):

        def inequality(item):
            return item < 0

    elif threshold is True:

        def inequality(item):
            return item >= 0

    else:
        assert isinstance(threshold, tuple) and len(threshold) == 2, repr(threshold)

        def inequality(item):
            return item >= abjad.Duration(threshold)

    attach_repeat_ties = []
    for leaf in abjad.select.leaves(argument):
        if abjad.get.has_indicator(leaf, abjad.Tie):
            next_leaf = abjad.get.leaf(leaf, 1)
            if next_leaf is None:
                continue
            if not isinstance(next_leaf, abjad.Chord | abjad.Note):
                continue
            if abjad.get.has_indicator(next_leaf, abjad.RepeatTie):
                continue
            duration = abjad.get.duration(leaf)
            if not inequality(duration):
                continue
            attach_repeat_ties.append(next_leaf)
            abjad.detach(abjad.Tie, leaf)
    for leaf in attach_repeat_ties:
        repeat_tie = abjad.RepeatTie()
        abjad.attach(repeat_tie, leaf, tag=tag)


def force_rest(argument, *, tag: abjad.Tag | None = None) -> None:
    r"""
    Replaces leaves in ``argument`` with rests.

    Forces first and last logical ties to rest:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     logical_ties = abjad.select.logical_ties(voice)
        ...     logical_ties = abjad.select.get(logical_ties, [0, -1])
        ...     rmakers.force_rest(logical_ties)
        ...     rmakers.beam(voice)
        ...     rmakers.attach_time_signatures(voice, time_signatures)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                        \time 3/8
                        c'8
                        c'4
                        \time 4/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        r8
                    }
                }
            }

    ..  container:: example

        Forces all logical ties to rest. Then sustains first and last logical ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     container = abjad.Container(tuplets)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     rmakers.force_rest(logical_ties)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0, -1])
        ...     rmakers.force_note(logical_ties)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        c'16
                        r8
                        r8.
                        \time 4/8
                        r4
                        r16
                        r8
                        r16
                        \time 3/8
                        r8
                        r4
                        \time 4/8
                        r16
                        r8
                        r8.
                        c'8
                    }
                }
            }

    ..  container:: example

        Forces every other tuplet to rest:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     rmakers.force_rest(tuplets)
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_rest_filled(voice)
        ...     rmakers.extract_trivial(voice)
        ...     rmakers.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        \time 4/8
                        r2
                        \time 3/8
                        c'8
                        c'4
                        \time 4/8
                        r2
                    }
                }
            }

    ..  container:: example

        Forces the first leaf and the last two leaves to rests:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     leaves = abjad.select.leaves(voice)
        ...     leaves = abjad.select.get(leaves, [0, -2, -1])
        ...     rmakers.force_rest(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     rmakers.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                        \time 3/8
                        c'8
                        c'4
                        \time 4/8
                        c'16
                        [
                        c'8
                        ]
                        r8.
                        r8
                    }
                }
            }

    ..  container:: example

        Forces first leaf of every tuplet to rest:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     leaves = [abjad.select.leaf(_, 0) for _ in tuplets]
        ...     rmakers.force_rest(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     rmakers.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        r16
                        c'8
                        [
                        c'8.
                        ]
                        \time 4/8
                        r4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        \time 3/8
                        r8
                        c'4
                        \time 4/8
                        r16
                        c'8
                        [
                        c'8.
                        c'8
                        ]
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    leaves = abjad.select.leaves(argument)
    for leaf in leaves:
        rest = abjad.Rest(leaf.written_duration, tag=tag)
        if leaf.multiplier is not None:
            rest.multiplier = leaf.multiplier
        previous_leaf = abjad.get.leaf(leaf, -1)
        next_leaf = abjad.get.leaf(leaf, 1)
        abjad.mutate.replace(leaf, [rest])
        if previous_leaf is not None:
            abjad.detach(abjad.Tie, previous_leaf)
        abjad.detach(abjad.Tie, rest)
        abjad.detach(abjad.RepeatTie, rest)
        if next_leaf is not None:
            abjad.detach(abjad.RepeatTie, next_leaf)


def hide_skip_filled(argument) -> None:
    """
    Hides skip-filled tuplets in ``argument``.
    """
    tuplets = abjad.select.tuplets(argument)
    for tuplet in tuplets:
        if all(isinstance(_, abjad.Skip) for _ in tuplet):
            tuplet.hide = True


def hide_trivial(argument) -> None:
    r"""
    Hides trivial tuplets in ``argument``.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     tuplets = abjad.select.tuplets(tuplets)[-2:]
        ...     rmakers.hide_trivial(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/3
                        {
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \scaleDurations #'(1 . 1)
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \scaleDurations #'(1 . 1)
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    tuplets = abjad.select.tuplets(argument)
    for tuplet in tuplets:
        if tuplet.trivial():
            tuplet.hide = True


def invisible_music(argument, *, tag: abjad.Tag | None = None) -> None:
    """
    Makes ``argument`` invisible.
    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    tag_1 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COMMAND"))
    literal_1 = abjad.LilyPondLiteral(r"\abjad-invisible-music", site="before")
    tag_2 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COLORING"))
    literal_2 = abjad.LilyPondLiteral(r"\abjad-invisible-music-coloring", site="before")
    for leaf in abjad.select.leaves(argument):
        abjad.attach(literal_1, leaf, tag=tag_1, deactivate=True)
        abjad.attach(literal_2, leaf, tag=tag_2)


def interpolate(
    start_duration: abjad.typings.Duration,
    stop_duration: abjad.typings.Duration,
    written_duration: abjad.typings.Duration,
) -> _classes.Interpolation:
    """
    Makes interpolation.
    """
    return _classes.Interpolation(
        abjad.Duration(start_duration),
        abjad.Duration(stop_duration),
        abjad.Duration(written_duration),
    )


def nongrace_leaves_in_each_tuplet(
    argument, *, level: int = -1
) -> list[list[abjad.Leaf]]:
    """
    Selects nongrace leaves in each tuplet.
    """
    tuplets = abjad.select.tuplets(argument, level=level)
    lists = [abjad.select.leaves(_, grace=False) for _ in tuplets]
    for list_ in lists:
        assert isinstance(list_, list)
        assert all(isinstance(_, abjad.Leaf) for _ in list_), repr(list_)
    return lists


def on_beat_grace_container(
    voice: abjad.Voice,
    voice_name: str,
    nongrace_leaf_lists: typing.Sequence[typing.Sequence[abjad.Leaf]],
    counts: typing.Sequence[int],
    *,
    grace_leaf_duration: abjad.typings.Duration | None = None,
    grace_polyphony_command: abjad.VoiceNumber = abjad.VoiceNumber(1),
    nongrace_polyphony_command: abjad.VoiceNumber = abjad.VoiceNumber(2),
    tag: abjad.Tag | None = None,
    talea: _classes.Talea = _classes.Talea([1], 8),
) -> None:
    r"""
    Makes on-beat grace containers.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4], extra_counts=[2])
        ...     voice = abjad.Voice(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     notes = [abjad.select.exclude(_, [0, -1]) for _ in notes]
        ...     notes = abjad.select.notes(notes)
        ...     groups = [[_] for _ in notes]
        ...     rmakers.on_beat_grace_container(
        ...         voice,
        ...         "RhythmMaker.Music",
        ...         groups,
        ...         [2, 4],
        ...         grace_leaf_duration=(1, 28)
        ...     )
        ...     components = abjad.mutate.eject_contents(voice)
        ...     music_voice = abjad.Voice(components, name="RhythmMaker.Music")
        ...     lilypond_file = rmakers.example(
        ...         [music_voice], time_signatures, includes=["abjad.ily"]
        ...     )
        ...     staff = lilypond_file["Staff"]
        ...     abjad.override(staff).TupletBracket.direction = abjad.UP
        ...     abjad.override(staff).TupletBracket.staff_padding = 5
        ...     return lilypond_file

        >>> pairs = [(3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                    \override TupletBracket.direction = #up
                    \override TupletBracket.staff-padding = 5
                }
                {
                    \context Voice = "Voice"
                    {
                        \context Voice = "RhythmMaker.Music"
                        {
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 5/3
                            {
                                \time 3/4
                                c'4
                                <<
                                    \context Voice = "On_Beat_Grace_Container"
                                    {
                                        \set fontSize = #-3
                                        \slash
                                        \voiceOne
                                        <
                                            \tweak font-size 0
                                            \tweak transparent ##t
                                            c'
                                        >8 * 10/21
                                        [
                                        (
                                        c'8 * 10/21
                                        )
                                        ]
                                    }
                                    \context Voice = "RhythmMaker.Music"
                                    {
                                        \voiceTwo
                                        c'4
                                    }
                                >>
                                <<
                                    \context Voice = "On_Beat_Grace_Container"
                                    {
                                        \set fontSize = #-3
                                        \slash
                                        \voiceOne
                                        <
                                            \tweak font-size 0
                                            \tweak transparent ##t
                                            c'
                                        >8 * 10/21
                                        [
                                        (
                                        c'8 * 10/21
                                        c'8 * 10/21
                                        c'8 * 10/21
                                        )
                                        ]
                                    }
                                    \context Voice = "RhythmMaker.Music"
                                    {
                                        \voiceTwo
                                        c'4
                                    }
                                >>
                                <<
                                    \context Voice = "On_Beat_Grace_Container"
                                    {
                                        \set fontSize = #-3
                                        \slash
                                        \voiceOne
                                        <
                                            \tweak font-size 0
                                            \tweak transparent ##t
                                            c'
                                        >8 * 10/21
                                        [
                                        (
                                        c'8 * 10/21
                                        )
                                        ]
                                    }
                                    \context Voice = "RhythmMaker.Music"
                                    {
                                        \voiceTwo
                                        c'4
                                    }
                                >>
                                \oneVoice
                                c'4
                            }
                        }
                    }
                }
            }

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [5], 16)
        ...     voice = abjad.Voice(tuplets)
        ...     rmakers.extract_trivial(voice)
        ...     logical_ties = abjad.select.logical_ties(voice)
        ...     rmakers.on_beat_grace_container(
        ...         voice,
        ...         "RhythmMaker.Music",
        ...         logical_ties,
        ...         [6, 2],
        ...         grace_leaf_duration=(1, 28)
        ...     )
        ...     components = abjad.mutate.eject_contents(voice)
        ...     music_voice = abjad.Voice(components, name="RhythmMaker.Music")
        ...     lilypond_file = rmakers.example(
        ...         [music_voice], time_signatures, includes=["abjad.ily"]
        ...     )
        ...     return lilypond_file

        >>> pairs = [(3, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \context Voice = "RhythmMaker.Music"
                        {
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \time 3/4
                                    \voiceTwo
                                    c'4
                                    ~
                                    c'16
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                    ~
                                    c'16
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'8
                                    ~
                                    c'8.
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                    ~
                                    c'16
                                }
                            >>
                            <<
                                \context Voice = "On_Beat_Grace_Container"
                                {
                                    \set fontSize = #-3
                                    \slash
                                    \voiceOne
                                    <
                                        \tweak font-size 0
                                        \tweak transparent ##t
                                        c'
                                    >8 * 2/7
                                    [
                                    (
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    c'8 * 2/7
                                    )
                                    ]
                                }
                                \context Voice = "RhythmMaker.Music"
                                {
                                    \voiceTwo
                                    c'4
                                }
                            >>
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert isinstance(voice, abjad.Voice), repr(voice)
    assert isinstance(voice_name, str), repr(voice_name)
    assert isinstance(talea, _classes.Talea), repr(talea)
    assert isinstance(grace_polyphony_command, abjad.VoiceNumber), repr(
        grace_polyphony_command
    )
    assert isinstance(nongrace_polyphony_command, abjad.VoiceNumber), repr(
        nongrace_polyphony_command
    )
    if voice_name:
        voice.name = voice_name
    cyclic_counts = abjad.CyclicTuple(counts)
    start = 0
    for i, nongrace_leaves in enumerate(nongrace_leaf_lists):
        assert all(isinstance(_, abjad.Leaf) for _ in nongrace_leaves), repr(
            nongrace_leaves
        )
        count = cyclic_counts[i]
        if not count:
            continue
        stop = start + count
        durations = talea[start:stop]
        grace_leaves = abjad.makers.make_leaves([0], durations)
        abjad.on_beat_grace_container(
            grace_leaves,
            nongrace_leaves,
            grace_leaf_duration=grace_leaf_duration,
            grace_polyphony_command=grace_polyphony_command,
            nongrace_polyphony_command=nongrace_polyphony_command,
            tag=tag,
        )


def repeat_tie(argument, *, tag: abjad.Tag | None = None) -> None:
    r"""
    Attaches repeat-ties to pitched leaves in ``argument``.

    Attaches repeat-tie to first pitched leaf in each nonfirst tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     voice = abjad.Voice(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)[1:]
        ...     notes = [abjad.select.note(_, 0) for _ in tuplets]
        ...     rmakers.repeat_tie(notes)
        ...     rmakers.beam(voice)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Attaches repeat-ties to nonfirst notes in each tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     voice = abjad.Voice(tuplets)
        ...     tuplets = abjad.select.tuplets(voice)
        ...     notes = [abjad.select.notes(_)[1:] for _ in tuplets]
        ...     rmakers.repeat_tie(notes)
        ...     rmakers.beam(voice)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    for leaf in abjad.select.leaves(argument, pitched=True):
        tie = abjad.RepeatTie()
        abjad.attach(tie, leaf, tag=tag)


def reduce_multiplier(argument) -> None:
    """
    Reduces multipliers of tuplets in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        fraction = abjad.Fraction(*tuplet.multiplier)
        pair = fraction.numerator, fraction.denominator
        tuplet.multiplier = pair


def rewrite_dots(argument, *, tag: abjad.Tag | None = None) -> None:
    """
    Rewrites dots of tuplets in ``argument``.
    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    for tuplet in abjad.select.tuplets(argument):
        tuplet.rewrite_dots()


def rewrite_meter(
    voice: abjad.Voice,
    *,
    boundary_depth: int | None = None,
    reference_meters: typing.Sequence[abjad.Meter] = (),
    tag: abjad.Tag | None = None,
) -> None:
    r"""
    Rewrites meter of components in ``voice``.

    Use ``rmakers.wrap_in_time_signature_staff()`` to make sure ``voice``
    appears together with time signature information in a staff.

    Rewrites meter:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [5, 4], 16)
        ...     voice = rmakers.wrap_in_time_signature_staff(
        ...         tuplets, time_signatures)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     rmakers.rewrite_meter(voice)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 4), (3, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \time 3/4
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        c'8
                        [
                        c'8
                        ]
                        ~
                        c'8
                        [
                        c'8
                        ]
                        ~
                        c'8.
                        [
                        c'16
                        ]
                        ~
                        c'8.
                        [
                        c'16
                        ]
                        ~
                        c'4
                        c'4
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    assert isinstance(voice, abjad.Container), repr(voice)
    staff = abjad.get.parentage(voice).parent
    assert isinstance(staff, abjad.Staff), repr(staff)
    time_signature_voice = staff["TimeSignatureVoice"]
    assert isinstance(time_signature_voice, abjad.Voice)
    meters, preferred_meters = [], []
    for skip in time_signature_voice:
        time_signature = abjad.get.indicator(skip, abjad.TimeSignature)
        rtc = abjad.meter.make_best_guess_rtc(time_signature.pair)
        meter = abjad.Meter(rtc)
        meters.append(meter)
    durations = [abjad.Duration(_) for _ in meters]
    reference_meters = reference_meters or ()
    split_measures(voice, durations=durations)
    lists = abjad.select.group_by_measure(voice[:])
    assert all(isinstance(_, list) for _ in lists), repr(lists)
    for meter, list_ in zip(meters, lists):
        for reference_meter in reference_meters:
            if reference_meter.pair == meter.pair:
                meter = reference_meter
                break
        preferred_meters.append(meter)
        nontupletted_leaves = []
        for leaf in abjad.iterate.leaves(list_):
            if not abjad.get.parentage(leaf).count(abjad.Tuplet):
                nontupletted_leaves.append(leaf)
        unbeam(nontupletted_leaves)
        meter.rewrite(
            list_,
            boundary_depth=boundary_depth,
            rewrite_tuplets=False,
        )
    lists = abjad.select.group_by_measure(voice[:])
    for meter, list_ in zip(preferred_meters, lists):
        leaves = abjad.select.leaves(list_, grace=False)
        beat_durations = []
        beat_offsets = meter.depthwise_offset_inventory[1]
        for start, stop in abjad.sequence.nwise(beat_offsets):
            beat_duration = stop - start
            beat_durations.append(beat_duration)
        beamable_groups = _make_beamable_groups(leaves, beat_durations)
        for beamable_group in beamable_groups:
            if not beamable_group:
                continue
            abjad.beam(
                beamable_group,
                beam_rests=False,
                tag=tag,
            )


def rewrite_rest_filled(
    argument, *, spelling=None, tag: abjad.Tag | None = None
) -> None:
    r"""
    Rewrites rest-filled tuplets in ``argument``.

    Does not rewrite rest-filled tuplets:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [-1], 16, extra_counts=[1])
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 5/4
                        {
                            \time 4/16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \tuplet 5/4
                        {
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            \time 5/16
                            r16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            r16
                            r16
                            r16
                            r16
                            r16
                            r16
                        }
                    }
                }
            }

        Rewrites rest-filled tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [-1], 16, extra_counts=[1])
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_rest_filled(container)
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \time 4/16
                        r4
                        r4
                        \time 5/16
                        r4
                        r16
                        r4
                        r16
                    }
                }
            }

        With spelling specifier:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [-1], 16, extra_counts=[1])
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_rest_filled(
        ...         container,
        ...         spelling=rmakers.Spelling(increase_monotonic=True)
        ...     )
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \time 4/16
                        r4
                        r4
                        \time 5/16
                        r16
                        r4
                        r16
                        r4
                    }
                }
            }

    ..  container:: example

        Working with ``rewrite_rest_filled``.

        Makes rest-filled tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, -6, -6], 16, extra_counts=[1, 0]
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                            c'8.
                            [
                            c'8.
                            ]
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            r4
                            r16
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/6
                        {
                            \time 3/8
                            r8.
                            c'8.
                            [
                            c'16
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'8
                            r4.
                        }
                    }
                }
            }

        Rewrites rest-filled tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, -6, -6], 16, extra_counts=[1, 0]
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_rest_filled(voice)
        ...     rmakers.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                            c'8.
                            [
                            c'8.
                            ]
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            r2
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 7/6
                        {
                            \time 3/8
                            r8.
                            c'8.
                            [
                            c'16
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'8
                            r4.
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    if spelling is not None:
        increase_monotonic = spelling.increase_monotonic
        forbidden_note_duration = spelling.forbidden_note_duration
        forbidden_rest_duration = spelling.forbidden_rest_duration
    else:
        increase_monotonic = None
        forbidden_note_duration = None
        forbidden_rest_duration = None
    for tuplet in abjad.select.tuplets(argument):
        if not tuplet.rest_filled():
            continue
        duration = abjad.get.duration(tuplet)
        rests = abjad.makers.make_leaves(
            [None],
            [duration],
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            tag=tag,
        )
        abjad.mutate.replace(tuplet[:], rests)
        tuplet.multiplier = (1, 1)


def rewrite_sustained(argument, *, tag: abjad.Tag | None = None) -> None:
    r"""
    Rewrites sustained tuplets in ``argument``.

    Sustained tuplets generalize a class of rhythms composers are likely to rewrite:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/2
                        {
                            \time 4/16
                            c'4.
                        }
                        \tuplet 5/4
                        {
                            c'4
                            ~
                            c'16
                            ~
                        }
                        \tuplet 5/4
                        {
                            c'4
                            ~
                            c'16
                            ~
                        }
                        \tuplet 5/4
                        {
                            c'4
                            c'16
                        }
                    }
                }
            }

        The first three tuplets in the example above qualify as sustained:

            >>> staff = lilypond_file["Score"]
            >>> for tuplet in abjad.select.tuplets(staff):
            ...     abjad.get.sustained(tuplet)
            ...
            True
            True
            True
            False

        Tuplets 0 and 1 each contain only a single **tuplet-initial** attack. Tuplet 2
        contains no attack at all. All three fill their duration completely.

        Tuplet 3 contains a **nonintial** attack that rearticulates the tuplet's duration
        midway through the course of the figure. Tuplet 3 does not qualify as sustained.

    ..  container:: example

        Rewrite sustained tuplets like this:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.rewrite_sustained(container)
        ...     rmakers.beam(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 1/1
                        {
                            \time 4/16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'4
                            ~
                        }
                        \tuplet 5/4
                        {
                            c'4
                            c'16
                        }
                    }
                }
            }

    ..  container:: example

        Rewrite sustained tuplets -- and then extract the trivial tuplets that result --
        like this:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     container = abjad.Container(tuplets)
        ...     rmakers.beam(container)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.rewrite_sustained(container)
        ...     rmakers.extract_trivial(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \time 4/16
                        c'4
                        c'4
                        ~
                        c'4
                        ~
                        \tuplet 5/4
                        {
                            c'4
                            c'16
                        }
                    }
                }
            }

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.rewrite_sustained(tuplets[-2:])
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/2
                        {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/2
                        {
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        Sustains every other tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.rewrite_sustained(tuplets)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                        \time 4/8
                        c'2
                        ~
                        \time 3/8
                        c'8
                        c'4
                        \time 4/8
                        c'2
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    for tuplet in abjad.select.tuplets(argument):
        if not abjad.get.sustained(tuplet):
            continue
        duration = abjad.get.duration(tuplet)
        leaves = abjad.select.leaves(tuplet)
        last_leaf = leaves[-1]
        if abjad.get.has_indicator(last_leaf, abjad.Tie):
            last_leaf_has_tie = True
        else:
            last_leaf_has_tie = False
        for leaf in leaves[1:]:
            tuplet.remove(leaf)
        assert len(tuplet) == 1, repr(tuplet)
        if not last_leaf_has_tie:
            abjad.detach(abjad.Tie, tuplet[-1])
        abjad.mutate._set_leaf_duration(tuplet[0], duration, tag=tag)
        tuplet.multiplier = (1, 1)


def split_measures(voice, *, durations=None, tag: abjad.Tag | None = None) -> None:
    r"""
    Splits measures in ``voice``.

    Uses ``durations`` when ``durations`` is not none.

    Tries to find time signature information (from the staff that contains ``voice``)
    when ``durations`` is none.
    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    if not durations:
        # TODO: implement abjad.get() method for measure durations
        staff = abjad.get.parentage(voice).parent
        assert isinstance(staff, abjad.Staff)
        voice_ = staff["TimeSignatureVoice"]
        assert isinstance(voice_, abjad.Voice)
        durations = [abjad.get.duration(_) for _ in voice_]
    total_duration = sum(durations)
    music_duration = abjad.get.duration(voice)
    if total_duration != music_duration:
        message = f"Total duration of splits is {total_duration!s}"
        message += f" but duration of music is {music_duration!s}:"
        message += f"\ndurations: {durations}."
        message += f"\nvoice: {voice[:]}."
        raise Exception(message)
    abjad.mutate.split(voice[:], durations=durations)


def swap_length_1(argument) -> None:
    """
    Swaps length-1 tuplets in ``argument`` with containers.
    """
    tuplets = abjad.select.tuplets(argument)
    for tuplet in tuplets:
        if len(tuplet) == 1:
            container = abjad.Container()
            abjad.mutate.swap(tuplet, container)


def swap_skip_filled(argument) -> None:
    """
    Swaps skip-filled tuplets in ``argument`` with containers.
    """
    tuplets = abjad.select.tuplets(argument)
    for tuplet in tuplets:
        if all(isinstance(_, abjad.Skip) for _ in tuplet):
            container = abjad.Container()
            abjad.mutate.swap(tuplet, container)


def swap_trivial(argument) -> None:
    r"""
    Swaps trivial tuplets in ``argument`` with containers.

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     tuplets = abjad.select.tuplets(tuplets)[-2:]
        ...     rmakers.swap_trivial(tuplets)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/3
                        {
                            \time 3/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/3
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    tuplets = abjad.select.tuplets(argument)
    for tuplet in tuplets:
        if tuplet.trivial():
            container = abjad.Container()
            abjad.mutate.swap(tuplet, container)


def tie(argument, *, tag: abjad.Tag | None = None) -> None:
    r"""
    Attaches ties to pitched leaves in ``argument``.

    Attaches tie to last pitched leaf in each nonlast tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(tuplets)[:-1]
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Ties the last leaf of nonlast tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [5, 3, 3, 3], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(tuplets)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \time 4/8
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        ~
                        \time 4/8
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                }
            }

    ..  container:: example

        Ties across every other tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [5, 3, 3, 3], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.get(tuplets[:-1], [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \time 4/8
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        \time 4/8
                        c'4
                        ~
                        c'16
                        [
                        c'8.
                        ]
                        ~
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                }
            }

    ..  container:: example

        TIE-CONSECUTIVE-NOTES RECIPE:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [5, -3, 3, 3], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.untie(voice)
        ...     runs = abjad.select.runs(voice)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in runs]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \time 4/8
                        c'4
                        ~
                        c'16
                        r8.
                        \time 3/8
                        c'8.
                        [
                        ~
                        c'8.
                        ]
                        ~
                        \time 4/8
                        c'4
                        ~
                        c'16
                        r8.
                        \time 3/8
                        c'8.
                        [
                        ~
                        c'8.
                        ]
                    }
                }
            }


    ..  container:: example

        Attaches ties to nonlast notes in each tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     rmakers.untie(notes)
        ...     rmakers.tie(notes)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    for leaf in abjad.select.leaves(argument, pitched=True):
        tie = abjad.Tie()
        abjad.attach(tie, leaf, tag=tag)


def time_signatures(pairs: list[tuple[int, int]]) -> list[abjad.TimeSignature]:
    """
    Makes time signatures from ``pairs``.

    Documentation helper.
    """
    assert all(isinstance(_, tuple) for _ in pairs), repr(pairs)
    return [abjad.TimeSignature(_) for _ in pairs]


def tremolo_container(argument, count: int, *, tag: abjad.Tag | None = None) -> None:
    r"""
    Replaces pitched leaves in ``argument`` with tremolo containers.

    Repeats figures two times each:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     groups = [abjad.select.get(_, [0, -1]) for _ in notes]
        ...     rmakers.tremolo_container(groups, 2)
        ...     rmakers.extract_trivial(voice)
        ...     containers = abjad.select.components(voice, abjad.TremoloContainer)
        ...     result = [abjad.slur(_) for _ in containers]
        ...     rmakers.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \repeat tremolo 2
                        {
                            \time 4/4
                            c'16
                            (
                            c'16
                            )
                        }
                        c'4
                        c'4
                        \repeat tremolo 2
                        {
                            c'16
                            (
                            c'16
                            )
                        }
                        \repeat tremolo 2
                        {
                            \time 3/4
                            c'16
                            (
                            c'16
                            )
                        }
                        c'4
                        \repeat tremolo 2
                        {
                            c'16
                            (
                            c'16
                            )
                        }
                    }
                }
            }

        Repeats figures four times each:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [4])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     groups = [abjad.select.get(_, [0, -1]) for _ in notes]
        ...     rmakers.tremolo_container(groups, 4)
        ...     rmakers.extract_trivial(voice)
        ...     containers = abjad.select.components(voice, abjad.TremoloContainer)
        ...     result = [abjad.slur(_) for _ in containers]
        ...     rmakers.attach_time_signatures(voice, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 4), (3, 4)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \repeat tremolo 4
                        {
                            \time 4/4
                            c'32
                            (
                            c'32
                            )
                        }
                        c'4
                        c'4
                        \repeat tremolo 4
                        {
                            c'32
                            (
                            c'32
                            )
                        }
                        \repeat tremolo 4
                        {
                            \time 3/4
                            c'32
                            (
                            c'32
                            )
                        }
                        c'4
                        \repeat tremolo 4
                        {
                            c'32
                            (
                            c'32
                            )
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    for leaf in abjad.select.leaves(argument, pitched=True):
        container_duration = leaf.written_duration
        note_duration = container_duration / (2 * count)
        left_note = abjad.Note("c'", note_duration)
        right_note = abjad.Note("c'", note_duration)
        container = abjad.TremoloContainer(count, [left_note, right_note], tag=tag)
        abjad.mutate.replace(leaf, container)


def trivialize(argument) -> None:
    r"""
    Trivializes tuplets in ``argument``.

    Leaves trivializable tuplets as-is when no tuplet command is given. The tuplets
    in measures 2 and 4 can be written as trivial tuplets, but they are not:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tuplet 3/2
                        {
                            \time 4/8
                            c'4.
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tuplet 3/2
                        {
                            \time 4/8
                            c'4.
                            c'4.
                        }
                    }
                }
            }

        Rewrites trivializable tuplets as trivial (1:1) tuplets when ``trivialize`` is
        true:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.trivialize(voice)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            c'4
                        }
                    }
                }
            }

        REGRESSION #907a. Rewrites trivializable tuplets even when tuplets contain
        multiple ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.trivialize(voice)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets[:-1]]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            c'8.
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            c'4
                        }
                    }
                }
            }

        REGRESSION #907b. Rewrites trivializable tuplets even when tuplets contain very
        long ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.trivialize(voice)
        ...     notes = abjad.select.notes(voice)[:-1]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            ~
                            c'8.
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            ~
                            c'4
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'8.
                            [
                            ~
                            c'8.
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 4/8
                            c'4
                            ~
                            c'4
                        }
                    }
                }
            }

    """
    for tuplet in abjad.select.tuplets(argument):
        tuplet.trivialize()


def unbeam(argument, *, smart: bool = False, tag: abjad.Tag | None = None) -> None:
    r"""
    Unbeams leaves in ``argument``.

    Adjusts adjacent start- and stop-beams when ``smart=True``.

    Unbeams 1 note:

    ..  container:: example

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[0], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        [
                        e'8
                        f'8
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[1], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        [
                        f'8
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[2], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        ]
                        e'8
                        f'8
                        [
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[3], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        ]
                        f'8
                        g'8
                        [
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[4], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        f'8
                        ]
                        g'8
                        a'8
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[5], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        f'8
                        g'8
                        ]
                        a'8
                    }
                }
            >>

    ..  container:: example

        Unbeams 2 notes:

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[:2], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        [
                        f'8
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[1:3], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        f'8
                        [
                        g'8
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[2:4], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        ]
                        e'8
                        f'8
                        g'8
                        [
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[3:5], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        ]
                        f'8
                        g'8
                        a'8
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' e' f' g' a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[4:], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        [
                        d'8
                        e'8
                        f'8
                        ]
                        g'8
                        a'8
                    }
                }
            >>

    ..  container:: example

        Unbeams 1 note:

        >>> voice = abjad.Voice("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[0], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        [
                        f'8
                        ]
                        g'8
                        [
                        a'8
                        ]
                    }
                }
            >>

        >>> voice = abjad.Voice("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> staff = abjad.Staff([voice])
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(voice[1], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    \new Voice
                    {
                        c'8
                        d'8
                        e'8
                        [
                        f'8
                        ]
                        g'8
                        [
                        a'8
                        ]
                    }
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(staff[2], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    f'8
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(staff[3], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    f'8
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(staff[4], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    [
                    f'8
                    ]
                    g'8
                    a'8
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(staff[5], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    [
                    f'8
                    ]
                    g'8
                    a'8
                }
            >>

    ..  container:: example

        Unbeams 2 notes:

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(staff[:2], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    d'8
                    e'8
                    [
                    f'8
                    ]
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(staff[1:3], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    d'8
                    e'8
                    f'8
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(staff[2:4], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    f'8
                    g'8
                    [
                    a'8
                    ]
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(staff[3:5], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    f'8
                    g'8
                    a'8
                }
            >>

        >>> staff = abjad.Staff("c'8 [ d' ] e' [ f' ] g' [ a' ]")
        >>> score = abjad.Score([staff])
        >>> abjad.setting(score).autoBeaming = False
        >>> rmakers.unbeam(staff[4:], smart=True)
        >>> abjad.show(score) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \new Score
            \with
            {
                autoBeaming = ##f
            }
            <<
                \new Staff
                {
                    c'8
                    [
                    d'8
                    ]
                    e'8
                    [
                    f'8
                    ]
                    g'8
                    a'8
                }
            >>

    """
    leaves = abjad.select.leaves(argument)
    leaf: abjad.Leaf | None
    for leaf in leaves:
        abjad.detach(abjad.BeamCount, leaf)
        abjad.detach(abjad.StartBeam, leaf)
        abjad.detach(abjad.StopBeam, leaf)
    if smart is True:
        tag = tag or abjad.Tag()
        tag = tag.append(_function_name(inspect.currentframe()))
        unmatched_start_beam = False
        leaf = leaves[0]
        leaf = abjad.get.leaf(leaf, -1)
        if leaf is not None:
            if abjad.get.has_indicator(leaf, abjad.StopBeam):
                pass
            elif abjad.get.has_indicator(leaf, abjad.StartBeam):
                abjad.detach(abjad.StartBeam, leaf)
            else:
                while True:
                    leaf = abjad.get.leaf(leaf, -1)
                    if leaf is None:
                        break
                    if abjad.get.has_indicator(leaf, abjad.StopBeam):
                        break
                    if abjad.get.has_indicator(leaf, abjad.StartBeam):
                        unmatched_start_beam = True
                        break
        unmatched_stop_beam = False
        leaf = leaves[-1]
        leaf = abjad.get.leaf(leaf, 1)
        if leaf is not None:
            if abjad.get.has_indicator(leaf, abjad.StartBeam):
                pass
            elif abjad.get.has_indicator(leaf, abjad.StopBeam):
                abjad.detach(abjad.StopBeam, leaf)
            else:
                while True:
                    leaf = abjad.get.leaf(leaf, 1)
                    if leaf is None:
                        break
                    if abjad.get.has_indicator(leaf, abjad.StartBeam):
                        break
                    if abjad.get.has_indicator(leaf, abjad.StopBeam):
                        unmatched_stop_beam = True
                        break
        if unmatched_start_beam is True:
            leaf = leaves[0]
            leaf = abjad.get.leaf(leaf, -1)
            abjad.attach(abjad.StopBeam(), leaf, tag=tag)
        if unmatched_stop_beam is True:
            leaf = leaves[-1]
            leaf = abjad.get.leaf(leaf, 1)
            abjad.attach(abjad.StartBeam(), leaf, tag=tag)


def untie(argument) -> None:
    r"""
    Unties leaves in ``argument``.

    Attaches ties to nonlast notes; then detaches ties from select notes:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     notes = abjad.select.notes(voice)[:-1]
        ...     rmakers.tie(notes)
        ...     notes = abjad.select.notes(voice)
        ...     notes = abjad.select.get(notes, [0], 4)
        ...     rmakers.untie(notes)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            ~
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            ~
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            ~
                            c'8
                            ]
                            ~
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            ~
                            c'8
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Attaches repeat-ties to nonfirst notes; then detaches ties from select notes:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[1])
        ...     voice = abjad.Voice(tuplets)
        ...     notes = abjad.select.notes(voice)[1:]
        ...     rmakers.repeat_tie(notes)
        ...     notes = abjad.select.notes(voice)
        ...     notes = abjad.select.get(notes, [0], 4)
        ...     rmakers.untie(notes)
        ...     rmakers.beam(voice)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> lilypond_file = make_lilypond_file(pairs)
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
                        \tuplet 3/2
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            \repeatTie
                            c'8
                            ]
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            c'8
                            \repeatTie
                            c'8
                            ]
                            \repeatTie
                        }
                        \tuplet 3/2
                        {
                            c'8
                            [
                            \repeatTie
                            c'8
                            c'8
                            ]
                            \repeatTie
                        }
                    }
                }
            }

    """
    for leaf in abjad.select.leaves(argument):
        abjad.detach(abjad.Tie, leaf)
        abjad.detach(abjad.RepeatTie, leaf)


def wrap_in_time_signature_staff(
    components, time_signatures: list[abjad.TimeSignature]
) -> abjad.Voice:
    """
    Wraps ``components`` in two-voice staff.

    One voice for ``components`` and another voice for ``time_signatures``.

    See ``rmakers.rewrite_meter()`` for examples of this function.
    """
    assert all(isinstance(_, abjad.Component) for _ in components), repr(components)
    assert all(isinstance(_, abjad.TimeSignature) for _ in time_signatures), repr(
        time_signatures
    )
    score = _make_time_signature_staff(time_signatures)
    music_voice = score["RhythmMaker.Music"]
    music_voice.extend(components)
    _validate_tuplets(music_voice)
    return music_voice


def written_duration(argument, duration: abjad.typings.Duration) -> None:
    """
    Sets written duration of leaves in ``argument``.
    """
    duration_ = abjad.Duration(duration)
    leaves = abjad.select.leaves(argument)
    for leaf in leaves:
        old_duration = leaf.written_duration
        if duration_ == old_duration:
            continue
        leaf.written_duration = duration_
        multiplier = old_duration / duration_
        pair = abjad.duration.pair(multiplier)
        leaf.multiplier = pair
