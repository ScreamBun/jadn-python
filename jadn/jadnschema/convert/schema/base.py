"""
Base JADN Schema Reader/Writer
"""
import re

from functools import partial

from io import (
    BufferedIOBase,
    TextIOBase
)

from typing import (
    Any,
    Callable,
    Tuple,
    Union
)

from . import enums

from ... import (
    definitions,
    schema,
    utils
)

registered = utils.FrozenDict(
    readers=utils.FrozenDict(),
    writers=utils.FrozenDict(),
)


def register(rw: str, fmt: Union[str, Callable] = None, override: bool = False):
    def wrapper(cls: Callable, fmt: str = fmt, override: bool = override):
        global registered
        registered = utils.toThawed(registered)

        regCls = registered[rw].get(fmt, None)
        if not hasattr(cls, "format"):
            raise AttributeError(f"{cls.__name__} requires attribute 'format'")

        if regCls and (regCls is not cls and not override):
            raise TypeError(f"{rw.title()} of type {fmt} has an implementation")

        registered[rw][fmt] = cls
        registered = utils.toFrozen(registered)
        return cls

    return wrapper if isinstance(fmt, str) else wrapper(fmt, fmt=getattr(fmt, "format", None))


register_reader = partial(register, "readers")
register_writer = partial(register, "writers")


class ReaderBase(object):
    """
    Base Schema Loader
    """
    format: str = None

    def __init__(self) -> None:
        """
        Schema Converter Init
        """

    def load(self, fname: Union[BufferedIOBase, TextIOBase], *args, **kwargs) -> schema.Schema:
        raise NotImplemented(f"{self.__class__.__name__} does not implement `load` as a class function")

    def loads(self, schema_str: Union[bytes, bytearray, str], *args, **kwargs) -> schema.Schema:
        raise NotImplemented(f"{self.__class__.__name__} does not implement `loads` as a class function")


class WriterBase(object):
    """
    Base JADN Converter
    """
    format: str = None

    escape_chars: Tuple[str] = (' ', )

    # Non Override
    _indent: str = ' ' * 2

    _meta_order: Tuple[str] = definitions.META_ORDER

    _space_start = re.compile(r"^\s+", re.MULTILINE)

    _table_field_headers: utils.FrozenDict = utils.FrozenDict({
        '#': 'options',
        'Description': 'description',
        'ID': 'id',
        'Name': ('name', 'value'),
        'Type': 'type',
        'Value': 'value'
    })

    def __init__(self, jadn: Union[dict, str], comm: str = enums.CommentLevels.ALL) -> None:
        """
        Schema Converter Init
        :param jadn: str or dict of the JADN schema
        :param comm: Comment level
        """
        jadn_schema = schema.Schema(jadn)
        self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        self._meta = jadn_schema.meta
        self._imports = dict(self._meta.get("imports", []))
        self._types = jadn_schema.types.values()
        self._customFields = {k: v.type for k, v in jadn_schema.types.items()}

    def dump(self, *args, **kwargs):
        raise NotImplemented(f"{self.__class__.__name__} does not implement `dump` as a class function")

    def dumps(self, *args, **kwargs) -> None:
        raise NotImplemented(f"{self.__class__.__name__} does not implement `dumps` as a class function")

    # Helper Functions
    def _makeStructures(self, default: Any = None, *args, **kwargs) -> list:
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype list
        """
        structs = []
        for t in self._types:
            df = getattr(self, f"_format{t.type if definitions.is_structure(t.type) else 'Custom'}", None)
            structs.append(df(t, *args, **kwargs) if df else default)

        return structs

    def formatStr(self, s: str) -> str:
        """
        Formats the string for use in schema
        :param s: string to format
        :return: formatted string
        """
        escape_chars = list(filter(None, self.escape_chars))
        if s == '*':
            return 'unknown'
        elif len(escape_chars) > 0:
            return re.compile(rf"[{''.join(escape_chars)}]").sub('_', s)
        else:
            return s

    def _is_optional(self, opts: Union[dict, schema.Options]) -> bool:
        """
        Check if the field is optional
        :param opts: field options
        :return: bool - optional
        """
        return opts.get('minc', 1) == 0

    def _is_array(self, opts: Union[dict, schema.Options]) -> bool:
        """
        Check if the field is an array
        :param opts: field options
        :return: bool - optional
        """
        if hasattr(opts, 'ktype') or hasattr(opts, 'vtype'):
            return False

        return opts.get('maxc', 1) != 1