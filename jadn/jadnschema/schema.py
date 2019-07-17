"""
JADN Schema Models
"""
import json
import os
import numbers
import re
import warnings

from io import BufferedIOBase, TextIOBase
from typeguard import check_type

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union
)

from .exceptions import (
    DuplicateError,
    FormatError,
    OptionError,
)

ModelData = Union[dict, list, "BaseModel"]

JADN_Types = {
    "Primitive": (
        "Binary",       # A sequence of octets. Length is the number of octets
        "Boolean",      # An element with one of two values: true or false
        "Integer",      # A positive or negative whole number
        "Number",       # A real number
        "Null",         # An unspecified or non-existent value
        "String",       # A sequence of characters, each of which has a Unicode codepoint. Length is the number of characters
    ),
    "Structures": (
        "Array",        # An ordered list of labeled fields with positionally-defined semantics. Each field has a position, label, and type
        "ArrayOf",       # An ordered list of fields with the same semantics. Each field has a position and type vtype
        "Choice",       # One key and value selected from a set of named or labeled fields. The key has an id and name or label, and is mapped to a type
        "Enumerated",   # One value selected from a set of named or labeled integers
        "Map",          # An unordered map from a set of specified keys to values with semantics bound to each key. Each key has an id and name or label, and is mapped to a type
        "MapOf",        # An unordered map from a set of keys of the same type to values with the same semantics. Each key has key type ktype, and is mapped to value type vtype
        "Record"        # An ordered map from a list of keys with positions to values with positionally-defined semantics. Each key has a position and name, and is mapped to a type. Represents a row in a spreadsheet or database table
    )
}


class BaseModel(object):
    _iter_idx: int

    def __init__(self, data: ModelData, **kwargs):
        if data:
            values, errs = init_model(self, data)
        else:
            values = {}

        kw_vals = {k: v for k, v in kwargs.items() if k in self.__slots__}
        values.update(kw_vals)
        values, errs = init_model(self, values)

        for k, v in values.items():
            setattr(self, k, v)

    def __setattr__(self, key, val):
        if key in self.__slots__:
            if hasattr(self, f"check_{key}"):
                val = getattr(self, f"check_{key}")(val)
            check_type(key, val, self.__annotations__.get(key))
            super(BaseModel, self).__setattr__(key, val)
        else:
            raise AttributeError(f"{self.__class__.__name__}.{key} is not a valid attribute that can be set by a user")

    def __iter__(self):
        self._iter_idx = 0
        return getattr(self, self.__slots__[self._iter_idx])

    def __next__(self):
        if self._iter_idx < len(self.__slots__):
            self._iter_idx += 1
            return getattr(self, self.__slots__[self._iter_idx])
        else:
            raise StopIteration

    def __contains__(self, key):
        return key in self.__slots__ and hasattr(self, key)

    def primitive(self) -> dict:
        return {attr: getattr(self, attr) for attr in self.__slots__ if hasattr(self, attr)}

    def dict(self) -> dict:
        return {attr: getattr(self, attr) for attr in self.__slots__ if hasattr(self, attr)}

    def get(self, attr: str, default: Any = None):
        return getattr(self, attr, default) if attr in self.__slots__ else default

    def items(self):
        return tuple((k, v) for k, v in self.dict().items())

    # Helper functions


class Meta(BaseModel):
    module: str
    patch: Optional[str]
    title: Optional[str]
    description: Optional[str]
    imports: Optional[List[List[str]]]  # min_size=2, max_size=2
    exports: Optional[List[str]]

    __slots__ = ["module", "patch", "title", "description", "imports", "exports"]

    def __init__(self, data: Union[dict, "Meta"] = None, **kwargs):
        super(Meta, self).__init__(data, **kwargs)

        if hasattr(self, "imports"):
            if any(len(imp) != 2 for imp in self.imports):
                raise ValueError(f"{self.__class__.__name__}.import improperly formatted")


