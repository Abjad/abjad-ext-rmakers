"""
Makers.
"""

import inspect
import math
import types
import typing

import abjad

from . import classes as _classes


def _apply_ties_to_split_notes(
    tuplets,
    unscaled_end_counts,
    unscaled_preamble,
    unscaled_talea,
    talea,
):
    leaves = abjad.select.leaves(tuplets)
    written_durations = [leaf.written_duration for leaf in leaves]
    written_durations = list(written_durations)
    total_duration = abjad.sequence.weight(written_durations)
    preamble_weights = []
    if unscaled_preamble:
        preamble_weights = []
        for numerator in unscaled_preamble:
            pair = (numerator, talea.denominator)
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
            pair = (numerator, talea.denominator)
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


def _assert_are_pairs_durations_or_time_signatures(argument):
    for item in abjad.sequence.flatten(argument, classes=(list,)):
        if not isinstance(item, tuple | abjad.Duration | abjad.TimeSignature):
            raise Exception(argument)


def _fix_rounding_error(leaves, total_duration, interpolation):
    duration = abjad.get.duration(leaves)
    if not duration == total_duration:
        needed_duration = total_duration - abjad.get.duration(leaves[:-1])
        multiplier = needed_duration / interpolation.written_duration
        pair = abjad.duration.pair(multiplier)
        leaves[-1].multiplier = pair


def _function_name(frame):
    function_name = frame.f_code.co_name
    string = f"rmakers.{function_name}()"
    return abjad.Tag(string)


def _get_interpolations(interpolations, previous_state):
    specifiers_ = interpolations
    if specifiers_ is None:
        specifiers_ = abjad.CyclicTuple([_classes.Interpolation()])
    elif isinstance(specifiers_, _classes.Interpolation):
        specifiers_ = abjad.CyclicTuple([specifiers_])
    else:
        specifiers_ = abjad.CyclicTuple(specifiers_)
    string = "durations_consumed"
    durations_consumed = previous_state.get(string, 0)
    specifiers_ = abjad.sequence.rotate(specifiers_, n=-durations_consumed)
    specifiers_ = abjad.CyclicTuple(specifiers_)
    return specifiers_


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


def _make_accelerando(
    duration, interpolations, index, *, tag: abjad.Tag = abjad.Tag()
) -> abjad.Tuplet:
    """
    Makes notes with LilyPond multipliers equal to ``duration``.

    Total number of notes not specified: total duration is specified instead.

    Selects interpolation specifier at ``index`` in ``interpolations``.

    Computes duration multipliers interpolated from interpolation specifier start to
    stop.

    Sets note written durations according to interpolation specifier.
    """
    assert isinstance(duration, abjad.Duration)
    assert all(isinstance(_, _classes.Interpolation) for _ in interpolations)
    assert isinstance(index, int)
    interpolation = interpolations[index]
    durations = _interpolate_divide(
        total_duration=duration,
        start_duration=interpolation.start_duration,
        stop_duration=interpolation.stop_duration,
    )
    if durations == "too small":
        notes = abjad.makers.make_notes([0], [duration], tag=tag)
        tuplet = abjad.Tuplet((1, 1), notes, tag=tag)
        return tuplet
    durations = _round_durations(durations, 2**10)
    notes = []
    for i, duration_ in enumerate(durations):
        written_duration = interpolation.written_duration
        multiplier = duration_ / written_duration
        pair = abjad.duration.pair(multiplier)
        note = abjad.Note(0, written_duration, multiplier=pair, tag=tag)
        notes.append(note)
    _fix_rounding_error(notes, duration, interpolation)
    tuplet = abjad.Tuplet((1, 1), notes, tag=tag)
    return tuplet


def _make_incised_duration_lists(
    pairs,
    prefix_talea,
    prefix_counts,
    suffix_talea,
    suffix_counts,
    extra_counts,
    incise,
):
    assert all(isinstance(_, tuple) for _ in pairs), repr(pairs)
    duration_lists, prefix_talea_index, suffix_talea_index = [], 0, 0
    for pair_index, pair in enumerate(pairs):
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
        numerator = pair[0] + (prolation_addendum % pair[0])
        duration_list = _make_duration_list(numerator, prefix, suffix, incise)
        duration_lists.append(duration_list)
    for duration_list in duration_lists:
        assert all(isinstance(_, abjad.Duration) for _ in duration_list)
    return duration_lists


def _make_leaf_and_tuplet_list(
    durations,
    increase_monotonic=None,
    forbidden_note_duration=None,
    forbidden_rest_duration=None,
    tag=None,
) -> list[abjad.Leaf | abjad.Tuplet]:
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    assert all(_ != 0 for _ in durations), repr(durations)
    leaves_and_tuplets: list[abjad.Leaf | abjad.Tuplet] = []
    pitches: list[int | None]
    for duration in durations:
        if 0 < duration:
            pitches = [0]
        else:
            pitches = [None]
        duration = abs(duration)
        leaves_and_tuplets_ = abjad.makers.make_leaves(
            pitches,
            [duration],
            increase_monotonic=increase_monotonic,
            forbidden_note_duration=forbidden_note_duration,
            forbidden_rest_duration=forbidden_rest_duration,
            tag=tag,
        )
        # TODO: is this needed?
        if (
            1 < len(leaves_and_tuplets_)
            and abjad.get.logical_tie(leaves_and_tuplets_[0]).is_trivial
            and not isinstance(leaves_and_tuplets_[0], abjad.Rest)
        ):
            abjad.tie(leaves_and_tuplets_)
        leaves_and_tuplets.extend(leaves_and_tuplets_)
    return leaves_and_tuplets


def _make_middle_durations(middle_duration, incise):
    assert isinstance(middle_duration, abjad.Duration), repr(middle_duration)
    assert middle_duration.denominator == 1, repr(middle_duration)
    assert isinstance(incise, _classes.Incise), repr(incise)
    durations = []
    if not (incise.fill_with_rests):
        if not incise.outer_tuplets_only:
            if 0 < middle_duration:
                if incise.body_ratio is not None:
                    shards = abjad.math.divide_integer_by_ratio(
                        middle_duration.numerator, incise.body_ratio
                    )
                    durations_ = [abjad.Duration(_) for _ in shards]
                    durations.extend(durations_)
                else:
                    durations.append(middle_duration)
        else:
            if 0 < middle_duration:
                durations.append(middle_duration)
    else:
        if not incise.outer_tuplets_only:
            if 0 < middle_duration:
                durations.append(-abs(middle_duration))
        else:
            if 0 < middle_duration:
                durations.append(-abs(middle_duration))
    assert isinstance(durations, list)
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    return durations


def _make_numerator_lists(
    pairs, preamble, talea, extra_counts, end_counts, read_talea_once_only
):
    assert all(isinstance(_, tuple) for _ in pairs), repr(pairs)
    assert all(isinstance(_, int) for _ in end_counts), repr(end_counts)
    assert all(isinstance(_, int) for _ in preamble), repr(preamble)
    for count in talea:
        assert isinstance(count, int) or count in "+-", repr(talea)
    if "+" in talea or "-" in talea:
        assert not preamble, repr(preamble)
    prolated_pairs = _make_prolated_pairs(pairs, extra_counts)
    pairs = []
    for item in prolated_pairs:
        if isinstance(item, tuple):
            pairs.append(item)
        else:
            pairs.append(item.pair)
    if not preamble and not talea:
        return pairs, None
    prolated_numerators = [_[0] for _ in pairs]
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
    numerator_lists = _split_talea_extended_to_weights(
        preamble, read_talea_once_only, talea, prolated_numerators
    )
    if end_counts:
        end_counts = list(end_counts)
        end_weight = abjad.sequence.weight(end_counts)
        numerator_list_weights = [abjad.sequence.weight(_) for _ in numerator_lists]
        counts = abjad.sequence.flatten(numerator_lists)
        counts_weight = abjad.sequence.weight(counts)
        assert end_weight <= counts_weight, repr(end_counts)
        left = counts_weight - end_weight
        right = end_weight
        counts = abjad.sequence.split(counts, [left, right])
        counts = counts[0] + end_counts
        assert abjad.sequence.weight(counts) == counts_weight
        numerator_lists = abjad.sequence.partition_by_weights(
            counts, numerator_list_weights
        )
    for numerator_list in numerator_lists:
        assert all(isinstance(_, int) for _ in numerator_list), repr(numerator_list)
    return numerator_lists, expanded_talea


