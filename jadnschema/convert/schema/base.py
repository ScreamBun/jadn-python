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
    schema as jadn_schema,
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

    def load(self, fname: Union[BufferedIOBase, TextIOBase], *args, **kwargs) -> jadn_schema.Schema:
        raise NotImplemented(f"{self.__class__.__name__} does not implement `load` as a class function")

    def loads(self, schema: Union[bytes, bytearray, str], *args, **kwargs) -> jadn_schema.Schema:
        raise NotImplemented(f"{self.__class__.__name__} does not implement `loads` as a class function")


class WriterBase(object):
    """
    Base JADN Converter
    """
    format: str = None

    escape_chars: Tuple[str] = (' ', )

    # Non Override
    _definition_order: Tuple[str] = ("OpenC2-Command", "OpenC2-Response", "Action", "Target", "Actuator", "Args",
                                     "Status-Code", "Results", "Artifact", "Device", "Domain-Name", "Email-Addr",
                                     "Features", "File", "IDN-Domain-Name", "IDN-Email-Addr", "IPv4-Net",
                                     "IPv4-Connection", "IPv6-Net", "IPv6-Connection", "IRI", "MAC-Addr", "Process",
                                     "Properties", "URI", "Action-Targets", "Targets", "Date-Time", "Duration",
                                     "Feature", "Hashes", "Hostname", "IDN-Hostname", "IPv4-Addr", "IPv6-Addr",
                                     "L4-Protocol", "Message-Type", "Nsid", "Payload", "Port", "Response-Type",
                                     "Version", "Binary", "Command-ID")

    _indent: str = ' ' * 2

    _meta_order: Tuple[str] = ('title', 'module', 'patch', 'description', 'exports', 'imports')

    _space_start = re.compile(r"^\s+", re.MULTILINE)

    _table_field_headers: utils.FrozenDict = utils.FrozenDict({
        '#': 'options',
        'Description': 'description',
        'ID': 'id',
        'Name': ('name', 'value'),
        'Type': 'type',
        'Value': 'value'
    })

    def __init__(self, jadn: Union[dict, str, jadn_schema.Schema], comm: str = enums.CommentLevels.ALL) -> None:
        """
        Schema Converter Init
        :param jadn: str/dict/Schema of the JADN schema
        :param comm: Comment level
        """
        self._schema = jadn if isinstance(jadn, jadn_schema.Schema) else jadn_schema.Schema(jadn)
        self._comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        self._meta = self._schema.meta
        self._imports = dict(self._meta.get("imports", []))
        self._types = self._schema.types.values()
        self._customFields = {k: v.type for k, v in self._schema.types.items()}

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
            df = getattr(self, f"_format{t.type if t.is_structure() else 'Custom'}", None)
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
        return s

    def _is_optional(self, opts: Union[dict, jadn_schema.Options]) -> bool:
        """
        Check if the field is optional
        :param opts: field options
        :return: bool - optional
        """
        return opts.get("minc", 1) == 0

    def _is_array(self, opts: Union[dict, jadn_schema.Options]) -> bool:
        """
        Check if the field is an array
        :param opts: field options
        :return: bool - optional
        """
        if "ktype" in opts or "vtype" in opts:
            return False

        return opts.get('maxc', 1) != 1
