"""
JADN to JADN IDL
"""
import re

from beautifultable import BeautifulTable
from datetime import datetime

from typing import (
    Any,
    List
)

from .. import WriterBase

from ....definitions import (
    multiplicity
)


class JADNtoIDL(WriterBase):
    format = "jidl"
    _alignment = {
        "^": BeautifulTable.ALIGN_CENTER,
        "<": BeautifulTable.ALIGN_LEFT,
        ">": BeautifulTable.ALIGN_RIGHT
    }

    def dump(self, fname, source="", comm=None) -> None:
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

    def dumps(self, comm=None) -> str:
        """
        Converts the JADN schema to JSON
        :param comm: Level of comments to include in converted schema, ignored
        :return: JSON schema
        """
        jidl_schema = self.makeHeader() + "\n".join(self._makeStructures(default=""))
        jidl_schema = "\n".join(l.rstrip() for l in re.sub(r"\t", " "*4, jidl_schema).split("\n"))
        return jidl_schema

    def makeHeader(self):
        """
        Create the headers for the schema
        :return: header for schema
        """
        meta = [[f"{meta_key}:", self._meta.get(meta_key, '')] for meta_key in self._meta_order]
        return self._makeTable(meta) + "\n\n"

    # Structure Formats
    def _formatArray(self, itm):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        fmt = f" /{itm.options.format}" if hasattr(itm.options, "format") else ""
        array_idl = f"{itm.name} = Array{fmt} {{"

        fields = []
        for i, f in enumerate(itm.fields):
            fType = f"{f.type}" + (f"({f.options.get('vtype', 'String')})" if f.type == "ArrayOf" else (f"({f.options.get('ktype', 'String')}, {f.options.get('vtype', 'String')})" if f.type == "MapOf" else ""))
            array = f"[{multiplicity(f.options.get('minc', 0), f.options.get('maxc', 0))}]" if self._is_array(f.options) else ""
            fmt = f" /{f.options.format}" if hasattr(f.options, "format") else ""
            opt = " optional" if self._is_optional(f.options) else ""
            cont = ',' if i + 1 != len(itm.fields) else ''
            tmp_field = [f.id, f"{fType}{array}{fmt}{'' if array else opt}{cont}", f"// {f.name}:: {f.description}" if f.description else ""]
            fields.append(tmp_field)
        fields = "\n".join(f"\t{r}" for r in re.sub(r"\t", " " * 4, self._makeTable(fields)).split("\n"))

        if itm.description:
            idx = fields.find("//") + 3
            if idx > len(array_idl):
                array_idl += " " * (idx - len(array_idl)) + f"// {itm.description}"
            else:
                array_idl += f"  // {itm.description}"

        array_idl += f"\n{fields}"
        return f"{array_idl}\n}}\n"

    def _formatArrayOf(self, itm):
        """
        Formats arrayOf for the given schema type
        :param itm: arrayOf to format
        :return: formatted arrayOf
        """
        return self._formatCustom(itm)

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        choice_idl = f"{itm.name} = Choice {{"

        fields = []
        for i, f in enumerate(itm.fields):
            fType = f"{f.type}" + (f"({f.options.get('vtype', 'String')})" if f.type == "ArrayOf" else (f"({f.options.get('ktype', 'String')}, {f.options.get('vtype', 'String')})" if f.type == "MapOf" else ""))
            array = f"[{multiplicity(f.options.get('minc', 0), f.options.get('maxc', 0))}]" if self._is_array(f.options) else ""
            fmt = f" /{f.options.format}" if hasattr(f.options, "format") else ""
            opt = " optional" if self._is_optional(f.options) else ""
            cont = ',' if i + 1 != len(itm.fields) else ''
            tmp_field = [f.id, f.name, f"{fType}{array}{fmt}{'' if array else opt}{cont}", f"// {f.description}" if f.description else ""]
            fields.append(tmp_field)
        fields = "\n".join(f"\t{r}" for r in re.sub(r"\t", " " * 4, self._makeTable(fields)).split("\n"))

        if itm.description:
            idx = fields.find("//") + 3
            if idx > len(choice_idl):
                choice_idl += " " * (idx - len(choice_idl)) + f"// {itm.description}"
            else:
                choice_idl += f"  // {itm.description}"

        choice_idl += f"\n{fields}"
        return f"{choice_idl}\n}}\n"

    def _formatEnumerated(self, itm):
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

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        map_idl = f"{itm.name} = Map"
        if hasattr(itm.options, "minv") or hasattr(itm.options, "maxv"):
            minv = itm.options.get('minv', 0)
            maxv = itm.options.get('maxv', 0)
            if minv > 0 or maxv > 0:
                map_idl += f"{{{multiplicity(minv, maxv)}}}"
        map_idl += " {"

        fields = []
        for i, f in enumerate(itm.fields):
            fType = f"{f.type}" + (f"({f.options.get('vtype', 'String')})" if f.type == "ArrayOf" else (f"({f.options.get('ktype', 'String')}, {f.options.get('vtype', 'String')})" if f.type == "MapOf" else ""))
            array = f"[{multiplicity(f.options.get('minc', 0), f.options.get('maxc', 0))}]" if self._is_array(f.options) else ""
            fmt = f" /{f.options.format}" if hasattr(f.options, "format") else ""
            opt = " optional" if self._is_optional(f.options) else ""
            cont = ',' if i + 1 != len(itm.fields) else ''
            tmp_field = [f.id, f.name, f"{fType}{array}{fmt}{'' if array else opt}{cont}", f"// {f.description}" if f.description else ""]
            fields.append(tmp_field)
        fields = "\n".join(f"\t{r}" for r in re.sub(r"\t", " " * 4, self._makeTable(fields)).split("\n"))

        if itm.description:
            idx = fields.find("//") + 3
            if idx > len(map_idl):
                map_idl += " " * (idx - len(map_idl)) + f"// {itm.description}"
            else:
                map_idl += f"  // {itm.description}"

        map_idl += f"\n{fields}"
        return f"{map_idl}\n}}\n"

    def _formatMapOf(self, itm):
        """
        Formats mapOf for the given schema type
        :param itm: mapOf to format
        :return: formatted mapOf
        """
        return self._formatCustom(itm)

    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        record_idl = f"{itm.name} = Record"
        if hasattr(itm.options, "minv") or hasattr(itm.options, "maxv"):
            minv = itm.options.get('minv', 0)
            maxv = itm.options.get('maxv', 0)
            if minv > 0 or maxv > 0:
                record_idl += f"{{{multiplicity(minv, maxv)}}}"
        record_idl += " {"

        fields = []
        for i, f in enumerate(itm.fields):
            fType = f"{f.type}" + (f"({f.options.get('vtype', 'String')})" if f.type == "ArrayOf" else (f"({f.options.get('ktype', 'String')}, {f.options.get('vtype', 'String')})" if f.type == "MapOf" else ""))
            array = f"[{multiplicity(f.options.get('minc', 0), f.options.get('maxc', 0))}]" if self._is_array(f.options) else ""
            fmt = f" /{f.options.format}" if hasattr(f.options, "format") else ""
            opt = " optional" if self._is_optional(f.options) else ""
            cont = ',' if i + 1 != len(itm.fields) else ''
            tmp_field = [f.id, f.name, f"{fType}{array}{fmt}{'' if array else opt}{cont}", f"// {f.description}" if f.description else ""]
            fields.append(tmp_field)
        fields = "\n".join(f"\t{r}" for r in re.sub(r"\t", " " * 4, self._makeTable(fields)).split("\n"))

        if itm.description:
            idx = fields.find("//") + 3
            if idx > len(record_idl):
                record_idl += " " * (idx - len(record_idl)) + f"// {itm.description}"
            else:
                record_idl += f"  // {itm.description}"

        record_idl += f"\n{fields}"
        return f"{record_idl}\n}}\n"

    def _formatCustom(self, itm):
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

        minv = itm.options.get('minv', 0)
        maxv = itm.options.get('maxv', 0)
        if minv > 0 or maxv > 0:
            itmType += f"{{{multiplicity(minv, maxv)}}}"

        fmt = f" /{itm.options.format}" if hasattr(itm.options, "format") else ""

        return f"{itm.name} = {itmType}{fmt}{'  // '+itm.description if itm.description else ''}\n"

    # Helper Functions
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