def _make_duration_list(numerator, prefix, suffix, incise, *, is_note_filled=True):
    numerator = abjad.Duration(numerator)
    prefix = [abjad.Duration(_) for _ in prefix]
    suffix = [abjad.Duration(_) for _ in suffix]
    prefix_weight = abjad.math.weight(prefix)
    suffix_weight = abjad.math.weight(suffix)
    middle_duration = numerator - prefix_weight - suffix_weight
    assert isinstance(middle_duration, abjad.Duration), repr(middle_duration)
    if numerator < prefix_weight:
        weights = [numerator]
        prefix = abjad.sequence.split(prefix, weights, cyclic=False, overhang=False)[0]
    middle_durations = _make_middle_durations(middle_duration, incise)
    suffix_space = numerator - prefix_weight
    if suffix_space <= 0:
        suffix = []
    elif suffix_space < suffix_weight:
        weights = [suffix_space]
        suffix = abjad.sequence.split(suffix, weights, cyclic=False, overhang=False)[0]
    assert all(isinstance(_, abjad.Duration) for _ in prefix), repr(prefix)
    assert all(isinstance(_, abjad.Duration) for _ in suffix), repr(suffix)
    duration_list = prefix + middle_durations + suffix
    assert all(isinstance(_, abjad.Duration) for _ in duration_list), repr(
        duration_list
    )
    return duration_list


def _make_outer_tuplets_only_incised_duration_lists(
    pairs,
    prefix_talea,
    prefix_counts,
    suffix_talea,
    suffix_counts,
    extra_counts,
    incise,
):
    assert all(isinstance(_, tuple) for _ in pairs), repr(pairs)
    numeric_map, prefix_talea_index, suffix_talea_index = [], 0, 0
    prefix_length, suffix_length = prefix_counts[0], suffix_counts[0]
    start = prefix_talea_index
    stop = prefix_talea_index + prefix_length
    prefix = prefix_talea[start:stop]
    start = suffix_talea_index
    stop = suffix_talea_index + suffix_length
    suffix = suffix_talea[start:stop]
    if len(pairs) == 1:
        prolation_addendum = extra_counts[0]
        numerator = getattr(pairs[0], "numerator", pairs[0][0])
        numerator += prolation_addendum % numerator
        numeric_map_part = _make_duration_list(numerator, prefix, suffix, incise)
        numeric_map.append(numeric_map_part)
    else:
        prolation_addendum = extra_counts[0]
        if isinstance(pairs[0], tuple):
            numerator = pairs[0][0]
        else:
            numerator = pairs[0].numerator
        numerator += prolation_addendum % numerator
        numeric_map_part = _make_duration_list(numerator, prefix, (), incise)
        numeric_map.append(numeric_map_part)
        for i, pair in enumerate(pairs[1:-1]):
            index = i + 1
            prolation_addendum = extra_counts[index]
            numerator = pair[0]
            numerator += prolation_addendum % numerator
            numeric_map_part = _make_duration_list(numerator, (), (), incise)
            numeric_map.append(numeric_map_part)
        try:
            index = i + 2
            prolation_addendum = extra_counts[index]
        except UnboundLocalError:
            index = 1 + 2
            prolation_addendum = extra_counts[index]
        if isinstance(pairs[-1], tuple):
            numerator = pairs[-1][0]
        else:
            numerator = pairs[-1].numerator
        numerator += prolation_addendum % numerator
        numeric_map_part = _make_duration_list(numerator, (), suffix, incise)
        numeric_map.append(numeric_map_part)
    return numeric_map


def _make_prolated_pairs(pairs, extra_counts):
    prolated_pairs = []
    for i, pair in enumerate(pairs):
        if not extra_counts:
            prolated_pairs.append(pair)
            continue
        prolation_addendum = extra_counts[i]
        numerator = pair[0]
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
        numerator, denominator = pair
        prolated_pair = (numerator + prolation_addendum, denominator)
        prolated_pairs.append(prolated_pair)
    assert all(isinstance(_, tuple) for _ in prolated_pairs)
    return prolated_pairs


def _make_state_dictionary(
    *,
    durations_consumed,
    logical_ties_produced,
    previous_durations_consumed,
    previous_incomplete_last_note,
    previous_logical_ties_produced,
    state,
):
    durations_consumed_ = previous_durations_consumed + durations_consumed
    state["durations_consumed"] = durations_consumed_
    logical_ties_produced_ = previous_logical_ties_produced + logical_ties_produced
    if previous_incomplete_last_note:
        logical_ties_produced_ -= 1
    state["logical_ties_produced"] = logical_ties_produced_
    state = dict(sorted(state.items()))
    return state


