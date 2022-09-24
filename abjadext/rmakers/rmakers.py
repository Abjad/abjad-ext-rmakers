import dataclasses
import math
import types
import typing

import abjad


def _apply_ties_to_split_notes(
    tuplets,
    unscaled_end_counts,
    unscaled_preamble,
    unscaled_talea,
    self_talea,
):
    leaves = abjad.select.leaves(tuplets)
    written_durations = [leaf.written_duration for leaf in leaves]
    written_durations = list(written_durations)
    total_duration = abjad.sequence.weight(written_durations)
    preamble_weights = []
    if unscaled_preamble:
        preamble_weights = []
        for numerator in unscaled_preamble:
            pair = (numerator, self_talea.denominator)
            duration = abjad.Duration(*pair)
            weight = abs(duration)
            preamble_weights.append(weight)
    preamble_duration = sum(preamble_weights)
    if total_duration <= preamble_duration:
        preamble_parts = abjad.sequence.partition_by_weights(
            written_durations,
            weights=preamble_weights,
            allow_part_weights=abjad.MORE,
            cyclic=True,
            overhang=True,
        )
        talea_parts = []
    else:
        assert preamble_duration < total_duration
        preamble_parts = abjad.sequence.partition_by_weights(
            written_durations,
            weights=preamble_weights,
            allow_part_weights=abjad.EXACT,
            cyclic=False,
            overhang=False,
        )
        talea_weights = []
        for numerator in unscaled_talea:
            pair = (numerator, self_talea.denominator)
            weight = abs(abjad.Duration(*pair))
            talea_weights.append(weight)
        preamble_length = len(abjad.sequence.flatten(preamble_parts))
        talea_written_durations = written_durations[preamble_length:]
        talea_parts = abjad.sequence.partition_by_weights(
            talea_written_durations,
            weights=talea_weights,
            allow_part_weights=abjad.MORE,
            cyclic=True,
            overhang=True,
        )
    parts = preamble_parts + talea_parts
    part_durations = abjad.sequence.flatten(parts)
    assert part_durations == list(written_durations)
    counts = [len(part) for part in parts]
    parts = abjad.sequence.partition_by_counts(leaves, counts)
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


def _do_grace_container_command(
    argument,
    counts,
    beam_and_slash=False,
    class_=None,
    talea=None,
):
    leaves = abjad.select.leaves(argument, grace=False)
    assert all(isinstance(_, int) for _ in counts), repr(counts)
    cyclic_counts = abjad.CyclicTuple(counts)
    start = 0
    for i, leaf in enumerate(leaves):
        count = cyclic_counts[i]
        if not count:
            continue
        stop = start + count
        durations = talea[start:stop]
        notes = abjad.makers.make_leaves([0], durations)
        if beam_and_slash:
            abjad.beam(notes)
            literal = abjad.LilyPondLiteral(r"\slash")
            abjad.attach(literal, notes[0])
        container = class_(notes)
        abjad.attach(container, leaf)


def _fix_rounding_error(selection, total_duration, interpolation):
    selection_duration = abjad.get.duration(selection)
    if not selection_duration == total_duration:
        needed_duration = total_duration - abjad.get.duration(selection[:-1])
        multiplier = needed_duration / interpolation.written_duration
        selection[-1].multiplier = multiplier


def _get_interpolations(self_interpolations, self_previous_state):
    specifiers_ = self_interpolations
    if specifiers_ is None:
        specifiers_ = abjad.CyclicTuple([Interpolation()])
    elif isinstance(specifiers_, Interpolation):
        specifiers_ = abjad.CyclicTuple([specifiers_])
    else:
        specifiers_ = abjad.CyclicTuple(specifiers_)
    string = "divisions_consumed"
    divisions_consumed = self_previous_state.get(string, 0)
    specifiers_ = abjad.sequence.rotate(specifiers_, n=-divisions_consumed)
    specifiers_ = abjad.CyclicTuple(specifiers_)
    return specifiers_


def _incised_numeric_map_to_leaf_selections(
    numeric_map, lcd, *, spelling=None, tag=None
):
    selections = []
    for numeric_map_part in numeric_map:
        numeric_map_part = [_ for _ in numeric_map_part if _ != abjad.Duration(0)]
        selection = _make_leaves_from_talea(
            numeric_map_part,
            lcd,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            increase_monotonic=spelling.increase_monotonic,
            tag=tag,
        )
        selections.append(selection)
    return selections


def _interpolate_cosine(y1, y2, mu) -> float:
    mu2 = (1 - math.cos(mu * math.pi)) / 2
    return y1 * (1 - mu2) + y2 * mu2


