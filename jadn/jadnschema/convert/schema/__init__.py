import importlib

from functools import partial

from typing import Union

from .base import (
    register_reader,
    register_writer,
    ReaderBase,
    WriterBase
)

from . import (
    enums,
    readers,
    writers
)


# Base Functions
def dump(schema: Union[str, dict], fname: str, source: str = "", comm: str = enums.CommentLevels.ALL, fmt: str = enums.SchemaFormats.JADN, *args, **kwargs):
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
        return cls(schema).dump(fname, source, comm, *args, **kwargs)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


def dumps(schema: Union[str, dict], comm: str = enums.CommentLevels.ALL, fmt: str = enums.SchemaFormats.JADN, *args, **kwargs):
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
        return cls(schema).dumps(comm, *args, **kwargs)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


def load(schema: Union[str, dict], source: str = "", fmt: str = enums.SchemaFormats.JADN, *args, **kwargs):
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
        return cls().load(schema, source, *args, **kwargs)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


def loads(schema: Union[str, dict], fmt: str = enums.SchemaFormats.JADN, *args, **kwargs):
    """
    Produce JADN schema from input schema
    :param schema: schema file to convert
    :param fmt: format of the input schema
    :return: loaded JADN schema
    """
    readers = importlib.import_module(".base", __package__).registered.readers
    cls = readers.get(fmt, None)
    if cls:
        return cls().loads(schema, *args, **kwargs)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


# Add format reader/writers
# HTML
register_writer(fmt=writers.JADNtoHTML)
html_dump = partial(dump, fmt="html")
html_dumps = partial(dumps, fmt="html")

# JADN IDL
register_writer(fmt=writers.JADNtoIDL)
# register_reader(fmt=readers.IDLtoJADN)
jidl_dump = partial(dump, fmt="jidl")
jidl_dumps = partial(dumps, fmt="jidl")
# jidl_load = partial(load, fmt="jidl")
# jidl_loads = partial(loads, fmt="jidl")

# JSON
register_writer(fmt=writers.JADNtoJSON)
# register_reader(fmt=readers.JSONtoJADN)
json_dump = partial(dump, fmt="json")
json_dumps = partial(dumps, fmt="json")
# json_load = partial(load, fmt="json")
# json_loads = partial(loads, fmt="json")

# Markdown
register_writer(fmt=writers.JADNtoMD)
md_dump = partial(dump, fmt="md")
md_dumps = partial(dumps, fmt="md")

__all__ = [
    # Base
    'ReaderBase',
    'WriterBase',
    # Convert to ...
    # 'cddl_dump',
    # 'cddl_dumps',
    'html_dump',
    'html_dumps',
    # 'jas_dump',
    # 'jas_dumps',
    'jidl_dump',
    'jidl_dumps',
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
    # 'jidl_load',
    # 'jidl_loads',
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
    # *dynamic_funs,
    # Helpers
    'register_reader',
    'register_writer'
]