def _make_talea_tuplets(
    durations,
    self_extra_counts,
    previous_state,
    self_read_talea_once_only,
    spelling,
    self_state,
    talea,
    tag,
):
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    prepared = _prepare_talea_rhythm_maker_input(
        self_extra_counts, previous_state, talea
    )
    scaled = _scale_rhythm_maker_input(durations, talea.denominator, prepared)
    assert scaled.counts.talea
    numerator_lists, expanded_talea = _make_numerator_lists(
        scaled.pairs,
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
    talea_weight_consumed = sum(abjad.sequence.weight(_) for _ in numerator_lists)
    duration_lists = [
        [abjad.Duration(_, scaled.lcd) for _ in n] for n in numerator_lists
    ]
    leaf_lists = []
    for duration_list in duration_lists:
        leaf_list = _make_leaf_and_tuplet_list(
            duration_list,
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        leaf_lists.append(leaf_list)
    if not scaled.counts.extra_counts:
        tuplets = [abjad.Tuplet((1, 1), _) for _ in leaf_lists]
    else:
        durations_ = [abjad.Duration(_) for _ in scaled.pairs]
        tuplets = _make_talea_rhythm_maker_tuplets(durations_, leaf_lists, tag=tag)
    _apply_ties_to_split_notes(
        tuplets,
        prepared.end_counts,
        prepared.preamble,
        unscaled_talea,
        talea,
    )
    for tuplet in abjad.iterate.components(tuplets, abjad.Tuplet):
        tuplet.normalize_multiplier()
    assert isinstance(self_state, dict)
    advanced_talea = _classes.Talea(
        counts=prepared.talea,
        denominator=talea.denominator,
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
    assert isinstance(previous_state, dict)
    self_state[string] = previous_state.get(string, 0)
    self_state[string] += talea_weight_consumed
    return tuplets


def _make_talea_rhythm_maker_tuplets(durations, leaf_lists, *, tag):
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    assert len(durations) == len(leaf_lists)
    tuplets = []
    for duration, leaf_list in zip(durations, leaf_lists):
        tuplet = abjad.Tuplet.from_duration(duration, leaf_list, tag=tag)
        tuplets.append(tuplet)
    return tuplets


def _make_tuplet_rhythm_maker_music(
    durations,
    self_tuplet_ratios,
    *,
    tag=None,
):
    tuplets = []
    tuplet_ratios = abjad.CyclicTuple(self_tuplet_ratios)
    for i, duration in enumerate(durations):
        ratio = tuplet_ratios[i]
        tuplet = abjad.makers.tuplet_from_duration_and_ratio(duration, ratio, tag=tag)
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


def _prepare_talea_rhythm_maker_input(self_extra_counts, previous_state, talea):
    talea_weight_consumed = previous_state.get("talea_weight_consumed", 0)
    talea = talea.advance(talea_weight_consumed)
    end_counts = talea.end_counts or ()
    preamble = talea.preamble or ()
    talea = talea.counts or ()
    talea = abjad.CyclicTuple(talea)
    extra_counts = list(self_extra_counts or [])
    durations_consumed = previous_state.get("durations_consumed", 0)
    extra_counts = abjad.sequence.rotate(extra_counts, -durations_consumed)
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


def _scale_rhythm_maker_input(durations, talea_denominator, counts):
    assert all(isinstance(_, abjad.Duration) for _ in durations), repr(durations)
    talea_denominator = talea_denominator or 1
    scaled_pairs = durations[:]
    dummy_pair = (1, talea_denominator)
    scaled_pairs.append(dummy_pair)
    scaled_pairs = abjad.Duration.durations_to_nonreduced_fractions(scaled_pairs)
    dummy_pair = scaled_pairs.pop()
    lcd = dummy_pair[1]
    multiplier = lcd / talea_denominator
    assert abjad.math.is_integer_equivalent(multiplier)
    multiplier = int(multiplier)
    scaled_counts = types.SimpleNamespace()
    for name, vector in counts.__dict__.items():
        vector = [multiplier * _ for _ in vector]
        cyclic_vector = abjad.CyclicTuple(vector)
        setattr(scaled_counts, name, cyclic_vector)
    assert len(scaled_pairs) == len(durations)
    assert len(scaled_counts.__dict__) == len(counts.__dict__)
    assert all(isinstance(_, tuple) for _ in scaled_pairs), repr(scaled_pairs)
    return types.SimpleNamespace(pairs=scaled_pairs, lcd=lcd, counts=scaled_counts)


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


def accelerando(
    durations,
    *interpolations: typing.Sequence[abjad.typings.Duration],
    previous_state: dict | None = None,
    spelling: _classes.Spelling = _classes.Spelling(),
    state: dict | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one accelerando (or ritardando) for each duration in ``durations``.

    ..  container:: example

        >>> def make_lilypond_file(pairs, interpolations):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.accelerando(durations, *interpolations)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.feather_beam(voice)
        ...     rmakers.duration_bracket(voice)
        ...     rmakers.swap_length_1(voice)
        ...     score = lilypond_file["Score"]
        ...     abjad.override(score).TupletBracket.padding = 2
        ...     abjad.override(score).TupletBracket.bracket_visibility = True
        ...     return lilypond_file

    ..  container:: example

        Makes accelerandi:

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> interpolations = [[(1, 8), (1, 20), (1, 16)]]
        >>> lilypond_file = make_lilypond_file(pairs, interpolations)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.padding = 2
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
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

    ..  container:: example

        Makes ritardandi:

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> interpolations = [[(1, 20), (1, 8), (1, 16)]]
        >>> lilypond_file = make_lilypond_file(pairs, interpolations)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.padding = 2
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
                }
            }

    ..  container:: example

        Makes accelerandi and ritardandi, alternatingly:

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8)]
        >>> interpolations = [[(1, 8), (1, 20), (1, 16)], [(1, 20), (1, 8), (1, 16)]]
        >>> lilypond_file = make_lilypond_file(pairs, interpolations)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.padding = 2
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 2 }
                        \tuplet 1/1
                        {
                            \time 4/8
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) \rhythm { 4. }
                        \tuplet 1/1
                        {
                            \time 3/8
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
                }
            }

    ..  container:: example

        Populates short duration with single note:

        >>> pairs = [(5, 8), (3, 8), (1, 8)]
        >>> interpolations = [[(1, 8), (1, 20), (1, 16)]]
        >>> lilypond_file = make_lilypond_file(pairs, interpolations)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score)
            >>> print(string)
            \context Score = "Score"
            \with
            {
                \override TupletBracket.bracket-visibility = ##t
                \override TupletBracket.padding = 2
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
                        \override TupletNumber.text = \markup \scale #'(0.75 . 0.75) { \rhythm { 2 } + \rhythm { 8 } }
                        \tuplet 1/1
                        {
                            \time 5/8
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
                        {
                            \time 1/8
                            c'8
                        }
                    }
                }
            }

    """
    _assert_are_pairs_durations_or_time_signatures(durations)
    durations = [abjad.Duration(_) for _ in durations]
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    interpolations_ = []
    for interpolation in interpolations:
        interpolation_durations = [abjad.Duration(_) for _ in interpolation]
        interpolation_ = _classes.Interpolation(*interpolation_durations)
        interpolations_.append(interpolation_)
    previous_state = previous_state or {}
    if state is None:
        state = {}
    interpolations_ = _get_interpolations(interpolations_, previous_state)
    tuplets = []
    for i, duration in enumerate(durations):
        tuplet = _make_accelerando(duration, interpolations_, i, tag=tag)
        tuplets.append(tuplet)
    voice = abjad.Voice(tuplets)
    logical_ties_produced = len(abjad.select.logical_ties(voice))
    new_state = _make_state_dictionary(
        durations_consumed=len(durations),
        logical_ties_produced=logical_ties_produced,
        previous_durations_consumed=previous_state.get("durations_consumed", 0),
        previous_incomplete_last_note=previous_state.get("incomplete_last_note", False),
        previous_logical_ties_produced=previous_state.get("logical_ties_produced", 0),
        state=state,
    )
    components, tuplets = abjad.mutate.eject_contents(voice), []
    for component in components:
        assert isinstance(component, abjad.Tuplet)
        abjad.attach("FEATHER_BEAM_CONTAINER", tuplet)
        tuplets.append(component)
    state.clear()
    state.update(new_state)
    return tuplets


def even_division(
    durations,
    denominators: typing.Sequence[int],
    *,
    denominator: str | int = "from_counts",
    extra_counts: typing.Sequence[int] = (0,),
    previous_state: dict | None = None,
    spelling: _classes.Spelling = _classes.Spelling(),
    state: dict | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one even-division tuplet for each duration in ``durations``.

    Basic example:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.even_division(durations, [8], extra_counts=[0, 0, 1])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.force_diminution(voice)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(5, 16), (6, 16), (6, 16)]
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
                        \tuplet 8/5
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
                        \tuplet 4/3
                        {
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

    ..  container:: example

        Understanding the ``denominators`` argument to ``rmakers.even_division()``.

        ..  container:: example

            Fills tuplets with 16th notes and 8th notes, alternately:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(durations, [16, 8])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 16), (3, 8), (3, 4)]
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
                    }
                }

        ..  container:: example

            Fills tuplets with 8th notes:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(durations, [8])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 16), (3, 8), (3, 4)]
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
                    }
                }

            (Fills tuplets less than twice the duration of an eighth note with a single
            attack.)

        ..  container:: example

            Fills tuplets with quarter notes:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(durations, [4])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 16), (3, 8), (3, 4)]
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
                            \time 3/16
                            c'8.
                            \time 3/8
                            c'4.
                            \time 3/4
                            c'4
                            c'4
                            c'4
                        }
                    }
                }

            (Fills tuplets less than twice the duration of a quarter note with a single
            attack.)

        ..  container:: example

            Fills tuplets with half notes:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(durations, [2])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 16), (3, 8), (3, 4)]
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
                            \time 3/16
                            c'8.
                            \time 3/8
                            c'4.
                            \time 3/4
                            c'2.
                        }
                    }
                }

            (Fills tuplets less than twice the duration of a half note with a single
            attack.)

    ..  container:: example

        Using ``rmakers.even_division()`` with the ``denominator`` keyword.

        ..  container:: example

            With ``denominator=None``. Expresses tuplet ratios in the usual way
            with numerator and denominator relatively prime:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=[4], denominator=None
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
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
                            \tuplet 3/2
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
                            \tuplet 5/3
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
                            \tuplet 3/2
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
                            \tuplet 5/3
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
                    }
                }

        ..  container:: example

            With ``denominator=4``:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=[4], denominator=4
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
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
                            \tuplet 6/4
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
                            \tuplet 5/3
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
                            \tuplet 6/4
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
                            \tuplet 5/3
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
                    }
                }

        ..  container:: example

            With ``denominator=8``:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=[4], denominator=8
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
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
                            \tuplet 12/8
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
                            \tuplet 5/3
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
                            \tuplet 12/8
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
                            \tuplet 5/3
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
                    }
                }

        ..  container:: example

            With ``denominator=16``:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=[4], denominator=16
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
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
                            \tuplet 24/16
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
                            \tuplet 5/3
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
                            \tuplet 24/16
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
                            \tuplet 5/3
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
                    }
                }

        ..  container:: example

            With ``denominator="from_counts"``:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=[4], denominator="from_counts"
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
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
                            \tuplet 12/8
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
                            \tuplet 10/6
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
                            \tuplet 12/8
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
                            \tuplet 10/6
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
                    }
                }

    ..  container:: example

        Using ``rmakers.even_division()`` with the ``extra_counts`` keyword.

        ..  container:: example

            Adds extra counts to tuplets according to a pattern of three elements:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=[0, 1, 2]
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 8), (3, 8), (3, 8), (3, 8), (3, 8)]
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
                            c'16
                            c'16
                            c'16
                            c'16
                            c'16
                            ]
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 7/6
                            {
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
                            \tuplet 8/6
                            {
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
                            \tuplet 7/6
                            {
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
                    }
                }

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

            >>> def make_lilypond_file(pairs, extra_counts):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=extra_counts
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = 12 * [(6, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts)
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
                {
                    \context RhythmicStaff = "Staff"
                    \with
                    {
                        \override Clef.stencil = ##f
                        \override TextScript.staff-padding = 7
                    }
                    {
                        \context Voice = "Voice"
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
                            \tuplet 7/6
                            {
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
                            \tuplet 8/6
                            {
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
                            \tuplet 9/6
                            {
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
                            \tuplet 10/6
                            {
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
                            \tuplet 11/6
                            {
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
                            \tuplet 7/6
                            {
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
                            \tuplet 8/6
                            {
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
                            \tuplet 9/6
                            {
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
                            \tuplet 10/6
                            {
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
                            \tuplet 11/6
                            {
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
                    }
                }

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

            >>> def make_lilypond_file(pairs, extra_counts):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.even_division(
            ...         durations, [16], extra_counts=extra_counts
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = 9 * [(6, 16)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts)
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
                {
                    \context RhythmicStaff = "Staff"
                    \with
                    {
                        \override Clef.stencil = ##f
                        \override TextScript.staff-padding = 8
                    }
                    {
                        \context Voice = "Voice"
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
                            \tuplet 5/6
                            {
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
                            \tuplet 4/6
                            {
                                c'16
                                ^ \markup {  -2 becomes -2 }
                                [
                                c'16
                                c'16
                                c'16
                                ]
                            }
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
                            \tuplet 5/6
                            {
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
                            \tuplet 4/6
                            {
                                c'16
                                ^ \markup {  -5 becomes -2 }
                                [
                                c'16
                                c'16
                                c'16
                                ]
                            }
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
                            \tuplet 5/6
                            {
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
                            \tuplet 4/6
                            {
                                c'16
                                ^ \markup {  -8 becomes -2 }
                                [
                                c'16
                                c'16
                                c'16
                                ]
                            }
                        }
                    }
                }

            This modular formula ensures that rhythm-maker ``denominators`` are
            always respected: a very small number of extra counts never causes
            a ``16``-denominated tuplet to result in 8th- or quarter-note
            rhythms.

    """
    _assert_are_pairs_durations_or_time_signatures(durations)
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    durations = [abjad.Duration(_) for _ in durations]
    assert all(isinstance(_, int) for _ in denominators), repr(denominators)
    if denominator is not None and not isinstance(denominator, int):
        assert denominator in ("from_counts",), repr(denominator)
    assert all(isinstance(_, int) for _ in extra_counts), repr(extra_counts)
    previous_state = previous_state or {}
    if state is None:
        state = {}
    tuplets = []
    assert isinstance(previous_state, dict)
    durations_consumed = previous_state.get("durations_consumed", 0)
    denominators_ = list(denominators)
    denominators_ = abjad.sequence.rotate(denominators_, -durations_consumed)
    cyclic_denominators = abjad.CyclicTuple(denominators_)
    extra_counts_ = extra_counts or [0]
    extra_counts__ = list(extra_counts_)
    extra_counts__ = abjad.sequence.rotate(extra_counts__, -durations_consumed)
    cyclic_extra_counts = abjad.CyclicTuple(extra_counts__)
    for i, duration in enumerate(durations):
        if not abjad.math.is_positive_integer_power_of_two(duration.denominator):
            raise Exception(f"non-power-of-two durations not implemented: {duration}")
        denominator_ = cyclic_denominators[i]
        extra_count = cyclic_extra_counts[i]
        basic_duration = abjad.Duration(1, denominator_)
        unprolated_note_count = None
        if duration < 2 * basic_duration:
            notes = abjad.makers.make_notes([0], [duration], tag=tag)
        else:
            unprolated_note_count = duration / basic_duration
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
            durations_ = note_count * [basic_duration]
            notes = abjad.makers.make_notes([0], durations_, tag=tag)
            assert all(_.written_duration.denominator == denominator_ for _ in notes)
        tuplet_duration = duration
        tuplet = abjad.Tuplet.from_duration(tuplet_duration, notes, tag=tag)
        if denominator == "from_counts" and unprolated_note_count is not None:
            tuplet.denominator = unprolated_note_count
        elif isinstance(denominator, int):
            tuplet.denominator = denominator
        tuplets.append(tuplet)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    voice = abjad.Voice(tuplets)
    logical_ties_produced = len(abjad.select.logical_ties(voice))
    new_state = _make_state_dictionary(
        durations_consumed=len(durations),
        logical_ties_produced=logical_ties_produced,
        previous_durations_consumed=previous_state.get("durations_consumed", 0),
        previous_incomplete_last_note=previous_state.get("incomplete_last_note", False),
        previous_logical_ties_produced=previous_state.get("logical_ties_produced", 0),
        state=state,
    )
    components, tuplets = abjad.mutate.eject_contents(voice), []
    for component in components:
        assert isinstance(component, abjad.Tuplet)
        tuplets.append(component)
    state.clear()
    state.update(new_state)
    return tuplets