class Options(BaseModel):
    # Type Structural
    id: bool
    vtype: str
    ktype: str
    enum: str
    # Type Validation
    format: str
    pattern: str
    minv: int
    maxv: int
    # Field
    minc: int
    maxc: int
    tfield: str  # Enumerated
    flatten: bool
    default: str

    _fieldOpts: Tuple[str] = ("minc", "maxc", "tfield", "flatten", "default")

    _ids: Dict[str, str] = {
        # Type Structural
        "=": "id",          # If present, Enumerated values and fields of compound types are denoted by FieldID rather than FieldName
        "*": "vtype",       # Value type for ArrayOf and MapOf
        "+": "ktype",       # Key type for MapOf
        "$": "enum",        # Enumerated type derived from the specified Array, Choice, Map or Record type
        # Type Validation
        "/": "format",      # Semantic validation keyword
        "%": "pattern",     # Regular expression used to validate a String type
        "{": "minv",        # Minimum numeric value, octet or character count, or element count
        "}": "maxv",        # Maximum numeric value, octet or character count, or element count
        # Field Structural
        "[": "minc",        # Minimum cardinality
        "]": "maxc",        # Maximum cardinality
        "&": "tfield",      # Field that specifies the type of this field, value is Enumerated
        "<": "flatten",     # Use FieldName as a qualifier for fields in FieldType
        "!": "default",     # Reserved for default value Section 3.2.2.4
    }

    _validFormats: List[str] = [
        # JSON Formats
        'date-time',                # RFC 3339 Section 5.6
        'date',                     # RFC 3339 Section 5.6
        'time',                     # RFC 3339 Section 5.6
        'email',                    # RFC 5322 Section 3.4.1
        'idn-email',                # RFC 6531, or email
        'hostname',                 # RFC 1034 Section 3.1
        'idn-hostname',             # RFC 5890 Section 2.3.2.3, or hostname
        'ipv4',                     # RFC 2673 Section 3.2 "dotted-quad"
        'ipv6',                     # RFC 4291 Section 2.2 "IPv6 address"
        'uri',                      # RFC 3986
        'uri-reference',            # RFC 3986, or uri
        'iri',                      # RFC 3987
        'iri-reference',            # RFC 3987
        'uri-template',             # RFC 6570
        'json-pointer',             # RFC 6901 Section 5
        'relative-json-pointer',    # JSONP
        'regex',                    # ECMA 262
        # JADN Formats
        'eui',                      # IEEE Extended Unique Identifier (MAC Address), EUI-48 or EUI-64 as specified in EUI
        'ipv4-addr',                # IPv4 address as specified in RFC 791 Section 3.1
        'ipv6-addr',                # IPv6 address as specified in RFC 8200 Section 3
        'ipv4-net',                 # Binary IPv4 address and Integer prefix length as specified in RFC 4632 Section 3.1
        'ipv6-net',                 # Binary IPv6 address and Integer prefix length as specified in RFC 4291 Section 2.3
        'i8',                       # Signed 8 bit integer, value must be between -128 and 127
        'i16',                      # Signed 16 bit integer, value must be between -32768 and 32767.
        'i32',                      # Signed 32 bit integer, value must be between ... and ...
        r'^u\d+$',                  # Unsigned integer or bit field of <n> bits, value must be between 0 and 2^<n> - 1
        # Serialization
        'x',                        # Binary - JSON string containing Base16 (hex) encoding of a binary value as defined in RFC 4648 Section 8. Note that the Base16 alphabet does not include lower-case letters.
        'ipv4-addr',                # Binary - JSON string containing a "dotted-quad" as specified in RFC 2673 Section 3.2.
        'ipv6-addr',                # Binary - JSON string containing the text representation of an IPv6 address as specified in RFC 4291 Section 2.2.
        'ipv4-net',                 # Array - JSON string containing the text representation of an IPv4 address range as specified in RFC 4632 Section 3.1.
        'ipv6-net'                  # Array - JSON string containing the text representation of an IPv6 address range as specified in RFC 4291 Section 2.3.'
    ]

    _validOptions: Dict[str, Tuple[str]] = {
        # Primitives
        "Binary": ("format", "minv", "maxv"),
        "Boolean": (),
        "Integer": ("format", "minv", "maxv"),
        "Number": ("format", "minv", "maxv"),
        "Null": (),
        "String": ("format", "minv", "maxv", "pattern"),
        # Structures
        "Array": ("format", "minv", "maxv"),
        "ArrayOf": ("minv", "maxv", "vtype"),
        "Choice": ("id", ),
        "Enumerated": ("id", "enum"),
        "Map": ("id", "minv", "maxv"),
        "MapOf": ("ktype", "minv", "maxv", "vtype"),
        "Record": ("minv", "maxv")
    }

    __slots__ = ["id", "vtype", "ktype", "enum", "format", "pattern", "minv", "maxv", "minc", "maxc", "tfield", "flatten", "default"]

    def __init__(self, data: Union[dict, list, "Options"] = None, **kwargs):
        if isinstance(data, list):
            tmp = {}
            for o in data:
                if not isinstance(o, str):
                    raise OptionError("f{basetype} - option not properly formatted")

                opt = self._ids.get(o[0], None)
                if opt:
                    inst = self.__annotations__.get(opt)
                    val = safe_cast(o[1:], inst)
                    check_type(opt, val, inst)
                    tmp[opt] = True if opt in ("id", "flatten") else val
            data = tmp

        super(Options, self).__init__(data, **kwargs)

    def primitive(self) -> list:
        keys = {v: k for k, v in self._ids.items()}
        return [f"{keys.get(o)}{getattr(self, o)}" for o in self.__slots__ if getattr(self, o, None) is not None]

    def verify(self, basetype: str, defname: str = None, field: bool = False) -> Optional[Exception]:
        valid_opts = (*self._validOptions.get(basetype, ()), *(self._fieldOpts if field else ()))
        opts = {o: getattr(self, o) for o in self.__slots__ if hasattr(self, o)}
        keys = {*opts.keys()} - {*valid_opts}
        loc = defname if defname else basetype

        if len(keys) > 0:
            return ValueError(f"Extra options given for {loc} - {', '.join(keys)}")
        elif basetype == "ArrayOf":
            keys = {"vtype"} - {*opts.keys()}
            if len(keys) != 0:
                return ValueError(f"ArrayOf {loc} requires options: vtype")
        elif basetype == "MapOf":
            keys = {"vtype", "ktype"} - {*opts.keys()}
            if len(keys) != 0:
                return ValueError(f"ArrayOf {loc} requires options: vtype and ktype")

        fmt = opts.get("format")
        if fmt and fmt not in self._validFormats:
            return ValueError(f"{basetype} {loc} specified unknown format {fmt}")


