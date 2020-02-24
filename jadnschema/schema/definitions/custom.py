"""
JADN Custom Structures
"""
import re

from functools import partial
from typing import (
    Any,
    List,
    Optional,
    Union
)

from .base import DefinitionBase, _Python_Types
from ...exceptions import ValidationError


class CustomDefinition(DefinitionBase):
    """
    Custom definition of a simple JADN type
    """
    def __init__(self, data: Union[dict, list, "CustomDefinition"] = None, **kwargs):
        super(CustomDefinition, self).__init__(data, **kwargs)

    def __str__(self):
        return f"{self.name}({self.type})"

    def validate(self, inst: Any) -> Optional[List[Exception]]:
        if self.type == "None" and inst is not None:
            return [ValidationError(f"{self} is not valid as {self.type}")]

        errors = []
        if self.type == "Binary":
            inst = bytes(inst, "utf-8") if isinstance(inst, str) else inst

        python_type = _Python_Types.get(self.type, None)
        if python_type and not isinstance(inst, python_type):
            errors.append(ValidationError(f"{self} is not valid as {self.type}"))

        fmt = self.options.get("format", None)
        if fmt:
            if re.match(r"^u\d+$", fmt):
                fun = partial(self._config._formats["unsigned"], int(fmt[1:]))
            else:
                fun = self._config._formats.get(fmt, None)

            err = fun(inst) if fun else None
            if err:
                errors.append(type(err)(f"{self} - {getattr(err, 'message', str(err))}"))

        if self.type in ("Binary", "String"):
            inst_len = len(inst)
            min_len = self.options.get("minv", 0)
            max_len = self.options.get("maxv", 255)
            if min_len > inst_len:
                errors.append(ValueError(f"{self} is invalid, minimum length of {min_len:,} bytes/characters not met"))
            elif max_len < inst_len:
                errors.append(ValueError(f"{self} is invalid, maximum length of {min_len:,} bytes/characters exceeded"))

        elif self.type in ("Integer", "Number"):
            min_val = self.options.get("minv", 0)
            max_val = self.options.get("maxv", 0)

            if min_val > inst:
                errors.append(ValueError(f"{self} is invalid, minimum of {min_val:,} not met"))
            elif max_val != 0 and max_val < inst:
                errors.append(ValueError(f"{self} is invalid, maximum of {max_val:,} exceeded"))

        # TODO: option validate - minv & maxv
        return errors if isinstance(errors, list) else [errors]
