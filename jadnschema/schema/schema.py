"""
JADN Schema Models
"""
import json
import numbers
import os

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
    Union
)

from .base import BaseModel
from .definitions import Definition
from .exceptions import (
    FormatError,
    ValidationError
)
from .formats import ValidationFormats


class Meta(BaseModel):
    module: str
    patch: Optional[str]
    title: Optional[str]
    description: Optional[str]
    imports: Optional[List[List[str]]]  # min_size=2, max_size=2
    exports: Optional[List[str]]

    __slots__ = ("module", "patch", "title", "description", "imports", "exports")

    def __init__(self, data: Union[dict, "Meta"] = None, **kwargs):
        super(Meta, self).__init__(data, **kwargs)

        if hasattr(self, "imports"):
            if any(len(imp) != 2 for imp in self.imports):
                raise ValueError(f"{self.__class__.__name__}.import improperly formatted")

    def schema(self):
        """
        Format this meta into valid JADN format
        :return: JADN formatted meta
        """
        return self.dict()


class Schema(BaseModel):
    meta: Meta
    types: Dict[str, Definition]
    _formats = Dict[str, Callable]
    _types: Dict[str, Definition]

    __slots__ = ("meta", "types")

    def __init__(self, schema: Union[dict, "Schema"] = None, **kwargs):
        kwargs["_schema"] = self
        super(Schema, self).__init__(schema, **kwargs)
        self._formats = ValidationFormats
        self._types = {}

        if schema:
            for type_name, type_def in tuple(self.types.items()):
                type_def.process_options()
                self._schema_types.update(type_def.fieldtypes)
            self.verify_schema()

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
        types = {*type_deps.keys()}.union(self._types.keys())

        return dict(
            module=f"{self.meta.get('module', '')}{self.meta.get('patch', '')}",
            exports=self.meta.get('exports', []),
            unreferenced=list(types.difference(refs).difference(self._types.keys())),
            undefined=list(refs.difference(types))
        )

    def dependencies(self) -> Dict[str, Set[str]]:
        """
        Determine the dependencies for each type within the schema
        :return: dictionary of dependencies
        """
        nsids = [n[0] for n in self.meta.get("imports", [])]
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
        # schema_types = [v for k, v in self.types.items() if not k.startswith("_")]
        return dict(
            meta=self.meta.schema(),
            types=[getattr(t, f"schema{'_strip' if strip else ''}")() for t in self.types.values()]
        )

    def schema_pretty(self, strip: bool = False, indent: int = 2) -> str:
        """
        Format this schema into valid pretty JADN format
        :param strip: strip comments from schema
        :param indent: spaces to indent
        :return: JADN formatted schema
        """
        return self._dumps(self.schema(strip=strip), indent)

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
    def _setSchema(self, data: dict) -> None:
        """
        Reset the schema based on the given data
        :param data:
        :return:
        """
        if not isinstance(data, (dict, type(self))):
            raise TypeError("Cannot load schema, incorrect type")
        kwargs = {"_schema": self}
        super(Schema, self).__init__(data, **kwargs)

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

