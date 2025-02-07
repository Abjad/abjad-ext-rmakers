import abjad
import abjadext
import pytest


@pytest.fixture(autouse=True)
def add_libraries(doctest_namespace):
    print(abjad, abjad.__version__)
    doctest_namespace["abjad"] = abjad
    doctest_namespace["abjadext"] = abjadext
    doctest_namespace["rmakers"] = abjadext.rmakers