def _interpolate_divide(
    total_duration, start_duration, stop_duration, exponent="cosine"
) -> str | list[float]:
    """
    Divides ``total_duration`` into durations computed from interpolating between
    ``start_duration`` and ``stop_duration``.

    ..  container:: example

        >>> rmakers.rmakers._interpolate_divide(
        ...     total_duration=10,
        ...     start_duration=1,
        ...     stop_duration=1,
        ...     exponent=1,
        ... )
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        >>> sum(_)
        10.0

        >>> rmakers.rmakers._interpolate_divide(
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


def _interpolate_divide_multiple(
    total_durations, reference_durations, exponent="cosine"
) -> list[float]:
    """
    Interpolates ``reference_durations`` such that the sum of the resulting
    interpolated values equals the given ``total_durations``.

    ..  container:: example

        >>> durations = rmakers.rmakers._interpolate_divide_multiple(
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
        ...     rmakers.rmakers._interpolate_exponential(100, 200, mu, exponent=1)
        ...
        100
        125.0
        150.0
        175.0
        200

        Exponents greater than 1 generate ritardandi:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.rmakers._interpolate_exponential(100, 200, mu, exponent=2)
        ...
        100
        106.25
        125.0
        156.25
        200

        Exponents less than 1 generate accelerandi:

        >>> for mu in (0, 0.25, 0.5, 0.75, 1):
        ...     rmakers.rmakers._interpolate_exponential(100, 200, mu, exponent=0.5)
        ...
        100.0
        150.0
        170.71067811865476
        186.60254037844388
        200.0

    """
    result = y1 * (1 - mu**exponent) + y2 * mu**exponent
    return result


def _is_accelerando(selection):
    first_leaf = abjad.select.leaf(selection, 0)
    last_leaf = abjad.select.leaf(selection, -1)
    first_duration = abjad.get.duration(first_leaf)
    last_duration = abjad.get.duration(last_leaf)
    if last_duration < first_duration:
        return True
    return False


def _is_ritardando(selection):
    first_leaf = abjad.select.leaf(selection, 0)
    last_leaf = abjad.select.leaf(selection, -1)
    first_duration = abjad.get.duration(first_leaf)
    last_duration = abjad.get.duration(last_leaf)
    if first_duration < last_duration:
        return True
    return False


def _make_accelerando(
    total_duration, interpolations, index, *, tag: abjad.Tag = abjad.Tag()
) -> abjad.Tuplet:
    """
    Makes notes with LilyPond multipliers equal to ``total_duration``.

    Total number of notes not specified: total duration is specified instead.

    Selects interpolation specifier at ``index`` in ``interpolations``.

    Computes duration multipliers interpolated from interpolation specifier start to
    stop.

    Sets note written durations according to interpolation specifier.
    """
    total_duration = abjad.Duration(total_duration)
    interpolation = interpolations[index]
    durations = _interpolate_divide(
        total_duration=total_duration,
        start_duration=interpolation.start_duration,
        stop_duration=interpolation.stop_duration,
    )
    if durations == "too small":
        notes = abjad.makers.make_notes([0], [total_duration], tag=tag)
        tuplet = abjad.Tuplet((1, 1), notes, tag=tag)
        return tuplet
    durations = _round_durations(durations, 2**10)
    notes = []
    for i, duration in enumerate(durations):
        written_duration = interpolation.written_duration
        multiplier = duration / written_duration
        note = abjad.Note(0, written_duration, multiplier=multiplier, tag=tag)
        notes.append(note)
    _fix_rounding_error(notes, total_duration, interpolation)
    tuplet = abjad.Tuplet((1, 1), notes, tag=tag)
    return tuplet


def _make_accelerando_rhythm_maker_music(
    divisions,
    *self_interpolations,
    self_previous_state,
    self_spelling,
    self_tag,
):
    interpolations = _get_interpolations(self_interpolations, self_previous_state)
    tuplets = []
    for i, division in enumerate(divisions):
        tuplet = _make_accelerando(division, interpolations, i, tag=self_tag)
        tuplets.append(tuplet)
    return tuplets


def _make_beamable_groups(components, durations):
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
            if component_timespan.happens_during_timespan(group_timespan):
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


def _make_division_incised_numeric_map(
    divisions,
    prefix_talea,
    prefix_counts,
    suffix_talea,
    suffix_counts,
    extra_counts,
    incise,
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
            numerator = division.numerator + (prolation_addendum % division.numerator)
        numeric_map_part = _make_numeric_map_part(numerator, prefix, suffix, incise)
        numeric_map.append(numeric_map_part)
    return numeric_map


def _make_even_division_rhythm_maker_music(
    divisions,
    self_denominators,
    *,
    self_denominator=None,
    self_extra_counts=None,
    self_previous_state=None,
    self_spelling=None,
    self_tag=None,
):
    tuplets = []
    assert isinstance(self_previous_state, dict)
    divisions_consumed = self_previous_state.get("divisions_consumed", 0)
    divisions = [abjad.NonreducedFraction(_) for _ in divisions]
    denominators_ = list(self_denominators)
    denominators_ = abjad.sequence.rotate(denominators_, -divisions_consumed)
    denominators = abjad.CyclicTuple(denominators_)
    extra_counts_ = self_extra_counts or [0]
    extra_counts__ = list(extra_counts_)
    extra_counts__ = abjad.sequence.rotate(extra_counts__, -divisions_consumed)
    extra_counts = abjad.CyclicTuple(extra_counts__)
    for i, division in enumerate(divisions):
        if not abjad.math.is_positive_integer_power_of_two(division.denominator):
            message = "non-power-of-two divisions not implemented:"
            message += f" {division}."
            raise Exception(message)
        denominator_ = denominators[i]
        extra_count = extra_counts[i]
        basic_duration = abjad.Duration(1, denominator_)
        unprolated_note_count = None
        if division < 2 * basic_duration:
            notes = abjad.makers.make_notes([0], [division], tag=self_tag)
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
            notes = abjad.makers.make_notes([0], durations, tag=self_tag)
            assert all(_.written_duration.denominator == denominator_ for _ in notes)
        tuplet_duration = abjad.Duration(division)
        tuplet = abjad.Tuplet.from_duration(tuplet_duration, notes, tag=self_tag)
        if self_denominator == "from_counts" and unprolated_note_count is not None:
            denominator = unprolated_note_count
            tuplet.denominator = denominator
        elif isinstance(self_denominator, int):
            tuplet.denominator = self_denominator
        tuplets.append(tuplet)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    return tuplets


def _make_incised_rhythm_maker_music(
    divisions, *, extra_counts, incise, spelling, tag
) -> list[abjad.Tuplet]:
    prepared = _prepare_incised_input(incise, extra_counts)
    counts = types.SimpleNamespace(
        prefix_talea=prepared.prefix_talea,
        suffix_talea=prepared.suffix_talea,
        extra_counts=prepared.extra_counts,
    )
    talea_denominator = incise.talea_denominator
    scaled = _scale_rhythm_maker_input(divisions, talea_denominator, counts)
    if not incise.outer_divisions_only:
        numeric_map = _make_division_incised_numeric_map(
            scaled.divisions,
            scaled.counts.prefix_talea,
            prepared.prefix_counts,
            scaled.counts.suffix_talea,
            prepared.suffix_counts,
            scaled.counts.extra_counts,
            incise,
        )
    else:
        assert incise.outer_divisions_only
        numeric_map = _make_output_incised_numeric_map(
            scaled.divisions,
            scaled.counts.prefix_talea,
            prepared.prefix_counts,
            scaled.counts.suffix_talea,
            prepared.suffix_counts,
            scaled.counts.extra_counts,
            incise,
        )
    selections = _incised_numeric_map_to_leaf_selections(
        numeric_map, scaled.lcd, spelling=spelling, tag=tag
    )
    tuplets = _make_talea_rhythm_maker_tuplets(scaled.divisions, selections, tag)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets)
    return tuplets


def _make_leaves_from_talea(
    talea,
    talea_denominator,
    increase_monotonic=None,
    forbidden_note_duration=None,
    forbidden_rest_duration=None,
    tag: abjad.Tag = abjad.Tag(),
):
    assert all(_ != 0 for _ in talea), repr(talea)
    result: list[abjad.Leaf | abjad.Tuplet] = []
    pitches: list[int | None]
    for note_value in talea:
        if 0 < note_value:
            pitches = [0]
        else:
            pitches = [None]
        division = abjad.Duration(abs(note_value), talea_denominator)
        durations = [division]
        leaves = abjad.makers.make_leaves(
            pitches,
            durations,
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            tag=tag,
        )
        if (
            1 < len(leaves)
            and abjad.get.logical_tie(leaves[0]).is_trivial
            and not isinstance(leaves[0], abjad.Rest)
        ):
            abjad.tie(leaves)
        result.extend(leaves)
    return result


def _make_middle_of_numeric_map_part(middle, incise):
    assert isinstance(incise, Incise), repr(incise)
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


def _make_note_rhythm_maker_music(
    divisions,
    *,
    spelling=None,
    tag=None,
) -> list[list[abjad.Leaf | abjad.Tuplet]]:
    selections = []
    for division in divisions:
        selection = abjad.makers.make_leaves(
            pitches=0,
            durations=[division],
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        selections.append(list(selection))
    return selections


def _make_numeric_map(
    divisions, preamble, talea, extra_counts, end_counts, read_talea_once_only
):
    assert all(isinstance(_, int) for _ in end_counts), repr(end_counts)
    assert all(isinstance(_, int) for _ in preamble), repr(preamble)
    for count in talea:
        assert isinstance(count, int) or count in "+-", repr(talea)
    if "+" in talea or "-" in talea:
        assert not preamble, repr(preamble)
    prolated_divisions = _make_prolated_divisions(divisions, extra_counts)
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
    result = _split_talea_extended_to_weights(
        preamble, read_talea_once_only, talea, prolated_numerators
    )
    if end_counts:
        end_counts = list(end_counts)
        end_weight = abjad.sequence.weight(end_counts)
        division_weights = [abjad.sequence.weight(_) for _ in result]
        counts = abjad.sequence.flatten(result)
        counts_weight = abjad.sequence.weight(counts)
        assert end_weight <= counts_weight, repr(end_counts)
        left = counts_weight - end_weight
        right = end_weight
        counts = abjad.sequence.split(counts, [left, right])
        counts = counts[0] + end_counts
        assert abjad.sequence.weight(counts) == counts_weight
        result = abjad.sequence.partition_by_weights(counts, division_weights)
    for sequence in result:
        assert all(isinstance(_, int) for _ in sequence), repr(sequence)
    return result, expanded_talea


def _make_numeric_map_part(numerator, prefix, suffix, incise, *, is_note_filled=True):
    prefix_weight = abjad.math.weight(prefix)
    suffix_weight = abjad.math.weight(suffix)
    middle = numerator - prefix_weight - suffix_weight
    if numerator < prefix_weight:
        weights = [numerator]
        prefix = list(prefix)
        prefix = abjad.sequence.split(prefix, weights, cyclic=False, overhang=False)[0]
    middle = _make_middle_of_numeric_map_part(middle, incise)
    suffix_space = numerator - prefix_weight
    if suffix_space <= 0:
        suffix = ()
    elif suffix_space < suffix_weight:
        weights = [suffix_space]
        suffix = list(suffix)
        suffix = abjad.sequence.split(suffix, weights, cyclic=False, overhang=False)[0]
    numeric_map_part = list(prefix) + list(middle) + list(suffix)
    return [abjad.Duration(_) for _ in numeric_map_part]


def _make_output_incised_numeric_map(
    divisions,
    prefix_talea,
    prefix_counts,
    suffix_talea,
    suffix_counts,
    extra_counts,
    incise,
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
        numeric_map_part = _make_numeric_map_part(numerator, prefix, suffix, incise)
        numeric_map.append(numeric_map_part)
    else:
        prolation_addendum = extra_counts[0]
        if isinstance(divisions[0], tuple):
            numerator = divisions[0][0]
        else:
            numerator = divisions[0].numerator
        numerator += prolation_addendum % numerator
        numeric_map_part = _make_numeric_map_part(numerator, prefix, (), incise)
        numeric_map.append(numeric_map_part)
        for i, division in enumerate(divisions[1:-1]):
            index = i + 1
            prolation_addendum = extra_counts[index]
            if isinstance(division, tuple):
                numerator = division[0]
            else:
                numerator = division.numerator
            numerator += prolation_addendum % numerator
            numeric_map_part = _make_numeric_map_part(numerator, (), (), incise)
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
        numeric_map_part = _make_numeric_map_part(numerator, (), suffix, incise)
        numeric_map.append(numeric_map_part)
    return numeric_map


def _make_prolated_divisions(divisions, extra_counts):
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


def _make_state_dictionary(
    *,
    divisions_consumed,
    logical_ties_produced,
    previous_divisions_consumed,
    previous_incomplete_last_note,
    previous_logical_ties_produced,
    state,
):
    divisions_consumed_ = previous_divisions_consumed + divisions_consumed
    state["divisions_consumed"] = divisions_consumed_
    logical_ties_produced_ = previous_logical_ties_produced + logical_ties_produced
    if previous_incomplete_last_note:
        logical_ties_produced_ -= 1
    state["logical_ties_produced"] = logical_ties_produced_
    state = dict(sorted(state.items()))
    return state


def _make_talea_rhythm_make_leaf_lists(numeric_map, talea_denominator, spelling, tag):
    leaf_lists = []
    for map_division in numeric_map:
        leaf_list = _make_leaves_from_talea(
            map_division,
            talea_denominator,
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        leaf_lists.append(leaf_list)
    return leaf_lists


def _make_talea_rhythm_maker_music(
    divisions,
    self_extra_counts,
    self_previous_state,
    self_read_talea_once_only,
    self_spelling,
    self_state,
    self_talea,
    self_tag,
):
    prepared = _prepare_talea_rhythm_maker_input(
        self_extra_counts, self_previous_state, self_talea
    )
    divisions = list(divisions)
    scaled = _scale_rhythm_maker_input(divisions, self_talea.denominator, prepared)
    assert scaled.counts.talea
    if scaled.counts.talea:
        numeric_map, expanded_talea = _make_numeric_map(
            scaled.divisions,
            scaled.counts.preamble,
            scaled.counts.talea,
            scaled.counts.extra_counts,
            scaled.counts.end_counts,
            self_read_talea_once_only,
        )
        if expanded_talea is not None:
            unscaled_talea = expanded_talea
        else:
            unscaled_talea = prepared.talea
        talea_weight_consumed = sum(abjad.sequence.weight(_) for _ in numeric_map)
        leaf_lists = _make_talea_rhythm_make_leaf_lists(
            numeric_map, scaled.lcd, self_spelling, self_tag
        )
        if not scaled.counts.extra_counts:
            tuplets = [abjad.Tuplet(1, _) for _ in leaf_lists]
        else:
            tuplets = _make_talea_rhythm_maker_tuplets(
                scaled.divisions, leaf_lists, self_tag
            )
        _apply_ties_to_split_notes(
            tuplets,
            prepared.end_counts,
            prepared.preamble,
            unscaled_talea,
            self_talea,
        )
    for tuplet in abjad.iterate.components(tuplets, abjad.Tuplet):
        tuplet.normalize_multiplier()
    assert isinstance(self_state, dict)
    advanced_talea = Talea(
        counts=prepared.talea,
        denominator=self_talea.denominator,
        end_counts=prepared.end_counts,
        preamble=prepared.preamble,
    )
    if "+" in prepared.talea or "-" in prepared.talea:
        pass
    elif talea_weight_consumed not in advanced_talea:
        last_leaf = abjad.get.leaf(tuplets, -1)
        if isinstance(last_leaf, abjad.Note):
            self_state["incomplete_last_note"] = True
    string = "talea_weight_consumed"
    assert isinstance(self_previous_state, dict)
    self_state[string] = self_previous_state.get(string, 0)
    self_state[string] += talea_weight_consumed
    return tuplets


def _make_talea_rhythm_maker_tuplets(divisions, leaf_lists, tag):
    assert len(divisions) == len(leaf_lists)
    tuplets = []
    for division, leaf_list in zip(divisions, leaf_lists):
        duration = abjad.Duration(division)
        tuplet = abjad.Tuplet.from_duration(duration, leaf_list, tag=tag)
        tuplets.append(tuplet)
    return tuplets


def _make_time_signature_staff(time_signatures):
    assert time_signatures, repr(time_signatures)
    staff = abjad.Staff(simultaneous=True)
    time_signature_voice = abjad.Voice(name="TimeSignatureVoice")
    for time_signature in time_signatures:
        duration = time_signature.pair
        skip = abjad.Skip(1, multiplier=duration)
        time_signature_voice.append(skip)
        abjad.attach(time_signature, skip, context="Staff")
    staff.append(time_signature_voice)
    staff.append(abjad.Voice(name="RhythmMaker.Music"))
    return staff


def _make_tuplet_rhythm_maker_music(
    divisions,
    self_tuplet_ratios,
    *,
    self_tag=None,
):
    tuplets = []
    tuplet_ratios = abjad.CyclicTuple(self_tuplet_ratios)
    for i, division in enumerate(divisions):
        ratio = tuplet_ratios[i]
        tuplet = abjad.makers.tuplet_from_duration_and_ratio(
            division, ratio, tag=self_tag
        )
        tuplets.append(tuplet)
    return tuplets


def _prepare_incised_input(incise, extra_counts):
    cyclic_prefix_talea = abjad.CyclicTuple(incise.prefix_talea)
    cyclic_prefix_counts = abjad.CyclicTuple(incise.prefix_counts or (0,))
    cyclic_suffix_talea = abjad.CyclicTuple(incise.suffix_talea)
    cyclic_suffix_counts = abjad.CyclicTuple(incise.suffix_counts or (0,))
    cyclic_extra_counts = abjad.CyclicTuple(extra_counts or (0,))
    return types.SimpleNamespace(
        prefix_talea=cyclic_prefix_talea,
        prefix_counts=cyclic_prefix_counts,
        suffix_talea=cyclic_suffix_talea,
        suffix_counts=cyclic_suffix_counts,
        extra_counts=cyclic_extra_counts,
    )


def _prepare_talea_rhythm_maker_input(
    self_extra_counts, self_previous_state, self_talea
):
    talea_weight_consumed = self_previous_state.get("talea_weight_consumed", 0)
    talea = self_talea.advance(talea_weight_consumed)
    end_counts = talea.end_counts or ()
    preamble = talea.preamble or ()
    talea = talea.counts or ()
    talea = abjad.CyclicTuple(talea)
    extra_counts = list(self_extra_counts or [])
    divisions_consumed = self_previous_state.get("divisions_consumed", 0)
    extra_counts = abjad.sequence.rotate(extra_counts, -divisions_consumed)
    extra_counts = abjad.CyclicTuple(extra_counts)
    return types.SimpleNamespace(
        end_counts=end_counts,
        extra_counts=extra_counts,
        preamble=preamble,
        talea=talea,
    )


def _round_durations(durations, denominator):
    durations_ = []
    for duration in durations:
        numerator = int(round(duration * denominator))
        duration_ = abjad.Duration(numerator, denominator)
        durations_.append(duration_)
    return durations_


def _scale_rhythm_maker_input(divisions, talea_denominator, counts):
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
    scaled_counts = types.SimpleNamespace()
    for name, vector in counts.__dict__.items():
        vector = [multiplier * _ for _ in vector]
        cyclic_vector = abjad.CyclicTuple(vector)
        setattr(scaled_counts, name, cyclic_vector)
    assert len(scaled_divisions) == len(divisions)
    assert len(scaled_counts.__dict__) == len(counts.__dict__)
    return types.SimpleNamespace(
        divisions=scaled_divisions, lcd=lcd, counts=scaled_counts
    )


def _split_talea_extended_to_weights(preamble, read_talea_once_only, talea, weights):
    assert abjad.math.all_are_positive_integers(weights)
    preamble_weight = abjad.math.weight(preamble)
    talea_weight = abjad.math.weight(talea)
    weight = abjad.math.weight(weights)
    if read_talea_once_only and preamble_weight + talea_weight < weight:
        message = f"{preamble!s} + {talea!s} is too short"
        message += f" to read {weights} once."
        raise Exception(message)
    if weight <= preamble_weight:
        talea = list(preamble)
        talea = abjad.sequence.truncate(talea, weight=weight)
    else:
        weight -= preamble_weight
        talea = abjad.sequence.repeat_to_weight(talea, weight)
        talea = list(preamble) + list(talea)
    talea = abjad.sequence.split(talea, weights, cyclic=True)
    return talea


def _validate_tuplets(selections):
    for tuplet in abjad.iterate.components(selections, abjad.Tuplet):
        assert abjad.Multiplier(tuplet.multiplier).normalized(), repr(tuplet)
        assert len(tuplet), repr(tuplet)


# CLASSES


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Incise:
    """
    See ``rmakers.incised()`` for examples.
    """

    body_ratio: abjad.typings.Ratio = abjad.Ratio([1])
    fill_with_rests: bool = False
    outer_divisions_only: bool = False
    prefix_counts: typing.Sequence[int] = ()
    prefix_talea: typing.Sequence[int] = ()
    suffix_counts: typing.Sequence[int] = ()
    suffix_talea: typing.Sequence[int] = ()
    talea_denominator: int | None = None

    __documentation_section__ = "Specifiers"

    def __post_init__(self):
        assert isinstance(self.prefix_talea, typing.Sequence), repr(self.prefix_talea)
        assert self._is_integer_tuple(self.prefix_talea)
        assert isinstance(self.prefix_counts, typing.Sequence), repr(self.prefix_counts)
        assert self._is_length_tuple(self.prefix_counts)
        if self.prefix_talea:
            assert self.prefix_counts
        assert isinstance(self.suffix_talea, typing.Sequence), repr(self.suffix_talea)
        assert self._is_integer_tuple(self.suffix_talea)
        assert isinstance(self.suffix_counts, typing.Sequence), repr(self.suffix_counts)
        assert self._is_length_tuple(self.suffix_counts)
        if self.suffix_talea:
            assert self.suffix_counts
        if self.talea_denominator is not None:
            assert abjad.math.is_nonnegative_integer_power_of_two(
                self.talea_denominator
            )
        if self.prefix_talea or self.suffix_talea:
            assert self.talea_denominator is not None
        assert isinstance(self.body_ratio, abjad.Ratio), repr(self.body_ratio)
        assert isinstance(self.fill_with_rests, bool), repr(self.fill_with_rests)
        assert isinstance(self.outer_divisions_only, bool), repr(
            self.outer_divisions_only
        )

    @staticmethod
    def _is_integer_tuple(argument):
        if argument is None:
            return True
        if all(isinstance(_, int) for _ in argument):
            return True
        return False

    @staticmethod
    def _is_length_tuple(argument):
        if argument is None:
            return True
        if abjad.math.all_are_nonnegative_integer_equivalent_numbers(argument):
            if isinstance(argument, tuple | list):
                return True
        return False

    @staticmethod
    def _reverse_tuple(argument):
        if argument is not None:
            return tuple(reversed(argument))


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Interpolation:
    """
    See ``rmakers.accelerando()`` for examples.
    """

    start_duration: abjad.Duration = abjad.Duration(1, 8)
    stop_duration: abjad.Duration = abjad.Duration(1, 16)
    written_duration: abjad.Duration = abjad.Duration(1, 16)

    __documentation_section__ = "Specifiers"

    def __post_init__(self) -> None:
        assert isinstance(self.start_duration, abjad.Duration), repr(
            self.start_duration
        )
        assert isinstance(self.stop_duration, abjad.Duration), repr(self.stop_duration)
        assert isinstance(self.written_duration, abjad.Duration), repr(
            self.written_duration
        )

    def reverse(self) -> "Interpolation":
        """
        Swaps start duration and stop duration of interpolation specifier.

        ..  container:: example

            Changes accelerando specifier to ritardando specifier:

            >>> specifier = rmakers.Interpolation(
            ...     start_duration=abjad.Duration(1, 4),
            ...     stop_duration=abjad.Duration(1, 16),
            ...     written_duration=abjad.Duration(1, 16),
            ... )
            >>> specifier.reverse()
            Interpolation(start_duration=Duration(1, 16), stop_duration=Duration(1, 4), written_duration=Duration(1, 16))

        ..  container:: example

            Changes ritardando specifier to accelerando specifier:

            >>> specifier = rmakers.Interpolation(
            ...     start_duration=abjad.Duration(1, 16),
            ...     stop_duration=abjad.Duration(1, 4),
            ...     written_duration=abjad.Duration(1, 16),
            ... )
            >>> specifier.reverse()
            Interpolation(start_duration=Duration(1, 4), stop_duration=Duration(1, 16), written_duration=Duration(1, 16))

        """
        return type(self)(
            start_duration=self.stop_duration,
            stop_duration=self.start_duration,
            written_duration=self.written_duration,
        )


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Spelling:
    r"""
    Duration spelling specifier.

    ..  container:: example

        Decreases monotically:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=False),
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
                    c'4
                    ~
                    c'16
                    c'4
                    ~
                    c'16
                    [
                    c'8
                    ]
                    ~
                    \time 3/4
                    c'8.
                    c'4
                    ~
                    c'16
                    c'4
                }
            >>

    ..  container:: example

        Increases monotically:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=True),
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
                    c'16
                    ~
                    c'4
                    c'16
                    ~
                    c'4
                    c'8
                    ~
                    \time 3/4
                    c'8.
                    [
                    c'16
                    ]
                    ~
                    c'4
                    c'4
                }
            >>

    ..  container:: example

        Forbids note durations equal to ``1/4`` or greater:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions,
        ...         [1, 1, 1, 1, 4, -4],
        ...         16,
        ...         spelling=rmakers.Spelling(forbidden_note_duration=abjad.Duration(1, 4)),
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'8
                    ~
                    c'8
                    ]
                    r4
                    \time 3/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'8
                    ~
                    c'8
                    ]
                    r4
                }
            >>

    ..  container:: example

        Forbids rest durations equal to ``1/4`` or greater:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions,
        ...         [1, 1, 1, 1, 4, -4],
        ...         16,
        ...         spelling=rmakers.Spelling(forbidden_rest_duration=abjad.Duration(1, 4)),
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    c'4
                    r8
                    r8
                    \time 3/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    c'4
                    r8
                    r8
                }
            >>

    """

    forbidden_note_duration: abjad.Duration | None = None
    forbidden_rest_duration: abjad.Duration | None = None
    increase_monotonic: bool = False

    __documentation_section__ = "Specifiers"

    def __post_init__(self):
        if self.forbidden_note_duration is not None:
            assert isinstance(self.forbidden_note_duration, abjad.Duration), repr(
                self.forbidden_note_duration
            )
        if self.forbidden_rest_duration is not None:
            assert isinstance(self.forbidden_rest_duration, abjad.Duration), repr(
                self.forbidden_rest_duration
            )
        assert isinstance(self.increase_monotonic, bool), repr(self.increase_monotonic)


@dataclasses.dataclass(frozen=True, order=True, slots=True, unsafe_hash=True)
class Talea:
    """
    Talea specifier.

    ..  container:: example

        >>> talea = rmakers.Talea(
        ...     [2, 1, 3, 2, 4, 1, 1],
        ...     16,
        ...     preamble=[1, 1, 1, 1],
        ... )

    ..  container:: example

        Equal to weight of counts:

        >>> rmakers.Talea([1, 2, 3, 4], 16).period
        10

        Rests make no difference:

        >>> rmakers.Talea([1, 2, -3, 4], 16).period
        10

        Denominator makes no difference:

        >>> rmakers.Talea([1, 2, -3, 4], 32).period
        10

        Preamble makes no difference:

        >>> talea = rmakers.Talea(
        ...     [1, 2, -3, 4],
        ...     32,
        ...     preamble=[1, 1, 1],
        ... )

        >>> talea.period
        10

    ..  container:: example

        >>> talea = rmakers.Talea(
        ...     [2, 1, 3, 2, 4, 1, 1],
        ...     16,
        ...     preamble=[1, 1, 1, 1],
        ... )

        >>> talea.preamble
        [1, 1, 1, 1]

    ..  container:: example

        >>> talea = rmakers.Talea(
        ...     [16, -4, 16],
        ...     16,
        ...     preamble=[1],
        ... )

        >>> for i, duration in enumerate(talea):
        ...     duration
        ...
        Duration(1, 16)
        Duration(1, 1)
        Duration(-1, 4)
        Duration(1, 1)

    """

    counts: typing.Sequence[int | str]
    denominator: int
    end_counts: typing.Sequence[int] = ()
    preamble: typing.Sequence[int] = ()

    __documentation_section__ = "Specifiers"

    def __post_init__(self):
        assert isinstance(self.counts, typing.Sequence), repr(self.counts)
        for count in self.counts:
            assert isinstance(count, int) or count in "+-", repr(count)
        assert abjad.math.is_nonnegative_integer_power_of_two(self.denominator)
        assert isinstance(self.end_counts, typing.Sequence), repr(self.end_counts)
        assert all(isinstance(_, int) for _ in self.end_counts)
        assert isinstance(self.preamble, typing.Sequence), repr(self.preamble)
        assert all(isinstance(_, int) for _ in self.preamble)

    def __contains__(self, argument: int) -> bool:
        """
        Is true when talea contains ``argument``.

        ..  container:: example

            With preamble:

            >>> talea = rmakers.Talea(
            ...     [10],
            ...     16,
            ...     preamble=[1, -1, 1],
            ...     )

            >>> for i in range(1, 23 + 1):
            ...     i, i in talea
            ...
            (1, True)
            (2, True)
            (3, True)
            (4, False)
            (5, False)
            (6, False)
            (7, False)
            (8, False)
            (9, False)
            (10, False)
            (11, False)
            (12, False)
            (13, True)
            (14, False)
            (15, False)
            (16, False)
            (17, False)
            (18, False)
            (19, False)
            (20, False)
            (21, False)
            (22, False)
            (23, True)

        """
        assert isinstance(argument, int), repr(argument)
        assert 0 < argument, repr(argument)
        if self.preamble:
            preamble = [abs(_) for _ in self.preamble]
            cumulative = abjad.math.cumulative_sums(preamble)[1:]
            if argument in cumulative:
                return True
            preamble_weight = abjad.sequence.weight(preamble)
        else:
            preamble_weight = 0
        if self.counts is not None:
            counts = [abs(_) for _ in self.counts]
        else:
            counts = []
        cumulative = abjad.math.cumulative_sums(counts)[:-1]
        argument -= preamble_weight
        argument %= self.period
        return argument in cumulative

    def __getitem__(
        self, argument
    ) -> abjad.NonreducedFraction | list[abjad.NonreducedFraction]:
        """
        Gets item or slice identified by ``argument``.

        ..  container:: example

            Gets item at index:

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> talea[0]
            NonreducedFraction(1, 16)

            >>> talea[1]
            NonreducedFraction(1, 16)

        ..  container:: example

            Gets items in slice:

            >>> for duration in talea[:6]:
            ...     duration
            ...
            NonreducedFraction(1, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(2, 16)
            NonreducedFraction(1, 16)

            >>> for duration in talea[2:8]:
            ...     duration
            ...
            NonreducedFraction(1, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(2, 16)
            NonreducedFraction(1, 16)
            NonreducedFraction(3, 16)
            NonreducedFraction(2, 16)

        """
        preamble: list[int | str] = list(self.preamble)
        counts = list(self.counts)
        counts_ = abjad.CyclicTuple(preamble + counts)
        if isinstance(argument, int):
            count = counts_.__getitem__(argument)
            return abjad.NonreducedFraction(count, self.denominator)
        elif isinstance(argument, slice):
            counts_ = counts_.__getitem__(argument)
            result = [
                abjad.NonreducedFraction(count, self.denominator) for count in counts_
            ]
            return result
        raise ValueError(argument)

    def __iter__(self) -> typing.Iterator[abjad.Duration]:
        """
        Iterates talea.

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> for duration in talea:
            ...     duration
            ...
            Duration(1, 16)
            Duration(1, 16)
            Duration(1, 16)
            Duration(1, 16)
            Duration(1, 8)
            Duration(1, 16)
            Duration(3, 16)
            Duration(1, 8)
            Duration(1, 4)
            Duration(1, 16)
            Duration(1, 16)

        """
        for count in self.preamble or []:
            duration = abjad.Duration(count, self.denominator)
            yield duration
        for item in self.counts or []:
            assert isinstance(item, int)
            duration = abjad.Duration(item, self.denominator)
            yield duration

    def __len__(self) -> int:
        """
        Gets length.

        ..  container:: example

            >>> len(rmakers.Talea([2, 1, 3, 2, 4, 1, 1], 16))
            7

        Defined equal to length of counts.
        """
        return len(self.counts or [])

    @property
    def period(self) -> int:
        """
        Gets period of talea.

        ..  container:: example

            Equal to weight of counts:

            >>> rmakers.Talea([1, 2, 3, 4], 16).period
            10

            Rests make no difference:

            >>> rmakers.Talea([1, 2, -3, 4], 16).period
            10

            Denominator makes no difference:

            >>> rmakers.Talea([1, 2, -3, 4], 32).period
            10

            Preamble makes no difference:

            >>> talea = rmakers.Talea(
            ...     [1, 2, -3, 4],
            ...     32,
            ...     preamble=[1, 1, 1],
            ... )

            >>> talea.period
            10

        """
        return abjad.sequence.weight(self.counts)

    def advance(self, weight: int) -> "Talea":
        """
        Advances talea by ``weight``.

        ..  container:: example

            >>> talea = rmakers.Talea(
            ...     [2, 1, 3, 2, 4, 1, 1],
            ...     16,
            ...     preamble=[1, 1, 1, 1],
            ... )

            >>> talea.advance(0)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 1, 1, 1])

            >>> talea.advance(1)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 1, 1])

            >>> talea.advance(2)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 1])

            >>> talea.advance(3)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1])

            >>> talea.advance(4)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=())

            >>> talea.advance(5)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 1, 3, 2, 4, 1, 1])

            >>> talea.advance(6)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[1, 3, 2, 4, 1, 1])

            >>> talea.advance(7)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[3, 2, 4, 1, 1])

            >>> talea.advance(8)
            Talea(counts=[2, 1, 3, 2, 4, 1, 1], denominator=16, end_counts=(), preamble=[2, 2, 4, 1, 1])

        ..  container:: example

            REGRESSION. Works when talea advances by period of talea:

            >>> talea = rmakers.Talea([1, 2, 3, 4], 16)
            >>> talea
            Talea(counts=[1, 2, 3, 4], denominator=16, end_counts=(), preamble=())

            >>> talea.advance(10)
            Talea(counts=[1, 2, 3, 4], denominator=16, end_counts=(), preamble=())

            >>> talea.advance(20)
            Talea(counts=[1, 2, 3, 4], denominator=16, end_counts=(), preamble=())

        """
        assert isinstance(weight, int), repr(weight)
        if weight < 0:
            raise Exception(f"weight {weight} must be nonnegative.")
        if weight == 0:
            return dataclasses.replace(self)
        preamble: list[int | str] = list(self.preamble)
        counts = list(self.counts)
        if weight < abjad.sequence.weight(preamble):
            consumed, remaining = abjad.sequence.split(
                preamble, [weight], overhang=True
            )
            preamble_ = remaining
        elif weight == abjad.sequence.weight(preamble):
            preamble_ = ()
        else:
            assert abjad.sequence.weight(preamble) < weight
            weight -= abjad.sequence.weight(preamble)
            preamble = counts[:]
            while True:
                if weight <= abjad.sequence.weight(preamble):
                    break
                preamble += counts
            if abjad.sequence.weight(preamble) == weight:
                consumed, remaining = preamble[:], ()
            else:
                consumed, remaining = abjad.sequence.split(
                    preamble, [weight], overhang=True
                )
            preamble_ = remaining
        return dataclasses.replace(
            self,
            counts=counts,
            denominator=self.denominator,
            preamble=preamble_,
        )


# FUNCTIONS


def accelerando(
    divisions,
    *interpolations: typing.Sequence[abjad.typings.Duration],
    previous_state: dict = None,
    spelling: Spelling = Spelling(),
    state: dict = None,
    tag: abjad.Tag = abjad.Tag(),
):
    r"""
    Makes accelerando figures in ``divisions``.

    ..  container:: example

        Makes accelerandi:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.feather_beam(container)
        ...     rmakers.duration_bracket(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 20), (1, 8), (1, 16)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.feather_beam(container)
        ...     rmakers.duration_bracket(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 3/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 3/8
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

        Sets duration bracket with no beams:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.duration_bracket(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \time 3/8
                        c'16 * 117/64
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.beam_groups(tuplets)
        ...     rmakers.duration_bracket(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 2
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        \time 3/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 2
                        \time 3/8
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

        Leave feathering turned off here because LilyPond feathers conjoint beams poorly.

    ..  container:: example

        Ties across tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.duration_bracket(container)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.feather_beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.duration_bracket(container)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     tuplets = abjad.select.get(tuplets, [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.feather_beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        c'16 * 63/32
                        [
                        c'16 * 115/64
                        c'16 * 91/64
                        c'16 * 35/32
                        c'16 * 29/32
                        c'16 * 13/16
                        ]
                        ~
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)], [(1, 20), (1, 8), (1, 16)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     leaves = abjad.select.leaves(container)
        ...     leaves = abjad.select.get(leaves, [0, -1])
        ...     rmakers.force_rest(leaves)
        ...     rmakers.feather_beam(
        ...         container, beam_rests=True, stemlet_length=0.75
        ...     )
        ...     rmakers.duration_bracket(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \override Staff.Stem.stemlet-length = 0.75
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \override Staff.Stem.stemlet-length = 0.75
                        \time 3/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \override Staff.Stem.stemlet-length = 0.75
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \override Staff.Stem.stemlet-length = 0.75
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)],
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     rmakers.force_rest(tuplets)
        ...     rmakers.rewrite_rest_filled(container)
        ...     rmakers.extract_trivial(container)
        ...     rmakers.duration_bracket(container)
        ...     rmakers.feather_beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                    \time 3/8
                    r4.
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                    \time 3/8
                    r4.
                }
            >>

    ..  container:: example

        Alternates accelerandi and ritardandi:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)], [(1, 20), (1, 8), (1, 16)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.duration_bracket(container)
        ...     rmakers.feather_beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 3/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.duration_bracket(container)
        ...     rmakers.feather_beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (3, 8), (1, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 5/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        c'16 * 117/64
                        [
                        c'16 * 99/64
                        c'16 * 69/64
                        c'16 * 13/16
                        c'16 * 47/64
                        ]
                    }
                    \revert TupletNumber.text
                    \time 1/8
                    c'8
                }
            >>

    ..  container:: example

        Consumes 3 divisions:

        >>> def make_statal_accelerandi(divisions, previous_state=None):
        ...     if previous_state is None:
        ...         previous_state = {}
        ...     state = {}
        ...     nested_music = rmakers.accelerando(
        ...         divisions,
        ...         [(1, 8), (1, 20), (1, 16)], [(1, 20), (1, 8), (1, 16)],
        ...         previous_state=previous_state,
        ...         state=state,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.duration_bracket(container)
        ...     rmakers.feather_beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music, state

        >>> divisions = [(3, 8), (4, 8), (3, 8)]
        >>> music, state = make_statal_accelerandi(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> state
        {'divisions_consumed': 3, 'logical_ties_produced': 17}

        Advances 3 divisions; then consumes another 3 divisions:

        >>> divisions = [(4, 8), (3, 8), (4, 8)]
        >>> music, state = make_statal_accelerandi(divisions, previous_state=state)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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

        >>> state
        {'divisions_consumed': 6, 'logical_ties_produced': 36}

        Advances 6 divisions; then consumes another 3 divisions:

        >>> divisions = [(3, 8), (4, 8), (3, 8)]
        >>> music, state = make_statal_accelerandi(divisions, previous_state=state)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #left
                        \time 4/8
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
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    \times 1/1
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
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

        >>> state
        {'divisions_consumed': 9, 'logical_ties_produced': 53}

    ..  container:: example

        Tags LilyPond output:

        >>> def make_rhythm(divisions):
        ...     tag = abjad.Tag("ACCELERANDO_RHYTHM_MAKER")
        ...     nested_music = rmakers.accelerando(
        ...         divisions, [(1, 8), (1, 20), (1, 16)], tag=tag
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.feather_beam(container, tag=tag)
        ...     rmakers.duration_bracket(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    %! ACCELERANDO_RHYTHM_MAKER
                    \times 1/1
                    %! ACCELERANDO_RHYTHM_MAKER
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 63/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        [
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 115/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 91/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 35/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 29/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16
                        %! ACCELERANDO_RHYTHM_MAKER
                        ]
                    %! ACCELERANDO_RHYTHM_MAKER
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    %! ACCELERANDO_RHYTHM_MAKER
                    \times 1/1
                    %! ACCELERANDO_RHYTHM_MAKER
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 117/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        [
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 99/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 69/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 47/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        ]
                    %! ACCELERANDO_RHYTHM_MAKER
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    %! ACCELERANDO_RHYTHM_MAKER
                    \times 1/1
                    %! ACCELERANDO_RHYTHM_MAKER
                    {
                        \once \override Beam.grow-direction = #right
                        \time 4/8
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 63/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        [
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 115/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 91/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 35/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 29/32
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16
                        %! ACCELERANDO_RHYTHM_MAKER
                        ]
                    %! ACCELERANDO_RHYTHM_MAKER
                    }
                    \revert TupletNumber.text
                    \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \score
                        {
                            \context Score = "Score"
                            \with
                            {
                                \override SpacingSpanner.spacing-increment = 0.5
                                proportionalNotationDuration = ##f
                            }
                            <<
                                \context RhythmicStaff = "Rhythmic_Staff"
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
                            \layout
                            {
                                indent = 0
                                ragged-right = ##t
                            }
                        }
                    %! ACCELERANDO_RHYTHM_MAKER
                    \times 1/1
                    %! ACCELERANDO_RHYTHM_MAKER
                    {
                        \once \override Beam.grow-direction = #right
                        \time 3/8
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 117/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        [
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 99/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 69/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 13/16
                        %! ACCELERANDO_RHYTHM_MAKER
                        c'16 * 47/64
                        %! ACCELERANDO_RHYTHM_MAKER
                        ]
                    %! ACCELERANDO_RHYTHM_MAKER
                    }
                    \revert TupletNumber.text
                }
            >>

    Set interpolations' ``written_duration`` to ``1/16`` or less for multiple beams.
    """
    interpolations_ = []
    for interpolation in interpolations:
        interpolation_durations = [abjad.Duration(_) for _ in interpolation]
        interpolation_ = Interpolation(*interpolation_durations)
        interpolations_.append(interpolation_)
    previous_state = previous_state or {}
    if state is None:
        state = {}
    tuplets = _make_accelerando_rhythm_maker_music(
        divisions,
        *interpolations_,
        self_previous_state=previous_state,
        self_spelling=spelling,
        self_tag=tag,
    )
    voice = abjad.Voice(tuplets)
    logical_ties_produced = len(abjad.select.logical_ties(voice))
    new_state = _make_state_dictionary(
        divisions_consumed=len(divisions),
        logical_ties_produced=logical_ties_produced,
        previous_divisions_consumed=previous_state.get("divisions_consumed", 0),
        previous_incomplete_last_note=previous_state.get("incomplete_last_note", False),
        previous_logical_ties_produced=previous_state.get("logical_ties_produced", 0),
        state=state,
    )
    tuplets = abjad.mutate.eject_contents(voice)
    state.clear()
    state.update(new_state)
    return tuplets


def after_grace_container(
    argument,
    counts: typing.Sequence[int],
    *,
    beam_and_slash: bool = False,
    talea: Talea = Talea([1], 8),
):
    r"""
    Makes after-grace containers.

    ..  container:: example

        Single after-graces with slurs applied manually:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [4], extra_counts=[2]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.after_grace_container(notes, [1])
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> staff = lilypond_file["Staff"]
        >>> containers = abjad.select.components(staff, abjad.AfterGraceContainer)
        >>> groups = [abjad.select.with_next_leaf(_) for _ in containers]
        >>> result = [abjad.slur(_) for _ in groups]
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
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
                            (
                        }
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        )
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            c'8
                            )
                            (
                        }
                    }
                }
            >>

    ..  container:: example

        Multiple after-graces with ``beam_and_slash=True`` and with slurs applied
        manually:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [4], extra_counts=[2]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.after_grace_container(
        ...         notes, [2, 4], beam_and_slash=True
        ...     )
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> staff = lilypond_file["Staff"]
        >>> containers = abjad.select.components(staff, abjad.AfterGraceContainer)
        >>> groups = [abjad.select.with_next_leaf(_) for _ in containers]
        >>> result = [abjad.slur(_) for _ in groups]
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
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
                            (
                            c'8
                            ]
                        }
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        )
                        c'4
                        c'4
                        c'4
                        \afterGrace
                        c'4
                        {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            )
                            ]
                        }
                    }
                }
            >>

    """
    _do_grace_container_command(
        argument,
        counts=counts,
        beam_and_slash=beam_and_slash,
        class_=abjad.AfterGraceContainer,
        talea=talea,
    )


def beam(
    argument,
    *,
    beam_lone_notes: bool = False,
    beam_rests: bool = False,
    stemlet_length: int | float | None = None,
    tag: abjad.Tag = abjad.Tag("rmakers.beam()"),
) -> None:
    """
    Calls ``abjad.beam()`` on leaves in ``argument``.
    """
    for selection in argument:
        unbeam(selection)
        leaves = abjad.select.leaves(selection)
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
    tag: abjad.Tag = abjad.Tag("rmakers.beam_groups()"),
) -> None:
    """
    Beams ``argument`` groups.
    """
    unbeam(argument)
    durations = []
    components: list[abjad.Component] = []
    for selection in argument:
        duration = abjad.get.duration(selection)
        durations.append(duration)
    for selection in argument:
        if isinstance(selection, abjad.Tuplet):
            components.append(selection)
        else:
            components.extend(selection)
    leaves = abjad.select.leaves(components)
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
    argument,
    counts: typing.Sequence[int],
    *,
    beam_and_slash: bool = False,
    talea: Talea = Talea([1], 8),
):
    r"""
    Makes before-grace containers.

    ..  container:: example

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [4], extra_counts=[2]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     notes = [abjad.select.exclude(_, [0, -1]) for _ in notes]
        ...     rmakers.before_grace_container(notes, [2, 4])
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> staff = lilypond_file["Staff"]
        >>> containers = abjad.select.components(staff, abjad.BeforeGraceContainer)
        >>> result = [abjad.beam(_) for _ in containers]
        >>> groups = [abjad.select.with_next_leaf(_) for _ in containers]
        >>> result = [abjad.slur(_) for _ in groups]
        >>> slash = abjad.LilyPondLiteral(r"\slash")
        >>> result = [abjad.attach(slash, _[0]) for _ in containers]
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                        c'4
                        )
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/4
                        c'4
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            ]
                        }
                        c'4
                        )
                        \grace {
                            \slash
                            c'8
                            [
                            (
                            c'8
                            c'8
                            c'8
                            ]
                        }
                        c'4
                        )
                        c'4
                    }
                }
            >>

    """
    _do_grace_container_command(
        argument,
        counts=counts,
        beam_and_slash=beam_and_slash,
        class_=abjad.BeforeGraceContainer,
        talea=talea,
    )


def denominator(argument, denominator: int | abjad.typings.Duration) -> None:
    r"""
    Sets denominator of every tuplet in ``argument`` to ``denominator``.

    ..  container:: example

        Tuplet numerators and denominators are reduced to numbers that are relatively
        prime when ``denominator`` is set to none. This means that ratios like ``6:4``
        and ``10:8`` do not arise:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(divisions, [(1, 4)])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 4/5
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set in terms of a unit duration when
        ``denominator`` is set to a duration. The setting does not affect the first
        tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(divisions, [(1, 4)])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, (1, 16))
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 8/10
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet in terms 32nd notes. The setting
        affects all tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(divisions, [(1, 4)])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, (1, 32))
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 16/20
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator each tuplet in terms 64th notes. The setting
        affects all tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(divisions, [(1, 4)])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, (1, 64))
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 8/10
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 16/20
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 24/20
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 32/40
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set directly when ``denominator`` is
        set to a positive integer. This example sets the preferred denominator of each
        tuplet to ``8``. Setting does not affect the third tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(divisions, [(1, 4)])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, 8)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 8/10
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 8/10
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``12``. Setting affects all
        tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(divisions, [(1, 4)])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, 12)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.setting(score).proportionalNotationDuration = "#(ly:make-moment 1 28)"
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
                proportionalNotationDuration = #(ly:make-moment 1 28)
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 12/15
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 12/15
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 12/15
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``13``. Setting does not affect
        any tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(divisions, [(1, 4)])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, 13)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> score = lilypond_file["Score"]
        >>> abjad.override(score).TupletBracket.staff_padding = 4.5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.staff-padding = 4.5
            }
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 4/5
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    """
    if isinstance(denominator, tuple):
        denominator = abjad.Duration(denominator)
    for tuplet in abjad.select.tuplets(argument):
        if isinstance(denominator, abjad.Duration):
            unit_duration = denominator
            assert unit_duration.numerator == 1
            duration = abjad.get.duration(tuplet)
            denominator_ = unit_duration.denominator
            nonreduced_fraction = duration.with_denominator(denominator_)
            tuplet.denominator = nonreduced_fraction.numerator
        elif abjad.math.is_positive_integer(denominator):
            tuplet.denominator = denominator
        else:
            raise Exception(f"invalid preferred denominator: {denominator!r}.")


def duration_bracket(argument) -> None:
    """
    Applies durtaion bracket to tuplets in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        duration_ = abjad.get.duration(tuplet)
        notes = abjad.makers.make_leaves([0], [duration_])
        string = abjad.illustrators.selection_to_score_markup_string(notes)
        string = rf"\markup \scale #'(0.75 . 0.75) {string}"
        abjad.override(tuplet).TupletNumber.text = string