class EnumeratedField(BaseModel):
    id: int  # the integer identifier of the item
    value: Union[int, str]  # the value of the item
    description: str  # a non-normative comment

    __slots__ = ["id", "value", "description"]

    def __init__(self, data: Union[dict, list, "EnumeratedField"] = None, **kwargs):
        super(EnumeratedField, self).__init__(data, **kwargs)

    def primitive(self) -> list:
        return list(super().primitive().values())


class Field(BaseModel):
    id: int  # the integer identifier of the field
    name: str  # the name or label of the field
    type: str  # the type of the field
    options: Options  # an array of zero or more FieldOption (Table 3-5) or TypeOption (Table 3-2) applicable to the field
    description: str  # a non-normative comment

    __slots__ = ["id", "name", "type", "options", "description"]

    def __init__(self, data: Union[dict, list, "Field"] = None, **kwargs):
        super(Field, self).__init__(data, **kwargs)

    def check_name(self, val: str) -> str:
        if not re.match(r"^[a-z][_A-Za-z0-9]{0,31}$", val):
            raise ValueError("Name invalid - {val}")
        return val

    def primitive(self) -> list:
        try:
            return [self.id, self.name, self.type, self.options.primitive(), self.description]
        except AttributeError as e:
            print(e)
            return [0, "error", "string", [], "Error has occured"]


