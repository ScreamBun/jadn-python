"""
Basic functions
"""
from typing import List, Tuple, Union

from .codec.codec import Codec
from . import (
    jadn
)


def validate_schema(schema: Union[bytearray, dict, str]) -> Union[dict, List[Exception]]:
    """
    Validate a JADN Schema
    :param schema: JADN schema to validate
    :return: list of errors or valid schema
    """
    if isinstance(schema, (bytearray, str)):
        schema = jadn.jadn_loads(schema)
    jadn_analysis = jadn.jadn_analyze(schema)

    errs = []

    if len(jadn_analysis['undefined']) > 0:
        errs.append(ReferenceError(f"schema contains undefined types: {', '.join(jadn_analysis['undefined'])}"))

    if len(jadn_analysis['unreferenced']) > 0:
        errs.append(ReferenceError(f"schema contains unreferenced types: {', '.join(jadn_analysis['unreferenced'])}"))

    return schema if len(errs) == 0 else errs


def validate_instance(schema: dict, instance: dict, _type: str = None) -> Union[Tuple[dict, str], List[Exception]]:
    schema_validate = validate_schema(schema)
    rtn = []

    if isinstance(schema_validate, list):
        rtn.extend(schema_validate)
    else:
        schema_codec = Codec(schema, True, True)
        if _type:
            try:
                return schema_codec.decode(_type, instance)
            except TypeError as e:
                rtn.extend(e)
        else:
            meta = schema.get('meta', {})
            for exp in meta.get('exports', []):
                try:
                    return schema_codec.decode(exp, instance), exp
                except (TypeError, ValueError) as e:
                    rtn.append(TypeError(f'instance not valid as {exp}'))

    return rtn