def even_division(
    divisions,
    denominators: typing.Sequence[int],
    *,
    denominator: str | int = "from_counts",
    extra_counts: typing.Sequence[int] = (0,),
    previous_state: dict = None,
    spelling: Spelling = Spelling(),
    state: dict = None,
    tag: abjad.Tag = abjad.Tag(),
):
    r"""
    Makes even-division tuplets in ``divisions``.

    ..  container:: example

        Forces tuplet diminution:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[0, 0, 1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.force_diminution(container)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 16), (6, 16), (6, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/8
                    {
                        \time 5/16
                        c'4
                        c'4
                    }
                    \time 6/16
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 6/16
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[0, 0, 1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.force_augmentation(container)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 16), (6, 16), (6, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4
                    {
                        \time 5/16
                        c'8
                        [
                        c'8
                        ]
                    }
                    \time 6/16
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 6/16
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(divisions, [8])
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0], 3)
        ...     rmakers.force_rest(logical_ties)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        r8
                        c'8
                        [
                        c'8
                        ]
                        r8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        ]
                        r8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        ]
                        r8
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        r8
                        c'8
                    }
                }
            >>

        Forces rest at every fourth logical tie:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(divisions, [8])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [3], 4)
        ...     rmakers.force_rest(logical_ties)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        r8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        r8
                        c'8
                        [
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        c'8
                        [
                        c'8
                        ]
                        r8
                        c'8
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        (Forcing rests at the fourth logical tie produces two rests. Forcing rests at the
        eighth logical tie produces only one rest.)

        Forces rest at leaf 0 of every tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(divisions, [8])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     leaves = [abjad.select.leaf(_, 0) for _ in tuplets]
        ...     rmakers.force_rest(leaves)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        r8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
                        r8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        r8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/4
                    {
                        \time 4/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [0], 2)
        ...     rmakers.force_rest(tuplets)
        ...     rmakers.rewrite_rest_filled(container)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    r2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                    \time 4/8
                    r2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [0], 2)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.rewrite_sustained(container)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    c'2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        c'8
                        ]
                    }
                    \time 4/8
                    c'2
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
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

    ..  container:: example

        No preferred denominator:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16], extra_counts=[4], denominator=None
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
                    {
                        \time 4/8
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
                    \times 3/5
                    {
                        \time 3/8
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
                    \times 2/3
                    {
                        \time 4/8
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
                    \times 3/5
                    {
                        \time 3/8
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

        Expresses tuplet ratios in the usual way with numerator and denominator
        relatively prime.

    ..  container:: example

        Preferred denominator equal to 4:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16], extra_counts=[4], denominator=4
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/6
                    {
                        \time 4/8
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
                    \times 3/5
                    {
                        \time 3/8
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
                    \times 4/6
                    {
                        \time 4/8
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
                    \times 3/5
                    {
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16], extra_counts=[4], denominator=8
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 8/12
                    {
                        \time 4/8
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
                    \times 3/5
                    {
                        \time 3/8
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
                    \times 8/12
                    {
                        \time 4/8
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
                    \times 3/5
                    {
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16], extra_counts=[4], denominator=16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 16/24
                    {
                        \time 4/8
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
                    \times 3/5
                    {
                        \time 3/8
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
                    \times 16/24
                    {
                        \time 4/8
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
                    \times 3/5
                    {
                        \time 3/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16], extra_counts=[4], denominator="from_counts"
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 8/12
                    {
                        \time 4/8
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
                    \times 6/10
                    {
                        \time 3/8
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
                    \times 8/12
                    {
                        \time 4/8
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
                    \times 6/10
                    {
                        \time 3/8
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

        Fills tuplets with 16th notes and 8th notes, alternately:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16, 8]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 16), (3, 8), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/16
                    c'16
                    [
                    c'16
                    c'16
                    ]
                    \time 3/8
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \time 3/4
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 16), (3, 8), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/16
                    c'8.
                    \time 3/8
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \time 3/4
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

        (Fills tuplets less than twice the duration of an eighth note with a single
        attack.)

        Fills tuplets with quarter notes:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [4]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 16), (3, 8), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/16
                    c'8.
                    \time 3/8
                    c'4.
                    \time 3/4
                    c'4
                    c'4
                    c'4
                }
            >>

        (Fills tuplets less than twice the duration of a quarter note with a single
        attack.)

        Fills tuplets with half notes:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [2]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 16), (3, 8), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/16
                    c'8.
                    \time 3/8
                    c'4.
                    \time 3/4
                    c'2.
                }
            >>

        (Fills tuplets less than twice the duration of a half note with a single
        attack.)


    ..  container:: example

        Adds extra counts to tuplets according to a pattern of three elements:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16], extra_counts=[0, 1, 2]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
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
                    \times 6/8
                    {
                        \time 3/8
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
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
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

        **Modular handling of positive values.** Denote by ``unprolated_note_count``
        the number counts included in a tuplet when ``extra_counts`` is set to zero.
        Then extra counts equals ``extra_counts % unprolated_note_count`` when
        ``extra_counts`` is positive.

        This is likely to be intuitive; compare with the handling of negative values,
        below.

        For positive extra counts, the modulus of transformation of a tuplet with six
        notes is six:

        >>> import math
        >>> unprolated_note_count = 6
        >>> modulus = unprolated_note_count
        >>> extra_counts = list(range(12))
        >>> labels = []
        >>> for count in extra_counts:
        ...     modular_count = count % modulus
        ...     label = rf"\markup {{ {count:3} becomes {modular_count:2} }}"
        ...     labels.append(label)

        Which produces the following pattern of changes:

        >>> def make_rhythm(divisions, extra_counts):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16], extra_counts=extra_counts
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = 12 * [(6, 16)]
        >>> music = make_rhythm(divisions, extra_counts)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> staff = lilypond_file["Staff"]
        >>> abjad.override(staff).TextScript.staff_padding = 7
        >>> leaves = abjad.select.leaves(staff)
        >>> groups = abjad.select.group_by_measure(leaves)
        >>> for group, label in zip(groups, labels):
        ...     markup = abjad.Markup(label)
        ...     abjad.attach(markup, group[0], direction=abjad.UP)
        ...

        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                    \override TextScript.staff-padding = 7
                }
                {
                    \time 6/16
                    c'16
                    ^ \markup {   0 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   1 becomes  1 }
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
                    \times 6/8
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   2 becomes  2 }
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
                    \times 6/9
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   3 becomes  3 }
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
                    \times 6/10
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   4 becomes  4 }
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
                    \times 6/11
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   5 becomes  5 }
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
                    \time 6/16
                    c'16
                    ^ \markup {   6 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   7 becomes  1 }
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
                    \times 6/8
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   8 becomes  2 }
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
                    \times 6/9
                    {
                        \time 6/16
                        c'16
                        ^ \markup {   9 becomes  3 }
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
                    \times 6/10
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  10 becomes  4 }
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
                    \times 6/11
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  11 becomes  5 }
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

        This modular formula ensures that rhythm-maker ``denominators`` are always
        respected: a very large number of extra counts never causes a
        ``16``-denominated tuplet to result in 32nd- or 64th-note rhythms.

    ..  container:: example

        **Modular handling of negative values.** Denote by ``unprolated_note_count``
        the number of counts included in a tuplet when ``extra_counts`` is set to
        zero. Further, let ``modulus = ceiling(unprolated_note_count / 2)``. Then
        extra counts equals ``-(abs(extra_counts) % modulus)`` when ``extra_counts``
        is negative.

        For negative extra counts, the modulus of transformation of a tuplet with six
        notes is three:

        >>> import math
        >>> unprolated_note_count = 6
        >>> modulus = math.ceil(unprolated_note_count / 2)
        >>> extra_counts = [0, -1, -2, -3, -4, -5, -6, -7, -8]
        >>> labels = []
        >>> for count in extra_counts:
        ...     modular_count = -(abs(count) % modulus)
        ...     label = rf"\markup {{ {count:3} becomes {modular_count:2} }}"
        ...     labels.append(label)

        Which produces the following pattern of changes:

        >>> def make_rhythm(divisions, extra_counts):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16], extra_counts=extra_counts
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = 9 * [(6, 16)]
        >>> music = make_rhythm(divisions, extra_counts)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> staff = lilypond_file["Staff"]
        >>> abjad.override(staff).TextScript.staff_padding = 8
        >>> leaves = abjad.select.leaves(staff)
        >>> groups = abjad.select.group_by_measure(leaves)
        >>> for group, label in zip(groups, labels):
        ...     markup = abjad.Markup(label)
        ...     abjad.attach(markup, group[0], direction=abjad.UP)
        ...

        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                    \override TextScript.staff-padding = 8
                }
                {
                    \time 6/16
                    c'16
                    ^ \markup {   0 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -1 becomes -1 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/4
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -2 becomes -2 }
                        [
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \time 6/16
                    c'16
                    ^ \markup {  -3 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -4 becomes -1 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/4
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -5 becomes -2 }
                        [
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \time 6/16
                    c'16
                    ^ \markup {  -6 becomes  0 }
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -7 becomes -1 }
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/4
                    {
                        \time 6/16
                        c'16
                        ^ \markup {  -8 becomes -2 }
                        [
                        c'16
                        c'16
                        c'16
                        ]
                    }
                }
            >>

        This modular formula ensures that rhythm-maker ``denominators`` are always
        respected: a very small number of extra counts never causes a ``16``-denominated
        tuplet to result in 8th- or quarter-note rhythms.

    ..  container:: example

        Fills divisions with 16th, 8th, quarter notes. Consumes 5:

        >>> def make_rhythm(divisions, *, previous_state=None):
        ...     state = {}
        ...     nested_music = rmakers.even_division(
        ...         divisions, [16, 8, 4], extra_counts=[0, 1],
        ...         previous_state=previous_state, state=state
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music, state

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music, state = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 2/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \time 2/8
                    c'4
                    \times 4/5
                    {
                        \time 2/8
                        c'16
                        [
                        c'16
                        c'16
                        c'16
                        c'16
                        ]
                    }
                    \time 2/8
                    c'8
                    [
                    c'8
                    ]
                }
            >>

        >>> state
        {'divisions_consumed': 5, 'logical_ties_produced': 15}

        Advances 5 divisions; then consumes another 5 divisions:

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music, state = make_rhythm(divisions, previous_state=state)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 2/8
                    c'4
                    \time 2/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \time 2/8
                    c'4
                    \times 4/5
                    {
                        \time 2/8
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

        >>> state
        {'divisions_consumed': 10, 'logical_ties_produced': 29}

    """
    previous_state = previous_state or {}
    if state is None:
        state = {}
    tuplets = _make_even_division_rhythm_maker_music(
        divisions,
        denominators,
        self_denominator=denominator,
        self_extra_counts=extra_counts,
        self_previous_state=previous_state,
        self_spelling=spelling,
        self_tag=tag,
    )
    voice = abjad.Voice(tuplets)
    logical_ties_produced = len(abjad.select.logical_ties(voice))
    new_state = _make_state_dictionary(
        divisions_consumed=len(divisions),
        logical_ties_produced=logical_ties_produced,
        previous_divisions_consumed=previous_state.get("divisions_consumed", 0),
        previous_incomplete_last_note=previous_state.get("incomplete_last_note", False),
        previous_logical_ties_produced=previous_state.get("logical_ties_produced", 0),
        state=state,
    )
    tuplets = abjad.mutate.eject_contents(voice)
    state.clear()
    state.update(new_state)
    return tuplets


