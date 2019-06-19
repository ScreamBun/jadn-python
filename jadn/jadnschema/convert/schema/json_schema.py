"""
JADN to JSON Schema
"""
import json

from datetime import datetime

from . import WriterBase

from ... import (
    enums,
    # jadn_utils,
    utils
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
            "minv": "minItems",
            "maxv": "maxItems"
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

    _validationMap = {
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
                    "description": self._cleanComment(exp_def[0].desc)
                })
        json_schema["oneOf"] = self._cleanEmpty(json_schema["oneOf"])

        for struct in self._makeStructures(default={}):
            json_schema["definitions"].update(struct)

        return json_schema

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

    def makeHeader(self):
        """
        Create the headers for the schema
        :return: header for schema
        """
        header = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id":  ("" if self._meta.get("module", "https").startswith("http") else "http://") + self._meta.get("module", ""),
            "title": self._meta.get("title", ""),
            "description":  self._cleanComment(self._meta.get("description", ""))
        }

        return self._cleanEmpty(header)

    # Structure Formats
    def _formatArray(self, itm):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        return {
            self.formatStr(itm.name): self._cleanEmpty({})
        }

    def _formatArrayOf(self, itm):
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """
        return {
            self.formatStr(itm.name): self._cleanEmpty({})
        }

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        return {
            self.formatStr(itm.name): self._cleanEmpty({})
        }

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        return {
            self.formatStr(itm.name): self._cleanEmpty({})
        }

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        return {
            self.formatStr(itm.name): self._cleanEmpty({})
        }

    def _formatMapOf(self, itm):
        """
        Formats mapOf for the given schema type
        :param itm: mapOf to format
        :return: formatted mapOf
        """
        return {
            self.formatStr(itm.name): self._cleanEmpty({})
        }

    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        record_json = dict(
            type="object",
            description=self._cleanComment(itm.desc),
            additionalProperties=False,
            required=[],
            properties={}
        )
        for field in itm.fields:
            if not self._is_optional(field.opts):
                record_json["required"].append(field.name)

            print(field)
            record_json["properties"][field.name] = dict(
                type="",
                description=self._cleanComment(field.desc),
                # **self._optReformat(self._getType(field.type), field.opts)
            )

        print("")

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
            type=self._getType(itm.type),
            description=self._cleanComment(itm.desc),
            **self._optReformat(itm.type, itm.opts)
        )

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
        ignoreOpts = ("ktype", "vtype")
        r_opts = {}

        def ignore(k, v):
            if k in ["object", "array"]:
                return False

            return k.startswith(("min", "max")) and utils.safe_cast(v, int, 0) < 1

        for key, val in opts.items():
            if key in ignoreOpts:
                continue

            if _type and ignore(key, val):
                continue

            if key in optKeys:
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
        field_type = getattr(field, 'type', field)
        field_type = field_type if isinstance(field_type, str) else 'String'
        print(field_type)

        return {}

    def _cleanComment(self, msg, **kargs):
        """
        Format a comment for the given schema
        :param msg: comment text
        :param kargs: key/value comments
        :return: formatted comment
        """
        if self.comm == enums.CommentLevels.NONE:
            return ""

        com = ""
        if msg not in ["", None, " "]:
            com += msg[:-1] if msg.endswith(".") else msg

        for k, v in kargs.items():
            com += f" #{k}:{json.dumps(v)}"

        return com

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
            return {k: self._cleanEmpty(v) for k, v in itm.items() if v is not None and (isinstance(v, (bool, int)) or len(v) > 0)}
        elif isinstance(itm, (list, tuple)):
            return [self._cleanEmpty(i) for i in itm]
        else:
            return itm
