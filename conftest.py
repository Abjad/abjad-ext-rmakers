import abjad
import pytest
import rmakers


@pytest.fixture(autouse=True)
def inject_abjad_into_doctest_namespace(doctest_namespace):
    """
    Inject Abjad and rmakers into doctest namespace.
    """
    doctest_namespace["abjad"] = abjad
    doctest_namespace["rmakers"] = rmakers
