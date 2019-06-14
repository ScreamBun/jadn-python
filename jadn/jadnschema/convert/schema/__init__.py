# from .cddl import cddl_dump, cddl_dumps, cddl_load, cddl_loads
# from .html import html_dump, html_dumps
# from .jas import jas_dump, jas_dumps, jas_load, jas_loads
# from .json import json_dump, json_dumps, json_load, json_loads
from .markdown import md_dump, md_dumps
# from .proto import proto_dump, proto_dumps, proto_load, proto_loads
# from .relax import relax_dump, relax_dumps, relax_load, relax_loads
# from .thrift import thrift_dump, thrift_dumps, thrift_load, thrift_loads

from ... import enums


def dump(schema, fname, source="", comm=enums.CommentLevels.ALL, fmt=enums.SchemaFormats.JADN):
    dump_fun = globals().get(f"{fmt}_dump")
    if dump_fun:
        return dump_fun(schema, fname, source, comm)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


def dumps(schema, comm=enums.CommentLevels.ALL, fmt=enums.SchemaFormats.JADN):
    dumps_fun = globals().get(f"{fmt}_dumps")
    if dumps_fun:
        return dumps_fun(schema, comm)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


def load(schema, fname, source="", fmt=enums.SchemaFormats.JADN):
    load_fun = globals().get(f"{fmt}_load")
    if load_fun:
        return load_fun(schema, fname, source)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


def loads(schema, fname, source="", fmt=enums.SchemaFormats.JADN):
    loads_fun = globals().get(f"{fmt}_load")
    if loads_fun:
        return loads_fun(schema, fname, source)

    raise ReferenceError(f"The format specified is not a known format - {fmt}")


__all__ = [
    # Convert to ...
    # 'cddl_dump',
    # 'cddl_dumps',
    # 'html_dump',
    # 'html_dumps',
    # 'jas_dump',
    # 'jas_dumps',
    # 'json_dump',
    # 'json_dumps',
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
    'loads'
]
