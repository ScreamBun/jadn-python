"""
JADN to JADN IDL
"""
import json
import os
import numbers
import re

from arpeggio import EOF, Optional, OneOrMore, ParserPython, PTNodeVisitor, visit_parse_tree, RegExMatch, OrderedChoice, UnorderedGroup, ZeroOrMore
from jadnschema.schema import (
    Schema
)
from typing import (
    Any,
    Tuple,
    Union
)
from ..base import ReaderBase

meta_keys = ("module", "patch", "title", "description", "imports", "exports", "config")
types = {
    "simple": ("Binary", "Boolean", "Integer", "Number", "Null", "String"),
    "selector": ("Enumerated", "Choice"),
    "compound": ("Array", "ArrayOf", "Map", "MapOf", "Record"),
    "fields": ("Choice",  "Map", "Record"),
    "options": ("ArrayOf", "MapOf")
}
jadn_types: Tuple[str] = tuple({t for tt in types.values() for t in tt})


def IDL_Rules():
    def endLine():
        return RegExMatch(fr'({os.linesep})?')

    def metadata():
        return OneOrMore(
            RegExMatch(fr"({'|'.join(meta_keys)}):.*"),
            endLine
        )

    # Types with defined fields except Enumerated and Array
    def def_field():
        return (
            RegExMatch(r"\d+"),                         # Field ID
            RegExMatch(r"[a-z][_A-Za-z0-9]{0,31}"),     # Field Name
            RegExMatch(r"[A-Z][-$A-Za-z0-9]{0,31}"),    # Field Type
            RegExMatch(r".*"),                          # Field Options & Description
            endLine
        )

    def def_fields():
        return (
            RegExMatch(r"[A-Z][-$A-Za-z0-9]{0,31}"),        # Def Name
            "=",
            RegExMatch(fr"({'|'.join(types['fields'])})"),  # Def Type
            Optional(RegExMatch(r".*$")),                   # Def Options & Description
            endLine,
            ZeroOrMore(def_field),                          # Def Fields
            endLine,
            "}",
            endLine
        )

    # Array
    def def_array_field():
        return (
            RegExMatch(r"\d+"),                         # Field ID
            RegExMatch(r"[A-Z][-$A-Za-z0-9]{0,31}"),    # Field Type
            RegExMatch(r"[^//]*"),                      # Field Options
            "//",
            RegExMatch(r"[^::]*"),                      # Field Name
            "::",
            RegExMatch(r".*"),                          # Field Description
            endLine
        )

    def def_array():
        return (
            RegExMatch(r"[A-Z][-$A-Za-z0-9]{0,31}"),    # Def Name
            "=",
            "Array",                                    # Def Type
            Optional(RegExMatch(r".*")),               # Def Options & Description
            endLine,
            ZeroOrMore(def_array_field),                # Def Fields
            endLine,
            "}",
            endLine
        )

    # Enumerations
    def def_enum_field():
        return (
            Optional(  # Normal Field
                RegExMatch(r"\d+"),     # Field ID
                RegExMatch(r"\w+"),     # Field Value
                Optional(","),
                Optional("//", RegExMatch(r".*")),      # Field Description
                endLine
            ),
            Optional(  # ID Field
                RegExMatch(r"\d+"),  # Field ID
                Optional(","),
                "//",
                RegExMatch(r"[^::]*"),  # Field Value
                "::",
                RegExMatch(r".*"),  # Field Description
            )
        )

    def def_enumerated():
        return (
            RegExMatch(r"[A-Z][-$A-Za-z0-9]{0,31}"),    # Def Name
            "=",
            RegExMatch(r"Enumerated(\.ID)?"),           # Def Type
            Optional(RegExMatch(r".*$")),               # Def Options & Description
            endLine,
            ZeroOrMore(def_enum_field),                 # Def Fields
            endLine,
            "}",
            endLine
        )

    # Custom Types
    def def_type():
        return (
            RegExMatch(r"[A-Z][-$A-Za-z0-9]{0,31}"),                                    # Def Name
            "=",
            RegExMatch(fr"({'|'.join(types['simple'] + types['options'])})"),           # Def Type
            RegExMatch(r".*$"),                                                         # Def Options & Description
            endLine
        )

    return (
        metadata,
        endLine,
        OneOrMore(
            Optional(def_type),
            Optional(def_fields),
            Optional(def_array),
            Optional(def_enumerated),
        ),
        EOF
    )


