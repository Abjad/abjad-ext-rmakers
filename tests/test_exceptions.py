import abjad
import pytest

import rmakers


def test_exceptions_01():
    """
    Code below raises an exception because talea would need to be read
    multiple times to handle all durations.
    """

    def make_lilypond_file(pairs):
        time_signatures = rmakers.time_signatures(pairs)
        durations = [abjad.Duration(_) for _ in time_signatures]
        rmakers.talea(durations, [1, 2, 3, 4], 16, read_talea_once_only=True)

    pairs = [(3, 8), (3, 8), (3, 8), (3, 8)]
    with pytest.raises(Exception) as e:
        make_lilypond_file(pairs)
    assert "is too short to read" in str(e)