def example(selection, time_signatures=None, *, includes=None):
    """
    Makes example LilyPond file for documentation examples.
    """
    lilypond_file = abjad.illustrators.selection(
        selection,
        time_signatures,
    )
    includes = [rf'\include "{_}"' for _ in includes or []]
    lilypond_file.items[0:0] = includes
    staff = lilypond_file["Staff"]
    staff.lilypond_type = "RhythmicStaff"
    abjad.override(staff).Clef.stencil = False
    return lilypond_file


def extract_trivial(argument) -> None:
    r"""
    Extracts trivial tuplets from ``argument``.

    ..  container:: example

        With selector:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(divisions, [8])
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     tuplets = abjad.select.tuplets(container)[-2:]
        ...     rmakers.extract_trivial(tuplets)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/3
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \time 3/8
                    c'8
                    [
                    c'8
                    c'8
                    ]
                    \time 3/8
                    c'8
                    [
                    c'8
                    c'8
                    ]
                }
            >>

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
    tag: abjad.Tag = abjad.Tag(),
) -> None:
    """
    Feather-beams leaves in ``argument``.
    """

    for selection in argument:
        unbeam(selection)
        leaves = abjad.select.leaves(selection)
        abjad.beam(
            leaves,
            beam_rests=beam_rests,
            stemlet_length=stemlet_length,
            tag=tag,
        )
    for selection in argument:
        first_leaf = abjad.select.leaf(selection, 0)
        if _is_accelerando(selection):
            abjad.override(first_leaf).Beam.grow_direction = abjad.RIGHT
        elif _is_ritardando(selection):
            abjad.override(first_leaf).Beam.grow_direction = abjad.LEFT


def force_augmentation(argument) -> None:
    r"""
    Forces each tuplet in ``argument`` to notate as an augmentation.

    ..  container:: example

        Without forced augmentation:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.force_fraction(container)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        With forced augmentation:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.force_augmentation(container)
        ...     rmakers.force_fraction(container)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                }
            >>

    """
    for tuplet in abjad.select.tuplets(argument):
        if not tuplet.augmentation():
            tuplet.toggle_prolation()


def force_diminution(argument) -> None:
    """
    Forces each tuplet in ``argument`` to notate as a diminution.
    """
    for tuplet in abjad.select.tuplets(argument):
        if not tuplet.diminution():
            tuplet.toggle_prolation()


def force_fraction(argument) -> None:
    """
    Sets ``force_fraction=True`` on all tuplets in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        tuplet.force_fraction = True