def incised(
    durations,
    *,
    body_ratio: tuple[int, ...] = (1,),
    extra_counts: typing.Sequence[int] = (),
    fill_with_rests: bool = False,
    outer_tuplets_only: bool = False,
    prefix_counts: typing.Sequence[int] = (),
    prefix_talea: typing.Sequence[int] = (),
    spelling: _classes.Spelling = _classes.Spelling(),
    suffix_counts: typing.Sequence[int] = (),
    suffix_talea: typing.Sequence[int] = (),
    tag: abjad.Tag | None = None,
    talea_denominator: int | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one incised tuplet for each duration in  ``durations``.

    Set ``prefix_talea=[-1]`` with ``prefix_counts=[1]`` to incise a rest at the start
    of each tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         talea_denominator=16,
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        r16
                        c'4
                        r16
                        c'4
                        r16
                        c'4
                        r16
                        c'4
                    }
                }
            }

    Set ``prefix_talea=[-1]`` with ``prefix_counts=[2]`` to incise 2 rests at the start
    of each tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         prefix_talea=[-1],
        ...         prefix_counts=[2],
        ...         talea_denominator=16,
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        r16
                        r16
                        c'8.
                        r16
                        r16
                        c'8.
                        r16
                        r16
                        c'8.
                        r16
                        r16
                        c'8.
                    }
                }
            }

    Set ``prefix_talea=[1]`` with ``prefix_counts=[1]`` to incise 1 note at the start
    of each tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         prefix_talea=[1],
        ...         prefix_counts=[1],
        ...         talea_denominator=16,
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        c'16
                        c'4
                        c'16
                        c'4
                        c'16
                        c'4
                        c'16
                        c'4
                    }
                }
            }

    Set ``prefix_talea=[1]`` with ``prefix_counts=[2]`` to incise 2 notes at the start
    of each tuplet:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         prefix_talea=[1],
        ...         prefix_counts=[2],
        ...         talea_denominator=16,
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        c'16
                        [
                        c'16
                        c'8.
                        ]
                        c'16
                        [
                        c'16
                        c'8.
                        ]
                        c'16
                        [
                        c'16
                        c'8.
                        ]
                        c'16
                        [
                        c'16
                        c'8.
                        ]
                    }
                }
            }

    Incise rests at the beginning and end of each tuplet like this:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         extra_counts=[1],
        ...         prefix_talea=[-1],
        ...         prefix_counts=[1],
        ...         suffix_talea=[-1],
        ...         suffix_counts=[1],
        ...         talea_denominator=16,
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \tuplet 6/5
                        {
                            \time 5/16
                            r16
                            c'4
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            r16
                            c'4
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            r16
                            c'4
                            r16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            r16
                            c'4
                            r16
                        }
                    }
                }
            }

    Set ``body_ratio=(1, 1)`` to divide the middle part of each tuplet ``1:1``:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         body_ratio=(1, 1),
        ...         talea_denominator=16,
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \time 5/16
                        c'8
                        [
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                        ]
                        c'8
                        [
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                        ]
                        c'8
                        [
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                        ]
                        c'8
                        [
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                        ]
                    }
                }
            }

    Set ``body_ratio=(1, 1, 1)`` to divide the middle part of each tuplet ``1:1:1``:

    ..  container:: example

        TODO. Allow nested tuplets to clean up notation:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.incised(
        ...         durations,
        ...         body_ratio=(1, 1, 1),
        ...         talea_denominator=16,
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = 4 * [(5, 16)]
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
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            \time 5/16
                            c'8
                            [
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                            ]
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            [
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                            ]
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            [
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                            ]
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            [
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 48/32
                        {
                            c'8
                            ~
                            c'32
                            ]
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    _assert_are_pairs_durations_or_time_signatures(durations)
    durations = [abjad.Duration(_) for _ in durations]
    incise = _classes.Incise(
        body_ratio=body_ratio,
        fill_with_rests=fill_with_rests,
        outer_tuplets_only=outer_tuplets_only,
        prefix_talea=prefix_talea,
        prefix_counts=prefix_counts,
        suffix_talea=suffix_talea,
        suffix_counts=suffix_counts,
        talea_denominator=talea_denominator,
    )
    prepared = _prepare_incised_input(incise, extra_counts)
    counts = types.SimpleNamespace(
        prefix_talea=prepared.prefix_talea,
        suffix_talea=prepared.suffix_talea,
        extra_counts=prepared.extra_counts,
    )
    talea_denominator = incise.talea_denominator
    scaled = _scale_rhythm_maker_input(durations, talea_denominator, counts)
    if incise.outer_tuplets_only:
        duration_lists = _make_outer_tuplets_only_incised_duration_lists(
            scaled.pairs,
            scaled.counts.prefix_talea,
            prepared.prefix_counts,
            scaled.counts.suffix_talea,
            prepared.suffix_counts,
            scaled.counts.extra_counts,
            incise,
        )
    else:
        duration_lists = _make_incised_duration_lists(
            scaled.pairs,
            scaled.counts.prefix_talea,
            prepared.prefix_counts,
            scaled.counts.suffix_talea,
            prepared.suffix_counts,
            scaled.counts.extra_counts,
            incise,
        )
    leaf_and_tuplet_lists = []
    for duration_list in duration_lists:
        duration_list = [_ for _ in duration_list if _ != abjad.Duration(0)]
        duration_list = [abjad.Duration(_, scaled.lcd) for _ in duration_list]
        leaf_and_tuplet_list_ = _make_leaf_and_tuplet_list(
            duration_list,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            increase_monotonic=spelling.increase_monotonic,
            tag=tag,
        )
        leaf_and_tuplet_lists.append(leaf_and_tuplet_list_)
    durations = [abjad.Duration(_) for _ in scaled.pairs]
    tuplets = _make_talea_rhythm_maker_tuplets(
        durations, leaf_and_tuplet_lists, tag=tag
    )
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets)
    return tuplets


def multiplied_duration(
    durations,
    prototype: type = abjad.Note,
    *,
    duration: abjad.typings.Duration = (1, 1),
    spelling: _classes.Spelling = _classes.Spelling(),
    tag: abjad.Tag | None = None,
) -> list[abjad.Leaf]:
    r"""
    Makes one leaf with multiplier for each duration in ``durations``.

    ..  container:: example

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = [abjad.Duration(_) for _ in time_signatures]
        >>> components = rmakers.multiplied_duration(durations)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

    ..  container:: example

        Makes multiplied-duration whole notes when ``duration`` is unset:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = [abjad.Duration(_) for _ in time_signatures]
        >>> components = rmakers.multiplied_duration(durations)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

        Makes multiplied-duration half notes when ``duration=(1, 2)``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = [abjad.Duration(_) for _ in time_signatures]
        >>> components = rmakers.multiplied_duration(durations, duration=(1, 2))
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

        Makes multiplied-duration quarter notes when ``duration=(1, 4)``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = [abjad.Duration(_) for _ in time_signatures]
        >>> components = rmakers.multiplied_duration(durations, duration=(1, 4))
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

    ..  container:: example

        Makes multiplied-duration notes when ``prototype`` is unset:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = [abjad.Duration(_) for _ in time_signatures]
        >>> components = rmakers.multiplied_duration(durations)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

    ..  container:: example

        Makes multiplied-duration rests when ``prototype=abjad.Rest``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = [abjad.Duration(_) for _ in time_signatures]
        >>> components = rmakers.multiplied_duration(durations, abjad.Rest)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

    ..  container:: example

        Makes multiplied-duration multimeasures rests when
        ``prototype=abjad.MultimeasureRest``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = [abjad.Duration(_) for _ in time_signatures]
        >>> components = rmakers.multiplied_duration(durations, abjad.MultimeasureRest)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

    ..  container:: example

        Makes multiplied-duration skips when ``prototype=abjad.Skip``:

        >>> time_signatures = rmakers.time_signatures([(1, 4), (3, 16), (5, 8), (1, 3)])
        >>> durations = [abjad.Duration(_) for _ in time_signatures]
        >>> components = rmakers.multiplied_duration(durations, abjad.Skip)
        >>> lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    _assert_are_pairs_durations_or_time_signatures(durations)
    durations = [abjad.Duration(_) for _ in durations]
    duration = abjad.Duration(duration)
    leaf: abjad.Leaf
    leaves = []
    for duration_ in durations:
        pair = duration_.numerator, duration_.denominator
        pair = abjad.duration.divide_pair(pair, duration)
        if prototype is abjad.Note:
            leaf = prototype("c'", duration, multiplier=pair, tag=tag)
        else:
            leaf = prototype(duration, multiplier=pair, tag=tag)
        leaves.append(leaf)
    assert all(isinstance(_, abjad.Leaf) for _ in leaves), repr(leaves)
    return leaves


def note(
    durations,
    *,
    spelling: _classes.Spelling = _classes.Spelling(),
    tag: abjad.Tag | None = None,
) -> list[abjad.Leaf | abjad.Tuplet]:
    r"""
    Makes one note for every duration in ``durations``.

    Silences every other logical tie:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0], 2)
        ...     rmakers.force_rest(logical_ties)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
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
                        r2
                        \time 3/8
                        c'4.
                        \time 4/8
                        r2
                        \time 3/8
                        c'4.
                    }
                }
            }

    ..  container:: example

        Forces rest at every logical tie:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     rmakers.force_rest(logical_ties)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (5, 8)]
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
                        r2
                        \time 3/8
                        r4.
                        \time 4/8
                        r2
                        \time 5/8
                        r2
                        r8
                    }
                }
            }

    ..  container:: example

        Force-rests every other note, except for the first and last:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0], 2)[1:-1]
        ...     rmakers.force_rest(logical_ties)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(4, 8), (3, 8), (4, 8), (3, 8), (2, 8)]
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
                }
            }

    ..  container:: example

        Beams the notes in each duration:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     logical_ties = abjad.select.logical_ties(voice, pitched=True)
        ...     rmakers.beam(logical_ties)
        ...     return lilypond_file

        >>> pairs = [(5, 32), (5, 32)]
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
                        \time 5/32
                        c'8
                        [
                        ~
                        c'32
                        ]
                        c'8
                        [
                        ~
                        c'32
                        ]
                    }
                }
            }

    ..  container:: example

        Beams notes grouped by ``durations``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     logical_ties = abjad.select.logical_ties(voice)
        ...     rmakers.beam_groups(logical_ties)
        ...     return lilypond_file

        >>> pairs = [(5, 32), (5, 32)]
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
                        c'8
                        ~
                        \set stemLeftBeamCount = 3
                        \set stemRightBeamCount = 0
                        c'32
                        ]
                    }
                }
            }

    ..  container:: example

        Makes no beams:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 32), (5, 32)]
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
                        \time 5/32
                        c'8
                        ~
                        c'32
                        c'8
                        ~
                        c'32
                    }
                }
            }

    ..  container:: example

        Does not tie across ``durations``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
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
                        c'2
                        \time 3/8
                        c'4.
                        \time 4/8
                        c'2
                        \time 3/8
                        c'4.
                    }
                }
            }

    ..  container:: example

        Ties across ``durations``:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in logical_ties]
        ...     rmakers.tie(leaves)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

    ..  container:: example

        Ties across every other logical tie:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)[:-1]
        ...     logical_ties = abjad.select.get(logical_ties, [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in logical_ties]
        ...     rmakers.tie(leaves)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
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
                }
            }

    ..  container:: example

        Strips all ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     rmakers.untie(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(7, 16), (1, 4), (5, 16)]
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
                        \time 1/4
                        c'4
                        \time 5/16
                        c'4
                        c'16
                    }
                }
            }

    ..  container:: example

        Spells tuplets as diminutions:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 14), (3, 7)]
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
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 14/8
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 5/14
                            c'2
                            ~
                            c'8
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 7/4
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 3/7
                            c'2.
                        }
                    }
                }
            }

    ..  container:: example

        Spells tuplets as augmentations:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     rmakers.force_augmentation(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 14), (3, 7)]
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
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 7/8
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 5/14
                            c'4
                            ~
                            c'16
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 7/8
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 3/7
                            c'4.
                        }
                    }
                }
            }

    ..  container:: example

        Forces rest in logical tie 0:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_tie = abjad.select.logical_tie(container, 0)
        ...     rmakers.force_rest(logical_tie)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        \time 5/8
                        r2
                        r8
                        \time 2/8
                        c'4
                        c'4
                        \time 5/8
                        c'2
                        ~
                        c'8
                    }
                }
            }

    ..  container:: example

        Forces rests in first two logical ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_tie = abjad.select.logical_ties(container)[:2]
        ...     rmakers.force_rest(logical_tie)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        \time 5/8
                        r2
                        r8
                        \time 2/8
                        r4
                        c'4
                        \time 5/8
                        c'2
                        ~
                        c'8
                    }
                }
            }

    ..  container:: example

        Forces rests in first and last logical ties:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     container = abjad.Container(components)
        ...     logical_ties = abjad.select.logical_ties(container)
        ...     logical_ties = abjad.select.get(logical_ties, [0, -1])
        ...     rmakers.force_rest(logical_ties)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (2, 8), (2, 8), (5, 8)]
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
                        \time 5/8
                        r2
                        r8
                        \time 2/8
                        c'4
                        c'4
                        \time 5/8
                        r2
                        r8
                    }
                }
            }

    ..  container:: example

        Rewrites meter:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     nested_music = rmakers.note(durations)
        ...     components = abjad.sequence.flatten(nested_music)
        ...     voice = rmakers.wrap_in_time_signature_staff(components, time_signatures)
        ...     rmakers.rewrite_meter(voice)
        ...     components = abjad.mutate.eject_contents(voice)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(3, 4), (6, 16), (9, 16)]
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
                        c'2.
                        \time 6/16
                        c'4.
                        \time 9/16
                        c'4.
                        ~
                        c'8.
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    _assert_are_pairs_durations_or_time_signatures(durations)
    durations = [abjad.Duration(_) for _ in durations]
    lists = []
    for duration in durations:
        list_ = abjad.makers.make_leaves(
            pitches=0,
            durations=[duration],
            increase_monotonic=spelling.increase_monotonic,
            forbidden_note_duration=spelling.forbidden_note_duration,
            forbidden_rest_duration=spelling.forbidden_rest_duration,
            tag=tag,
        )
        lists.append(list(list_))
    components = abjad.sequence.flatten(lists)
    assert all(isinstance(_, abjad.Leaf | abjad.Tuplet) for _ in components)
    return components


