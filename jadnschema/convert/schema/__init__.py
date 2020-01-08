import importlib

from functools import partial

from typing import Union

from .base import (
    register_reader,
    register_writer
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
# CDDL
# register_writer(fmt=writers.JADNtoCDDL)
# cddl_dump = partial(dump, fmt="cddl")
# cddl_dumps = partial(dumps, fmt="cddl")
# cddl_load = partial(load, fmt="cddl")
# cddl_loads = partial(loads, fmt="cddl")

# HTML
register_writer(fmt=writers.JADNtoHTML)
html_dump = partial(dump, fmt="html")
html_dumps = partial(dumps, fmt="html")

# JADN
register_writer(fmt=writers.JADNtoJADN)
jadn_dump = partial(dump, fmt="jadn")
jadn_dumps = partial(dumps, fmt="jadn")
# jadn_load = partial(load, fmt="jadn")
# jadn_loads = partial(loads, fmt="jadn")

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

# ProtoBuf
# register_writer(fmt=writers.JADNtoProto)
# proto_dump = partial(dump, fmt="proto")
# proto_dumps = partial(dumps, fmt="proto")
# proto_load = partial(load, fmt="proto")
# proto_loads = partial(loads, fmt="proto")

# Relax-NG
# register_writer(fmt=writers.JADNtoRelax)
# relax_dump = partial(dump, fmt="relax")
# relax_dumps = partial(dumps, fmt="relax")
# relax_load = partial(load, fmt="relax")
# relax_loads = partial(loads, fmt="relax")

# Thrift
# register_writer(fmt=writers.JADNtoThrift)
# thrift_dump = partial(dump, fmt="thrift")
# thrift_dumps = partial(dumps, fmt="thrift")
# thrift_load = partial(load, fmt="thrift")
# thrift_loads = partial(loads, fmt="thrift")

__all__ = [
    # Convert to ...
    # 'cddl_dump',
    # 'cddl_dumps',
    'html_dump',
    'html_dumps',
    'jadn_dump',
    'jadn_dumps',
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
    # Load From ...
    # 'cddl_load',
    # 'cddl_loads',
    # 'jadn_load',
    # 'jadn_loads',
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
    # Helpers
    'register_reader',
    'register_writer'
]
