"""
JADN Schema Models
"""
import copy
import inflect
import json
import numbers
import os
import re

from io import (
    BufferedIOBase,
    TextIOBase
)
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union
)

from .base import BaseModel
from .definitions import Definition
from .exceptions import (
    FormatError,
    ValidationError
)
from .formats import ValidationFormats
from .options import Options


class Config(BaseModel):
    MaxBinary: Optional[int]    # Default maximum number of octets
    MaxString: Optional[int]    # Default maximum number of characters
    MaxElements: Optional[int]  # Default maximum number of items/properties
    FS: Optional[str]           # Field Separator character used in pathnames
    Sys: Optional[str]          # System character for TypeName
    TypeName: Optional[str]     # TypeName regex
    FieldName: Optional[str]    # FieldName regex
    NSID: Optional[str]         # Namespace Identifier regex

    # Helper Vars
    _defaults: Dict[str, Union[int, str]] = {
        "MaxBinary": 255,
        "MaxString": 255,
        "MaxElements": 100,
        "FS": "/",
        "Sys": "$",
        "TypeName": "^[A-Z][-$A-Za-z0-9]{0,31}$",
        "FieldName": "^[a-z][_A-Za-z0-9]{0,31}$",
        "NSID": "^[A-Za-z][A-Za-z0-9]{0,7}$"
    }
    _overrides: Tuple[str, ...]

    __slots__ = ("MaxBinary", "MaxString", "MaxElements", "FS", "Sys", "TypeName", "FieldName", "NSID")

    def __init__(self, data: Union[dict, "Config"] = None, **kwargs):
        data = {re.sub(r"^\$", "", k): v for k, v in (data.items() if data else {})}
        self._overrides = tuple(data.keys()) if data else ()
        super(Config, self).__init__(data, **kwargs)

        for k, v in self._defaults.items():
            if v and not hasattr(self, k):
                setattr(self, k, v)

    def schema(self):
        """
        Format this meta into valid JADN format
        :return: JADN formatted meta
        """
        return {f"${k}": v for k, v in self.dict().items() if k in self._overrides}

    # Validation functions
    def check_MaxBinary(self, val: int) -> int:
        if val < 1:
            raise ValueError(f"MaxBinary invalid, must be greater than 1 - {val}")
        return val

    def check_MaxString(self, val: int) -> int:
        if val < 1:
            raise ValueError(f"MaxString invalid, must be greater than 1 - {val}")
        return val

    def check_MaxElements(self, val: int) -> int:
        if val < 1:
            raise ValueError(f"MaxElements invalid, must be greater than 1 - {val}")
        return val

    def check_FS(self, val: str) -> str:
        if len(val) != 1:
            raise ValueError(f"FS invalid, must be 1 character - given {len(val)}")
        return val

    def check_Sys(self, val: str) -> str:
        if len(val) != 1:
            raise ValueError(f"Sys invalid, must be 1 character - given {len(val)}")
        return val

    def check_TypeName(self, val: str) -> str:
        if len(val) < 1 or len(val) > 127:
            raise ValueError(f"TypeName invalid, must be greater 1 and less than 127 characters - given {len(val)}")
        try:
            re.compile(val)
        except Exception as e:
            raise e
        return val

    def check_FieldName(self, val: str) -> str:
        if len(val) < 1 or len(val) > 127:
            raise ValueError(f"FieldName invalid, must be greater 1 and less than 127 characters - given {len(val)}")
        try:
            re.compile(val)
        except Exception as e:
            raise e
        return val

    def check_NSID(self, val: str) -> str:
        if len(val) < 1 or len(val) > 127:
            raise ValueError(f"NSID invalid, must be greater 1 and less than 127 characters - given {len(val)}")
        try:
            re.compile(val)
        except Exception as e:
            raise e
        return val


