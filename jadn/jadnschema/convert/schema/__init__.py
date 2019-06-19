import importlib
import sys

from functools import partial

from typing import (
    Union
)

from .base import register_reader, register_writer, ReaderBase, WriterBase

from . import (
    # cddl,
    # html,
    # jas,
    json_schema,
    markdown,
    # protobuf,
    # relax_ng,
    # thrift,
)

from ... import (
    enums
)


# Base Functions
def dump(schema: Union[str, dict], fname: str, source: str = "", comm: str = enums.CommentLevels.ALL, fmt: str = enums.SchemaFormats.JADN):
    """
    Produce formatted schema from JADN schema
    :param schema: JADN Schema to convert
    :param fname: file to output
    :param source: name of original schema file
    :param comm: Level of comments to include in converted schema
    :param fmt: format of the desired output schema
    :return: None
    """
    writers = importlib.import_module(".base", __package__).registered.writers
    cls = writers.get(fmt, None)
    if cls:
        comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
        return cls(schema).dump(fname, source, comm)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


def dumps(schema: Union[str, dict], comm: str = enums.CommentLevels.ALL, fmt: str = enums.SchemaFormats.JADN):
    """
    Produce formatted schema from JADN schema
    :param schema: JADN Schema to convert
    :param comm: Level of comments to include in converted schema
    :param fmt: format of the desired output schema
    :return: formatted schema
    """
    writers = importlib.import_module(".base", __package__).registered.writers
    cls = writers.get(fmt, None)
    if cls:
        comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
        return cls(schema).dumps(comm)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


def load(schema: Union[str, dict], source: str = "", fmt: str = enums.SchemaFormats.JADN):
    """
    Produce JADN schema from input schema
    :param schema: Schema to convert
    :param source: name of original schema file
    :param fmt: format of the input schema
    :return: loaded JADN schema
    """
    readers = importlib.import_module(".base", __package__).registered.readers
    cls = readers.get(fmt, None)
    if cls:
        return cls(schema).load(source)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


def loads(schema: Union[str, dict], fmt: str = enums.SchemaFormats.JADN):
    """
    Produce JADN schema from input schema
    :param schema: schema file to convert
    :param fmt: format of the input schema
    :return: loaded JADN schema
    """
    readers = importlib.import_module(".base", __package__).registered.readers
    cls = readers.get(fmt, None)
    if cls:
        return cls(schema).loads()

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


# Register Readers
# register_reader(fmt=json_schema.JSONtoJADN)

# Register Writers
register_writer(fmt=json_schema.JADNtoJSON)
register_writer(fmt=markdown.JADNtoMD)


# JSON
json_dump = partial(dump, fmt="json")
json_dumps = partial(dumps, fmt="json")
# json_load = partial(load, fmt="json")
# json_loadss = partial(loads, fmt="json")

# Markdown
md_dump = partial(dump, fmt="md")
md_dumps = partial(dumps, fmt="md")


# Dynamically add Reader/Writer
registered = importlib.import_module(".base", __package__).registered
dynamic_funs = []

# Reference this modules vars
self = dir(sys.modules[__name__])

for suffix, fmts in registered.items():
    suffix = "load" if suffix == "readers" else "dump"
    for fmt in fmts.keys():
        if f"{fmt}_{suffix}" not in self:
            setattr(self, f"{fmt}_{suffix}", partial(getattr(self, f"{suffix}"), fmt=fmt))
            dynamic_funs.append(f"{fmt}_{suffix}")

        if f"{fmt}_{suffix}s" not in self:
            setattr(self, f"{fmt}_{suffix}s", partial(getattr(self, f"{suffix}s"), fmt=fmt))
            dynamic_funs.append(f"{fmt}_{suffix}s")

__all__ = [
    # Base
    'ReaderBase',
    'WriterBase',
    # Convert to ...
    # 'cddl_dump',
    # 'cddl_dumps',
    # 'html_dump',
    # 'html_dumps',
    # 'jas_dump',
    # 'jas_dumps',
    'json_dump',
    'json_dumps',
    'md_dump',
    'md_dumps',
    # 'proto_dump',
    # 'proto_dumps',
    # 'relax_dump',
    # 'relax_dumps',
    # 'thrift_dump',
    # 'thrift_dumps',
    # Convert From ...
    # 'cddl_load',
    # 'cddl_loads',
    # 'jas_load',
    # 'jas_loads',
    # 'json_load',
    # 'json_loads',
    # 'proto_load',
    # 'proto_loads',
    # 'relax_load',
    # 'relax_load',
    # 'thrift_load',
    # 'thrift_loads',
    # Dynamic
    'dump',
    'dumps',
    'load',
    'loads',
    *dynamic_funs,
    # Helpers
    'register_reader',
    'register_writer'
]
