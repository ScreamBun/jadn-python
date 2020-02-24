"""
JADN Base Structures
"""
from typing import (
    List,
    Union
)

from .base import DefinitionBase
from ...exceptions import ValidationError


class MapOf(DefinitionBase):
    """
    An unordered map from a set of keys of the same type to values with the same semantics
    Each key has key type ktype, and is mapped to value type vtype
    """
    __slots__ = ["name", "type", "options", "description"]

    def __init__(self, data: Union[dict, list, "MapOf"] = None, **kwargs):
        super(MapOf, self).__init__(data, **kwargs)

    def validate(self, inst: dict) -> List[Exception]:
        errors = []
        key_count = len(inst.keys())
        min_keys = self.options.get("minv", 0)
        max_keys = self.options.get("maxv", 0)
        max_keys = 100 if max_keys <= 0 else max_keys

        ktype = self.options.ktype
        key_cls = getattr(self._config, f"{'_' if ktype.startswith('$') else ''}types").get(ktype, None)

        vtype = self.options.vtype
        value_cls = getattr(self._config, f"{'_' if vtype.startswith('$') else ''}types").get(vtype, None)

        if min_keys > key_count:
            errors.append(ValidationError(f"{self} - minimum field count not met; min of {min_keys}, given {key_count}"))
        elif key_count > max_keys:
            errors.append(ValidationError(f"{self} - maximum field count exceeded; max of {max_keys}, given {key_count}"))

        for key, val in inst.items():
            errors.append(key_cls.validate(key))
            errs = value_cls.validate(val)
            getattr(errors, "extend" if isinstance(errs, list) else "append")(errs)

        return errors if isinstance(errors, list) else [errors]