def talea(
    durations,
    counts: typing.Sequence[int],
    denominator: int,
    *,
    advance: int = 0,
    end_counts: typing.Sequence[int] = (),
    extra_counts: typing.Sequence[int] = (),
    preamble: typing.Sequence[int] = (),
    previous_state: dict | None = None,
    read_talea_once_only: bool = False,
    spelling: _classes.Spelling = _classes.Spelling(),
    state: dict | None = None,
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Reads ``counts`` cyclically and makes one tuplet for each duration in ``durations``.

    Repeats talea of 1/16, 2/16, 3/16, 4/16:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(durations, [1, 2, 3, 4], 16)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
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
                }
            }

    ..  container:: example

        Using ``rmakers.talea()`` with the ``extra_counts`` keyword.

        >>> def make_lilypond_file(pairs, extra_counts):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.talea(
        ...         durations,
        ...         [1, 2, 3, 4],
        ...         16,
        ...         extra_counts=extra_counts,
        ...     )
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.swap_trivial(voice)
        ...     return lilypond_file

        ..  container:: example

            **#1.** Set ``extra_counts=[0, 1]`` to add one extra count to every
            other tuplet:

            >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts=[0, 1])
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
                                \time 3/8
                                c'16
                                [
                                c'8
                                c'8.
                                ]
                            }
                            \tuplet 9/8
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
                            {
                                \time 3/8
                                c'16
                                c'4
                                c'16
                            }
                            \tuplet 9/8
                            {
                                \time 4/8
                                c'8
                                [
                                c'8.
                                ]
                                c'4
                            }
                        }
                    }
                }

        ..  container:: example

            **#2.** Set ``extra_counts=[0, 2]`` to add two extra counts to
            every other tuplet:

            >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts=[0, 2])
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
                                \time 3/8
                                c'16
                                [
                                c'8
                                c'8.
                                ]
                            }
                            \tuplet 5/4
                            {
                                \time 4/8
                                c'4
                                c'16
                                [
                                c'8
                                c'8.
                                ]
                            }
                            {
                                \time 3/8
                                c'4
                                c'16
                                [
                                c'16
                                ]
                                ~
                            }
                            \tuplet 5/4
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
                    }
                }

        ..  container:: example

            **#3.** Set ``extra_counts=[0, -1]`` to remove one count from every
            other tuplet:

            >>> pairs = [(3, 8), (4, 8), (3, 8), (4, 8)]
            >>> lilypond_file = make_lilypond_file(pairs, extra_counts=[0, -1])
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
                                \time 3/8
                                c'16
                                [
                                c'8
                                c'8.
                                ]
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 7/8
                            {
                                \time 4/8
                                c'4
                                c'16
                                [
                                c'8
                                ]
                            }
                            {
                                \time 3/8
                                c'8.
                                [
                                c'8.
                                ]
                                ~
                            }
                            \tweak text #tuplet-number::calc-fraction-text
                            \tuplet 7/8
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
                    }
                }

    ..  container:: example

        **Reading talea once only.** Set ``read_talea_once_only=True`` to raise
        an exception if input durations exceed that of a single reading of
        talea. The effect is to ensure that a talea is long enough to cover all
        durations without repeating. Useful when, for example, interpolating
        from short durations to long durations.

    ..  container:: example

        Using ``rmakers.talea()`` with the ``preamble`` keyword.

        ..  container:: example

            Preamble less than total duration:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.talea(
            ...         durations, [8, -4, 8], 32, preamble=[1, 1, 1, 1]
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
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
                    }
                }

        .. container:: example

            Preamble more than total duration; ignores counts:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.talea(
            ...         durations, [8, -4, 8], 32, preamble=[32, 32, 32, 32]
            ...     )
            ...     container = abjad.Container(tuplets)
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
                    }
                }

    ..  container:: example

        Using ``rmakers.talea()`` with the ``end_counts`` keyword.

        ..  container:: example

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.talea(
            ...         durations, [8, -4, 8], 32, end_counts=[1, 1, 1, 1]
            ...     )
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
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
                    }
                }

        ..  container:: example

            REGRESSION. End counts leave 5-durated tie in tact:

            >>> def make_lilypond_file(pairs):
            ...     time_signatures = rmakers.time_signatures(pairs)
            ...     durations = [abjad.Duration(_) for _ in time_signatures]
            ...     tuplets = rmakers.talea(durations, [6], 16, end_counts=[1])
            ...     lilypond_file = rmakers.example(tuplets, time_signatures)
            ...     voice = lilypond_file["Voice"]
            ...     rmakers.beam(voice)
            ...     rmakers.extract_trivial(voice)
            ...     return lilypond_file

            >>> pairs = [(3, 8), (3, 8)]
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
                            c'4.
                            c'4
                            ~
                            c'16
                            [
                            c'16
                            ]
                        }
                    }
                }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    _assert_are_pairs_durations_or_time_signatures(durations)
    durations = [abjad.Duration(_) for _ in durations]
    talea = _classes.Talea(
        counts=counts,
        denominator=denominator,
        end_counts=end_counts,
        preamble=preamble,
    )
    talea = talea.advance(advance)
    previous_state = previous_state or {}
    if state is None:
        state = {}
    tuplets = _make_talea_tuplets(
        durations,
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
        durations_consumed=len(durations),
        logical_ties_produced=logical_ties_produced,
        previous_durations_consumed=previous_state.get("durations_consumed", 0),
        previous_incomplete_last_note=previous_state.get("incomplete_last_note", False),
        previous_logical_ties_produced=previous_state.get("logical_ties_produced", 0),
        state=state,
    )
    tuplets = abjad.mutate.eject_contents(voice)
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    state.clear()
    state.update(new_state)
    return tuplets


