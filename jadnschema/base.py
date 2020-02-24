"""
Basic functions
"""
from typing import List, Tuple, Union

from . import jadn, schema as jadn_schema


def validate_schema(schema: Union[dict, str]) -> Union[dict, List[Exception]]:
    """
    Validate a JADN Schema
    :param schema: JADN schema to validate
    :return: list of errors or valid schema
    """
    if isinstance(schema, str):
        schema = jadn.loads(schema)
    jadn_analysis = jadn.analyze(schema)

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
        schema_obj = jadn_schema.Schema(schema)
        if _type:
            err = schema_obj.validate_as(instance, _type)
            if err:
                rtn.extend(err)
        else:
            err = schema_obj.validate(instance)
            if err:
                rtn.append(err)

    return rtn