class Definition(BaseModel):
    name: str
    type: str
    options: Options
    description: str
    fields: Optional[List[Union[Field, EnumeratedField]]]

    _field_req: Tuple[str] = ("Array", "Choice", "Enumerated", "Map", "Record")
    __slots__ = ["name", "type", "options", "description", "fields"]

    def __init__(self, data: Union[dict, list, "Definition"] = None, **kwargs):
        super(Definition, self).__init__(data, **kwargs)
        def_count = len([0 for a in self.__slots__ if getattr(self, a, None) is not None])

        if self.type in self._field_req and def_count != 5:
            raise FormatError(f"{self.name}({self.type}) must have defined fields")

        elif self.type not in self._field_req and def_count == 5:
            raise FormatError(f"{self.name}({self.type}) improperly formatted")

    def check_name(self, val: str) -> str:
        if not re.match(r"^[A-Z][-$A-Za-z0-9]{0,31}$", val):
            raise ValueError("Name invalid - {val}")
        return val

    def primitive(self) -> list:
        values = [self.name, self.type, self.options.primitive(), self.description]
        if hasattr(self, "fields"):
            values.append([f.primitive() for f in self.fields])
        return values


class Schema(object):
    __slots__ = ["meta", "types"]
    meta: Meta
    types: Dict[str, Definition]

    _schemaTypes: Set[str] = {*JADN_Types["Primitive"], *JADN_Types["Structures"]}

    def __init__(self, schema: dict = None, **kwargs):
        self.meta = Meta()
        self.types = {}
        if schema:
            self._setSchema(schema)
        else:
            warnings.warn("Schema Not set on init, use load/loads")

    @property
    def schema(self) -> dict:
        return dict(
            meta=self.meta.primitive(),
            types=[t.primitive() for n, t in self.types.items()]
        )

    @property
    def schema_pretty(self):
        return self.dumps()

    @property
    def schema_types(self):
        return tuple(self._schemaTypes)

    def load(self, fname: Union[str, BufferedIOBase, TextIOBase]) -> None:
        """
        Load a JADN schema from a file
        :param fname: JADN schema file to load
        :return: loaded schema
        """
        if isinstance(fname, (BufferedIOBase, TextIOBase)):
            self._setSchema(json.load(fname))
            return

        if isinstance(fname, str):
            if os.path.isfile(fname):
                with open(fname, "rb") as f:
                    self._setSchema(json.load(f))
                    return
            else:
                raise FileNotFoundError(f"Schema file not found - '{fname}'")

        raise TypeError("fname is not a valid type")

    def loads(self, schema: Union[dict, str]) -> None:
        """
        load a JADN schema from a string
        :param schema: JADN schema to load
        """
        if isinstance(schema, dict):
            self._setSchema(schema)
            return

        try:
            self._setSchema(json.loads(schema))
        except Exception:
            raise ValueError("Schema improperly formatted")

    def dump(self, fname: Union[str, BufferedIOBase, TextIOBase], indent: int = 2, strip: bool = False) -> None:
        """
        Write the JADN to a file
        :param fname: file to write to
        :param indent: spaces to indent
        :param strip: strip comments from schema
        """
        if isinstance(fname, (BufferedIOBase, TextIOBase)):
            fname.write(f"{self.dumps(indent=indent, strip=strip)}\n")
        elif isinstance(fname, str):
            with open(fname, "w") as f:
                f.write(f"{self.dumps(indent=indent, strip=strip)}\n")
        else:
            raise TypeError("fname is not a valid type")

    def dumps(self, indent: int = 2, strip: bool = False) -> str:
        """
        Properly format a JADN schema
        :param indent: spaces to indent
        :param strip: strip comments from schema
        :return: Formatted JADN schema
        """
        return self._dumps(self.schema, indent, strip)

    def verify_schema(self, silent=False) -> Optional[List[Exception]]:
        errors = []
        for type_name, type_def in self.types.items():
            if type_def.type not in self._schemaTypes:
                errors.append(TypeError(f"Type of {type_name} not defined: {type_def.type}"))
            errors.append(type_def.options.verify(type_def.type, defname=type_name))

            if type_def.type in ("Array", "Choice", "Map", "Record"):
                for field in getattr(type_def, "fields", []):
                    if field.type not in self._schemaTypes:
                        errors.append(TypeError(f"Type of {type_name}.{field.name} not defined: {field.type}"))
                    errors.append(field.options.verify(field.type, defname=f"{type_name}.{field.name}", field=True))

        errors = list(filter(None, errors))
        if len(errors) > 0:
            if silent:
                return errors
            else:
                raise Exception(errors)

    def validate_message(self, inst: dict, fmt: str) -> Optional[List[Exception]]:
        pass

    # Helper Functions
    def _setSchema(self, data):
        keys = {*data.keys()} - {"meta", "types"}
        if len(keys) != 0:
            raise KeyError(f"Missing required key(s): {', '.join(keys)}")

        self.meta = Meta(data["meta"])
        self.types = {}
        for t in data["types"]:
            t = Definition(t)
            self._schemaTypes.add(t.type)
            self.types[t.name] = t

            if t.type in ("Array", "Choice", "Map", "Record"):
                self._schemaTypes.update({f.type for f in t.fields})

    def _dumps(self, schema: Union[complex, dict, float, int, str, tuple], indent: int = 2, strip: bool = False, _level: int = 0) -> str:
        """
        Properly format a JADN schema
        :param schema: Schema to format
        :param indent: spaces to indent
        :param strip: strip comments from schema
        :param _level: current indent level
        :return: Formatted JADN schema
        """
        schema = schema if strip and _level == 0 and isinstance(schema, dict) else schema
        _indent = indent - 1 if indent % 2 == 1 else indent
        _indent += (_level * 2)
        ind, ind_e = " " * _indent, " " * (_indent - 2)

        if isinstance(schema, dict):
            lines = f",\n".join(f"{ind}\"{k}\": {self._dumps(schema[k], indent, strip, _level+1)}" for k in schema)
            return f"{{\n{lines}\n{ind_e}}}"

        elif isinstance(schema, (list, tuple)):
            nested = schema and isinstance(schema[0], (list, tuple))
            lvl = _level+1 if nested and isinstance(schema[-1], (list, tuple)) else _level
            lines = [self._dumps(val, indent, strip, lvl) for val in schema]
            if nested:
                return f"[\n{ind}" + f",\n{ind}".join(lines) + f"\n{ind_e}]"
            return f"[{', '.join(lines)}]"

        elif isinstance(schema, (numbers.Number, str)):
            return json.dumps(schema)
        else:
            return "???"


