"""
Basic JADN functions
load, dump, format, validate
"""
import json
import numbers
import os
import warnings

from datetime import datetime
from io import BufferedIOBase, TextIOBase
from typing import (
    List,
    Tuple,
    Union
)

from . import (
    definitions,
    schema as jadn_schema
)


def check_schema(schema: Union[dict, str]) -> dict:
    """
    Validate JADN structure against JSON schema,
    Validate JADN structure against JADN schema, then
    Perform additional checks on type definitions
    :param schema: schema to check
    :return: validated schema
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        schema_obj = jadn_schema.Schema()

    if isinstance(schema, dict):
        schema_obj.loads(schema)
    else:
        try:
            schema_obj.loads(schema)
        except ValueError:
            schema_obj.load(schema)

    errors = schema_obj.verify_schema(silent=True)
    if errors:
        for err in errors:
            print(f"{err.__class__.__name__}: {err}")
        raise ValueError("Schema error")

    return schema_obj.schema


def jadn_strip(schema: dict) -> dict:
    """
    Strip comments from schema
    :param schema: schema to strip comments
    :return: comment stripped JADN schema
    """
    schema = jadn_idx2key(schema)

    for type_def in schema.get("types", []):
        type_def["desc"] = ""
        for field in type_def.get("fields", []):
            field["desc"] = ""
    return jadn_key2idx(schema)


def loads(jadn_str: str) -> dict:
    """
    load a JADN schema from a string
    :param jadn_str: JADN schema to load
    :return: loaded schema
    """
    try:
        return check_schema(json.loads(jadn_str))
    except Exception:
        raise ValueError("Schema improperly formatted")


def load(fname: Union[str, BufferedIOBase, TextIOBase]) -> dict:
    """
    Load a JADN schema from a file
    :param fname: JADN schema file to load
    :return: loaded schema
    """
    if isinstance(fname, (BufferedIOBase, TextIOBase)):
        return check_schema(json.load(fname))

    if isinstance(fname, str):
        if os.path.isfile(fname):
            with open(fname, "rb") as f:
                return check_schema(json.load(f))
        else:
            raise FileNotFoundError(f"Schema file not found - '{fname}'")

    raise TypeError("fname is not a valid type")


def dumps(schema: Union[complex, dict, float, int, str, tuple], indent: int = 2, strip: bool = False, _level: int = 0) -> str:
    """
    Properly format a JADN schema
    :param schema: Schema to format
    :param indent: spaces to indent
    :param strip: strip comments from schema
    :param _level: current indent level
    :return: Formatted JADN schema
    """
    schema = jadn_strip(schema) if strip and _level == 0 and isinstance(schema, dict) else schema
    _indent = indent - 1 if indent % 2 == 1 else indent
    _indent += (_level * 2)
    ind, ind_e = " " * _indent, " " * (_indent - 2)

    if isinstance(schema, dict):
        lines = f",\n".join(f"{ind}\"{k}\": {dumps(schema[k], indent, strip, _level+1)}" for k in schema)
        return f"{{\n{lines}\n{ind_e}}}"

    elif isinstance(schema, (list, tuple)):
        nested = schema and isinstance(schema[0], (list, tuple))
        lvl = _level+1 if nested and isinstance(schema[-1], (list, tuple)) else _level
        lines = [dumps(val, indent, strip, lvl) for val in schema]
        if nested:
            return f"[\n{ind}" + f",\n{ind}".join(lines) + f"\n{ind_e}]"
        return f"[{', '.join(lines)}]"

    elif isinstance(schema, (numbers.Number, str)):
        return json.dumps(schema)
    else:
        return "???"


def dump(schema: dict, fname: Union[str, BufferedIOBase, TextIOBase], source: str = "", strip: bool = False) -> None:
    """
    Write the JADN to a file
    :param schema: schema to write
    :param fname: file to write to
    :param source: name of source file
    :param strip: strip comments from schema
    """
    if isinstance(fname, str):
        with open(fname, "w") as f:
            if source:
                f.write(f"\"Generated from {source}, {datetime.ctime(datetime.now())}\"\n\n")
            f.write(f"{dumps(schema, strip=strip)}\n")

    elif isinstance(fname, (BufferedIOBase, TextIOBase)):
        if source:
            fname.write(f"\"Generated from {source}, {datetime.ctime(datetime.now())}\"\n\n")
        fname.write(f"{dumps(schema, strip=strip)}\n")
    else:
        raise TypeError("fname is not a valid type")


# Option Conversion
def topts_s2d(ostr: Union[List[str], Tuple[str]]) -> dict:
    """
    Convert list of type definition option strings to options dictionary
    :param ostr: list type options
    :return: key/value type options
    """
    if isinstance(ostr, (list, tuple)):
        opts = {}
        for o in ostr:
            opt, val = o[0], o[1:]
            opt_val = definitions.TYPE_CONFIG.OPTIONS.get(opt, None)
            if opt_val:
                if opt_val[0] in opts:
                    raise ValueError(f"Repeated value for type option: `{opt}` - `{val}`")
                try:
                    opts[opt_val[0]] = opt_val[1](val)
                    continue
                except ValueError as e:
                    raise ValueError(f"Invalid value for type option: `{opt}` - `{val}`")
            raise ValueError(f"Unknown type option: `{opt}` - `{val}`")
        return opts
    else:
        raise TypeError(f"Type options given are not list/tuple, given {type(ostr)}")


def topts_d2s(opts: dict) -> List[str]:
    """
    Convert options dictionary to list of option strings
    :param opts: key/value type options
    :return: list field options
    """
    if isinstance(opts, dict):
        ostr = []
        for k, v in opts.items():
            val = definitions.TYPE_CONFIG.D2S.get(k, ())
            if val and isinstance(v, val[1]):
                ostr.append(f"{val[0]}{'' if val[1] == bool else v}")
                continue
            raise TypeError(f"Unknown type option '{k}'")
        return ostr
    else:
        raise TypeError(f"Type options given are not a dict, given {type(opts)}")


def fopts_s2d(ftype: str, ostr: List[str]) -> dict:
    """
    Convert list of field definition option strings to options dictionary
    :param ftype: field type to convert options as
    :param ostr: list field options
    :return: key/value field options
    """
    def valid_opts(f):
        opts = dict(definitions.FIELD_CONFIG.OPTIONS)
        sup_opts = definitions.TYPE_CONFIG.SUPPORTED_OPTIONS.get(f, ())
        opts.update({k: v for k, v in definitions.TYPE_CONFIG.OPTIONS.items() if v[0] in sup_opts})
        return opts

    if isinstance(ostr, (list, tuple)):
        valid_opts = valid_opts(ftype)
        opts = {}
        for o in ostr:
            opt, val = o[0], o[1:]
            opt_val = valid_opts.get(opt, None)
            if opt_val:
                if opt_val[0] in opts:
                    raise ValueError(f"Repeated value for field option: `{opt}` - `{val}`")
                try:
                    opts[opt_val[0]] = opt_val[1](val)
                    continue
                except ValueError as e:
                    raise ValueError(f"Invalid value for field option: `{opt}` - `{val}`")
            raise ValueError(f"Unknown field option: `{opt}` - `{val}`")
        return opts
    else:
        raise TypeError(f"Field options given are not list/tuple, given {type(ostr)}")


def fopts_d2s(ftype: str, opts: dict) -> List[str]:
    """
    Convert options dictionary to list of option strings
    :param ftype: field type to convert options as
    :param opts: key/value field options
    :return: list field options
    """
    if isinstance(opts, dict):
        ostr = []
        for k, v in opts.items():
            val = definitions.FIELD_CONFIG.D2S.get(k, ())
            if val and isinstance(v, val[1]):
                ostr.append(f"{val[0]}{'' if val[1] == bool else v}")
                continue
            raise TypeError(f"Unknown field option '{k}'")
        return ostr
    else:
        raise TypeError(f"Field options given are not a dict, given {type(opts)}")


# Schema Conversion
def jadn_idx2key(schema: Union[str, dict], opts: bool = False) -> dict:
    if isinstance(schema, str):
        try:
            if os.path.isfile(schema):
                with open(schema, 'rb') as f:
                    schema = json.load(f)
            else:
                schema = json.loads(schema)
        except Exception as e:
            raise ValueError("Schema improperly formatted")

    tmp_schema = dict(
        meta=schema.get("meta", {}),
        types=[]
    )

    for type_def in schema.get('types', []):
        type_def = dict(zip(definitions.COLUMN_KEYS.STRUCTURE, type_def))
        base_type = definitions.basetype(type_def['type'])
        type_def['opts'] = topts_s2d(type_def['opts']) if opts else type_def['opts']

        if "fields" in type_def:
            tmp_fields = []
            for field in type_def['fields']:
                field = dict(zip(definitions.COLUMN_KEYS['ENUMERATED' if base_type == 'Enumerated' else 'GENERAL'], field))
                if 'opts' in field:
                    field['opts'] = fopts_s2d(field['type'], field['opts']) if opts else field['opts']
                tmp_fields.append(field)
            type_def['fields'] = tmp_fields
        tmp_schema['types'].append(type_def)

    return tmp_schema


def jadn_key2idx(schema: Union[str, dict]) -> dict:
    if isinstance(schema, str):
        try:
            if os.path.isfile(schema):
                with open(schema, 'rb') as f:
                    schema = json.load(f)
            else:
                schema = json.loads(schema)
        except Exception as e:
            raise ValueError("Schema improperly formatted")

    tmp_schema = dict(
        meta=schema.get("meta", {}),
        types=[]
    )

    for type_def in schema.get('types', []):
        if 'fields' in type_def:
            tmp_fields = []
            for field in type_def['fields']:
                if 'opts' in field:
                    field['opts'] = fopts_d2s(field['type'], field['opts']) if isinstance(field['opts'], dict) else field['opts']
                tmp_fields.append(list(field.values()))
            type_def['fields'] = tmp_fields

        type_def['opts'] = topts_d2s(type_def['opts']) if isinstance(type_def['opts'], dict) else type_def['opts']
        tmp_schema['types'].append(list(type_def.values()))

    return tmp_schema
