"""
JADN to JSON Schema
"""
import json
import re

from datetime import datetime
from typing import (
    Any,
    Dict,
    Tuple,
    Union
)

from .. import (
    base,
    enums
)

from .... import (
    schema
)


class JADNtoJSON(base.WriterBase):
    format = "json"

    _fieldMap: Dict[str, str] = {
        "Binary": "string",
        "Boolean": "bool",
        "Integer": "integer",
        "Number": "number",
        "Null": "null",
        "String": "string"
    }

    _ignoreOpts: Tuple[str] = ("id", "ktype", "vtype")

    _jadn_fmt: Dict[str, dict] = {
        "eui": {"pattern": r"^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}((:[0-9a-fA-F]{2}){2})?$"},
        "ipv4-net": {"pattern": r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])(\/(3[0-2]|[0-2]?[0-9]))?$"},
        "ipv6-net": {"pattern": r"^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(%.+)?s*(\/([0-9]|[1-9][0-9]|1[0-1][0-9]|12[0-8]))?$"},
        "i8": {"minimum": -128, "maximum": 127},
        "i16": {"minimum": -32768, "maximum": 32767},
        "i32": {"minimum": -2147483648, "maximum": 2147483647}
    }

    _optKeys: Dict[Tuple[str], Dict[str, str]] = {
        ("array",): {
            "minv": "minItems",
            "maxv": "maxItems"
        },
        ("integer", "number"): {
            "minc": "minimum",
            "maxc": "maximum",
            "minv": "minimum",
            "maxv": "maximum",
            "format": "format"
        },
        ("choice", "map", "object"): {
            "minv": "minProperties",
            "maxv": "maxProperties"
        },
        ("binary", "enumerated", "string"): {
            "format": "format",
            "minc": "minLength",
            "maxc": "maxLength",
            "minv": "minLength",
            "maxv": "maxLength",
            "pattern": "pattern"
        }
    }

    _schema_order: Tuple[str] = ("$schema", "$id", "title", "type", "$ref", "const", "description",
                                 "additionalProperties", "minProperties", "maxProperties", "minItems", "maxItems",
                                 "oneOf", "required", "items", "format", "contentEncoding", "definitions")

    _validationMap: Dict[str, Union[str, None]] = {
        # JADN: JSON
        # JADN
        "b": "binary",
        "eui": None,
        "i8": None,
        "i16": None,
        "i32": None,
        "ipv4-addr": "ipv4",  # ipv4
        "ipv6-addr": "ipv6",  # ipv6
        "ipv4-net": None,
        "ipv6-net": None,
        "x": "binary",
        # JSON
        "date-time": "date-time",
        "date": "date",
        "email": "email",
        "hostname": "hostname",
        "idn-email": "idn-email",
        "idn-hostname": "idn-hostname",
        "ipv4": "ipv4",
        "ipv6": "ipv6",
        "iri": "iri",
        "iri-reference": "iri-reference",
        "json-pointer": "json-pointer",  # Draft 6
        "relative-json-pointer": "relative-json-pointer",
        "regex": "regex",
        "time": "time",
        "uri": "uri",
        "uri-reference": "uri-reference",  # Draft 6
        "uri-template": "uri-template",  # Draft 6
    }

    def dump(self, fname: str, source: str = None, comm: str = None) -> None:
        """
        Produce JSON schema from JADN schema and write to file provided
        :param fname: Name of file to write
        :param source: Name of the original schema file
        :param comm: Level of comments to include in converted schema
        :return: None
        """
        self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        with open(fname, "w") as f:
            if source:
                f.write(f"; Generated from {source}, {datetime.ctime(datetime.now())}\n")
            json.dump(self.dumps(comm), f, indent=2)

    def dumps(self, comm: str = None) -> dict:
        """
        Converts the JADN schema to JSON
        :param comm: Level of comments to include in converted schema
        :return: JSON schema
        """
        self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        return self._cleanEmpty(dict(
            **self.makeHeader(),
            type="object",
            oneOf=[{
                "$ref": self.formatStr(f"#/definitions/{t.name}"),
                "description": self._cleanComment(t.description or "<Fill Me In>")
            } for t in self._types if t.name in self._meta.exports],
            definitions={k: v for s in self._makeStructures(default={}) for k, v in s.items()}
        ))

    def makeHeader(self) -> dict:
        """
        Create the headers for the schema
        :return: header for schema
        """
        return self._cleanEmpty({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id":  ("" if self._meta.get("module", "https").startswith("http") else "http://") + self._meta.get("module", ""),
            "title": self._meta.title if hasattr(self._meta, "title") else (self._meta.module + (f" v.{self._meta.patch}" if hasattr(self._meta, "patch") else "")),
            "description": self._cleanComment(self._meta.get("description", ""))
        })

    # Structure Formats
    def _formatArray(self, itm: schema.definitions.Array) -> dict:
        """
        Formats an Array for the given schema type
        :param itm: Array to format
        :return: formatted Array
        """
        opts = self._optReformat("array", itm.options, False)
        if 'pattern' in opts:
            array_json = dict(
                title=itm.name.replace("-", " "),
                type="string",
                description=self._cleanComment(itm.description),
                **opts
            )
        else:
            array_json = dict(
                title=itm.name.replace("-", " "),
                type="array",
                description=self._cleanComment(itm.description),
                items=[]
            )

        return {
            self.formatStr(itm.name): self._cleanEmpty(array_json)
        }

    def _formatArrayOf(self, itm: schema.definitions.ArrayOf) -> dict:
        """
        Formats ArrayOf for the given schema type
        :param itm: ArrayOf to format
        :return: formatted ArrayOf
        """
        vtype = itm.options.get("vtype", "String")
        arrayof_def = dict(
            title=itm.name.replace("-", " "),
            type="array",
            description=self._cleanComment(itm.description),
            **self._optReformat("array", itm.options, False)
        )

        if vtype.startswith("$"):
            val_def = list(filter(lambda d: d.name == vtype[1:], self._types))
            val_def = val_def[0] if len(val_def) == 1 else {}
            id_val = val_def.opts.get("id", None)
            enum_val = "id" if id_val else ("value" if val_def.type == "Enumerated" else "name")

            arrayof_def["items"] = dict(
                type="integer" if id_val else "string",
                enum=[f[enum_val] for f in val_def.fields]
            )
        else:
            arrayof_def["items"] = self._getFieldType(vtype)

        return {
            self.formatStr(itm.name): self._cleanEmpty(arrayof_def)
        }

    def _formatChoice(self, itm: schema.definitions.Choice) -> dict:
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        return {
            self.formatStr(itm.name): self._cleanEmpty(dict(
                title=itm.name.replace("-", " "),
                type="object",
                description=self._cleanComment(itm.description),
                additionalProperties=False,
                minProperties=1,
                maxProperties=1,
                **self._optReformat("object", itm.options, False),
                properties={f.name: self._makeField(f) for f in itm.fields}
            ))
        }

    def _formatEnumerated(self, itm: schema.definitions.Enumerated) -> dict:
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        use_id = hasattr(itm.options, "id")

        return {
            self.formatStr(itm.name): self._cleanEmpty(dict(
                title=itm.name.replace("-", " "),
                type="integer" if use_id else "string",
                description=self._cleanComment(itm.description),
                **self._optReformat("object", itm.options, False),
                oneOf=[{
                    "const": f.id if use_id else f.value,
                    "description": self._cleanComment(f"{(f.value + ' - ') if use_id else ''}{f.description}")
                } for f in itm.fields]
            ))
        }

    def _formatMap(self, itm: schema.definitions.Map) -> dict:
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        return {
            self.formatStr(itm.name): self._cleanEmpty(dict(
                title=itm.name.replace("-", " "),
                type="object",
                description=self._cleanComment(itm.description),
                additionalProperties=False,
                **self._optReformat("object", itm.options, False),
                required=[f.name for f in itm.fields if not self._is_optional(f.options)],
                properties={f.name: self._makeField(f) for f in itm.fields}
            ))
        }

    def _formatMapOf(self, itm: schema.definitions.MapOf) -> dict:
        """
        Formats mapOf for the given schema type
        :param itm: mapOf to format
        :return: formatted mapOf
        """
        key_type = self._jadn_schema.types.get(itm.options.get("ktype"))
        if key_type.type in ("Choice", "Enumerated", "Map", "Record"):
            attr = "value" if key_type.type == "Enumerated" else "name"
            key_values = [getattr(f, attr) for f in key_type.get("fields", [])]
            keys = f"^({'|'.join(key_values)})$"
        else:
            print(f"Invalid MapOf definition for {itm.name}")
            keys = "^.*$"

        return {
            self.formatStr(itm.name): self._cleanEmpty(dict(
                title=itm.name.replace("-", " "),
                type="object",
                description=self._cleanComment(itm.description),
                additionalProperties=False,
                patternProperties={
                    keys: self._getFieldType(itm.options.get("vtype", "String"))
                }
            ))
        }

    def _formatRecord(self, itm: schema.definitions.Record) -> dict:
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        return {
            self.formatStr(itm.name): self._cleanEmpty(dict(
                title=itm.name.replace("-", " "),
                type="object",
                description=self._cleanComment(itm.description),
                additionalProperties=False,
                **self._optReformat("object", itm.options, False),
                required=[f.name for f in itm.fields if not self._is_optional(f.options)],
                properties={f.name: self._makeField(f) for f in itm.fields}
            ))
        }

    def _formatCustom(self, itm: schema.definitions.Definition) -> dict:
        """
        Formats custom for the given schema type
        :param itm: custom to format
        :return: formatted custom
        """
        custom_json = dict(
            title=itm.name.replace("-", " "),
            **self._getFieldType(itm.type),
            description=self._cleanComment(itm.description)
        )

        # TODO: Fix ME!!
        opts = self._optReformat(itm.type, itm.options, base_ref=True)
        keys = {*custom_json.keys()}.intersection({*opts.keys()})
        if keys:
            keys = {k: (custom_json[k], opts[k]) for k in keys}
            print(f"{itm.name} Key duplicate - {keys}")
            # map(opts.pop, keys)

        if "pattern" in opts:
            custom_json.pop("format", None)
            custom_json["type"] = "string"

        custom_json.update(opts)

        return {
            self.formatStr(itm.name): self._cleanEmpty(custom_json)
        }

    # Helper Functions
    def _getType(self, name: str) -> dict:
        """
        Get the JSON type of the field based of the type defined in JADN
        :param name: type of field as defined in JADN
        :return: type of the field as defined in JSON
        """
        type_def = [t for t in self._types if t.name == name]
        return (type_def[0] if len(type_def) == 1 else {}).get("type", "String")

    def _optReformat(self, optType: str, opts: schema.Options, base_ref: bool = False) -> dict:
        """
        Reformat options for the given schema
        :param optType: type to reformat the options for
        :param opts: original options to reformat
        :param numeric: is numeric type
        :return: dict - reformatted options
        """
        optType = optType.lower()
        optKeys = self._getOptKeys(optType)
        r_opts = {}

        def ignore(k, v):
            if k in ("object", "array"):
                return False
            if base_ref:
                return False
            if k in ("minc", "maxc", "minv", "maxv"):
                return v == 0
            return False

        for key, val in opts.dict().items():
            if ignore(key, val) or key in self._ignoreOpts:
                continue

            fmt = self._jadn_fmt.get(val)
            if key == "format" and fmt:
                r_opts.update(fmt)

            elif key in optKeys:
                r_opts[optKeys[key]] = self._validationMap.get(val, val) if key == "format" else val
            else:
                print(f"unknown option for type of {optType}: {key} - {val}")
        return r_opts

    def _getFieldType(self, field: Union[str, schema.fields.EnumeratedField, schema.fields.Field]) -> dict:
        """
        Determines the field type for the schema
        :param field: current type
        :return: type mapped to the schema
        """
        field_type = getattr(field, "type", field)
        field_type = field_type if isinstance(field_type, str) else "String"

        if isinstance(field, schema.fields.Field):
            rtn = {
                "MapOf": self._formatMapOf,
                "ArrayOf": self._formatArrayOf
            }.get(field.type, lambda f: {})(field)

            if rtn:
                rtn.pop("title", None)
                return rtn

            elif field.type in self._fieldMap:
                rtn = {"type": self.formatStr(self._fieldMap.get(field.type, field.type))}
                if field.type.lower() == "binary":
                    rtn.update({"format": field.options.format} if "format" in field.options else {"contentEncoding": "base64url"})
                return rtn

        if field_type in self._customFields:
            return {"$ref": f"#/definitions/{self.formatStr(field_type)}"}

        elif field_type in self._fieldMap:
            rtn = {"type": self.formatStr(self._fieldMap.get(field_type, field_type))}
            rtn.update({"format": "binary"} if field_type.lower() == "binary" else {})
            return rtn

        elif ":" in field_type:
            src, attr = field_type.split(":", 1)
            if src in self._imports:
                fmt = "" if self._imports[src].endswith(".json") else ".json"
                return {"$ref": f"{self._imports[src]}{fmt}#/{attr}"}

        elif re.match(r"^Enum\(.*?\)$", field_type):
            f_type = self._jadn_schema.types.get(field_type[5:-1])
            if f_type.type in ("Array", "Choice", "Map", "Record"):
                return {
                    "type": "string",
                    "description": f"Derived enumeration from {f_type.name}",
                    "enum": [f.name for f in f_type.get("fields", [])]
                }
            else:
                print(f"Invalid derived enumeration - {f_type.name} should be a Array, Choice, Map or Record type")

        elif re.match(r"^MapOf\(.*?\)$", field_type):
            print(f"Derived MapOf - {field_type}")

        print(f"unknown type: {field_type}")
        return {"type": "string"}

    def _makeField(self, field: schema.fields.Field) -> dict:
        if self._is_array(field.options):
            field_def = dict(
                type="array",
                items=self._getFieldType(field)
            )
        else:
            field_def = self._getFieldType(field)
            field_def = field_def[field.name] if len(field_def.keys()) == 1 and field.name in field_def else field_def

        ref = "$ref" not in field_def and field.type in ("Integer", "Number")
        field_type = field_def.get("type", "")
        field_type = field_def.get("$ref", "") if field_type == "" else field_type
        field_type = self._getType(field_type.split("/")[-1]) if field_type.startswith("#") else field_type
        field_def.update(
            description=self._cleanComment(field.description),
            **self._optReformat(field_type, field.options, base_ref=ref)
        )
        field_def.pop("title", None)
        return field_def

    def _cleanComment(self, msg: str, **kargs) -> str:
        """
        Format a comment for the given schema
        :param msg: comment text
        :param kargs: key/value comments
        :return: formatted comment
        """
        if self.comm == enums.CommentLevels.NONE:
            return ""
        return ("" if msg in ["", None, " "] else msg) + ''.join(f" #{k}:{json.dumps(v)}" for k, v in kargs.items())

    def _getOptKeys(self, _type: str) -> dict:
        """
        Get the option keys for conversion
        :param _type: the type to get the keys of
        :return: dict - option keys for translation
        """
        for opts, conv in self._optKeys.items():
            if _type in opts:
                return conv
        return {}

    def _cleanEmpty(self, itm: Any) -> Any:
        if isinstance(itm, dict):
            tmp = {k: self._cleanEmpty(v) for k, v in itm.items() if v is not None and (isinstance(v, (bool, int)) or len(v) > 0)}
            rtn = {k: tmp[k] for k in self._schema_order if k in tmp}
            rtn.update({k: tmp[k] for k in tmp if k not in self._schema_order})
            return rtn
        elif isinstance(itm, (list, tuple)):
            return [self._cleanEmpty(i) for i in itm]
        else:
            return itm