class Meta(BaseModel):
    module: str
    patch: Optional[str]
    title: Optional[str]
    description: Optional[str]
    imports: Optional[Dict[str, str]]
    exports: Optional[List[str]]
    config: Optional[Config]

    # Helper Vars
    _config: bool

    __slots__ = ("module", "patch", "title", "description", "imports", "exports", "config")

    def __init__(self, data: Union[dict, "Meta"] = None, **kwargs):
        keys = data.keys() if data else ()
        self._config = "config" in keys
        if not self._config:
            self.config = Config()

        super(Meta, self).__init__(data, **kwargs)

    def schema(self):
        """
        Format this meta into valid JADN format
        :return: JADN formatted meta
        """
        d = self.dict()
        if self._config:
            if "config" in d:
                d["config"] = self.config.schema()
        elif "config" in d:
            del d["config"]
        return d


class Schema(BaseModel):
    meta: Meta
    types: Dict[str, Definition]

    # Helper vars
    _derived: Dict[str, Definition]
    _formats: Dict[str, Callable]
    _definition_order: Tuple[str] = ("OpenC2-Command", "OpenC2-Response", "Action", "Target", "Actuator", "Args",
                                     "Status-Code", "Results", "Artifact", "Device", "Domain-Name", "Email-Addr",
                                     "Features", "File", "IDN-Domain-Name", "IDN-Email-Addr", "IPv4-Net",
                                     "IPv4-Connection", "IPv6-Net", "IPv6-Connection", "IRI", "MAC-Addr", "Process",
                                     "Properties", "URI", "Action-Targets", "Date-Time", "Duration", "Feature",
                                     "Hashes", "Hostname", "IDN-Hostname", "IPv4-Addr", "IPv6-Addr", "L4-Protocol",
                                     "Message-Type", "Nsid", "Payload", "Port", "Response-Type", "Version")
    _schema_types: Set[str]

    __slots__ = ("meta", "types")

    def __init__(self, schema: Union[dict, "Schema"] = None, **kwargs):
        self.types = {}
        self.meta = Meta()
        self._derived = {}
        self._formats = ValidationFormats
        super(Schema, self).__init__({}, _config=self)

        if schema:
            self._setSchema(schema)

    @property
    def schema_types(self):
        """
        Tuple of all the types defined within the schema
        :return: schema types
        """
        return tuple(self._schema_types)

    @property
    def formats(self):
        return tuple(self._formats.keys())

    def analyze(self) -> dict:
        """
        Analyze the given schema for unreferenced and undefined types
        :return: analysis results
        """
        type_deps = self.dependencies()
        refs = {dep for tn, td in type_deps.items() for dep in td}.union({*self.meta.get("exports", [])})
        types = {*type_deps.keys()}.union(self._derived.keys())

        return dict(
            module=f"{self.meta.get('module', '')}{self.meta.get('patch', '')}",
            exports=self.meta.get('exports', []),
            unreferenced=list(types.difference(refs).difference(self._derived.keys())),
            undefined=list(refs.difference(types))
        )

    def dependencies(self) -> Dict[str, Set[str]]:
        """
        Determine the dependencies for each type within the schema
        :return: dictionary of dependencies
        """
        nsids = [n for n in self.meta.get("imports", {}).keys()]
        type_deps = {imp: set() for imp in nsids}

        def ns(name: str) -> str:
            """
            :param name: namespace of the type
            Return namespace if name has a known namespace, otherwise return full name
            """
            nsp = name.split(":")[0]
            return nsp if nsp in nsids else name

        for tn, td in self.types.items():
            type_deps[tn] = {ns(dep) for dep in td.dependencies}
        return type_deps

    def schema(self, strip: bool = False) -> dict:
        """
        Format this schema into valid JADN format
        :param strip: strip comments from schema
        :return: JADN formatted schema
        """
        schema_def = lambda d: getattr(d, f"schema{'_strip' if strip else ''}")()

        schema_types = [
            *[schema_def(self.types[dn]) if dn in self.types else None for dn in self._definition_order],
            *[None if dn in self._definition_order else schema_def(do) for dn, do in self.types.items()]
        ]

        return dict(
            meta=self.meta.schema(),
            types=list(filter(None, schema_types))
        )

    def schema_pretty(self, strip: bool = False, indent: int = 2) -> str:
        """
        Format this schema into valid pretty JADN format
        :param strip: strip comments from schema
        :param indent: spaces to indent
        :return: JADN formatted schema
        """
        return self._dumps(self.schema(strip=strip), indent)

    def simplify(self, schema: Union[dict, "Schema"] = None, anon: bool = True, multi: bool = True, derived: bool = True, map_of: bool = True, simple: bool = True) -> Union[dict, "Schema"]:
        """
        Given a schema, return a simplified schema with schema extensions removed
        :param schema: JADN schema to simplify
        :param anon: Replace all anonymous type definitions with explicit
        :param multi: Replace all multiple-value fields with explicit ArrayOf type definitions
        :param derived: Replace all derived enumerations with explicit Enumerated type definitions
        :param map_of: Replace all MapOf types with listed keys with explicit Map type definitions
        :param simple: return a simple type (dict) instead of an object (Schema)
        :return: simplified schema
        """
        config = self.meta.config
        p = inflect.engine()

        def remove_anonymous_type(schema: dict) -> dict:
            for type_def in list(schema.get("types", [])):
                for field_def in type_def.get("fields", []):
                    if "options" in field_def:
                        field_opts, type_opts = field_def["options"].split()
                        if type_opts.dict():
                            new_name = f"{field_def['type']}{config.Sys}{field_def['name']}".replace("_", "-")
                            schema["types"].append({
                                "name": new_name,
                                "type": field_def["type"],
                                "options": type_opts,
                                "description": field_def["description"]
                            })
                            field_def.update(
                                type=new_name,
                                options=field_opts
                            )

            return schema

        def remove_multiplicity(schema: dict) -> dict:
            for type_def in schema.get("types", []):
                for field_def in type_def.get("fields", []):
                    if "options" in field_def:
                        field_opts, type_opts = field_def["options"].split()
                        minc = field_opts.get("minc", 0)
                        maxc = field_opts.get("maxc", None)
                        if (maxc is not None and maxc != 1) or (minc is not None and minc > 1):
                            delattr(field_opts, "maxc")

                            type_opts.vtype = field_def["type"]
                            type_opts.minv = max(minc, 1)
                            if maxc is not None and maxc > 1:
                                type_opts.maxv = maxc

                            new_name = field_def['name'].split("_")
                            new_name[-1] = p.plural(new_name[-1]) if p.get_count(new_name[-1]) == 1 else new_name[-1]
                            new_name = "-".join(map(str.capitalize, new_name))
                            # new_name = f"{field_def['type']}{config.Sys}{field_def['name']}".replace("_", "-")
                            if not [t for t in schema.get("types", []) if t["name"] == new_name]:
                                schema["types"].append({
                                    "name": new_name,
                                    "type": "ArrayOf",
                                    "options": type_opts,
                                    "description": field_def["description"]
                                })
                            field_def.update(
                                type=new_name,
                                options=field_opts
                            )

            return schema

        def remove_derived_enum(schema: dict) -> dict:
            opt_checks = {
                "enum": lambda v: True,
                "ktype": lambda v: v.startswith("$"),
                "vtype": lambda v: v.startswith("$")
            }

            for type_def in schema.get("types", []):
                if type_def["type"] in ("ArrayOf", "Enumerated", "MapOf"):
                    for opt_name, opt_check in opt_checks.items():
                        opt = type_def["options"].get(opt_name, None)
                        if opt and opt_check(opt):
                            opt = opt[1:] if opt.startswith("$") else opt
                            orig_type = [t for t in schema.get("types", []) if t["name"] == opt]
                            if len(orig_type) != 1:
                                raise TypeError(f"Type of {opt} does not exist within the schema")

                            orig_type = orig_type[0]
                            new_name = f"{opt}{config.Sys}Enum".replace("_", "-")
                            if not [t for t in schema.get("types", []) if t["name"] == new_name]:
                                schema["types"].append({
                                    "name": new_name,
                                    "type": "Enumerated",
                                    "options": Options(),
                                    "description": f"Derived enumeration of {opt}",
                                    "fields": [{"id": f["id"], "value": f["name"], "description": f["description"]} for f in orig_type.get("fields", [])]
                                })
                            setattr(type_def["options"], opt_name, new_name)

            return schema

        def remove_map_of_enum(schema: dict) -> dict:
            for idx, type_def in enumerate(schema.get("types", [])):
                if type_def["type"] == "MapOf":
                    key_type = [t for t in schema.get("types", []) if t["name"] == type_def["options"].ktype]
                    value_type = type_def["options"].vtype
                    if len(key_type) != 1:
                        raise TypeError(f"Type of {type_def['options'].ktype} does not exist within the schema")
                    key_type = key_type[0]
                    if key_type["type"] == "Enumerated":
                        delattr(type_def["options"], "ktype")
                        delattr(type_def["options"], "vtype")
                        schema["types"][idx] = {
                            "name": type_def["name"],
                            "type": "Map",
                            "options": type_def["options"],
                            "description": type_def["description"],
                            "fields": [dict(id=f["id"], name=f["value"], type=value_type, options=Options(), description=f["description"]) for f in key_type.get("fields", [])]
                        }

            return schema

        schema = (schema if isinstance(schema, dict) else schema.schema()) if schema else self.schema()
        simple_schema = self._convert_types(schema)

        simple_schema = remove_anonymous_type(simple_schema) if anon else simple_schema
        simple_schema = remove_multiplicity(simple_schema) if multi else simple_schema
        simple_schema = remove_derived_enum(simple_schema) if derived else simple_schema
        simple_schema = remove_map_of_enum(simple_schema) if map_of else simple_schema
        simple_schema = self._convert_types(simple_schema)

        return simple_schema if simple else Schema(simple_schema)

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

    def loads(self, schema: Union[bytes, bytearray, dict, str]) -> None:
        """
        load a JADN schema from a string
        :param schema: JADN schema to load
        """
        if isinstance(schema, dict):
            self._setSchema(schema)
            return

        schema = schema.decode("utf-8", "backslashreplace") if isinstance(schema, (bytes, bytearray)) else schema

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
        return self._dumps(self.schema(strip=strip), indent)

    # Validation
    def verify_schema(self, silent=False) -> Optional[List[Exception]]:
        """
        Verify the schema is proper
        :param silent: bool - raise or return errors
        :return: OPTIONAL(list of errors)
        """
        errors = []
        schema_types = tuple(self._schema_types)

        if len(getattr(self, "meta", {}).keys()) == 0 or len(getattr(self, "types", {}).keys()) == 0:
            err = FormatError("Schema not properly defined")
            if silent:
                return [err]
            else:
                raise err

        for type_name, type_def in self.types.items():
            if type_def.type not in self._schema_types:
                errors.append(TypeError(f"Type of {type_name} not defined: {type_def.type}"))

            errors.extend(type_def.verify(schema_types, silent=silent) or [])

        errors = list(filter(None, errors))
        if len(errors) > 0:
            if silent:
                return errors
            else:
                raise errors[0]

    def validate(self, inst: dict, silent: bool = True) -> Optional[Exception]:
        for exp in self.meta.exports:
            rtn = self.validate_as(inst, exp)
            if not rtn:
                return

        err = ValidationError(f"instance not valid as under the current schema")
        if silent:
            return err
        else:
            raise err

    def validate_as(self, inst: dict, _type: str, silent: bool = True) -> Optional[List[Exception]]:
        errors = []
        if _type in self.meta.exports:
            rtn = self.types.get(_type).validate(inst)
            if rtn and len(rtn) != 0:
                errors.extend(rtn or [])
        else:
            errors.append(ValidationError(f"invalid export type, {_type}"))

        errors = list(filter(None, errors))
        if silent and errors:
            return errors
        elif not silent and errors:
            raise errors[0]

    # Helper Functions
    def _setSchema(self, data: Union[dict, "Schema"]) -> None:
        """
        Reset the schema based on the given data
        :param data:
        :return:
        """
        if not isinstance(data, (dict, type(self))):
            raise TypeError("Cannot load schema, incorrect type")

        self.meta = Meta(data.get("meta", {}))
        data = self.simplify(data, False, True, False, False)
        super(Schema, self).__init__(data, _config=self)

        for type_name, type_def in tuple(self.types.items()):
            type_def.process_options()
            self._schema_types.update(type_def.fieldtypes)

        self.verify_schema()

    def _dumps(self, schema: Union[dict, float, int, str, tuple], indent: int = 2, _level: int = 0) -> str:
        """
        Properly format a JADN schema
        :param schema: Schema to format
        :param indent: spaces to indent
        :param _level: current indent level
        :return: Formatted JADN schema
        """
        schema = schema if _level == 0 and isinstance(schema, dict) else schema
        _indent = indent - 1 if indent % 2 == 1 else indent
        _indent += (_level * 2)
        ind, ind_e = " " * _indent, " " * (_indent - 2)

        if isinstance(schema, dict):
            lines = f",\n".join(f"{ind}\"{k}\": {self._dumps(schema[k], indent, _level+1)}" for k in schema)
            return f"{{\n{lines}\n{ind_e}}}"

        elif isinstance(schema, (list, tuple)):
            nested = schema and isinstance(schema[0], (list, tuple))
            lvl = _level+1 if nested and isinstance(schema[-1], (list, tuple)) else _level
            lines = [self._dumps(val, indent, lvl) for val in schema]
            if nested:
                return f"[\n{ind}" + f",\n{ind}".join(lines) + f"\n{ind_e}]"
            return f"[{', '.join(lines)}]"

        elif isinstance(schema, (numbers.Number, str)):
            return json.dumps(schema)
        else:
            return "???"

    def addFormat(self, fmt: str, fun: Callable[[Any], Optional[List[Exception]]], override: bool = False) -> None:
        """
        Add a format validation function
        :param fmt: format to validate
        :param fun: function that performs the validation
        :param override: override the format if it exists
        :return: None
        """
        if fmt in self.formats and not override:
            raise FormatError(f"format {fmt} is already defined, user arg `override=True` to override format validation")
        self._formats[fmt] = fun

    def _convert_types(self, schema: dict) -> dict:
        type_keys = ("name", "type", "options", "description", "fields")
        gen_field_keys = ("id", "name", "type", "options", "description")
        enum_field_keys = ("id", "value", "description")
        schema = copy.deepcopy(schema)

        if "types" in schema:
            if all(isinstance(t, dict) for t in schema["types"]):
                # convert dict types to list
                schema_types = []
                for type_def in schema.get("types", []):
                    type_def["options"] = type_def["options"].schema(type_def["type"])
                    field_keys = enum_field_keys if type_def["type"] == "Enumerated" else gen_field_keys
                    if "fields" in type_def:
                        tmp_fields = []
                        for field in type_def["fields"]:
                            if "options" in field:
                                field["options"] = field["options"].schema(field["type"], field["name"], True)
                            tmp_fields.append([field[f] for f in field_keys if f in field])
                        type_def["fields"] = tmp_fields

                    type_def = [type_def[f] for f in type_keys if f in type_def]
                    schema_types.append(type_def)

                schema["types"] = schema_types
            elif all(isinstance(t, list) for t in schema["types"]):
                # convert list types to dict
                schema_types = []
                for type_def in schema.get("types", []):
                    type_def = dict(zip(type_keys, type_def))
                    type_def["options"] = Options(type_def["options"])
                    field_keys = enum_field_keys if type_def["type"] == "Enumerated" else gen_field_keys
                    if "fields" in type_def:
                        tmp_fields = []
                        for field in type_def["fields"]:
                            field = dict(zip(field_keys, field))
                            if "options" in field:
                                field["options"] = Options(field["options"])
                            tmp_fields.append(field)

                        type_def["fields"] = tmp_fields

                    schema_types.append(type_def)
                schema["types"] = schema_types
            else:
                raise TypeError("Schema types improperly formatted")

        return schema



