"""
JADN to JADN IDL
"""
import re

from beautifultable import BeautifulTable
from datetime import datetime

from typing import (
    Any,
    Dict,
    List
)

from ..base import WriterBase

from .... import schema


class JADNtoIDL(WriterBase):
    format = "jidl"

    _alignment: Dict[str, str] = {
        "^": BeautifulTable.ALIGN_CENTER,
        "<": BeautifulTable.ALIGN_LEFT,
        ">": BeautifulTable.ALIGN_RIGHT
    }

    def dump(self, fname: str, source: str = None, comm: str = None) -> None:
        """
        Produce JSON schema from JADN schema and write to file provided
        :param fname: Name of file to write
        :param source: Name of the original schema file
        :param comm: Level of comments to include in converted schema, ignored
        :return: None
        """
        with open(fname, "w") as f:
            if source:
                f.write(f"/* Generated from {source}, {datetime.ctime(datetime.now())}*/\n")
            f.write(self.dumps())

    def dumps(self, comm: str = None) -> str:
        """
        Converts the JADN schema to JSON
        :param comm: Level of comments to include in converted schema, ignored
        :return: JSON schema
        """
        jidl_schema = self.makeHeader() + "\n".join(self._makeStructures(default=""))
        jidl_schema = "\n".join(l.rstrip() for l in re.sub(r"\t", " "*4, jidl_schema).split("\n"))
        return jidl_schema

    def makeHeader(self) -> str:
        """
        Create the headers for the schema
        :return: header for schema
        """
        meta = [[f"{meta_key}:", self._meta.get(meta_key, '')] for meta_key in self._meta_order]
        return f"{self._makeTable(meta)}\n\n"

    # Structure Formats
    def _formatArray(self, itm: schema.definitions.Array) -> str:
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        fmt = f" /{itm.options.format}" if hasattr(itm.options, "format") else ""
        array_idl = f"{itm.name} = Array{fmt} {{"

        fields = []
        for idx, field in enumerate(itm.fields):
            field_type = f"{field.type}"
            if field.type == "ArrayOf":
                field_type += f"({field.options.get('vtype', 'String')})"
            elif field.type == "MapOf":
                field_type += f"({field.options.get('ktype', 'String')}, {field.options.get('vtype', 'String')})"

            array = f"[{field.options.multiplicity()}]" if self._is_array(field.options) else ""
            fmt = f" /{field.options.format}" if hasattr(field.options, "format") else ""
            opt = " optional" if self._is_optional(field.options) else ""
            cont = ',' if idx + 1 != len(itm.fields) else ''

            fields.append([
                field.id,
                f"{field_type}{array}{fmt}{'' if array else opt}{cont}",
                f"// {field.name}:: {field.description}" if field.description else ""
            ])
        fields = "\n".join(f"\t{r}" for r in re.sub(r"\t", " " * 4, self._makeTable(fields)).split("\n"))

        if itm.description:
            idx = fields.find("//") + 3
            if idx > len(array_idl):
                array_idl += " " * (idx - len(array_idl)) + f"// {itm.description}"
            else:
                array_idl += f"  // {itm.description}"

        array_idl += f"\n{fields}"
        return f"{array_idl}\n}}\n"

    def _formatArrayOf(self, itm: schema.definitions.ArrayOf) -> str:
        """
        Formats arrayOf for the given schema type
        :param itm: arrayOf to format
        :return: formatted arrayOf
        """
        return self._formatCustom(itm)

    def _formatChoice(self, itm: schema.definitions.Choice) -> str:
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        choice_idl = f"{itm.name} = Choice {{"
        fields = self._makeFields(itm.fields)

        if itm.description:
            idx = fields.find("//") + 3
            if idx > len(choice_idl):
                choice_idl += " " * (idx - len(choice_idl)) + f"// {itm.description}"
            else:
                choice_idl += f"  // {itm.description}"

        choice_idl += f"\n{fields}"
        return f"{choice_idl}\n}}\n"

    def _formatEnumerated(self, itm: schema.definitions.Enumerated) -> str:
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        enum_id = hasattr(itm.options, "id")
        enumerated_idl = f"{itm.name} = Enumerated{'.ID' if enum_id else ''} {{"
        fields = []
        for i, f in enumerate(itm.fields):
            if enum_id:
                fields.append([f.id, f"// {f.value}:: {f.description}"])
            else:
                fields.append([f.id, f"{f.value}{',' if i + 1 != len(itm.fields) else ''}", f"// {f.description}"])

        fields = "\n".join(f"\t{r}" for r in re.sub(r"\t", " " * 4, self._makeTable(fields)).split("\n"))
        if itm.description:
            idx = fields.find("//") + 3
            if idx > len(enumerated_idl):
                enumerated_idl += " " * (idx - len(enumerated_idl)) + f"// {itm.description}"
            else:
                enumerated_idl += f"  // {itm.description}"

        enumerated_idl += f"\n{fields}"
        return f"{enumerated_idl}\n}}\n"

    def _formatMap(self, itm: schema.definitions.Map) -> str:
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        map_idl = f"{itm.name} = Map"
        multi = itm.options.multiplicity(check=lambda x, y: x > 0 or y > 0)
        if multi:
            map_idl += f"{{{multi}}}"

        map_idl += " {"
        fields = self._makeFields(itm.fields)

        if itm.description:
            idx = fields.find("//") + 3
            if idx > len(map_idl):
                map_idl += " " * (idx - len(map_idl)) + f"// {itm.description}"
            else:
                map_idl += f"  // {itm.description}"

        map_idl += f"\n{fields}"
        return f"{map_idl}\n}}\n"

    def _formatMapOf(self, itm: schema.definitions.MapOf) -> str:
        """
        Formats mapOf for the given schema type
        :param itm: mapOf to format
        :return: formatted mapOf
        """
        return self._formatCustom(itm)

    def _formatRecord(self, itm: schema.definitions.Record) -> str:
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        record_idl = f"{itm.name} = Record"
        multi = itm.options.multiplicity(check=lambda x, y: x > 0 or y > 0)
        if multi:
            record_idl += f"{{{multi}}}"

        record_idl += " {"
        fields = self._makeFields(itm.fields)

        if itm.description:
            idx = fields.find("//") + 3
            if idx > len(record_idl):
                record_idl += " " * (idx - len(record_idl)) + f"// {itm.description}"
            else:
                record_idl += f"  // {itm.description}"

        record_idl += f"\n{fields}"
        return f"{record_idl}\n}}\n"

    def _formatCustom(self, itm: schema.definitions.Definition) -> str:
        """
        Formats custom type for the given schema type
        :param itm: custom type to format
        :return: formatted custom type
        """
        itmType = f"{itm.type}"
        if itm.type == "ArrayOf":
            itmType += f"({itm.options.get('vtype', 'String')})"

        elif itm.type == "MapOf":
            itmType += f"({itm.options.get('ktype', 'String')}, {itm.options.get('vtype', 'String')})"

        opts = {} if itm.type in ("Integer", "Number") else {"check": lambda x, y: x > 0 or y > 0}
        multi = itm.options.multiplicity(**opts)
        if multi:
            itmType += f"{{{multi}}}"

        itmType += f"(%{itm.options.pattern}%)" if hasattr(itm.options, "pattern") else ""
        itmType += f" /{itm.options.format}" if hasattr(itm.options, "format") else ""

        return f"{itm.name} = {itmType}{'  // '+itm.description if itm.description else ''}\n"

    # Helper Functions
    def _makeFields(self, fields: List[schema.fields.Field]) -> str:
        tmp_fields = []
        for idx, field in enumerate(fields):
            field_type = f"{field.type}"
            if field.type == "ArrayOf":
                field_type += f"({field.options.get('vtype', 'String')})"
                field_type += f"{{{field.options.multiplicity(field=False)}}}"

            elif field.type == "MapOf":
                field_type += f"({field.options.get('ktype', 'String')}, {field.options.get('vtype', 'String')})"
                field_type += f"{{{field.options.multiplicity(field=False)}}}"
            else:
                mltiOpts = {} if field.type in ("Integer", "Number") else {"check": lambda x, y: x > 0 or y > 0}
                multi = field.options.multiplicity(**mltiOpts)
                multi_noCheck = field.options.multiplicity()
                field_type += f"[{multi_noCheck}]" if self._is_array(field.options) else (f"{{{multi}}}" if multi else "")

            fmt = f" /{field.options.format}" if hasattr(field.options, "format") else ""
            pattern = f"(%{field.options.pattern}%)" if hasattr(field.options, "pattern") else ""
            opt = " optional" if self._is_optional(field.options) else ""
            cont = ',' if idx + 1 != len(fields) else ''

            tmp_fields.append([
                field.id,
                field.name,
                f"{field_type}{fmt}{pattern}{opt}{cont}",
                f"// {field.description}" if field.description else ""
            ])
        return "\n".join(f"\t{r}" for r in re.sub(r"\t", " " * 4, self._makeTable(tmp_fields)).split("\n"))

    def _makeTable(self, rows: List[List[Any]], alignment: list = None) -> str:
        table = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=250)
        table.set_style(BeautifulTable.STYLE_NONE)

        for row in rows:
            table.append_row(row)

        if alignment:
            alignment = [self._alignment.get(align, BeautifulTable.ALIGN_LEFT) for align in alignment]
            if len(alignment) < table.column_count:
                alignment.extend([BeautifulTable.ALIGN_LEFT] * (table.column_count - len(alignment)))
        else:
            alignment = [BeautifulTable.ALIGN_RIGHT] + [BeautifulTable.ALIGN_LEFT]*(table.column_count-1)

        for column in range(table.column_count):
            table.column_alignments[column] = alignment[column]

        return str(table)