def tuplet(
    durations,
    tuplet_ratios: typing.Sequence[tuple[int, ...]],
    *,
    # TODO: is 'denominator' unused?
    # TODO: remove in favor of dedicated denominator control commands:
    denominator: int | abjad.Duration | str | None = None,
    # TODO: is 'spelling' unused?
    spelling: _classes.Spelling = _classes.Spelling(),
    tag: abjad.Tag | None = None,
) -> list[abjad.Tuplet]:
    r"""
    Makes one tuplet for each duration in ``durations``.

    Makes tuplets with ``3:2`` ratios:

    ..  container:: example

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(3, 2)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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
                            \time 1/2
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 5/16
                            c'8.
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, -1), (3, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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
                            \time 1/2
                            c'4
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'4.
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            \time 5/16
                            c'8.
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/5
                        {
                            c'8.
                            [
                            c'16
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Beams each tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 1, 1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (3, 8), (6, 8), (4, 8)]
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
                        \tuplet 6/5
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
                        \tuplet 1/1
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
                        \tuplet 1/1
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
                        \tuplet 1/1
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
                }
            }

    ..  container:: example

        Beams each tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 1, 1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (3, 8), (6, 8), (4, 8)]
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
                        \tuplet 6/5
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
                        \tuplet 1/1
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
                        \tuplet 1/1
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
                        \tuplet 1/1
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
                }
            }

    ..  container:: example

        Beams tuplets together:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 1, 2, 1, 1), (3, 1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     rmakers.beam_groups(tuplets)
        ...     return lilypond_file

        >>> pairs = [(5, 8), (3, 8), (6, 8), (4, 8)]
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
                        \tuplet 9/5
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
                        \tuplet 5/3
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
                        \tuplet 1/1
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
                        \tuplet 5/4
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
                }
            }

    ..  container:: example

        Ties nothing:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, -2, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16)]
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
                            \time 1/2
                            c'4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'16.
                            r8.
                            c'16.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 5/16
                            c'8
                            [
                            c'8.
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Ties across all tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, -2, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16)]
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
                            \time 1/2
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'16.
                            r8.
                            c'16.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 5/16
                            c'8
                            [
                            c'8.
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Ties across every other tuplet:

        >>> def make_lilypond_file(durations):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, -2, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     tuplets = abjad.select.get(tuplets, [0], 2)
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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
                            \time 1/2
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 3/8
                            c'16.
                            r8.
                            c'16.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 5/16
                            c'8
                            [
                            c'8.
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            c'16.
                            r8.
                            c'16.
                        }
                    }
                }
            }

    ..  container:: example

        Makes diminished tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(2, 1)])
        ...     container = abjad.Container(tuplets)
        ...     rmakers.force_diminution(container)
        ...     rmakers.beam(container)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (4, 8)]
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
                            c'4
                            c'8
                        }
                        \tuplet 3/2
                        {
                            c'4
                            c'8
                        }
                        \tuplet 3/2
                        {
                            \time 4/8
                            c'2
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        Makes augmented tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(2, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.force_augmentation(voice)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (2, 8), (4, 8)]
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
                        \tuplet 3/4
                        {
                            \time 2/8
                            c'8
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            c'8
                            [
                            c'16
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 3/4
                        {
                            \time 4/8
                            c'4
                            c'8
                        }
                    }
                }
            }

    ..  container:: example

        Makes diminished tuplets and does not rewrite dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.force_diminution(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (3, 8), (7, 16)]
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
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
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
                            \time 7/16
                            c'8..
                            [
                            c'8..
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Makes diminished tuplets and rewrites dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.force_diminution(voice)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (3, 8), (7, 16)]
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
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'4
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 8/7
                        {
                            \time 7/16
                            c'4
                            c'4
                        }
                    }
                }
            }

    ..  container:: example

        Makes augmented tuplets and does not rewrite dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.force_augmentation(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (3, 8), (7, 16)]
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
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
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
                            \time 7/16
                            c'8..
                            [
                            c'8..
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Makes augmented tuplets and rewrites dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.force_augmentation(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 8), (3, 8), (7, 16)]
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
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            \time 3/8
                            c'8
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/7
                        {
                            \time 7/16
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Leaves trivializable tuplets as-is when ``trivialize`` is false:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(3, -2), (1,), (-2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            r4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Rewrites trivializable tuplets when ``trivialize`` is true. Measures 2 and 4
        contain trivial tuplets with 1:1 ratios. To remove these trivial tuplets, set
        ``extract_trivial`` as shown in the next example:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(3, -2), (1,), (-2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.trivialize(voice)
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            r4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'8.
                            [
                            c'8.
                            ]
                        }
                    }
                }
            }

        REGRESSION: Ignores ``trivialize`` and respects ``rewrite_dots`` when both are
        true. Measures 2 and 4 are first rewritten as trivial but then supplied again
        with nontrivial prolation when removing dots. The result is that measures 2 and 4
        carry nontrivial prolation with no dots:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(3, -2), (1,), (-2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.trivialize(voice)
        ...     rmakers.rewrite_dots(voice)
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            r4
                            c'4.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 2/3
                        {
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Leaves trivial tuplets as-is when ``extract_trivial`` is false:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (2, 8), (3, 8), (2, 8)]
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
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4
                            c'4.
                            ~
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 2/8
                            c'8
                            [
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Extracts trivial tuplets when ``extract_trivial`` is true. Measures 2 and 4 in
        the example below now contain only a flat list of notes:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     tuplets = abjad.select.tuplets(voice)[:-1]
        ...     leaves = [abjad.select.leaf(_, -1) for _ in tuplets]
        ...     rmakers.tie(leaves)
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (2, 8), (3, 8), (2, 8)]
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
                        \tuplet 5/3
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
                        \tuplet 5/3
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
                }
            }

        .. note:: Flattening trivial tuplets makes it possible
            subsequently to rewrite the meter of the untupletted notes.

    ..  container:: example

        REGRESSION: Very long ties are preserved when ``extract_trivial`` is true:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(2, 3), (1, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.extract_trivial(voice)
        ...     notes = abjad.select.notes(voice)[:-1]
        ...     rmakers.tie(notes)
        ...     return lilypond_file

        >>> pairs = [(3, 8), (2, 8), (3, 8), (2, 8)]
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
                        \tuplet 5/3
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
                        \tuplet 5/3
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
                }
            }

    ..  container:: example

        Force-rests every other tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(4, 1)])
        ...     container = abjad.Container(tuplets)
        ...     tuplets = abjad.select.tuplets(container)
        ...     tuplets = abjad.select.get(tuplets, [1], 2)
        ...     rmakers.force_rest(tuplets)
        ...     rmakers.rewrite_rest_filled(container)
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
                        \tuplet 5/4
                        {
                            \time 3/8
                            c'4.
                            c'16.
                        }
                        \time 4/8
                        r2
                        \tuplet 5/4
                        {
                            \time 3/8
                            c'4.
                            c'16.
                        }
                        \time 4/8
                        r2
                    }
                }
            }


    ..  container:: example

        Tuplet numerators and denominators are reduced to numbers that are relatively
        prime when ``denominator`` is set to none. This means that ratios like
        ``6:4`` and ``10:8`` do not arise:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 4)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     return lilypond_file

        >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                            \time 2/16
                            c'32
                            [
                            c'8
                            ]
                        }
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

        The preferred denominator of each tuplet is set in terms of a unit duration
        when ``denominator`` is set to a duration. The setting does not affect the
        first tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 4)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.denominator(voice, (1, 16))
        ...     return lilypond_file

        >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                            \time 2/16
                            c'32
                            [
                            c'8
                            ]
                        }
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

        Sets the preferred denominator of each tuplet in terms 32nd notes. The
        setting affects all tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 4)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.denominator(voice, (1, 32))
        ...     return lilypond_file

        >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                            \time 2/16
                            c'32
                            [
                            c'8
                            ]
                        }
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

        Sets the preferred denominator each tuplet in terms 64th notes. The setting
        affects all tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 4)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.denominator(voice, (1, 64))
        ...     return lilypond_file

        >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \tuplet 10/8
                        {
                            \time 2/16
                            c'32
                            [
                            c'8
                            ]
                        }
                        \tuplet 20/16
                        {
                            \time 4/16
                            c'16
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 20/24
                        {
                            \time 6/16
                            c'16
                            c'4
                        }
                        \tuplet 40/32
                        {
                            \time 8/16
                            c'8
                            c'2
                        }
                    }
                }
            }

    ..  container:: example

        The preferred denominator of each tuplet is set directly when ``denominator``
        is set to a positive integer. This example sets the preferred denominator of
        each tuplet to ``8``. Setting does not affect the third tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 4)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.denominator(voice, 8)
        ...     return lilypond_file

        >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \tuplet 10/8
                        {
                            \time 2/16
                            c'32
                            [
                            c'8
                            ]
                        }
                        \tuplet 10/8
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

        Sets the preferred denominator of each tuplet to ``12``. Setting affects all
        tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 4)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.denominator(voice, 12)
        ...     return lilypond_file

        >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                        \tuplet 15/12
                        {
                            \time 2/16
                            c'32
                            [
                            c'8
                            ]
                        }
                        \tuplet 15/12
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
                        \tuplet 15/12
                        {
                            \time 8/16
                            c'8
                            c'2
                        }
                    }
                }
            }

    ..  container:: example

        Sets the preferred denominator of each tuplet to ``13``. Setting does not
        affect any tuplet:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, 4)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     rmakers.rewrite_dots(voice)
        ...     rmakers.denominator(voice, 13)
        ...     return lilypond_file

        >>> pairs = [(2, 16), (4, 16), (6, 16), (8, 16)]
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
                            \time 2/16
                            c'32
                            [
                            c'8
                            ]
                        }
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

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tag = abjad.Tag("TUPLET_RHYTHM_MAKER")
        ...     tuplets = rmakers.tuplet(durations, [(3, 2)], tag=tag)
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice, tag=tag)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
        >>> lilypond_file = make_lilypond_file(pairs)
        >>> abjad.show(lilypond_file) # doctest: +SKIP

        ..  docs::

            >>> score = lilypond_file["Score"]
            >>> string = abjad.lilypond(score, tags=True)
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
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tuplet 5/4
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        {
                            \time 1/2
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'4.
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'4
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        }
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tweak text #tuplet-number::calc-fraction-text
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tuplet 5/3
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        {
                            \time 3/8
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'4.
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'4
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        }
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tweak text #tuplet-number::calc-fraction-text
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tuplet 1/1
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        {
                            \time 5/16
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'8.
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.beam()
                            [
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'8
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.beam()
                            ]
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        }
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tweak text #tuplet-number::calc-fraction-text
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        \tuplet 1/1
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        {
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'8.
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.beam()
                            [
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.tuplet()
                            c'8
                              %! TUPLET_RHYTHM_MAKER
                              %! rmakers.beam()
                            ]
                          %! TUPLET_RHYTHM_MAKER
                          %! rmakers.tuplet()
                        }
                    }
                }
            }

    ..  container:: example

        Makes tuplets with ``3:2`` ratios:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(3, 2)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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
                            \time 1/2
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 5/3
                        {
                            \time 3/8
                            c'4.
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 5/16
                            c'8.
                            [
                            c'8
                            ]
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            c'8.
                            [
                            c'8
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Makes tuplets with alternating ``1:-1`` and ``3:1`` ratios:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1, -1), (3, 1)])
        ...     lilypond_file = rmakers.example(tuplets, time_signatures)
        ...     voice = lilypond_file["Voice"]
        ...     rmakers.beam(voice)
        ...     return lilypond_file

        >>> pairs = [(1, 2), (3, 8), (5, 16), (5, 16)]
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
                            \time 1/2
                            c'4
                            r4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/3
                        {
                            \time 3/8
                            c'4.
                            c'8
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 6/5
                        {
                            \time 5/16
                            c'8.
                            r8.
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 4/5
                        {
                            c'8.
                            [
                            c'16
                            ]
                        }
                    }
                }
            }

    ..  container:: example

        Makes length-1 tuplets:

        >>> def make_lilypond_file(pairs):
        ...     time_signatures = rmakers.time_signatures(pairs)
        ...     durations = [abjad.Duration(_) for _ in time_signatures]
        ...     tuplets = rmakers.tuplet(durations, [(1,)])
        ...     container = abjad.Container(tuplets)
        ...     components = abjad.mutate.eject_contents(container)
        ...     lilypond_file = rmakers.example(components, time_signatures)
        ...     return lilypond_file

        >>> pairs = [(1, 5), (1, 4), (1, 6), (7, 9)]
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
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 5/4
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 1/5
                            c'4
                        }
                        \tweak text #tuplet-number::calc-fraction-text
                        \tuplet 1/1
                        {
                            \time 1/4
                            c'4
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 3/2
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 1/6
                            c'4
                        }
                        \tweak edge-height #'(0.7 . 0)
                        \tuplet 9/8
                        {
                            #(ly:expect-warning "strange time signature found")
                            \time 7/9
                            c'2..
                        }
                    }
                }
            }

    """
    tag = tag or abjad.Tag()
    tag = tag.append(_function_name(inspect.currentframe()))
    _assert_are_pairs_durations_or_time_signatures(durations)
    durations = [abjad.Duration(_) for _ in durations]
    tuplets = _make_tuplet_rhythm_maker_music(
        durations,
        tuplet_ratios,
        tag=tag,
    )
    assert all(isinstance(_, abjad.Tuplet) for _ in tuplets), repr(tuplets)
    return tuplets
