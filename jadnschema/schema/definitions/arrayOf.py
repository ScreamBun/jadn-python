"""
JADN Array Structures
"""
import collections

from typing import (
    List,
    Optional,
    Union
)

from .base import DefinitionBase, _Python_Types
from ...exceptions import SchemaException, ValidationError


class ArrayOf(DefinitionBase):
    """
    An ordered list of fields with the same semantics
    Each field has a position and type vtype
    """
    __slots__ = ["name", "type", "options", "description"]

    def __init__(self, data: Union[dict, list, "ArrayOf"] = None, **kwargs):
        super(ArrayOf, self).__init__(data, **kwargs)

    def validate(self, inst: Union[list, tuple]) -> Optional[List[Exception]]:
        errors = []

        key_count = len(inst)
        min_keys = self.options.get("minv", 0)
        max_keys = self.options.get("maxv", 0)
        max_keys = 100 if max_keys <= 0 else max_keys

        if min_keys > key_count:
            errors.append(ValidationError(f"{self} - minimum field count not met; min of {min_keys}, given {key_count}"))
        elif key_count > max_keys:
            errors.append(ValidationError(f"{self} - maximum field count exceeded; max of {max_keys}, given {key_count}"))

        if "unique" in self.options:
            if (key_count - len(set(inst))) > 0:
                dups = [item for item, count in collections.Counter(inst).items() if count > 1]
                errors.append(ValidationError(f"{self} - fields are not unique, duplicated {','.join(dups)}"))

        vtype = self.options.get("vtype", None)
        if vtype:
            python_type = _Python_Types.get(vtype, None)
            if python_type:
                if not all([isinstance(idx, python_type) for idx in inst]):
                    errors.append(ValidationError(f"{self} values are not valid as {vtype}"))
            else:
                schema_type = self._config._derived.get(vtype) if vtype.startswith("$") else self._config.types.get(vtype)
                for idx in inst:
                    errs = schema_type.validate(idx)
                    errors.extend(errs if isinstance(errs, list) else [errs])
        else:
            errors.append(SchemaException(f"{self} invalid value type given, {vtype}"))

        return errors if isinstance(errors, list) else [errors]
