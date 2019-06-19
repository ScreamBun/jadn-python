"""
Base JADN Schema Reader/Writer
"""
import json
import os
import re

from functools import partial

from io import (
    BufferedIOBase,
    TextIOBase
)
from typing import (
    Callable,
    Tuple,
    Union
)

from ... import (
    enums,
    definitions,
    jadn,
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
        if regCls and (regCls is not cls and not override):
            raise TypeError(f"Reader of type {fmt} has an implementation")
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

    def __init__(self, schema: Union[str, BufferedIOBase, TextIOBase]):
        """
        Schema Converter Init
        :param schema: schema file to load
        """
        if isinstance(schema, (BufferedIOBase, TextIOBase)):
            self.orig_schema = schema.read()
        elif isinstance(schema, str):
            if os.path.isfile(schema):
                with open(schema, 'rb') as f:
                    self.orig_schema = f.read()
            else:
                self.orig_schema = schema
        else:
            raise TypeError(f"Unknown schema format - {type(schema)}")

    def load(self, *args, **kwargs):
        raise NotImplemented(f"{self.__class__.__name__} does not implement `load` as a class function")

    def loads(self, *args, **kwargs):
        raise NotImplemented(f"{self.__class__.__name__} does not implement `loads` as a class function")


class WriterBase(object):
    """
    Base JADN Converter
    """
    format = None

    escape_chars: Tuple[str] = ('-', ' ')

    # Non Override
    _indent: str = ' ' * 2

    _meta_order: Tuple[str] = definitions.META_ORDER

    _space_start = re.compile(r"^\s+", re.MULTILINE)

    _table_field_headers: utils.FrozenDict = utils.FrozenDict({
        '#': 'opts',
        'Description': 'desc',
        'ID': 'id',
        'Name': ('name', 'value'),
        'Type': 'type',
        'Value': 'value'
    })

    def __init__(self, schema: Union[dict, str], comm: str = enums.CommentLevels.ALL):
        """
        Schema Converter Init
        :param schema: str or dict of the JADN schema
        :param comm: Comment level
        """
        if isinstance(schema, str):
            if os.path.isfile(schema):
                with open(schema, 'rb') as f:
                    schema = json.load(f)
            else:
                schema = json.loads(schema)
        elif isinstance(schema, dict):
            pass
        else:
            raise TypeError('JADN improperly formatted')

        schema = utils.toFrozen(jadn.jadn_idx2key(schema, True))
        self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        self._meta = schema.get('meta', {})
        self._types = []
        self._custom = []
        self._customFields = {}

        for type_def in schema.get('types', []):
            self._customFields[type_def.name] = type_def.type
            self._types.append(type_def)

    def dump(self, *args, **kwargs):
        raise NotImplemented(f"{self.__class__.__name__} does not implement `dump` as a class function")

    def dumps(self, *args, **kwargs):
        raise NotImplemented(f"{self.__class__.__name__} does not implement `dumps` as a class function")

    # Helper Functions
    def _makeStructures(self, default=None):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype list
        """
        structs = []
        for t in self._types:
            df = getattr(self, f"_format{t.type if definitions.is_structure(t.type) else 'Custom'}", None)
            structs.append(df(t) if df else default)

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

    def _is_optional(self, opts: dict) -> bool:
        """
        Check if the field is optional
        :param opts: field options
        :return: bool - optional
        """
        return opts.get('minc', 1) == 0

    def _is_array(self, opts: dict) -> bool:
        """
        Check if the field is an array
        :param opts: field options
        :return: bool - optional
        """
        if 'ktype' in opts or 'vtype' in opts:
            return False

        return opts.get('maxc', 1) != 1