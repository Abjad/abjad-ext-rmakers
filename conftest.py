import abjad
import abjadext
import pytest


@pytest.fixture(autouse=True)
def inject_abjad_into_doctest_namespace(doctest_namespace):
    """
    Inject Abjad and rmakers into doctest namespace.
    """
    doctest_namespace["abjad"] = abjad
    doctest_namespace["rmakers"] = abjadext.rmakers
