"""
Base JADN Schema Reader/Writer
"""
import os
import re

from functools import partial
from io import (
    BufferedIOBase,
    TextIOBase
)
from typing import (
    Any,
    Callable,
    Dict,
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
        global registered  # pylint: disable=global-statement
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


class ReaderBase:
    """
    Base Schema Loader
    """
    format: str = None

    def load(self, fname: Union[str, BufferedIOBase, TextIOBase]) -> jadn_schema.Schema:
        """
        Load the schema file as a JADN schema
        :param fname: file to load schema from
        :return: JADN Schema
        """
        schema = ""
        if isinstance(fname, (BufferedIOBase, TextIOBase)):
            schema = fname.read()

        if isinstance(fname, str):
            if os.path.isfile(fname):
                with open(fname, "rb") as f:
                    schema = f.read()
            else:
                raise FileNotFoundError(f"Schema file not found - '{fname}'")

        return self.parse(schema)

    def loads(self, schema: Union[bytes, bytearray, str]) -> jadn_schema.Schema:
        """
        Loads the schema string to a JADN schema
        :param schema: schema string to load
        :return: JADN schema
        """
        return self.parse(schema)

    def parse(self, schema: Union[bytes, str]) -> jadn_schema.Schema:
        raise NotImplementedError(f"{self.__class__.__name__} does not implement `parse` as a class function")


class WriterBase:
    """
    Base JADN Converter
    """
    format: str = None
    escape_chars: Tuple[str] = (" ", )

    # Non Override
    _definition_order: Tuple[str] = ("OpenC2-Command", "OpenC2-Response", "Action", "Target", "Actuator", "Args",
                                     "Status-Code", "Results", "Artifact", "Device", "Domain-Name", "Email-Addr",
                                     "Features", "File", "IDN-Domain-Name", "IDN-Email-Addr", "IPv4-Net",
                                     "IPv4-Connection", "IPv6-Net", "IPv6-Connection", "IRI", "MAC-Addr", "Process",
                                     "Properties", "URI", "Action-Targets", "Targets", "Date-Time", "Duration",
                                     "Feature", "Hashes", "Hostname", "IDN-Hostname", "IPv4-Addr", "IPv6-Addr",
                                     "L4-Protocol", "Message-Type", "Nsid", "Payload", "Port", "Response-Type",
                                     "Versions", "Version", "Profiles", "Rate-Limit", "Binary", "Command-ID")
    _indent: str = " " * 2
    _meta_order: Tuple[str] = ("title", "module", "patch", "description", "exports", "imports", "config")
    _title_overrides: Dict[str, str] = {
        "Addr": "Address",
        "IDN": "Internationalized",
        "L4": "Layer 4",
        "Nsid": "Namespace Identifier"
    }
    _space_start = re.compile(r"^\s+", re.MULTILINE)
    _table_field_headers: utils.FrozenDict = utils.FrozenDict({
        "#": "options",
        "Description": "description",
        "ID": "id",
        "Name": ("name", "value"),
        "Type": "type",
        "Value": "value"
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

    def dump(self, fname: str, source: str = None, comm: str = enums.CommentLevels.ALL, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__} does not implement `dump` as a class function")

    def dumps(self, comm: str = enums.CommentLevels.ALL, **kwargs) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} does not implement `dumps` as a class function")

    # Helper Functions
    def _makeStructures(self, default: Any = None, **kwargs) -> Dict[str, Union[dict, str]]:
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype list
        """
        structs = {}
        for t in self._types:
            df = getattr(self, f"_format{t.type if t.is_structure() else 'Custom'}", None)
            structs[t.name] = df(t, **kwargs) if df else default

        return structs

    def formatTitle(self, title: str) -> str:
        words = [self._title_overrides.get(w, w) for w in title.split("-")]
        return " ".join(words)

    def formatStr(self, s: str) -> str:
        """
        Formats the string for use in schema
        :param s: string to format
        :return: formatted string
        """
        escape_chars = list(filter(None, self.escape_chars))
        if s == "*":
            return "unknown"
        if len(escape_chars) > 0:
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

        return opts.get("maxc", 1) != 1
