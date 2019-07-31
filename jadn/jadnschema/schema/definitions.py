"""
JADN Base Structures
"""
import re

from typing import (
    List,
    Optional,
    Set,
    Union
)

from .base import BaseModel
from .exceptions import (
    DuplicateError,
    FormatError,
)
from .fields import (
    EnumeratedField,
    Field
)
from .options import Options


class Definition(BaseModel):
    name: str
    type: str
    options: Options
    description: str
    fields: Optional[List[Union[Field, EnumeratedField]]]

    __slots__ = ("name", "type", "options", "description", "fields")

    def __init__(self, data: Union[dict, list, "Definition"] = None, **kwargs):
        super(Definition, self).__init__(data, **kwargs)
        has_fields = hasattr(self, "fields")

        if getattr(self, "name", None) in (t for jt in self._jadn_types.values() for t in jt):
            raise FormatError(f"{self.name}({self.type}) cannot be the name of a JADN type")

        if self.is_compound() and not has_fields:
            raise FormatError(f"{self.name}({self.type}) must have defined fields")

        elif not self.is_compound() and has_fields:
            raise FormatError(f"{self.name}({self.type}) improperly formatted")

        if has_fields:
            field = EnumeratedField if self.basetype == "Enumerated" else Field
            if not all(isinstance(f, field) for f in self.fields):
                raise FormatError(f"{self.name}({self.type}) has improperly formatted field(s)")

    def __str__(self):
        defType = f"({self.type})" if self.__class__.__name__ == "Definition" else ""
        return f"{self.__class__.__name__} {self.name}{defType}"

    @property
    def basetype(self) -> str:
        """
        Return base type of derived subtypes
        :return: basetype
        """
        return self.type.rsplit(".")[0]  # Strip off subtype (e.g., .ID)

    @property
    def dependencies(self) -> Set[str]:
        """
        Determine the dependencies of the definition
        :return: SET - dependencies names
        """
        deps = set()

        def optionDeps(typ_def):
            kv = typ_def.options.get("ktype"), typ_def.options.get("vtype")
            return {d for d in kv if d and not self.is_builtin(d)}

        if self.basetype in ("ArrayOf", "MapOf"):
            deps.update(optionDeps(self))

        if self.is_compound() and self.basetype != "Enumerated":
            for field in self.fields:
                if field.type in ("ArrayOf", "MapOf"):
                    deps.update(optionDeps(field))
                elif not self.is_builtin(field.type):
                    if field.type != self.name:
                        deps.add(field.type)

        return deps

    @property
    def fieldtypes(self) -> Set[str]:
        """
        Determine the types of the field for the definition
        :return: SET - field types
        """
        if self.is_compound() and self.type != "Enumerated":
            return {f.type for f in self.fields if not self.is_builtin(f.type)}
        return set()

    def check_name(self, val: str) -> str:
        """
        Validate the name of the definition
        :param val: name to validate
        :return: original name or raise error
        """
        if not re.match(r"^[A-Z][-$A-Za-z0-9]{0,31}$", val):
            raise ValueError("Name invalid - {val}")
        return val

    def schema(self) -> list:
        """
        Format this definition into valid JADN format
        :return: JADN formatted definition
        """
        values = [self.name, self.type, self.options.schema(self.type, self.name), self.description]
        if self.is_compound():
            values.append([f.schema() for f in self.fields])
        return values

    def schema_strip(self) -> list:
        """
        Format this definition into valid JADN format, without comments
        :return: JADN formatted definition
        """
        values = [self.name, self.type, self.options.schema(self.type, self.name), ""]
        if self.is_compound():
            values.append([f.schema_strip() for f in self.fields])
        return values

    def verify(self, schema_types: tuple, silent=False) -> Optional[List[Exception]]:
        """
        Verify the definition is proper
        :param schema_types: types within the schema
        :param silent: bool - raise or return errors
        :return: OPTIONAL(list of errors)
        """
        errors = [
            *(self.options.verify(self.basetype, defname=self.name, silent=silent) or [])
        ]

        if hasattr(self, "fields"):
            if self.basetype in ("Array", "Choice", "Enumerated", "Map", "Record"):
                if self.basetype != "Enumerated":
                    ordinal = self.basetype in ("Array", "Record")
                    tags = set()
                    names = set()

                    for i, field in enumerate(self.fields):
                        tags.add(field.id)
                        names.add(field.name)

                        if ordinal and field.id != (i + 1):
                            errors.append(FormatError(f"Item ID - {self.name}({self.basetype}).{field.name} -- {field.id} should be {i + 1}"))

                        if field.type not in schema_types:
                            errors.append(TypeError(f"Type of {self.name}.{field.name} not defined: {field.type}"))

                        errors.extend(field.options.verify(field.type, defname=f"{self.name}.{field.name}", field=True, silent=silent) or [])

                    if len(self.fields) != len(tags):
                        errors.append(DuplicateError(f"Tag count mismatch in {self.name} - {len(self.fields)} items, {len(tags)} unique tags"))

                    if len(self.fields) != len(names) and self.basetype != "Array":
                        errors.append(DuplicateError(f"Name/Value count mismatch in {self.name} - {len(self.fields)} items, {len(names)} unique names"))

            else:
                errors.append(FormatError(f"Type of {self.name}({self.type}) should have defined fields"))

        errors = list(filter(None, errors))
        if len(errors) > 0:
            if silent:
                return errors
            else:
                raise errors[0]

    # Helper functions
    def is_builtin(self, vtype: str = None) -> bool:
        """
        Determine if the type is a JADN builtin type
        :param vtype: Type
        :return: is builtin type
        """
        vtype = vtype if vtype else self.basetype
        return self.is_primitive(vtype) or self.is_structure(vtype)

    def is_primitive(self, vtype: str = None) -> bool:
        """
        Determine if the given type is a JADN builtin primitive
        :param vtype: Type
        :return: is builtin primitive
        """
        vtype = vtype if vtype else self.basetype
        return vtype in self._jadn_types["Simple"]

    def is_structure(self, vtype: str = None) -> bool:
        """
        Determine if the type is a JADN builtin structure
        :param vtype: Type
        :return: is builtin structure
        """
        vtype = vtype if vtype else self.basetype
        return vtype in self._jadn_types["Compound"] + self._jadn_types["Selector"]

    def is_compound(self, vtype: str = None) -> bool:
        """
        Determine if the type is a JADN builtin compound (has defined fields)
        :param vtype: Type
        :return: is builtin compound
        """
        vtype = vtype if vtype else self.basetype
        return vtype in ("Array", "Choice", "Enumerated", "Map", "Record")


