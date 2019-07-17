"""
JADN IDL to JADN
"""
import json
import os
import re
import warnings

from arpeggio import EOF, Optional, OneOrMore, ParserPython, PTNodeVisitor, visit_parse_tree, RegExMatch, OrderedChoice, UnorderedGroup, ZeroOrMore

from io import (
    BufferedIOBase,
    TextIOBase
)

from typing import (
    Union
)

from .. import ReaderBase

from .... import (
    schema,
    utils
)


def IDL_Rules():
    def endLine():
        return RegExMatch(r"({})?".format(os.linesep))

    def number():
        return RegExMatch(r"\d+(\.\d+)?")

    def metaLines():
        return OneOrMore(
            RegExMatch(r"\s*?\w+:"),
            RegExMatch(r"\s{,2}.*$"),
            endLine
        )

    def typeField():
        return (
            number,
            RegExMatch(r"[a-z][_A-Za-z0-9]{0,31}"),
            RegExMatch(r"[A-Z][-$A-Za-z0-9]{0,31}"),
            Optional(RegExMatch(r"[\d+\.\.(\d+|\*)]")),
            Optional("optional"),
            Optional(","),
            Optional(
                "// ",
                RegExMatch(r".*$")
            ),
            OneOrMore(endLine)
        )

    def typeDef():
        return (
            RegExMatch(r"[A-Z][-$A-Za-z0-9]{0,31}"),
            "=",
            [
                "Array",
                # "ArrayOf",
                "Choice",
                # "Enumerated",
                "Map",
                # "MapOf",
                "Record"
            ],
            "{",
            Optional(
                "//",
                RegExMatch(r".*$")
            ),
            OneOrMore(typeField),
            "}",
            OneOrMore(endLine)
        )

    return (
        OneOrMore(metaLines),
        OneOrMore(endLine),
        OneOrMore(typeDef),
        OneOrMore(RegExMatch(r'.*')),
        EOF
    )


class IDL_Visitor(PTNodeVisitor):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        schema = schema.Schema()

    def visit_IDL_Rules(self, node, children):
        return self.schema

    def visit_number(self, node, children):
        node = str(node)
        return float(node) if re.match(r"\d+\.\d+", node) else int(node)

    def visit_metaLines(self, node, children):
        meta = {children[i].strip()[:-1]: children[i+1] for i in range(0, len(children), 2)}
        for key, val in meta.items():
            try:
                val = json.loads(re.sub(r"\'", "\"", val))
            except ValueError:
                pass
            setattr(self.schema.meta, key, val)

    def visit_typeField(self, node, children):
        children = list(filter(lambda c: not re.match(r"^.*?,.*?$", str(c)), children))
        print(children)
        field = schema.Field(
            id=children[0],
            name=children[1],
            type=children[2],
            options=[],
            description=children[-1]
        )
        print(field.primitive())
        return field

    def visit_typeDef(self, node, children):
        print(children)
        print("")


class IDLtoJADN(ReaderBase):
    format = "jidl"

    def load(self, fname: Union[BufferedIOBase, TextIOBase], *args, **kwargs) -> schema.Schema:
        """
        Load and convert a JADN IDL schema file to JADN
        :param fname: schema file to load
        :return: loaded schema
        """
        return self.loads(fname.read())

    def loads(self, schema_str: Union[bytes, bytearray, str], *args, **kwargs) -> schema.Schema:
        """
        Load and convert a JADN IDL schema string to JADN
        :param schema_str:  schema string to load
        :return: loaded schema
        """
        schema_str = schema_str.decode("utf-8") if isinstance(schema_str, (bytes, bytearray)) else schema_str
        try:
            parser = ParserPython(IDL_Rules)
            parse_tree = parser.parse(str(schema_str))
            return visit_parse_tree(parse_tree, IDL_Visitor())

        except Exception as e:
            raise Exception('JADN IDL parsing error has occurred: {}'.format(e))
