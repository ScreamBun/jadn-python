"""
JADN Base Definition Structures
"""
import re

from typing import (
    Any,
    List,
    Optional,
    Set,
    Union
)

from ..base import BaseModel
from ...exceptions import (
    DuplicateError,
    FormatError
)
from jadnschema.schema.fields import (
    EnumeratedField,
    Field
)
from jadnschema.schema.options import Options

_Python_Types = {
    "Binary": bytes,
    "Boolean": bool,
    "Integer": int,
    "Number": float,
    "String": str
}


class DefinitionBase(BaseModel):
    name: str
    type: str
    options: Options
    description: str
    fields: Optional[List[Union[Field, EnumeratedField]]]

    __slots__ = ("name", "type", "options", "description", "fields")

    # TODO: check for optional namespace - NSID:TYPE
    def __init__(self, data: Union[dict, list, "DefinitionBase"] = None, **kwargs):
        super(DefinitionBase, self).__init__(data, **kwargs)
        self.options = getattr(self, "options", Options())
        has_fields = hasattr(self, "fields")

        if getattr(self, "name", None) in (t for jt in self._jadn_types.values() for t in jt):
            raise FormatError(f"{self.name}({self.type}) cannot be the name of a JADN type")

        if self.is_compound() and not has_fields:
            raise FormatError(f"{self.name}({self.type}) must have defined fields")

        if not self.is_compound() and has_fields:
            raise FormatError(f"{self.name}({self.type}) improperly formatted")

        if has_fields:
            field = EnumeratedField if self.basetype == "Enumerated" else Field
            if not all(isinstance(f, field) for f in self.fields):
                raise FormatError(f"{self.name}({self.type}) has improperly formatted field(s)")

    def __str__(self):
        defType = self.type if self.__class__.__name__ == "Definition" else self.__class__.__name__
        return f"{self.name}({defType})"

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
        # TODO: Read TypeName regex from schema.meta.config
        TypeName = self._config.meta.config.TypeName
        if not re.match(TypeName, val):
            raise ValueError(f"Name invalid - {val}")
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
        errors = list(self.options.verify(self.basetype, defname=self.name, silent=silent) or [])

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
            raise errors[0]

    def validate(self, inst: Any) -> Optional[List[Exception]]:
        raise NotImplementedError(f"{self} does not implement \"validate\"")

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

    def get_field(self, name: str) -> Field:
        field = [f for f in self.fields if f.name == name]
        return field[0] if len(field) == 1 else None

    # Extended Helper functions
    def process_options(self) -> None:
        if hasattr(self.options, "ktype") and self.options.ktype.startswith("$"):
            ktype = self.options.ktype
            if ktype not in self._config._derived:
                type_def = self._config.types.get(ktype[1:], None)
                self._config._derived[ktype] = type_def.enumerated()

        if hasattr(self.options, "vtype") and self.options.vtype.startswith("$"):
            vtype = self.options.vtype
            if vtype not in self._config._derived:
                type_def = self._config.types.get(vtype[1:], None)
                self._config._derived[vtype] = type_def.enumerated()

    def enumerated(self) -> "DefinitionBase":
        if self.type in ("Binary", "Boolean", "Integer", "Number", "Null", "String"):
            raise TypeError(f"{self} cannot be extended as an enumerated type")

        if self.type == "Enumerated":
            return self

        from .enumerated import Enumerated  # pylint: disable=import-outside-toplevel
        return Enumerated(dict(
            name=f"Enum-{self.name}",
            type="Enumerated",
            description=f"Derived Enumerated from {self.name}",
            fields=[f.enum_field() for f in self.fields]
        ), _config=self._config)
