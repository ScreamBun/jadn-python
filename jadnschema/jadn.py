"""
Basic JADN functions
load, dump, format, validate
"""
from io import BufferedIOBase, TextIOBase
from typing import (
    Dict,
    Set,
    Union
)

from . import schema as jadn_schema


def check_schema(schema: Union[dict, str]) -> jadn_schema.Schema:
    """
    Validate JADN structure against JSON schema,
    Validate JADN structure against JADN schema, then
    Perform additional checks on type definitions
    :param schema: schema to check
    :return: validated schema
    """
    schema_obj = jadn_schema.Schema()

    if isinstance(schema, dict):
        schema_obj.loads(schema)

    elif isinstance(schema, str):
        if schema.endswith(".jadn"):
            schema_obj.load(schema)
        else:
            schema_obj.loads(schema)

    errors = schema_obj.verify_schema(silent=True)
    if errors:
        raise Exception(errors)

    for k, v in schema_obj.analyze().items():
        print(f"{k}: {v}")

    return schema_obj


def strip(schema: dict) -> dict:
    """
    Strip comments from schema
    :param schema: schema to strip comments
    :return: comment stripped JADN schema
    """
    return jadn_schema.Schema(schema).schema(strip=True)


def analyze(schema: dict) -> Dict[str, Set[str]]:
    """
    Analyze the given schema for unreferenced and undefined types
    :param schema: schema to analyse
    :return: analysis results
    """
    return jadn_schema.Schema(schema).analyze()


def loads(jadn_str: str) -> jadn_schema.Schema:
    """
    load a JADN schema from a string
    :param jadn_str: JADN schema to load
    :return: loaded schema
    """
    schema_obj = jadn_schema.Schema()
    schema_obj.loads(jadn_str)
    return schema_obj


def load(fname: Union[str, BufferedIOBase, TextIOBase]) -> jadn_schema.Schema:
    """
    Load a JADN schema from a file
    :param fname: JADN schema file to load
    :return: loaded schema
    """
    schema_obj = jadn_schema.Schema()
    schema_obj.load(fname)
    return schema_obj


def dumps(schema: Union[dict, jadn_schema.Schema], indent: int = 2, comments: bool = False) -> str:
    """
    Properly format a JADN schema
    :param schema: Schema to format
    :param indent: spaces to indent
    :param comments: strip comments from schema
    :return: Formatted JADN schema
    """
    return jadn_schema.Schema(schema).dumps(indent, comments)


def dump(schema: dict, fname: Union[str, BufferedIOBase, TextIOBase], indent: int = 2, comments: bool = False) -> None:
    """
    Write the JADN to a file
    :param schema: schema to write
    :param fname: file to write to
    :param indent: spaces to indent
    :param comments: strip comments from schema
    """
    return jadn_schema.Schema(schema).dump(fname, indent, comments)
