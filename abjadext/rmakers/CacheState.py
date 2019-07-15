import abjad
import typing


class CacheState(object):
    """
    Cache state directive.
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = "Specifiers"

    _publish_storage_format = True

    ### SPECIAL METHODS ###

    def __format__(self, format_specification="") -> str:
        """
        Formats directive.

        ..  container:: example

            >>> specifier = rmakers.CacheState()
            >>> abjad.f(specifier)
            abjadext.rmakers.CacheState()

        """
        return abjad.StorageFormatManager(self).get_storage_format()

    def __repr__(self) -> str:
        """
        Gets interpreter representation of directive.

        ..  container:: example

            >>> rmakers.CacheState()
            CacheState()

        """
        return abjad.StorageFormatManager(self).get_repr_format()
