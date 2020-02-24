"""
JADN Enumerated Structures
"""
from typing import (
    Optional,
    Union
)

from .base import DefinitionBase
from ...exceptions import ValidationError


class Enumerated(DefinitionBase):
    """
    One value selected from a set of named or labeled integers
    """
    def __init__(self, data: Union[dict, list, "Enumerated"] = None, **kwargs):
        super(Enumerated, self).__init__(data, **kwargs)

    def __str__(self):
        return f"{self.name}(Enumerated{'.ID' if 'id' in self.options else ''})"

    def validate(self, inst: Union[int, str]) -> Optional[Exception]:
        """
        Validate the given value is valid under the defined enumeration
        :param inst:
        :return:
        """
        attr = "id" if hasattr(self.options, "id") else "value"
        if inst not in [getattr(f, attr) for f in self.fields]:
            return ValidationError(f"{self} - invalid value, {inst}")
