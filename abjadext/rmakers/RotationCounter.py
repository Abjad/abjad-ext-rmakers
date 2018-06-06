import abjad
import typing


class RotationCounter(abjad.TypedCounter):
    r"""
    Rotation counter.

    >>> import abjadext

    ..  container:: example

        >>> counter = abjadext.rmakers.RotationCounter(default=3)

        >>> counter['talea__counts']
        3

        >>> counter['talea__counts'] += 1
        >>> counter['talea__counts']
        4

    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Specifiers'

    __slots__ = (
        '_autoincrement',
        '_default',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        *,
        autoincrement: bool = None,
        default: int = None,
        items=None,
        **keywords
        ) -> None:
        abjad.TypedCounter.__init__(
            self,
            items=items,
            **keywords
            )
        if autoincrement is not None:
            autoincrement = bool(autoincrement)
        self._autoincrement = autoincrement
        if default is not None:
            default = int(default or 0)
        self._default = default

    ### SPECIAL METHODS ###

    def __getitem__(self, argument) -> typing.Any:
        """
        Gets item or slice identified by ``argument``.
        """
        argument = self._item_coercer(argument)
        if argument not in self._collection:
            self._collection[argument] = self._default or 0
        return self._collection.__getitem__(argument)

    ### PRIVATE METHODS ###

    def _get_format_specification(self):
        agent = abjad.StorageFormatManager(self)
        names = list(agent.signature_keyword_names)
        names.extend(sorted(self._collection.keys()))
        if 'items' in names:
            names.remove('items')
        if not self.autoincrement:
            names.remove('autoincrement')
        return abjad.FormatSpecification(
            self,
            repr_is_indented=False,
            storage_format_args_values=[],
            storage_format_kwargs_names=names,
            template_names=names,
            )

    ### PUBLIC PROPERTIES ###

    @property
    def autoincrement(self) -> typing.Optional[bool]:
        """
        Is true if rotation counter should be auto-incremented.
        """
        return self._autoincrement

    @property
    def default(self) -> typing.Optional[int]:
        """
        Gets default count.
        """
        return self._default