class Array(Definition):
    """
    An ordered list of labeled fields with positionally-defined semantics
    Each field has a position, label, and type
    """
    def __init__(self, data: Union[dict, list, "Array"] = None, **kwargs):
        super(Array, self).__init__(data, **kwargs)


class ArrayOf(Definition):
    """
    An ordered list of fields with the same semantics
    Each field has a position and type vtype
    """
    __slots__ = ["name", "type", "options", "description"]

    def __init__(self, data: Union[dict, list, "ArrayOf"] = None, **kwargs):
        super(ArrayOf, self).__init__(data, **kwargs)


class Choice(Definition):
    """
    One key and value selected from a set of named or labeled fields
    The key has an id and name or label, and is mapped to a type
    """
    def __init__(self, data: Union[dict, list, "Choice"] = None, **kwargs):
        super(Choice, self).__init__(data, **kwargs)


class Enumerated(Definition):
    """
    One value selected from a set of named or labeled integers
    """
    def __init__(self, data: Union[dict, list, "Enumerated"] = None, **kwargs):
        super(Enumerated, self).__init__(data, **kwargs)


class Map(Definition):
    """
    An unordered map from a set of specified keys to values with semantics bound to each key
    Each key has an id and name or label, and is mapped to a type
    """
    def __init__(self, data: Union[dict, list, "Map"] = None, **kwargs):
        super(Map, self).__init__(data, **kwargs)


class MapOf(Definition):
    """
    An unordered map from a set of keys of the same type to values with the same semantics
    Each key has key type ktype, and is mapped to value type vtype
    """
    __slots__ = ["name", "type", "options", "description"]

    def __init__(self, data: Union[dict, list, "MapOf"] = None, **kwargs):
        super(MapOf, self).__init__(data, **kwargs)


class Record(Definition):
    """
    An ordered map from a list of keys with positions to values with positionally-defined semantics
    Each key has a position and name, and is mapped to a type
    Represents a row in a spreadsheet or database table
    """
    def __init__(self, data: Union[dict, list, "Record"] = None, **kwargs):
        super(Record, self).__init__(data, **kwargs)


# Helper Functions
DefinitionData = Union[Definition, Array, ArrayOf, Choice, Enumerated, Map, MapOf, Record]


def make_definition(data: Union[dict, list, DefinitionData]) -> DefinitionData:
    """
    Create a specific definition based on the given data
    :param data: data to create a definition
    :return: created definition
    """
    data = dict(zip(Definition.__slots__, data)) if isinstance(data, list) else data

    return {
        "Array": Array,
        "ArrayOf": ArrayOf,
        "Choice": Choice,
        "Enumerated": Enumerated,
        "Map": Map,
        "MapOf": MapOf,
        "Record": Record
    }.get(data['type'], Definition)(data)