def force_note(argument, *, tag: abjad.Tag = abjad.Tag()) -> None:
    r"""
    Replaces leaves in ``argument`` with notes.

    ..  container:: example

        Changes logical ties 1 and 2 to notes:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     leaves = abjad.select.leaves(container)
        ...     rmakers.force_rest(leaves)
        ...     logical_ties = abjad.select.logical_ties(container)[1:3]
        ...     rmakers.force_note(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Changes patterned selection of leaves to notes. Works inverted composite pattern:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     leaves = abjad.select.leaves(container)
        ...     rmakers.force_rest(leaves)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     leaves = abjad.select.get(logical_ties, [0, -1])
        ...     rmakers.force_note(leaves)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    """
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
    tag: abjad.Tag = None,
    threshold: bool | tuple[int, int] | typing.Callable = True,
) -> None:
    """
    Changes all ties in argument to repeat-ties.
    """
    assert isinstance(argument, abjad.Container), argument
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


def force_rest(argument, *, tag=None) -> None:
    r"""
    Replaces leaves in ``argument`` with rests.

    ..  container:: example

        Changes logical ties 1 and 2 to rests:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)[1:3]
        ...     rmakers.force_rest(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Changes logical ties -1 and -2 to rests:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)[-2:]
        ...     rmakers.force_rest(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 7/16
                    c'4..
                    \time 3/8
                    c'4.
                    \time 7/16
                    r4..
                    \time 3/8
                    r4.
                }
            >>

    ..  container:: example

        Changes patterned selection of logical ties to rests:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)[1:-1]
        ...     rmakers.force_rest(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(7, 16), (3, 8), (7, 16), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    """
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


def incised(
    divisions,
    extra_counts: typing.Sequence[int] = (),
    *,
    body_ratio: abjad.typings.Ratio = abjad.Ratio((1,)),
    fill_with_rests: bool = False,
    outer_divisions_only: bool = False,
    prefix_talea: typing.Sequence[int] = (),
    prefix_counts: typing.Sequence[int] = (),
    suffix_talea: typing.Sequence[int] = (),
    suffix_counts: typing.Sequence[int] = (),
    talea_denominator: int = None,
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
):
    r"""
    Makes incised tuplets in ``divisions``.

    ..  container:: example

        Specifies one sixteenth rest cut out of the beginning of every division:

        >>> specifier = rmakers.Incise(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     talea_denominator=16,
        ... )

    ..  container:: example

        Specifies sixteenth rests cut out of the beginning and end of each division:

        >>> specifier = rmakers.Incise(
        ...     prefix_talea=[-1],
        ...     prefix_counts=[1],
        ...     suffix_talea=[-1],
        ...     suffix_counts=[1],
        ...     talea_denominator=16,
        ... )

    ..  container:: example

        Divides middle part of every division ``1:1``:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[0, 1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=16,
        ...         body_ratio=abjad.Ratio((1, 1)),
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions =  4 * [(5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/16
                    c'8
                    [
                    c'8
                    ]
                    r16
                    \time 5/16
                    r16
                    c'16.
                    [
                    c'16.
                    ]
                    r16
                    \time 5/16
                    c'8
                    [
                    c'8
                    ]
                    r16
                    \time 5/16
                    r16
                    c'16.
                    [
                    c'16.
                    ]
                    r16
                }
            >>

    ..  container:: example

        Forces rest at every other tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=16,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [1], 2)
        ...     rmakers.force_rest(logical_ties)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    r16
                    r4..
                    \time 3/8
                    c'4.
                    \time 4/8
                    r2
                    \time 3/8
                    c'4
                    ~
                    c'16
                    r16
                }
            >>

    ..  container:: example

        Ties nonlast tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 8/8
                    r8
                    c'2..
                    ~
                    \time 4/8
                    c'2
                    ~
                    \time 6/8
                    c'2
                    ~
                    c'8
                    r8
                }
            >>

    ..  container:: example

        Repeat-ties nonfirst tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[1:]
        ...     leaves = [abjad.select.leaf(_, 0) for _ in tuplets]
        ...     rmakers.repeat_tie(leaves)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 8/8
                    r8
                    c'2..
                    \time 4/8
                    c'2
                    \repeatTie
                    \time 6/8
                    c'2
                    \repeatTie
                    ~
                    c'8
                    r8
                }
            >>

    ..  container:: example

        Add one extra count per tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         extra_counts=[1],
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.force_augmentation(container)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 16/9
                    {
                        \time 8/8
                        r16
                        c'2
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 8/5
                    {
                        \time 4/8
                        c'4
                        ~
                        c'16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/7
                    {
                        \time 6/8
                        c'4.
                        r16
                    }
                }
            >>

    ..  container:: example

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[0, 1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=16,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = 4 * [(5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/16
                    c'4
                    r16
                    \time 5/16
                    r16
                    c'8.
                    r16
                    \time 5/16
                    c'4
                    r16
                    \time 5/16
                    r16
                    c'8.
                    r16
                }
            >>

    ..  container:: example

        Fills divisions with notes. Incises outer divisions only:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-8, -7],
        ...         prefix_counts=[2],
        ...         suffix_talea=[-3],
        ...         suffix_counts=[4],
        ...         talea_denominator=32,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (5, 8), (5, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/8
                    r4
                    r8..
                    c'8
                    [
                    ~
                    c'32
                    ]
                    \time 5/8
                    c'2
                    ~
                    c'8
                    \time 5/8
                    c'4
                    r16.
                    r16.
                    r16.
                    r16.
                }
            >>

    ..  container:: example

        Fills divisions with rests. Incises outer divisions only:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         fill_with_rests=True,
        ...         outer_divisions_only=True,
        ...         prefix_talea=[7, 8],
        ...         prefix_counts=[2],
        ...         suffix_talea=[3],
        ...         suffix_counts=[4],
        ...         talea_denominator=32,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (5, 8), (5, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/8
                    c'8..
                    c'4
                    r8
                    r32
                    \time 5/8
                    r2
                    r8
                    \time 5/8
                    r4
                    c'16.
                    [
                    c'16.
                    c'16.
                    c'16.
                    ]
                }
            >>

    ..  container:: example

        Spells durations with the fewest number of glyphs:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 8/8
                    r8
                    c'2..
                    \time 4/8
                    c'2
                    \time 6/8
                    c'2
                    ~
                    c'8
                    r8
                }
            >>

    ..  container:: example

        Forbids notes with written duration greater than or equal to ``1/2``:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         spelling=rmakers.Spelling(forbidden_note_duration=abjad.Duration(1, 2)),
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 8/8
                    r8
                    c'4
                    ~
                    c'4
                    ~
                    c'4.
                    \time 4/8
                    c'4
                    ~
                    c'4
                    \time 6/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...     )
        ...     voice = rmakers.wrap_in_time_signature_staff(nested_music, divisions)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     rmakers.rewrite_meter(voice)
        ...     music = abjad.mutate.eject_contents(voice)
        ...     return music

        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 8/8
                    r8
                    c'2..
                    \time 4/8
                    c'2
                    \time 6/8
                    c'4.
                    ~
                    c'4
                    r8
                }
            >>

    ..  container:: example

        Makes augmentations:

        >>> def make_rhythm(divisions):
        ...     tag = abjad.Tag("INCISED_RHYTHM_MAKER")
        ...     nested_music = rmakers.incised(
        ...         divisions,
        ...         extra_counts=[1],
        ...         outer_divisions_only=True,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=8,
        ...         tag=tag,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.force_augmentation(container)
        ...     rmakers.beam(container, tag=tag)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(8, 8), (4, 8), (6, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
            >>> print(string)
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
    divisions_ = [abjad.NonreducedFraction(_) for _ in divisions]
    return _make_incised_rhythm_maker_music(
        divisions_,
        extra_counts=extra_counts,
        incise=Incise(
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


def invisible_music(argument, *, tag: abjad.Tag = abjad.Tag()) -> None:
    """
    Makes ``argument`` invisible.
    """
    tag_1 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COMMAND"))
    literal_1 = abjad.LilyPondLiteral(r"\abjad-invisible-music")
    tag_2 = tag.append(abjad.Tag("INVISIBLE_MUSIC_COLORING"))
    literal_2 = abjad.LilyPondLiteral(r"\abjad-invisible-music-coloring")
    for leaf in abjad.select.leaves(argument):
        abjad.attach(literal_1, leaf, tag=tag_1, deactivate=True)
        abjad.attach(literal_2, leaf, tag=tag_2)


def interpolate(
    start_duration: abjad.typings.Duration,
    stop_duration: abjad.typings.Duration,
    written_duration: abjad.typings.Duration,
) -> Interpolation:
    """
    Makes interpolation.
    """
    return Interpolation(
        abjad.Duration(start_duration),
        abjad.Duration(stop_duration),
        abjad.Duration(written_duration),
    )


def multiplied_duration(
    divisions,
    prototype: type = abjad.Note,
    *,
    duration: abjad.typings.Duration = (1, 1),
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
) -> list[abjad.Leaf]:
    r"""
    Makes one multiplied duration for each division in ``divisions``.

    ..  container:: example

        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> music = rmakers.multiplied_duration(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 1/4
                    c'1 * 1/4
                    \time 3/16
                    c'1 * 3/16
                    \time 5/8
                    c'1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'1 * 1/3
                }
            >>

    ..  container:: example

        Makes multiplied-duration whole notes when ``duration`` is unset:

        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> music = rmakers.multiplied_duration(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 1/4
                    c'1 * 1/4
                    \time 3/16
                    c'1 * 3/16
                    \time 5/8
                    c'1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'1 * 1/3
                }
            >>

        Makes multiplied-duration half notes when ``duration=(1, 2)``:

        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> music = rmakers.multiplied_duration(divisions, duration=(1, 2))
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 1/4
                    c'2 * 2/4
                    \time 3/16
                    c'2 * 6/16
                    \time 5/8
                    c'2 * 10/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'2 * 2/3
                }
            >>

        Makes multiplied-duration quarter notes when ``duration=(1, 4)``:

        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> music = rmakers.multiplied_duration(divisions, duration=(1, 4))
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 1/4
                    c'4 * 4/4
                    \time 3/16
                    c'4 * 12/16
                    \time 5/8
                    c'4 * 20/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'4 * 4/3
                }
            >>

    ..  container:: example

        Makes multiplied-duration notes when ``prototype`` is unset:

        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> music = rmakers.multiplied_duration(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 1/4
                    c'1 * 1/4
                    \time 3/16
                    c'1 * 3/16
                    \time 5/8
                    c'1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    c'1 * 1/3
                }
            >>

    ..  container:: example

        Makes multiplied-duration rests when ``prototype=abjad.Rest``:

        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> music = rmakers.multiplied_duration(divisions, abjad.Rest)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 1/4
                    r1 * 1/4
                    \time 3/16
                    r1 * 3/16
                    \time 5/8
                    r1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    r1 * 1/3
                }
            >>

    ..  container:: example

        Makes multiplied-duration multimeasures rests when
        ``prototype=abjad.MultimeasureRest``:

        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> music = rmakers.multiplied_duration(divisions, abjad.MultimeasureRest)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 1/4
                    R1 * 1/4
                    \time 3/16
                    R1 * 3/16
                    \time 5/8
                    R1 * 5/8
                    #(ly:expect-warning "strange time signature found")
                    \time 1/3
                    R1 * 1/3
                }
            >>

    ..  container:: example

        Makes multiplied-duration skips when ``prototype=abjad.Skip``:

        >>> divisions = [(1, 4), (3, 16), (5, 8), (1, 3)]
        >>> music = rmakers.multiplied_duration(divisions, abjad.Skip)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    """
    duration = abjad.Duration(duration)
    component: abjad.Leaf
    components = []
    for division in divisions:
        division = abjad.NonreducedFraction(division)
        assert isinstance(division, abjad.NonreducedFraction)
        multiplier = division / duration
        if prototype is abjad.Note:
            component = prototype("c'", duration, multiplier=multiplier, tag=tag)
        else:
            component = prototype(duration, multiplier=multiplier, tag=tag)
        components.append(component)
    return components


def nongrace_leaves_in_each_tuplet(argument, level: int = -1):
    """
    Selects nongrace leaves in each tuplet.
    """
    tuplets = abjad.select.tuplets(argument, level=level)
    leaves = [abjad.select.leaves(_, grace=False) for _ in tuplets]
    return leaves


def note(
    divisions, *, spelling: Spelling = Spelling(), tag: abjad.Tag = abjad.Tag()
) -> list[list[abjad.Leaf | abjad.Tuplet]]:
    r"""
    Makes one note for every division in ``divisions``.

    ..  container:: example

        Silences every other logical tie:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0], 2)
        ...     rmakers.force_rest(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    r2
                    \time 3/8
                    c'4.
                    \time 4/8
                    r2
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Forces rest at every logical tie:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     rmakers.force_rest(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (5, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    r2
                    \time 3/8
                    r4.
                    \time 4/8
                    r2
                    \time 5/8
                    r2
                    r8
                }
            >>

    ..  container:: example

        Silences every other output division except for the first and last:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0], 2)[1:-1]
        ...     rmakers.force_rest(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    c'2
                    \time 3/8
                    c'4.
                    \time 4/8
                    r2
                    \time 3/8
                    c'4.
                    \time 2/8
                    c'4
                }
            >>

    ..  container:: example

        Beams each division:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container, pitched=True)
        ...     rmakers.beam(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 32), (5, 32)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/32
                    c'8
                    [
                    ~
                    c'32
                    ]
                    \time 5/32
                    c'8
                    [
                    ~
                    c'32
                    ]
                }
            >>

    ..  container:: example

        Beams divisions together:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     rmakers.beam_groups(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 32), (5, 32)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \set stemLeftBeamCount = 0
                    \set stemRightBeamCount = 1
                    \time 5/32
                    c'8
                    [
                    ~
                    \set stemLeftBeamCount = 3
                    \set stemRightBeamCount = 1
                    c'32
                    \set stemLeftBeamCount = 1
                    \set stemRightBeamCount = 1
                    \time 5/32
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 32), (5, 32)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/32
                    c'8
                    ~
                    c'32
                    \time 5/32
                    c'8
                    ~
                    c'32
                }
            >>

    ..  container:: example

        Does not tie across divisions:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    c'2
                    \time 3/8
                    c'4.
                    \time 4/8
                    c'2
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Ties across divisions:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in logical_ties]
        ...     rmakers.tie(leaves)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'4.
                    ~
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Ties across every other logical tie:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)[:-1]
        ...     logical_ties = abjad.select.get(logical_ties, [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in logical_ties]
        ...     rmakers.tie(leaves)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'4.
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'4.
                }
            >>

    ..  container:: example

        Strips all ties:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     rmakers.untie(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(7, 16), (1, 4), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 7/16
                    c'4..
                    \time 1/4
                    c'4
                    \time 5/16
                    c'4
                    c'16
                }
            >>

    ..  container:: example

        Spells tuplets as diminutions:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 14), (3, 7)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak edge-height #'(0.7 . 0)
                    \times 8/14
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 5/14
                        c'2
                        ~
                        c'8
                    }
                    \tweak edge-height #'(0.7 . 0)
                    \times 4/7
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 3/7
                        c'2.
                    }
                }
            >>

    ..  container:: example

        Spells tuplets as augmentations:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     rmakers.force_augmentation(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 14), (3, 7)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \tweak edge-height #'(0.7 . 0)
                    \times 16/14
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 5/14
                        c'4
                        ~
                        c'16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \tweak edge-height #'(0.7 . 0)
                    \times 8/7
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 3/7
                        c'4.
                    }
                }
            >>

    ..  container:: example

        Forces rest in logical tie 0:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_tie = abjad.select.logical_tie(container, 0)
        ...     rmakers.force_rest(logical_tie)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/8
                    r2
                    r8
                    \time 2/8
                    c'4
                    \time 2/8
                    c'4
                    \time 5/8
                    c'2
                    ~
                    c'8
                }
            >>

    ..  container:: example

        Forces rests in first two logical ties:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_tie = abjad.select.logical_ties(container)[:2]
        ...     rmakers.force_rest(logical_tie)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/8
                    r2
                    r8
                    \time 2/8
                    r4
                    \time 2/8
                    c'4
                    \time 5/8
                    c'2
                    ~
                    c'8
                }
            >>

    ..  container:: example

        Forces rests in first and last logical ties:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0, -1])
        ...     rmakers.force_rest(logical_ties)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (2, 8), (2, 8), (5, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/8
                    r2
                    r8
                    \time 2/8
                    c'4
                    \time 2/8
                    c'4
                    \time 5/8
                    r2
                    r8
                }
            >>

    ..  container:: example

        Rewrites meter:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.note(divisions)
        ...     voice = rmakers.wrap_in_time_signature_staff(nested_music, divisions)
        ...     rmakers.rewrite_meter(voice)
        ...     music = abjad.mutate.eject_contents(voice)
        ...     return music

        >>> divisions = [(3, 4), (6, 16), (9, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
                    c'2.
                    \time 6/16
                    c'4.
                    \time 9/16
                    c'4.
                    ~
                    c'8.
                }
            >>

    """

    return _make_note_rhythm_maker_music(divisions, spelling=spelling, tag=tag)


def on_beat_grace_container(
    voice: abjad.Voice,
    voice_name: str,
    argument,
    counts: typing.Sequence[int],
    *,
    leaf_duration: abjad.typings.Duration = None,
    # TODO: activate tag
    tag: abjad.Tag = None,
    talea: Talea = Talea([1], 8),
):
    r"""
    Makes on-beat grace containers.

    ..  container:: example

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [4], extra_counts=[2]
        ...     )
        ...     voice = abjad.Voice(nested_music)
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
        ...         leaf_duration=(1, 28)
        ...     )
        ...     music = abjad.mutate.eject_contents(voice)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> music_voice = abjad.Voice(music, name="RhythmMaker.Music")
        >>> lilypond_file = rmakers.example(
        ...     [music_voice], divisions, includes=["abjad.ily"]
        ... )
        >>> staff = lilypond_file["Staff"]
        >>> abjad.override(staff).TupletBracket.direction = abjad.UP
        >>> abjad.override(staff).TupletBracket.staff_padding = 5
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                    \override TupletBracket.direction = #up
                    \override TupletBracket.staff-padding = 5
                }
                {
                    \context Voice = "RhythmMaker.Music"
                    {
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5
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
                        \tweak text #tuplet-number::calc-fraction-text
                        \times 3/5
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
                            \oneVoice
                            c'4
                        }
                    }
                }
            >>

    ..  container:: example

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(divisions, [5], 16)
        ...     voice = abjad.Voice(nested_music)
        ...     rmakers.extract_trivial(voice)
        ...     logical_ties = abjad.select.logical_ties(voice)
        ...     rmakers.on_beat_grace_container(
        ...         voice,
        ...         "RhythmMaker.Music",
        ...         logical_ties,
        ...         [6, 2],
        ...         leaf_duration=(1, 28)
        ...     )
        ...     music = abjad.mutate.eject_contents(voice)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> music_voice = abjad.Voice(music, name="RhythmMaker.Music")
        >>> lilypond_file = rmakers.example(
        ...     [music_voice], divisions, includes=["abjad.ily"]
        ... )
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
                                \time 3/4
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
            >>

    """
    assert isinstance(voice, abjad.Voice), repr(voice)
    assert isinstance(voice_name, str), repr(voice_name)
    assert isinstance(talea, Talea), repr(talea)
    assert isinstance(voice, abjad.Voice), repr(voice)
    assert isinstance(voice_name, str), repr(voice_name)
    if voice_name:
        voice.name = voice_name
    assert isinstance(talea, Talea), repr(talea)
    cyclic_counts = abjad.CyclicTuple(counts)
    start = 0
    for i, selection in enumerate(argument):
        count = cyclic_counts[i]
        if not count:
            continue
        stop = start + count
        durations = talea[start:stop]
        notes = abjad.makers.make_leaves([0], durations)
        abjad.on_beat_grace_container(
            notes,
            selection,
            anchor_voice_number=2,
            grace_voice_number=1,
            leaf_duration=leaf_duration,
        )


def repeat_tie(argument, *, tag=None) -> None:
    r"""
    Attaches repeat-tie to each leaf in ``argument``.

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE. Attaches repeat-ties to first note in nonfirst
        tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[1:]
        ...     notes = [abjad.select.note(_, 0) for _ in tuplets]
        ...     rmakers.repeat_tie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        With pattern:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     notes = [abjad.select.note(_, 0) for _ in tuplets]
        ...     rmakers.repeat_tie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    """
    for note in abjad.select.notes(argument):
        tie = abjad.RepeatTie()
        abjad.attach(tie, note, tag=tag)


def reduce_multiplier(argument) -> None:
    """
    Reduces multipliers of tuplets in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        tuplet.multiplier = abjad.Multiplier(tuplet.multiplier)


