"""
JADN Field Models - Enumerated and General
"""
import re

from typing import (
    Union
)

from .base import BaseModel
from .options import Options


class EnumeratedField(BaseModel):
    id: int  # the integer identifier of the item
    value: Union[int, str]  # the value of the item
    description: str  # a non-normative comment

    __slots__ = ("id", "value", "description")

    def __init__(self, data: Union[dict, list, "EnumeratedField"] = None, **kwargs):
        super(EnumeratedField, self).__init__(data, **kwargs)

    def __str__(self):
        return f"Enumerated Field {self.value}({self.id})"

    def schema(self) -> list:
        """
        Format this enumerated field into valid JADN format
        :return: JADN formatted enumerated field
        """
        try:
            return [self.id, self.value, self.description]
        except AttributeError as e:
            print(e)
            return [0, "error", "Error has occured"]

    def schema_strip(self) -> list:
        """
        Format this enumerated field into valid JADN format, without comments
        :return: JADN formatted enumerated definition
        """
        try:
            return [self.id, self.value, ""]
        except AttributeError as e:
            print(e)
            return [0, "error", ""]


class Field(BaseModel):
    id: int  # the integer identifier of the field
    name: str  # the name or label of the field
    type: str  # the type of the field
    options: Options  # an array of zero or more FieldOption (Table 3-5) or TypeOption (Table 3-2) applicable to the field
    description: str  # a non-normative comment

    __slots__ = ("id", "name", "type", "options", "description")

    def __init__(self, data: Union[dict, list, "Field"] = None, **kwargs):
        super(Field, self).__init__(data, **kwargs)

    def __str__(self):
        return f"Field {self.name}({self.type})"

    @property
    def required(self):
        """
        Check is the field is a required field
        :return: bool - required/optional
        """
        return self.options.get("minc", 0) != 0

    def check_name(self, val: str) -> str:
        """
        Validate the name of the definition
        :param val: name to validate
        :return: original name or raise error
        """
        if not re.match(r"^[a-z][_A-Za-z0-9]{0,31}$", val):
            raise ValueError("Name invalid - {val}")
        return val

    def schema(self) -> list:
        """
        Format this field into valid JADN format
        :return: JADN formatted field
        """
        try:
            return [self.id, self.name, self.type, self.options.schema(self.type, self.name, True), self.description]
        except AttributeError as e:
            print(e)
            return [0, "error", "string", [], "Error has occured"]

    def schema_strip(self) -> list:
        """
        Format this field into valid JADN format, without comments
        :return: JADN formatted field
        """
        try:
            return [self.id, self.name, self.type, self.options.schema(self.type, self.name, True), ""]
        except AttributeError as e:
            print(e)
            return [0, "error", "string", [], ""]

