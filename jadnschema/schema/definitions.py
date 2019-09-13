"""
JADN Base Structures
"""
import collections
import re
import sys

from functools import partial
from typing import (
    Any,
    List,
    Optional,
    Set,
    Union
)
from .base import BaseModel
from .exceptions import (
    DuplicateError,
    FormatError,
    SchemaException,
    ValidationError
)
from .fields import (
    EnumeratedField,
    Field
)
from .options import Options

_Python_Types = {
    "Binary": bytes,
    "Boolean": bool,
    "Integer": int,
    "Number": float,
    "String": str
}


class Definition(BaseModel):
    name: str
    type: str
    options: Options
    description: str
    fields: Optional[List[Union[Field, EnumeratedField]]]

    __slots__ = ("name", "type", "options", "description", "fields")

    # TODO: check for optional namespace - NSID:TYPE
    def __init__(self, data: Union[dict, list, "Definition"] = None, **kwargs):
        super(Definition, self).__init__(data, **kwargs)
        self.options = getattr(self, "options", Options())
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

    def enumerated(self) -> "Definition":
        if self.type in ("Binary", "Boolean", "Integer", "Number", "Null", "String"):
            raise TypeError(f"{self} cannot be extended as an enumerated type")

        if self.type == "Enumerated":
            return self

        return Enumerated(dict(
            name=f"Enum-{self.name}",
            type="Enumerated",
            description=f"Derived Enumerated from {self.name}",
            fields=[f.enum_field() for f in self.fields]
        ), _config=self._config)


class Array(Definition):
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


class ArrayOf(Definition):
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


class Choice(Definition):
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


class Enumerated(Definition):
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


class Map(Definition):
    """
    An unordered map from a set of specified keys to values with semantics bound to each key
    Each key has an id and name or label, and is mapped to a type
    """
    def __init__(self, data: Union[dict, list, "Map"] = None, **kwargs):
        super(Map, self).__init__(data, **kwargs)

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
                errors.extend(field_def.validate(value, False) or [])

        return errors if isinstance(errors, list) else [errors]


class MapOf(Definition):
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


class Record(Definition):
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


class CustomDefinition(Definition):
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


# Helper Functions
DefinitionData = Union[Definition, Array, ArrayOf, Choice, Enumerated, Map, MapOf, Record]


def make_definition(data: Union[dict, list, DefinitionData], **kwargs) -> DefinitionData:
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
    }.get(data['type'], CustomDefinition)(data, **kwargs)
