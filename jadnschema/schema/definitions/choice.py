"""
JADN Choice Structures
"""
from typing import (
    List,
    Optional,
    Union
)

from .base import DefinitionBase
from ...exceptions import ValidationError


class Choice(DefinitionBase):
    """
    One key and value selected from a set of named or labeled fields
    The key has an id and name or label, and is mapped to a type
    """
    def __init__(self, data: Union[dict, list, "Choice"] = None, **kwargs):
        super(Choice, self).__init__(data, **kwargs)

    def validate(self, inst: dict) -> Optional[List[Exception]]:
        """
        Validate the given value is valid under the defined choice
        :param inst:
        :return:
        """
        key = list(inst.keys())
        key = key[0] if len(key) == 1 else None
        attr = "id" if hasattr(self.options, "id") else "name"

        if key and key in [getattr(f, attr) for f in self.fields]:
            type_def = self._config.types.get(self.get_field(key).type)
            rtn = type_def.validate(inst[key]) if type_def else ValidationError(f"{self} - invalid value for choice of {key}")
            return rtn if isinstance(rtn, list) else [rtn]

        return [ValidationError(f"{self} - invalid value for choice of {key}")]
