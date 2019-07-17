"""
JADN to JSON Schema
"""
import json

from datetime import datetime

from .. import (
    enums,
    WriterBase
)

from .... import (
    # jadn_utils,
    utils,
    schema
)


class JADNtoJSON(WriterBase):
    format = "json"

    _fieldMap = {
        "Binary": "string",
        "Boolean": "bool",
        "Integer": "integer",
        "Number": "number",
        "Null": "null",
        "String": "string"
    }

    _ignoreOpts = [
        "ktype",
        "vtype"
    ]

    _jadn_fmt = {
        "eui": {"pattern": r"^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}((:[0-9a-fA-F]{2}){2})?$"},
        "ipv4-net": {"pattern": r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])(\/(3[0-2]|[0-2]?[0-9]))?$"},
        "ipv6-net": {"pattern": r"^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(%.+)?s*(\/([0-9]|[1-9][0-9]|1[0-1][0-9]|12[0-8]))?$"},
        "i8": {"minimum": -128, "maximum": 127},
        "i16": {"minimum": -32768, "maximum": 32767},
        "i32": {"minimum": -2147483648, "maximum": 2147483647}
    }

    _optKeys = {
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

    _schema_order = [
        "$schema",
        "$id",
        "title",
        "type",
        "$ref",
        "const",
        "description",
        "additionalProperties",
        "minProperties",
        "maxProperties",
        "minItems",
        "maxItems",
        "oneOf",
        "required",
        "items",
        "format",
        "contentEncoding"
    ]

    _validationMap = {
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

    def dump(self, fname, source="", comm=enums.CommentLevels.ALL):
        """
        Produce JSON schema from JADN schema and write to file provided
        :param fname: Name of file to write
        :param source: Name of the original schema file
        :param comm: Level of comments to include in converted schema
        :return: None
        """
        comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        with open(fname, "w") as f:
            if source:
                f.write(f"; Generated from {source}, {datetime.ctime(datetime.now())}\n")
            json.dump(self.dumps(comm), f, indent=2)

    def dumps(self, comm=None):
        """
        Converts the JADN schema to JSON
        :param comm: Level of comments to include in converted schema
        :return: JSON schema
        """
        if comm:
            self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        json_schema = dict(
            **self.makeHeader(),
            type="object",
            oneOf=[],
            definitions={}
        )

        for exp in self._meta.exports:
            exp_def = [t for t in self._types if t.name == exp]
            if len(exp_def) == 1:
                json_schema["oneOf"].append({
                    "$ref": self.formatStr(f"#/definitions/{exp}"),
                    "description": self._cleanComment(exp_def[0].description or "<Fill Me In>")
                })
        json_schema["oneOf"] = self._cleanEmpty(json_schema["oneOf"])

        for struct in self._makeStructures(default={}):
            json_schema["definitions"].update(struct)

        return json_schema

    def makeHeader(self):
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
    def _formatArray(self, itm):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        opts = self._optReformat("array", itm.options, True)
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

    def _formatArrayOf(self, itm):
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """
        vtype = itm.options.get("vtype", "String")
        arrayof_def = dict(
            title=itm.name.replace("-", " "),
            type="array",
            description=self._cleanComment(itm.description),
            **self._optReformat("array", itm.options, True)
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

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        choice_json = dict(
            title=itm.name.replace("-", " "),
            type="object",
            description=self._cleanComment(itm.description),
            additionalProperties=False,
            minProperties=1,
            maxProperties=1,
            **self._optReformat("object", itm.options, True),
            properties={}
        )

        for field in itm.fields:
            field_def = self._getFieldType(field)
            field_type = field_def.get("type", "")
            field_type = field_def.get("$ref", "") if field_type == "" else field_type
            field_type = self._getType(field_type.split("/")[-1]) if field_type.startswith("#") else field_type
            field_def.update(
                description = self._cleanComment(field.description),
                **self._optReformat(field_type, field.options)
            )
            field_def.pop("title", None)
            choice_json["properties"][field.name] = field_def

        return {
            self.formatStr(itm.name): self._cleanEmpty(choice_json)
        }

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        use_id = hasattr(itm.options, "id")

        def enum_const(f):
            return {
                "const": f.id if use_id else f.value,
                "description": self._cleanComment(f"{(f.value + ' - ') if use_id else ''}{f.description}")
            }

        enum_json = dict(
            title=itm.name.replace("-", " "),
            type="integer" if use_id else "string",
            description=self._cleanComment(itm.description),
            **self._optReformat("object", itm.options, True),
            oneOf=[enum_const(f) for f in itm.fields]
        )

        return {
            self.formatStr(itm.name): self._cleanEmpty(enum_json)
        }

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        map_json = dict(
            title=itm.name.replace("-", " "),
            type="object",
            description=self._cleanComment(itm.description),
            additionalProperties=False,
            **self._optReformat("object", itm.options, True),
            required=[f.name for f in itm.fields if not self._is_optional(f.options)],
            properties={}
        )

        for field in itm.fields:
            if self._is_array(field.options):
                field_def = dict(
                    type="array",
                    items=self._getFieldType(field)
                )
            else:
                field_def = self._getFieldType(field)
                field_def = field_def[field.name] if len(field_def.keys()) == 1 and field.name in field_def else field_def

            field_type = field_def.get("type", "")
            field_type = field_def.get("$ref", "") if field_type == "" else field_type
            field_type = self._getType(field_type.split("/")[-1]) if field_type.startswith("#") else field_type
            field_def.update(
                description=self._cleanComment(field.description),
                **self._optReformat(field_type, field.options)
            )
            field_def.pop("title", None)
            map_json["properties"][field.name] = field_def

        return {
            self.formatStr(itm.name): self._cleanEmpty(map_json)
        }

    def _formatMapOf(self, itm):
        """
        Formats mapOf for the given schema type
        :param itm: mapOf to format
        :return: formatted mapOf
        """
        mapof_json = dict(
            title=itm.name.replace("-", " "),
            type="object",
            description=self._cleanComment(itm.description),
            additionalProperties=False
            # TODO: Finish mapping
        )

        return {
            self.formatStr(itm.name): self._cleanEmpty(mapof_json)
        }

    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        record_json = dict(
            title=itm.name.replace("-", " "),
            type="object",
            description=self._cleanComment(itm.description),
            additionalProperties=False,
            **self._optReformat("object", itm.options, True),
            required=[f.name for f in itm.fields if not self._is_optional(f.options)],
            properties={}
        )

        for field in itm.fields:
            field_def = self._getFieldType(field)
            field_type = field_def.get("type", "")
            field_type = field_def.get("$ref", "") if field_type == "" else field_type
            field_type = self._getType(field_type.split("/")[-1]) if field_type.startswith("#") else field_type
            field_def.update(
                description=self._cleanComment(field.description),
                **self._optReformat(field_type, field.options)
            )
            field_def.pop("title", None)
            record_json["properties"][field.name] = field_def

        return {
            self.formatStr(itm.name): self._cleanEmpty(record_json)
        }

    def _formatCustom(self, itm):
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
        opts = self._optReformat(itm.type, itm.options)
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
    def _getType(self, name):
        """
        Get the JSON type of the field based of the type defined in JADN
        :param name: type of field as defined in JADN
        :return: type of the field as defined in JSON
        """
        type_def = [t for t in self._types if t.name == name]
        type_def = type_def[0] if len(type_def) == 1 else {}
        return type_def.get("type", "String")

    def _optReformat(self, optType, opts, _type=False):
        """
        Reformat options for the given schema
        :param optType: type to reformat the options for
        :param opts: original options to reformat
        :param _type: is type of field
        :return: dict - reformatted options
        """
        _type = _type if isinstance(_type, bool) else False
        optType = optType.lower()
        optKeys = self._getOptKeys(optType)
        r_opts = {}

        def ignore(k, v):
            if k in ["object", "array"]:
                return False

            return any([
                k == "minc" and utils.safe_cast(v, int, 1) < 1,
                k == "maxc" and utils.safe_cast(v, int, 0) < 1,
                k == "minv" and utils.safe_cast(v, int, 1) < 1,
                k == "maxv" and utils.safe_cast(v, int, 0) < 1,
            ])

        for key, val in opts.dict().items():
            if _type and not ignore(key, val):
                fmt = self._jadn_fmt.get(val)
                if key == "format" and fmt:
                    r_opts.update(fmt)
                elif key in optKeys:
                    r_opts[optKeys[key]] = self._validationMap.get(val, val) if key == "format" else val
                continue

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

    def _getFieldType(self, field):
        """
        Determines the field type for the schema
        :param field: current type
        :return: type mapped to the schema
        """
        field_type = getattr(field, "type", field)
        field_type = field_type if isinstance(field_type, str) else "String"

        if isinstance(field, schema.Field):
            rtn = {
                "MapOf": self._formatMapOf,
                "ArrayOf": self._formatArrayOf
            }.get(field_type, lambda f: {})(field)

            if rtn:
                rtn.pop("title", None)
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

        print(f"unknown type: {field_type}")
        return {"type": "string"}

    def _cleanComment(self, msg, **kargs):
        """
        Format a comment for the given schema
        :param msg: comment text
        :param kargs: key/value comments
        :return: formatted comment
        """
        if self.comm == enums.CommentLevels.NONE:
            return ""
        return ("" if msg in ["", None, " "] else msg) + ''.join(f" #{k}:{json.dumps(v)}" for k, v in kargs.items())

    def _getOptKeys(self, _type):
        """
        Get the option keys for conversion
        :param _type: the type to get the keys of
        :return: dict - option keys for translation
        """
        for opts, conv in self._optKeys.items():
            if _type in opts:
                return conv
        return {}

    def _cleanEmpty(self, itm):
        if isinstance(itm, dict):
            tmp = {k: self._cleanEmpty(v) for k, v in itm.items() if v is not None and (isinstance(v, (bool, int)) or len(v) > 0)}
            rtn = {k: tmp[k] for k in self._schema_order if k in tmp}
            rtn.update({k: tmp[k] for k in tmp if k not in self._schema_order})
            return rtn
        elif isinstance(itm, (list, tuple)):
            return [self._cleanEmpty(i) for i in itm]
        else:
            return itm
