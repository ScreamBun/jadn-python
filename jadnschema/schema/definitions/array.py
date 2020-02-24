"""
JADN Array Structures
"""
from typing import (
    List,
    Optional,
    Union
)

from .base import DefinitionBase
from ...exceptions import ValidationError


class Array(DefinitionBase):
    """
    An ordered list of labeled fields with positionally-defined semantics
    Each field has a position, label, and type
    """
    def __init__(self, data: Union[dict, list, "Array"] = None, **kwargs):
        super(Array, self).__init__(data, **kwargs)

    def validate(self, inst: Union[list, tuple]) -> Optional[List[Exception]]:
        errors = []
        if "format" in self.options:
            fun = self._config._formats.get(self.options.get("format", ""), None)
            if fun:
                errors.append(fun(inst))
        else:
            print(f"Array: {inst}")
            key_count = len(inst)
            min_keys = self.options.get("minv", 0)
            max_keys = self.options.get("maxv", 0)
            max_keys = 100 if max_keys <= 0 else max_keys

            if min_keys > key_count:
                errors.append(ValidationError(f"{self} - minimum field count not met; min of {min_keys}, given {key_count}"))
            elif key_count > max_keys:
                errors.append(ValidationError(f"{self} - maximum field count exceeded; max of {max_keys}, given {key_count}"))

        # TODO: finish validation
        return errors if isinstance(errors, list) else [errors]
