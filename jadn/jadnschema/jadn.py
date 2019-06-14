"""
Basic JADN functions
load, dump, format, validate
"""
import json
import jsonschema
import os
import re

from io import BufferedIOBase, TextIOBase
from typing import (
    List,
    Tuple,
    Union
)

from . import (
    definitions,
    exceptions,
)

from .exceptions import (
    DuplicateError,
    FormatError,
    OptionError,
)

_jadn_format = {
    "type": "object",
    "required": [
        "meta",
        "types"
    ],
    "additionalProperties": False,
    "properties": {
        "meta": {
            "type": "object",
            "required": [
                "module"
            ],
            "additionalProperties": False,
            "properties": {
                "module": {
                    "type": "string"
                },
                "patch": {
                    "type": "string"
                },
                "title": {
                    "type": "string"
                },
                "description": {
                    "type": "string"
                },
                "imports": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": [
                            {
                                "type": "string"
                            },
                            {
                                "type": "string"
                            }
                        ]
                    }
                },
                "exports": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },
        "types": {
            "type": "array",
            "items": {
                "type": "array",
                "minItems": 4,
                "maxItems": 5,
                "items": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "string"
                    },
                    {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    {
                        "type": "string"
                    },
                    {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 5,
                            "items": [
                                {
                                    "type": "integer"
                                },
                                {
                                    "type": "string"
                                },
                                {
                                    "type": "string"
                                },
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                {
                                    "type": "string"
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}


def check_schema(schema: Union[dict, str]) -> dict:
    """
    Validate JADN structure against JSON schema,
    Validate JADN structure against JADN schema, then
    Perform additional checks on type definitions
    :param schema: schema to check
    :return: validated schema
    """
    if isinstance(schema, str):
        try:
            schema = loads(schema)
        except ValueError:
            schema = load(schema)

    val = jsonschema.Draft7Validator(_jadn_format).validate(schema)
    if val:
        raise exceptions.FormatError("Schema Invalid")

    valid_fmts = set(list(definitions.FORMATS.SEMANTIC.keys()) + list(definitions.FORMATS.SERIALIZE.keys()))
    valid_fmts_reg = set(filter(lambda f: re.match(r"^\^.*\$$", f), valid_fmts))
    valid_fmts = valid_fmts - valid_fmts_reg

    for type_def in jadn_idx2key(schema, True).get("types", []):
        base_type = definitions.basetype(type_def["type"])

        # Check if JADN Type
        if not definitions.is_builtin(base_type):
            raise TypeError(f"{type_def['name']} has invalid base type {base_type}")

        # Check if options are Valid
        type_opts = type_def.get("opts", {})
        valid_opts = definitions.TYPE_CONFIG.SUPPORTED_OPTIONS.get(base_type, ())
        diff_opts = set(type_opts.keys()).difference(set(valid_opts))
        if diff_opts:
            raise OptionError(f"{type_def['name']} type {type_def['type']} invalid type option {', '.join(diff_opts)}")

        if base_type in ("ArrayOf", "MapOf"):
            if base_type == "MapOf":
                if "ktype" in type_opts:
                    pass
                else:
                    raise OptionError(f"{type_def['name']} - Missing key type")

            if "vtype" in type_opts:
                pass
            else:
                raise OptionError(f"{type_def['name']} - Missing value type")

        # Check Type Format
        fmt = type_opts.get("format", None)
        if fmt:
            if fmt not in valid_fmts or any([re.match(f, fmt) for f in valid_fmts_reg]):
                raise ValueError(f"Unsupported value constraint \"{fmt}\" on {base_type}: {type_def.name}")

        # Verify properly defined Type
        if definitions.is_compound(base_type) and "fields" in type_def:
            # Verify Fields
            ordinal = base_type in ("Array", "Record")
            tags = set()
            names = set()

            for k, field in enumerate(type_def['fields']):
                name = field["value" if base_type == "Enumerated" else "name"]

                if ordinal and field["id"] != k + 1:
                    raise KeyError(f"Item tag: {type_def['name']} ({base_type}): {field['name']} -- {field['id']} should be {k + 1}")

                if base_type != "Enumerated":  # and definitions.is_builtin(field['type']):
                    valid_opts = list(definitions.TYPE_CONFIG.SUPPORTED_OPTIONS.get(field["type"], ())) + list(o[0] for o in definitions.FIELD_CONFIG.OPTIONS.values())
                    field_opts = field["opts"]

                    opts_diff = set(field_opts.keys()).difference({*valid_opts})
                    if opts_diff:
                        raise OptionError(f"{type_def['name']}: {field['name']} {field['type']} invalid field option(s) {', '.join(opts_diff)}")

                    if 'minc' in field_opts and 'maxc' in field_opts:
                        if field_opts['minc'] < 0 or (field_opts['maxc'] != 0 and field_opts['maxc'] < field_opts['minc']):
                            raise OptionError(f"{type_def['name']}: {field['name']} bad cardinality {field_opts['minc']} {field_opts['maxc']}")

                tags.add(field["id"])
                names.add(name)

            if len(type_def["fields"]) != len(tags):
                raise DuplicateError(f"Tag collision in {type_def['name']} - {len(type_def['fields'])} items, {len(tags)} unique tags")

            if len(type_def["fields"]) != len(names) and base_type not in ("Array", "ArrayOf", "MapOf"):
                raise DuplicateError(f"Name collision in {type_def['name']} - {len(type_def['fields'])} items, {len(names)} unique names")

        elif not definitions.is_compound(base_type) and "fields" in type_def:
            # Invalid Type
            raise FormatError(f"{type_def['name']} - cannot have fields")

    return schema


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
        type_def = dict(zip(definitions.COLUMN_KEYS.Structure, type_def))
        base_type = definitions.basetype(type_def['type'])
        type_def['opts'] = topts_s2d(type_def['opts']) if opts else type_def['opts']

        if "fields" in type_def:
            tmp_fields = []
            for field in type_def['fields']:
                field = dict(zip(definitions.COLUMN_KEYS['Enum_Def' if base_type == 'Enumerated' else 'Gen_Def'], field))
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