def rewrite_dots(argument, *, tag: abjad.Tag = abjad.Tag()) -> None:
    """
    Rewrites dots of tuplets in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        tuplet.rewrite_dots()


def rewrite_meter(
    voice: abjad.Voice,
    *,
    boundary_depth: int = None,
    reference_meters: typing.Sequence[abjad.Meter] = (),
    tag=None,
) -> None:
    """
    Rewrites meter of material in ``voice``.

    Use ``rmakers.wrap_in_time_signature_staff()`` to make sure ``voice``
    appears together with time signature information in a staff.
    """
    assert isinstance(voice, abjad.Container), repr(voice)
    tag = tag or abjad.Tag()
    tag = tag.append(abjad.Tag("rmakers.RewriteMeterCommand.__call__"))
    staff = abjad.get.parentage(voice).parent
    assert isinstance(staff, abjad.Staff), repr(staff)
    time_signature_voice = staff["TimeSignatureVoice"]
    assert isinstance(time_signature_voice, abjad.Voice)
    meters, preferred_meters = [], []
    for skip in time_signature_voice:
        time_signature = abjad.get.indicator(skip, abjad.TimeSignature)
        meter = abjad.Meter(time_signature)
        meters.append(meter)
    durations = [abjad.Duration(_) for _ in meters]
    reference_meters = reference_meters or ()
    split_measures(voice, durations=durations)
    selections = abjad.select.group_by_measure(voice[:])
    for meter, selection in zip(meters, selections):
        for reference_meter in reference_meters:
            if reference_meter == meter:
                meter = reference_meter
                break
        preferred_meters.append(meter)
        nontupletted_leaves = []
        for leaf in abjad.iterate.leaves(selection):
            if not abjad.get.parentage(leaf).count(abjad.Tuplet):
                nontupletted_leaves.append(leaf)
        unbeam(nontupletted_leaves)
        abjad.Meter.rewrite_meter(
            selection,
            meter,
            boundary_depth=boundary_depth,
            rewrite_tuplets=False,
        )
    selections = abjad.select.group_by_measure(voice[:])
    for meter, selection in zip(preferred_meters, selections):
        leaves = abjad.select.leaves(selection, grace=False)
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


def rewrite_rest_filled(argument, *, spelling=None, tag=None) -> None:
    r"""
    Rewrites rest-filled tuplets in ``argument``.

    ..  container:: example

        Does not rewrite rest-filled tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [-1], 16, extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 4/16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \times 4/5
                    {
                        \time 4/16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
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
                    \times 5/6
                    {
                        \time 5/16
                        r16
                        r16
                        r16
                        r16
                        r16
                        r16
                    }
                }
            >>

        Rewrites rest-filled tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [-1], 16, extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_rest_filled(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/16
                    r4
                    \time 4/16
                    r4
                    \time 5/16
                    r4
                    r16
                    \time 5/16
                    r4
                    r16
                }
            >>

        With spelling specifier:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [-1], 16, extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.rewrite_rest_filled(
        ...         container,
        ...         spelling=rmakers.Spelling(increase_monotonic=True)
        ...     )
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 16), (4, 16), (5, 16), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/16
                    r4
                    \time 4/16
                    r4
                    \time 5/16
                    r16
                    r4
                    \time 5/16
                    r16
                    r4
                }
            >>

    """
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
        tuplet.multiplier = abjad.Multiplier(1)


def rewrite_sustained(argument, *, tag=None) -> None:
    r"""
    Rewrites sustained tuplets in ``argument``.

    ..  container:: example

        Sustained tuplets generalize a class of rhythms composers are likely to rewrite:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
                    {
                        \time 4/16
                        c'4.
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        ~
                        c'16
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        ~
                        c'16
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        c'16
                    }
                }
            >>

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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.rewrite_sustained(container)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/16
                        c'4
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/16
                        c'4
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        c'16
                    }
                }
            >>

    ..  container:: example

        Rewrite sustained tuplets -- and then extract the trivial tuplets that result --
        like this:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [6, 5, 5, 4, 1], 16, extra_counts=[2, 1, 1, 1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     tuplets = abjad.select.tuplets(container)[1:3]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.rewrite_sustained(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 16), (4, 16), (4, 16), (4, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/16
                    c'4
                    \time 4/16
                    c'4
                    ~
                    \time 4/16
                    c'4
                    ~
                    \times 4/5
                    {
                        \time 4/16
                        c'4
                        c'16
                    }
                }
            >>

    ..  container:: example

        With selector:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.rewrite_sustained(tuplets[-2:])
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
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
                    \times 2/3
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
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/2
                    {
                        \time 2/8
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 2/2
                    {
                        \time 2/8
                        c'4
                    }
                }
            >>

    """
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
        tuplet.multiplier = abjad.Multiplier(1)


def split_measures(voice, *, durations=None, tag=None) -> None:
    r"""
    Splits measures in ``voice``.

    Uses ``durations`` when ``durations`` is not none.

    Tries to find time signature information (from the staff that contains ``voice``)
    when ``durations`` is none.
    """
    if not durations:
        # TODO: implement abjad.get() method for measure durations
        staff = abjad.get.parentage(voice).parent
        assert isinstance(staff, abjad.Staff)
        voice_ = staff["TimeSignatureVoice"]
        assert isinstance(voice_, abjad.Voice)
        durations = [abjad.get.duration(_) for _ in voice_]
    total_duration = abjad.sequence.sum(durations)
    music_duration = abjad.get.duration(voice)
    if total_duration != music_duration:
        message = f"Total duration of splits is {total_duration!s}"
        message += f" but duration of music is {music_duration!s}:"
        message += f"\ndurations: {durations}."
        message += f"\nvoice: {voice[:]}."
        raise Exception(message)
    abjad.mutate.split(voice[:], durations=durations)


def talea(
    divisions,
    counts: typing.Sequence[int],
    denominator: int,
    *,
    advance: int = 0,
    end_counts: typing.Sequence[int] = (),
    extra_counts: typing.Sequence[int] = (),
    preamble: typing.Sequence[int] = (),
    previous_state: dict = None,
    read_talea_once_only: bool = False,
    spelling: Spelling = Spelling(),
    state: dict = None,
    tag: abjad.Tag = abjad.Tag(),
) -> list[abjad.Tuplet]:
    r"""
    Reads ``counts`` cyclically and makes one tuplet for each division in ``divisions``.

    ..  container:: example

        Repeats talea of 1/16, 2/16, 3/16, 4/16:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(divisions, [1, 2, 3, 4], 16)
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'16
                    [
                    c'8
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
                    c'8
                    ]
                }
            >>

    ..  container:: example

        Silences first and last logical ties:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(divisions, [1, 2, 3, 4], 16)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0, -1])
        ...     rmakers.force_rest(logical_ties)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Silences all logical ties. Then sustains first and last logical ties:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(divisions, [1, 2, 3, 4], 16)
        ...     container = abjad.Container(nested_music)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     rmakers.force_rest(logical_ties)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0, -1])
        ...     rmakers.force_note(logical_ties)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        REGRESSION. Spells tuplet denominator in terms of duration when denominator is
        given as a duration:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16, extra_counts=[1, 1, 2, 2]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.denominator(container, (1, 16))
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        c'16
                        ]
                        ~
                    }
                    \times 8/9
                    {
                        \time 4/8
                        c'8.
                        [
                        c'16
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/8
                    {
                        \time 3/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                    }
                    \times 8/10
                    {
                        \time 4/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \time 4/8
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
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    ]
                    \time 4/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.beam_groups(tuplets)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Beams nothing:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    \time 4/8
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    \time 3/8
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    c'16
                    \time 4/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 1, 1, -1], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
                    \time 3/8
                    c'16
                    r16
                    c'16
                    [
                    c'16
                    c'16
                    ]
                    r16
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
            >>

    ..  container:: example

        Does beam rests:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 1, 1, -1], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container, beam_rests=True)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'16
                    [
                    c'16
                    c'16
                    r16
                    c'16
                    c'16
                    ]
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
                    \time 3/8
                    c'16
                    [
                    r16
                    c'16
                    c'16
                    c'16
                    r16
                    ]
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
                }
            >>

    ..  container:: example

        Beams rests with stemlets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 1, 1, -1], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container, beam_rests=True, stemlet_length=0.75)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \override Staff.Stem.stemlet-length = 0.75
                    \time 3/8
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
                    \time 4/8
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
                    \time 3/8
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
                    \time 4/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [5, 3, 3, 3], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 4/8
                    c'4
                    ~
                    c'16
                    [
                    c'8.
                    ]
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
                    \time 3/8
                    c'8.
                    [
                    c'8.
                    ]
                }
            >>

    ..  container:: example

        Ties across divisions:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [5, 3, 3, 3], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Ties across every other tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [5, 3, 3, 3], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     tuplets = abjad.select.get(tuplets, [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        TIE-CONSECUTIVE-NOTES RECIPE:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [5, -3, 3, 3], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.untie(container)
        ...     runs = abjad.select.runs(container)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in runs]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Working with ``denominator``.

        Reduces terms in tuplet ratio to relative primes when no tuplet command is given:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16, extra_counts=[1, 1, 2, 2]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        c'16
                        ]
                        ~
                    }
                    \times 8/9
                    {
                        \time 4/8
                        c'8.
                        [
                        c'16
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/8
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

        REGRESSION. Spells tuplet denominator in terms of duration when denominator is
        given as a duration:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16, extra_counts=[1, 1, 2, 2]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.denominator(container, (1, 16))
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        c'16
                        ]
                        ~
                    }
                    \times 8/9
                    {
                        \time 4/8
                        c'8.
                        [
                        c'16
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/8
                    {
                        \time 3/8
                        c'4
                        c'16
                        [
                        c'8
                        c'16
                        ]
                        ~
                    }
                    \times 8/10
                    {
                        \time 4/8
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

        Makes diminished tuplets when ``diminution`` is true (or when no tuplet command
        is given):

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1], 16, extra_counts=[0, -1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                }
            >>

        Forces augmented tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1], 16, extra_counts=[0, -1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.force_augmentation(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
                        c'16
                        [
                        c'16
                        c'16
                        ]
                    }
                    \time 1/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 1/4
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

        Leaves trivializable tuplets as-is when no tuplet command is given. The tuplets
        in measures 2 and 4 can be written as trivial tuplets, but they are not:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \times 2/3
                    {
                        \time 4/8
                        c'4.
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \times 2/3
                    {
                        \time 4/8
                        c'4.
                        c'4.
                    }
                }
            >>

        Rewrites trivializable tuplets as trivial (1:1) tuplets when ``trivialize`` is
        true:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.trivialize(container)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        c'4
                    }
                }
            >>

        REGRESSION #907a. Rewrites trivializable tuplets even when tuplets contain
        multiple ties:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.trivialize(container)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        c'4
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        c'4
                    }
                }
            >>

        REGRESSION #907b. Rewrites trivializable tuplets even when tuplets contain very
        long ties:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [3, 3, 6, 6], 16, extra_counts=[0, 4]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.trivialize(container)
        ...     notes = abjad.select.notes(container)[:-1]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
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
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        ~
                        c'4
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
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
                    \times 1/1
                    {
                        \time 4/8
                        c'4
                        ~
                        c'4
                    }
                }
            >>

    ..  container:: example

        Working with ``rewrite_rest_filled``.

        Makes rest-filled tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [3, 3, -6, -6], 16, extra_counts=[1, 0]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        r16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        r4
                        r16
                        r8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
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
                    \times 1/1
                    {
                        \time 4/8
                        c'8
                        r4.
                    }
                }
            >>

        Rewrites rest-filled tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [3, 3, -6, -6], 16, extra_counts=[1, 0]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_rest_filled(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        r16
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
                        r2
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
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
                    \times 1/1
                    {
                        \time 4/8
                        c'8
                        r4.
                    }
                }
            >>

    ..  container:: example

        No rest commands:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'16
                    [
                    c'8
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
                    c'8
                    ]
                }
            >>

    ..  container:: example

        Silences every other output division:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     rmakers.force_rest(tuplets)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_rest_filled(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Sustains every other output division:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.rewrite_sustained(tuplets)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Forces the first leaf and the last two leaves to be rests:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     leaves = abjad.select.leaves(container)
        ...     leaves = abjad.select.get(leaves, [0, -2, -1])
        ...     rmakers.force_rest(leaves)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Forces rest at first leaf of every tuplet:


        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     leaves = [abjad.select.leaf(_, 0) for _ in tuplets]
        ...     rmakers.force_rest(leaves)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
            >>

    ..  container:: example

        Spells nonassignable durations with monontonically decreasing durations:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=False),
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (5, 8), (5, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/8
                    c'4
                    ~
                    c'16
                    c'4
                    ~
                    c'16
                    \time 5/8
                    c'4
                    ~
                    c'16
                    c'4
                    ~
                    c'16
                    \time 5/8
                    c'4
                    ~
                    c'16
                    c'4
                    ~
                    c'16
                }
            >>

    ..  container:: example

        Spells nonassignable durations with monontonically increasing durations:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions,
        ...         [5],
        ...         16,
        ...         spelling=rmakers.Spelling(increase_monotonic=True),
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (5, 8), (5, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 5/8
                    c'16
                    ~
                    c'4
                    c'16
                    ~
                    c'4
                    \time 5/8
                    c'16
                    ~
                    c'4
                    c'16
                    ~
                    c'4
                    \time 5/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 1, 1, 1, 4, 4], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
                    c'16
                    [
                    c'16
                    c'16
                    c'16
                    ]
                    c'4
                    c'4
                    \time 3/4
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 1, 1, 1, 4, 4], 16,
        ...         spelling=rmakers.Spelling(forbidden_note_duration=abjad.Duration(1, 4)),
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/4
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
                    \time 3/4
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [5, 4], 16
        ...     )
        ...     voice = rmakers.wrap_in_time_signature_staff(nested_music, divisions)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     rmakers.rewrite_meter(voice)
        ...     music = abjad.mutate.eject_contents(voice)
        ...     return music

        >>> divisions = [(3, 4), (3, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
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
                    \time 3/4
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
                    \time 3/4
                    c'8.
                    [
                    c'16
                    ]
                    ~
                    c'4
                    c'4
                }
            >>

    ..  container:: example

        No extra counts:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'16
                    [
                    c'8
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
                    c'8
                    ]
                }
            >>

    ..  container:: example

        Adds one extra count to every other division:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16, extra_counts=[0, 1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                    }
                    \times 8/9
                    {
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16
                        c'4
                        c'16
                    }
                    \times 8/9
                    {
                        \time 4/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16, extra_counts=[0, 2]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'4
                        c'16
                        [
                        c'16
                        ]
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/8
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

        The duration of each added count equals the duration of each count in the
        rhythm-maker's input talea.

    ..  container:: example

        Removes one count from every other division:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16, extra_counts=[0, -1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16
                        [
                        c'8
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 8/7
                    {
                        \time 4/8
                        c'4
                        c'16
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 8/7
                    {
                        \time 4/8
                        c'16
                        [
                        c'16
                        c'8
                        c'8.
                        ]
                    }
                }
            >>

    ..  container:: example

        Reads talea cyclically:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'16
                    [
                    c'8
                    c'8.
                    ]
                    \time 3/8
                    c'4
                    c'16
                    [
                    c'16
                    ]
                    ~
                    \time 3/8
                    c'16
                    [
                    c'8.
                    c'8
                    ]
                    ~
                    \time 3/8
                    c'8
                    [
                    c'16
                    c'8
                    c'16
                    ]
                }
            >>

    ..  container:: example

        **Reading talea once only.** Set ``read_talea_once_only=True`` to
        ensure talea is long enough to cover all divisions without repeating.
        Provides way of using talea noncyclically when, for example,
        interpolating from short durations to long durations:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16, read_talea_once_only=True
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        Code below raises an exception because talea would need to be read
        multiple times to handle all divisions:

        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        Traceback (most recent call last):
            ...
        Exception: CyclicTuple(items=()) + CyclicTuple(items=(1, 2, 3, 4)) is too short to read [6, 6, 6, 6] once.

    ..  container:: example

        **Examples showing state.** Consumes 4 divisions and 31 counts:

        >>> def make_rhythm(divisions, *, previous_state=None):
        ...     state = {}
        ...     nested_music = rmakers.talea(
        ...         divisions, [4], 16, extra_counts=[0, 1, 2],
        ...         previous_state=previous_state,
        ...         state=state,
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music, state

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music, state = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'4
                    c'8
                    ~
                    \times 8/9
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'8.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
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
            >>

        >>> state
        {'divisions_consumed': 4, 'incomplete_last_note': True, 'logical_ties_produced': 8, 'talea_weight_consumed': 31}

        Advances 4 divisions and 31 counts; then consumes another 4 divisions and 31
        counts:

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music, state = make_rhythm(divisions, previous_state=state)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        c'4
                        c'8
                        ~
                    }
                    \times 4/5
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
                    \times 8/9
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'8.
                    }
                }
            >>

        >>> state
        {'divisions_consumed': 8, 'incomplete_last_note': True, 'logical_ties_produced': 16, 'talea_weight_consumed': 63}

        Advances 8 divisions and 62 counts; then consumes 4 divisions and 31 counts:

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music, state = make_rhythm(divisions, previous_state=state)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
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
                    \times 6/7
                    {
                        \time 3/8
                        c'16
                        c'4
                        c'8
                        ~
                    }
                    \times 4/5
                    {
                        \time 4/8
                        c'8
                        c'4
                        c'4
                    }
                }
            >>

        >>> state
        {'divisions_consumed': 12, 'logical_ties_produced': 24, 'talea_weight_consumed': 96}

    ..  container:: example

        >>> def make_rhythm(divisions):
        ...     tag = abjad.Tag("TALEA_RHYTHM_MAKER")
        ...     nested_music = rmakers.talea(
        ...         divisions, [1, 2, 3, 4], 16, extra_counts=[0, 1], tag=tag
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container, tag=tag)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    %! TALEA_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TALEA_RHYTHM_MAKER
                    \times 1/1
                    %! TALEA_RHYTHM_MAKER
                    {
                        \time 3/8
                        %! TALEA_RHYTHM_MAKER
                        c'16
                        %! TALEA_RHYTHM_MAKER
                        [
                        %! TALEA_RHYTHM_MAKER
                        c'8
                        %! TALEA_RHYTHM_MAKER
                        c'8.
                        %! TALEA_RHYTHM_MAKER
                        ]
                    %! TALEA_RHYTHM_MAKER
                    }
                    %! TALEA_RHYTHM_MAKER
                    \times 8/9
                    %! TALEA_RHYTHM_MAKER
                    {
                        \time 4/8
                        %! TALEA_RHYTHM_MAKER
                        c'4
                        %! TALEA_RHYTHM_MAKER
                        c'16
                        %! TALEA_RHYTHM_MAKER
                        [
                        %! TALEA_RHYTHM_MAKER
                        c'8
                        %! TALEA_RHYTHM_MAKER
                        c'8
                        %! TALEA_RHYTHM_MAKER
                        ]
                        ~
                    %! TALEA_RHYTHM_MAKER
                    }
                    %! TALEA_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TALEA_RHYTHM_MAKER
                    \times 1/1
                    %! TALEA_RHYTHM_MAKER
                    {
                        \time 3/8
                        %! TALEA_RHYTHM_MAKER
                        c'16
                        %! TALEA_RHYTHM_MAKER
                        c'4
                        %! TALEA_RHYTHM_MAKER
                        c'16
                    %! TALEA_RHYTHM_MAKER
                    }
                    %! TALEA_RHYTHM_MAKER
                    \times 8/9
                    %! TALEA_RHYTHM_MAKER
                    {
                        \time 4/8
                        %! TALEA_RHYTHM_MAKER
                        c'8
                        %! TALEA_RHYTHM_MAKER
                        [
                        %! TALEA_RHYTHM_MAKER
                        c'8.
                        %! TALEA_RHYTHM_MAKER
                        ]
                        %! TALEA_RHYTHM_MAKER
                        c'4
                    %! TALEA_RHYTHM_MAKER
                    }
                }
            >>

    ..  container:: example

        Working with ``preamble``.

        Preamble less than total duration:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [8, -4, 8], 32, preamble=[1, 1, 1, 1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'32
                    [
                    c'32
                    c'32
                    c'32
                    ]
                    c'4
                    \time 4/8
                    r8
                    c'4
                    c'8
                    ~
                    \time 3/8
                    c'8
                    r8
                    c'8
                    ~
                    \time 4/8
                    c'8
                    c'4
                    r8
                }
            >>

        Preamble more than total duration; ignores counts:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [8, -4, 8], 32, preamble=[32, 32, 32, 32]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'4.
                    ~
                    \time 4/8
                    c'2
                    ~
                    \time 3/8
                    c'8
                    c'4
                    ~
                    \time 4/8
                    c'2
                }
            >>

    ..  container:: example

        Working with ``end_counts``.

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [8, -4, 8], 32, end_counts=[1, 1, 1, 1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'4
                    r8
                    \time 4/8
                    c'4
                    c'4
                    \time 3/8
                    r8
                    c'4
                    \time 4/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.talea(
        ...         divisions, [6], 16, end_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \time 3/8
                    c'4.
                    \time 3/8
                    c'4
                    ~
                    c'16
                    [
                    c'16
                    ]
                }
            >>

    """
    talea = Talea(
        counts=counts,
        denominator=denominator,
        end_counts=end_counts,
        preamble=preamble,
    )
    talea = talea.advance(advance)
    previous_state = previous_state or {}
    if state is None:
        state = {}
    tuplets = _make_talea_rhythm_maker_music(
        divisions,
        extra_counts,
        previous_state,
        read_talea_once_only,
        spelling,
        state,
        talea,
        tag,
    )
    voice = abjad.Voice(tuplets)
    logical_ties_produced = len(abjad.select.logical_ties(voice))
    new_state = _make_state_dictionary(
        divisions_consumed=len(divisions),
        logical_ties_produced=logical_ties_produced,
        previous_divisions_consumed=previous_state.get("divisions_consumed", 0),
        previous_incomplete_last_note=previous_state.get("incomplete_last_note", False),
        previous_logical_ties_produced=previous_state.get("logical_ties_produced", 0),
        state=state,
    )
    tuplets = abjad.mutate.eject_contents(voice)
    state.clear()
    state.update(new_state)
    return tuplets


def tie(argument, *, tag: abjad.Tag = abjad.Tag()) -> None:
    r"""
    Attaches one tie to each notes in ``argument``.

    ..  container:: example

        TIE-CONSECUTIVE-NOTES RECIPE. Attaches ties notes in selection:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = abjad.select.notes(container)[5:15]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE. Attaches ties to last note in nonlast tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

        With pattern:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     tuplets = abjad.select.get(tuplets, [0], 2)
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        TIE-ACROSS-DIVISIONS RECIPE:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(divisions, [(5, 2)])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     notes = [abjad.select.note(_, -1) for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 8), (4, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/7
                    {
                        \time 4/8
                        c'2
                        ~
                        c'8
                        c'4
                        ~
                    }
                    \times 4/7
                    {
                        \time 4/8
                        c'2
                        ~
                        c'8
                        c'4
                        ~
                    }
                    \times 4/7
                    {
                        \time 4/8
                        c'2
                        ~
                        c'8
                        c'4
                    }
                }
            >>

    ..  container:: example

        TIE-WITHIN-DIVISIONS RECIPE:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     rmakers.untie(notes)
        ...     rmakers.tie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
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
                    \times 2/3
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
                    \times 2/3
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
                    \times 2/3
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
                    \times 2/3
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
                    \times 2/3
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
                }
            >>

        With pattern:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [0], 2)
        ...     notes = [abjad.select.notes(_)[:-1] for _ in tuplets]
        ...     rmakers.tie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                    \times 2/3
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    """
    for note in abjad.select.notes(argument):
        tie = abjad.Tie()
        abjad.attach(tie, note, tag=tag)


def tremolo_container(argument, count: int, *, tag: abjad.Tag = None) -> None:
    r"""
    Replaces each note in ``argument`` with a tremolo container.

    ..  container:: example

        Repeats figures two times each:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(divisions, [4])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     groups = [abjad.select.get(_, [0, -1]) for _ in notes]
        ...     rmakers.tremolo_container(groups, 2)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> containers = abjad.select.components(music, abjad.TremoloContainer)
        >>> result = [abjad.slur(_) for _ in containers]
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \repeat tremolo 2 {
                        \time 4/4
                        c'16
                        (
                        c'16
                        )
                    }
                    c'4
                    c'4
                    \repeat tremolo 2 {
                        c'16
                        (
                        c'16
                        )
                    }
                    \repeat tremolo 2 {
                        \time 3/4
                        c'16
                        (
                        c'16
                        )
                    }
                    c'4
                    \repeat tremolo 2 {
                        c'16
                        (
                        c'16
                        )
                    }
                }
            >>

        Repeats figures four times each:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(divisions, [4])
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     notes = [abjad.select.notes(_) for _ in tuplets]
        ...     groups = [abjad.select.get(_, [0, -1]) for _ in notes]
        ...     rmakers.tremolo_container(groups, 4)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(4, 4), (3, 4)]
        >>> music = make_rhythm(divisions)
        >>> containers = abjad.select.components(music, abjad.TremoloContainer)
        >>> result = [abjad.slur(_) for _ in containers]
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \repeat tremolo 4 {
                        \time 4/4
                        c'32
                        (
                        c'32
                        )
                    }
                    c'4
                    c'4
                    \repeat tremolo 4 {
                        c'32
                        (
                        c'32
                        )
                    }
                    \repeat tremolo 4 {
                        \time 3/4
                        c'32
                        (
                        c'32
                        )
                    }
                    c'4
                    \repeat tremolo 4 {
                        c'32
                        (
                        c'32
                        )
                    }
                }
            >>

    """
    for note in abjad.select.notes(argument):
        container_duration = note.written_duration
        note_duration = container_duration / (2 * count)
        left_note = abjad.Note("c'", note_duration)
        right_note = abjad.Note("c'", note_duration)
        container = abjad.TremoloContainer(count, [left_note, right_note], tag=tag)
        abjad.mutate.replace(note, container)


def trivialize(argument) -> None:
    """
    Trivializes each tuplet in ``argument``.
    """
    for tuplet in abjad.select.tuplets(argument):
        tuplet.trivialize()


def tuplet(
    divisions,
    tuplet_ratios: typing.Sequence[abjad.typings.Ratio],
    *,
    # TODO: is 'denominator' unused?
    # TODO: remove in favor of dedicated denominator control commands:
    denominator: int | abjad.Duration | str | None = None,
    # TODO: is 'spelling' unused?
    spelling: Spelling = Spelling(),
    tag: abjad.Tag = abjad.Tag(),
) -> list[abjad.Tuplet]:
    r"""
    Makes one tuplet for each division in ``divisions``.

    ..  container:: example

        Makes tuplets with ``3:2`` ratios:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(3, 2)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 1/2
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8.
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8.
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, -1), (3, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 1/2
                        c'4
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'4.
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/16
                        c'8.
                        r8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4
                    {
                        \time 5/16
                        c'8.
                        [
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Beams each division:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 1, 1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/8
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        [
                        c'16.
                        c'16.
                        c'16.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 6/8
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 1, 1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/8
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        [
                        c'16.
                        c'16.
                        c'16.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 6/8
                        c'8.
                        [
                        c'8.
                        c'8.
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 4/8
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

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 1, 2, 1, 1), (3, 1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     rmakers.beam_groups(tuplets)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(5, 8), (3, 8), (6, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/9
                    {
                        \set stemLeftBeamCount = 0
                        \set stemRightBeamCount = 1
                        \time 5/8
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
                    \times 3/5
                    {
                        \time 3/8
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
                    \times 1/1
                    {
                        \set stemLeftBeamCount = 1
                        \set stemRightBeamCount = 1
                        \time 6/8
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
                    \times 4/5
                    {
                        \time 4/8
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

        Ties nothing:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(2, 3), (1, -2, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 2), (3, 8), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 1/2
                        c'4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        r8.
                        c'16.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8
                        [
                        c'8.
                        ]
                    }
                }
            >>

    ..  container:: example

        Ties across all divisions:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(2, 3), (1, -2, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 2), (3, 8), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 1/2
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        r8.
                        c'16.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8
                        [
                        c'8.
                        ]
                    }
                }
            >>

    ..  container:: example

        Ties across every other division:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(2, 3), (1, -2, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     tuplets = abjad.select.get(tuplets, [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 1/2
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'16.
                        r8.
                        c'16.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8
                        [
                        c'8.
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/16
                        c'16.
                        r8.
                        c'16.
                    }
                }
            >>

    ..  container:: example

        Makes diminished tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(2, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.force_diminution(container)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
                    {
                        \time 2/8
                        c'4
                        c'8
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'4
                        c'8
                    }
                    \times 2/3
                    {
                        \time 4/8
                        c'2
                        c'4
                    }
                }
            >>

    ..  container:: example

        Makes augmented tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(2, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.force_augmentation(container)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 2/8
                        c'8
                        [
                        c'16
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 4/3
                    {
                        \time 4/8
                        c'4
                        c'8
                    }
                }
            >>

    ..  container:: example

        Makes diminished tuplets and does not rewrite dots:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.force_diminution(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 7/16
                        c'8..
                        [
                        c'8..
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes diminished tuplets and rewrites dots:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.force_diminution(container)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'4
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 7/8
                    {
                        \time 7/16
                        c'4
                        c'4
                    }
                }
            >>

    ..  container:: example

        Makes augmented tuplets and does not rewrite dots:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.force_augmentation(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 7/16
                        c'8..
                        [
                        c'8..
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes augmented tuplets and rewrites dots:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.force_augmentation(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (3, 8), (7, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 7/4
                    {
                        \time 7/16
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Leaves trivializable tuplets as-is when ``trivialize`` is false:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(3, -2), (1,), (-2, 3), (1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_dots(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        r4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Rewrites trivializable tuplets when ``trivialize`` is true. Measures 2 and 4
        contain trivial tuplets with 1:1 ratios. To remove these trivial tuplets, set
        ``extract_trivial`` as shown in the next example:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(3, -2), (1,), (-2, 3), (1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.trivialize(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        r4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 3/8
                        c'8.
                        [
                        c'8.
                        ]
                    }
                }
            >>

        REGRESSION: Ignores ``trivialize`` and respects ``rewrite_dots`` when both are
        true. Measures 2 and 4 are first rewritten as trivial but then supplied again
        with nontrivial prolation when removing dots. The result is that measures 2 and 4
        carry nontrivial prolation with no dots:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(3, -2), (1,), (-2, 3), (1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.trivialize(container)
        ...     rmakers.rewrite_dots(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (3, 8), (3, 8), (3, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        r4
                        c'4.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/2
                    {
                        \time 3/8
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Leaves trivial tuplets as-is when ``extract_trivial`` is false:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(2, 3), (1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        c'4.
                        ~
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 2/8
                        c'8
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Extracts trivial tuplets when ``extract_trivial`` is true. Measures 2 and 4 in
        the example below now contain only a flat list of notes:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(2, 3), (1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        c'4.
                        ~
                    }
                    \time 2/8
                    c'8
                    [
                    c'8
                    ]
                    ~
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        c'4.
                        ~
                    }
                    \time 2/8
                    c'8
                    [
                    c'8
                    ]
                }
            >>

        .. note:: Flattening trivial tuplets makes it possible
            subsequently to rewrite the meter of the untupletted notes.

    ..  container:: example

        REGRESSION: Very long ties are preserved when ``extract_trivial`` is true:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(2, 3), (1, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.extract_trivial(container)
        ...     notes = abjad.select.notes(container)[:-1]
        ...     rmakers.tie(notes)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (2, 8), (3, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        ~
                        c'4.
                        ~
                    }
                    \time 2/8
                    c'8
                    [
                    ~
                    c'8
                    ]
                    ~
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4
                        ~
                        c'4.
                        ~
                    }
                    \time 2/8
                    c'8
                    [
                    ~
                    c'8
                    ]
                }
            >>

    ..  container:: example

        Masks every other output division:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(4, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     rmakers.force_rest(tuplets)
        ...     rmakers.rewrite_rest_filled(container)
        ...     rmakers.extract_trivial(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(3, 8), (4, 8), (3, 8), (4, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 3/8
                        c'4.
                        c'16.
                    }
                    \time 4/8
                    r2
                    \times 4/5
                    {
                        \time 3/8
                        c'4.
                        c'16.
                    }
                    \time 4/8
                    r2
                }
            >>


    ..  container:: example

        Tuplet numerators and denominators are reduced to numbers that are relatively
        prime when ``denominator`` is set to none. This means that ratios like
        ``6:4`` and ``10:8`` do not arise:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 4)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_dots(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 4/5
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set in terms of a unit duration
        when ``denominator`` is set to a duration. The setting does not affect the
        first tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 4)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, (1, 16))
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 8/10
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet in terms 32nd notes. The
        setting affects all tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 4)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, (1, 32))
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 16/20
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator each tuplet in terms 64th notes. The setting
        affects all tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 4)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, (1, 64))
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 8/10
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 16/20
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 24/20
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 32/40
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        The preferred denominator of each tuplet is set directly when ``denominator``
        is set to a positive integer. This example sets the preferred denominator of
        each tuplet to ``8``. Setting does not affect the third tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 4)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, 8)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 8/10
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 8/10
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 8/10
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``12``. Setting affects all
        tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 4)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, 12)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 12/15
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 12/15
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 12/10
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 12/15
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``13``. Setting does not
        affect any tuplet:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, 4)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     rmakers.rewrite_dots(container)
        ...     rmakers.denominator(container, 13)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 16), (4, 16), (6, 16), (8, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 2/16
                        c'32
                        [
                        c'8
                        ]
                    }
                    \times 4/5
                    {
                        \time 4/16
                        c'16
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 6/5
                    {
                        \time 6/16
                        c'16
                        c'4
                    }
                    \times 4/5
                    {
                        \time 8/16
                        c'8
                        c'2
                    }
                }
            >>

    ..  container:: example

        >>> def make_rhythm(divisions):
        ...     tag = abjad.Tag("TUPLET_RHYTHM_MAKER")
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(3, 2)], tag=tag
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container, tag=tag)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    %! TUPLET_RHYTHM_MAKER
                    \times 4/5
                    %! TUPLET_RHYTHM_MAKER
                    {
                        \time 1/2
                        %! TUPLET_RHYTHM_MAKER
                        c'4.
                        %! TUPLET_RHYTHM_MAKER
                        c'4
                    %! TUPLET_RHYTHM_MAKER
                    }
                    %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TUPLET_RHYTHM_MAKER
                    \times 3/5
                    %! TUPLET_RHYTHM_MAKER
                    {
                        \time 3/8
                        %! TUPLET_RHYTHM_MAKER
                        c'4.
                        %! TUPLET_RHYTHM_MAKER
                        c'4
                    %! TUPLET_RHYTHM_MAKER
                    }
                    %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TUPLET_RHYTHM_MAKER
                    \times 1/1
                    %! TUPLET_RHYTHM_MAKER
                    {
                        \time 5/16
                        %! TUPLET_RHYTHM_MAKER
                        c'8.
                        %! TUPLET_RHYTHM_MAKER
                        [
                        %! TUPLET_RHYTHM_MAKER
                        c'8
                        %! TUPLET_RHYTHM_MAKER
                        ]
                    %! TUPLET_RHYTHM_MAKER
                    }
                    %! TUPLET_RHYTHM_MAKER
                    \tweak text #tuplet-number::calc-fraction-text
                    %! TUPLET_RHYTHM_MAKER
                    \times 1/1
                    %! TUPLET_RHYTHM_MAKER
                    {
                        \time 5/16
                        %! TUPLET_RHYTHM_MAKER
                        c'8.
                        %! TUPLET_RHYTHM_MAKER
                        [
                        %! TUPLET_RHYTHM_MAKER
                        c'8
                        %! TUPLET_RHYTHM_MAKER
                        ]
                    %! TUPLET_RHYTHM_MAKER
                    }
                }
            >>

    ..  container:: example

        Makes tuplets with ``3:2`` ratios:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(3, 2)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 4/5
                    {
                        \time 1/2
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/5
                    {
                        \time 3/8
                        c'4.
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8.
                        [
                        c'8
                        ]
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 5/16
                        c'8.
                        [
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1, -1), (3, 1)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 1/2
                        c'4
                        r4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 3/4
                    {
                        \time 3/8
                        c'4.
                        c'8
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/6
                    {
                        \time 5/16
                        c'8.
                        r8.
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 5/4
                    {
                        \time 5/16
                        c'8.
                        [
                        c'16
                        ]
                    }
                }
            >>

    ..  container:: example

        Makes length-1 tuplets:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.tuplet(
        ...         divisions, [(1,)]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(1, 5), (1, 4), (1, 6), (7, 9)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \tweak edge-height #'(0.7 . 0)
                    \times 4/5
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 1/5
                        c'4
                    }
                    \tweak text #tuplet-number::calc-fraction-text
                    \times 1/1
                    {
                        \time 1/4
                        c'4
                    }
                    \tweak edge-height #'(0.7 . 0)
                    \times 2/3
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 1/6
                        c'4
                    }
                    \tweak edge-height #'(0.7 . 0)
                    \times 8/9
                    {
                        #(ly:expect-warning "strange time signature found")
                        \time 7/9
                        c'2..
                    }
                }
            >>

    """
    tuplet_ratios_ = [abjad.Ratio(_) for _ in tuplet_ratios]
    return _make_tuplet_rhythm_maker_music(
        divisions,
        tuplet_ratios_,
        # denominator=denominator,
        # spelling=spelling,
        self_tag=tag,
    )


def unbeam(argument) -> None:
    """
    Unbeams each leaf in ``argument``.
    """
    leaves = abjad.select.leaves(argument)
    for leaf in leaves:
        abjad.detach(abjad.BeamCount, leaf)
        abjad.detach(abjad.StartBeam, leaf)
        abjad.detach(abjad.StopBeam, leaf)


def untie(argument) -> None:
    r"""
    Deatches ties from each leaf in ``argument``.

    ..  container:: example

        Attaches ties to nonlast notes; then detaches ties from select notes:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     notes = abjad.select.notes(container)[:-1]
        ...     rmakers.tie(notes)
        ...     notes = abjad.select.notes(container)
        ...     notes = abjad.select.get(notes, [0], 4)
        ...     rmakers.untie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        ~
                        c'8
                        ]
                        ~
                    }
                    \times 2/3
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        ~
                        c'8
                        c'8
                        ]
                    }
                }
            >>

    ..  container:: example

        Attaches repeat-ties to nonfirst notes; then detaches ties from select notes:

        >>> def make_rhythm(divisions):
        ...     nested_music = rmakers.even_division(
        ...         divisions, [8], extra_counts=[1]
        ...     )
        ...     container = abjad.Container(nested_music)
        ...     notes = abjad.select.notes(container)[1:]
        ...     rmakers.repeat_tie(notes)
        ...     notes = abjad.select.notes(container)
        ...     notes = abjad.select.get(notes, [0], 4)
        ...     rmakers.untie(notes)
        ...     rmakers.beam(container)
        ...     music = abjad.mutate.eject_contents(container)
        ...     return music

        >>> divisions = [(2, 8), (2, 8), (2, 8), (2, 8), (2, 8), (2, 8)]
        >>> music = make_rhythm(divisions)
        >>> lilypond_file = rmakers.example(music, divisions)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            <<
                \context RhythmicStaff = "Staff"
                \with
                {
                    \override Clef.stencil = ##f
                }
                {
                    \times 2/3
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                        \repeatTie
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        \repeatTie
                        c'8
                        ]
                    }
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        \repeatTie
                        c'8
                        ]
                        \repeatTie
                    }
                    \times 2/3
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
                    \times 2/3
                    {
                        \time 2/8
                        c'8
                        [
                        \repeatTie
                        c'8
                        c'8
                        ]
                        \repeatTie
                    }
                }
            >>

    """
    for leaf in abjad.select.leaves(argument):
        abjad.detach(abjad.Tie, leaf)
        abjad.detach(abjad.RepeatTie, leaf)


def wrap_in_time_signature_staff(music, divisions):
    """
    Makes staff with two voices: one voice for ``music`` and another voice
    with time signatures (equal to divisions).

    See ``rmakers.rewrite_meter()`` for examples of this function.
    """
    music = abjad.sequence.flatten(music, depth=-1)
    assert all(isinstance(_, abjad.Component) for _ in music), repr(music)
    assert isinstance(music, list), repr(music)
    time_signatures = [abjad.TimeSignature(_) for _ in divisions]
    staff = _make_time_signature_staff(time_signatures)
    music_voice = staff["RhythmMaker.Music"]
    music_voice.extend(music)
    _validate_tuplets(music_voice)
    return music_voice


def written_duration(argument, duration: abjad.typings.Duration) -> None:
    """
    Sets written duration of each leaf in ``argument`` to ``duration``.
    """
    duration_ = abjad.Duration(duration)
    leaves = abjad.select.leaves(argument)
    for leaf in leaves:
        old_duration = leaf.written_duration
        if duration_ == old_duration:
            continue
        leaf.written_duration = duration_
        multiplier = old_duration / duration_
        leaf.multiplier = multiplier