def init_model(model: BaseModel, input_data: ModelData, raise_exc: bool = True) -> Tuple[dict, Optional[List[Exception]]]:
    """
    Validate data against a model.
    """
    model_class = model.__class__.__name__
    input_data = dict(zip(model.__slots__, input_data)) if isinstance(input_data, list) else input_data
    basetype = input_data.get("type")
    fields = {}
    errors = []

    if "options" in input_data and isinstance(input_data.get("options"), list):
        try:
            input_data["options"] = Options(input_data["options"])
        except Exception as e:
            if raise_exc:
                raise e
            else:
                errors.append(e)

    if "fields" in input_data and isinstance(input_data["fields"], list):
        field = EnumeratedField if basetype == "Enumerated" else Field
        input_data["fields"] = [field(f) for f in input_data["fields"]]

    for var, val in input_data.items():
        inst = model.__annotations__.get(var)
        try:
            if var not in model.__slots__:
                raise KeyError(f"{model_class} has extra keys")
            check_type(var, val, inst)
        except Exception as e:
            if raise_exc:
                raise e
            else:
                errors.append(e)
        fields[var] = val

    return fields, errors


def safe_cast(val: Any, cast: Type, default: Any = None) -> Any:
    try:
        return cast(val)
    except Exception as e:
        return default