class IDL_Visitor(PTNodeVisitor):
    data = dict(
        meta={},
        types=[]
    )

    def visit_IDL_Rules(self, node, children) -> dict:
        return self.data

    def visit_metadata(self, node, children) -> None:
        for c in children:
            key, val = c.split(":", 1)
            self.data["meta"][key.strip()] = self._safe_json(val.strip())

    # Types with defined fields except Enumerated
    def visit_def_field(self, node, children) -> dict:
        field = children[:-1]
        field.extend(children[-1].split("//", 1) if "//" in children[-1] else [children[-1]])
        field[-1] = field[-1].replace("//", "")

        field = dict(zip(("id", "name", "type", "options", "description"), map(str.strip, field)))
        field["id"] = int(field["id"])

        parsed = self._parse_opts(field["options"])
        if parsed["description"]:
            field["description"] = f"{parsed['description']} {field['description']}"
        field["options"] = parsed["options"]

        return field

    def visit_def_fields(self, node, children) -> None:
        children = list(children)
        type_def = dict(
            name=children[0],
            type=children[1],
            options=[],
            description="",
            fields=[list(c.values()) for c in children if isinstance(c, dict)]
        )
        opt_desc = [c for c in children[2:4] if not isinstance(c, dict)]

        if len(opt_desc) == 1:
            type_def.update(self._parse_opts(opt_desc[0]))

        self.data["types"].append(list(type_def.values()))

    # Array
    def visit_def_array_field(self, node, children) -> dict:
        field = dict(zip(("id", "type", "options", "name", "description"), map(str.strip, children)))
        field["id"] = int(field["id"])
        field["options"] = self._parse_opts(field["options"])["options"]
        return {k: field.get(k) for k in ("id", "name", "type", "options", "description")}

    def visit_def_array(self, node, children) -> None:
        children = list(children)
        type_def = dict(
            name=children[0],
            type="Array",
            options=[],
            description="",
            fields=[list(c.values()) for c in children if isinstance(c, dict)]
        )
        opt_desc = [c for c in children[1:4] if not isinstance(c, dict)]
        if len(opt_desc) == 1:
            type_def.update(self._parse_opts(opt_desc[0]))

        self.data["types"].append(list(type_def.values()))

    # Enumerated
    def visit_def_enum_field(self, node, children) -> dict:
        field = dict(zip(("id", "value", "description"), [c for c in children if c != ","]))
        field["id"] = int(field["id"])
        return field

    def visit_def_enumerated(self, node, children) -> None:
        children = list(children)
        type_def = dict(
            name=children[0],
            type="Enumerated",
            options=[],
            description="",
            fields=[list(c.values()) for c in children if isinstance(c, dict)]
        )
        opt_desc = [c for c in children[1:4] if not isinstance(c, dict)]
        if "Enumerated.ID" == opt_desc[0]:
            type_def["options"].append("=")

        opt_desc = opt_desc[1:]
        if len(opt_desc) == 1:
            tmp = self._parse_opts(opt_desc[0])
            type_def["options"].extend(tmp["options"])
            type_def["description"] = tmp["description"]

        self.data["types"].append(list(type_def.values()))

    # Custom Types
    def visit_def_type(self, node, children) -> None:
        type_def = dict(zip(("name", "type", "options", "description"), children))
        type_def.update(self._parse_opts(type_def["options"]))
        self.data["types"].append(list(type_def.values()))

    # Helper Functions
    def _safe_json(self, value) -> str:
        try:
            return json.loads(value)
        except Exception:
            return value

    def _parse_opts(self, opts: str) -> dict:
        tmp_opts = {
            "options": [],
            "description": ""
        }

        if opts and opts not in ("", " ", None):
            # TODO: Parse field options
            # Comment matched by mistake
            if "//" in opts:
                opts, desc = opts.split("//", 1)
                tmp_opts["description"] = desc.strip()
                opts = re.sub(r"\s?{\s*?$", "", opts)

            # Optional Field
            if "optional" in opts:
                tmp_opts["options"].append("[0")
                opts = opts.replace("optional", "")

            # ktype & vtype
            kv_type = re.match(r"\((\$?[A-Z][-$A-Za-z0-9]{0,31})(, \$?[A-Z][-$A-Za-z0-9]{0,31})?\)", opts)
            if kv_type and len(kv_type.groups()) in (1, 2):
                if kv_type.groups()[1] is None:
                    tmp_opts["options"].append(f"*{kv_type.groups()[0]}")
                else:
                    tmp_opts["options"].extend([f"+{kv_type.groups()[0]}", f"*{kv_type.groups()[1][2:]}"])
                opts = opts.replace(kv_type.group(), "")

            # Format
            fmt = re.match(r"(?P<format>/[^\s]*)", opts)
            if fmt and len(fmt.groups()) == 1:
                tmp_opts["options"].append(fmt.groups()[0])
                opts = opts.replace(fmt.group(), "")

            # Type Size
            size = re.match(r"{(?P<min>\d+)\.\.(?P<max>(\*|\d+))}", opts)
            if size and len(size.groupdict()) == 2:
                sizes = size.groupdict()
                sizes = [
                    f"{{{sizes.get('min', 0)}",
                    "" if sizes.get("max", 0) in ("0", "*") else f"}}{sizes.get('max', 0)}"
                ]
                tmp_opts["options"].extend(filter(None, sizes))
                opts = opts.replace(size.group(), "")

        return tmp_opts


class IDLtoJADN(ReaderBase):
    format = "jidl"

    # Helper Functions
    def parse(self, idl_string: Union[bytes, str]) -> Schema:
        """
        Parse the given IDL string to a JADN Schema
        :param idl_string:
        :return:
        """
        idl_string = idl_string.decode("utf-8") if isinstance(idl_string, bytes) else idl_string
        try:
            parser = ParserPython(IDL_Rules)
            parse_tree = parser.parse(idl_string)
            parsed_schema = visit_parse_tree(parse_tree, IDL_Visitor())

        except Exception as e:
            raise Exception('IDL parsing error has occurred: {}'.format(e))

        schema = self._cleanEmpty(parsed_schema)
        with open("parsed.json", "w") as f:
            f.write(self._dumps(schema))

        return  Schema(schema)

    def _cleanEmpty(self, itm: Any) -> Any:
        if isinstance(itm, dict):
            return {k: self._cleanEmpty(v) for k, v in itm.items() if v is not None and (isinstance(v, (bool, int)) or len(v) > 0)}
        elif isinstance(itm, (list, tuple)):
            return [self._cleanEmpty(i) for i in itm]
        else:
            return itm

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
