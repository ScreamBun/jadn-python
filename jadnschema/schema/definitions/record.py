"""
JADN Base Structures
"""
from typing import (
    List,
    Union
)

from .base import DefinitionBase
from ...exceptions import ValidationError


class Record(DefinitionBase):
    """
    An ordered map from a list of keys with positions to values with positionally-defined semantics
    Each key has a position and name, and is mapped to a type
    Represents a row in a spreadsheet or database table
    """
    def __init__(self, data: Union[dict, list, "Record"] = None, **kwargs):
        super(Record, self).__init__(data, **kwargs)

    def validate(self, inst: dict) -> List[Exception]:
        errors = []
        key_count = len(inst.keys())
        min_keys = self.options.get("minv", 0)
        max_keys = self.options.get("maxv", 0)
        max_keys = 100 if max_keys <= 0 else max_keys
        extra_fields = {*inst.keys()} - {f.name for f in self.fields}

        if extra_fields:
            errors.append(ValidationError(f"{self} - unknown field(s): {', '.join(extra_fields)}"))
        elif min_keys > key_count:
            errors.append(ValidationError(f"{self} - minimum field count not met; min of {min_keys}, given {key_count}"))
        elif key_count > max_keys:
            errors.append(ValidationError(f"{self} - maximum field count exceeded; max of {max_keys}, given {key_count}"))
        else:
            for field, value in inst.items():
                field_def = self.get_field(field)
                errors.extend(field_def.validate(value) or [])

        return errors if isinstance(errors, list) else [errors]
