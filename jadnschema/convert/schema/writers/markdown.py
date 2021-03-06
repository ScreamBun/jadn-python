"""
JADN to Markdown tables
"""
from beautifultable import BeautifulTable
from datetime import datetime
from typing import (
    Callable,
    Dict,
    Union
)

from .. import base, enums
from ....schema import definitions, fields, Options


class JADNtoMD(base.WriterBase):
    format = "md"

    _alignment: Dict[str, Callable[[str], str]] = {
        "^": lambda a: f":{a[1:-1]}:",
        "<": lambda a: f":{a[1:]}",
        ">": lambda a: f"{a[:-1]}:",
    }

    def dump(self, fname: str, source: str = None, comm: str = enums.CommentLevels.ALL, **kwargs) -> None:
        """
        Convert the given JADN schema to MarkDown Tables
        :param fname: Name of file to write
        :param source: Name of the original schema file
        :param comm: Level of comments to include in converted schema, ignored
        :return: None
        """
        with open(fname, "w") as f:
            if source:
                f.write(f"<!-- Generated from {source}, {datetime.ctime(datetime.now())} -->\n")
            f.write(self.dumps())

    def dumps(self, comm: str = enums.CommentLevels.ALL, **kwargs) -> str:
        """
        Convert the given JADN schema to MarkDown Tables
        :param comm: Level of comments to include in converted schema, ignored
        :return: formatted MarkDown tables of the given Schema
        """
        schema_md = self.makeHeader()
        structures = self._makeStructures(default="")
        for name in self._definition_order:
            str_def = structures.pop(name, "")
            schema_md += f"{str_def}\n" if str_def else ""

        for name in tuple(structures):
            str_def = structures.pop(name, "")
            schema_md += f"{str_def}\n" if str_def else ""

        return schema_md.replace("\t", " "*4)

    def makeHeader(self) -> str:
        """
        Create the headers for the schema
        :return: header for schema
        """
        def mkrow(k, v):
            if isinstance(v, dict) or hasattr(v, "schema"):
                v = v.schema() if hasattr(v, "schema") else v
                v = " ".join([f"**{k1}**: {v1}" for k1, v1 in v.items()])
            elif isinstance(v, (list, tuple)):
                v = ", ".join(v)
            return {".": f"**{k}:**", "..": v}

        headers = {
            ".": {'align': ">"},
            "..": {}
        }
        meta_table = self._makeTable(headers, [mkrow(meta, self._meta.get(meta, '')) for meta in self._meta_order])
        meta_table = str(meta_table).replace(" .. ", " .  ")

        return f"## Schema\n{meta_table}\n"

    # Structure Formats
    def _formatArray(self, itm: definitions.Array) -> str:
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        fmt = f" /{itm.options.format}" if hasattr(itm.options, "format") else ""
        array_md = f"**_Type: {itm.name} (Array{fmt})_**\n\n"
        headers = {
            'ID': {'align': '>'},
            'Type': {},
            '#': {'align': '>'},
            'Description': {}
        }
        rows = []
        for f in itm.fields:
            desc = f.description[:-1] if f.description.endswith(".") else f.description
            rows.append({"id": f.id, "type": f.type, "options": f.options, "description": f"**{f.name}**::{desc}"})

        array_md += self._makeTable(headers, rows)
        return array_md

    def _formatArrayOf(self, itm: definitions.ArrayOf) -> str:
        """
        Formats arrayOf for the given schema type
        :param itm: arrayOf to format
        :return: formatted arrayOf
        """
        return self._formatCustom(itm)

    def _formatChoice(self, itm: definitions.Choice) -> str:
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        fmt = ".ID" if hasattr(itm.options, "id") else ""
        choice_md = f"**_Type: {itm.name} (Choice{fmt})_**\n\n"
        headers = {
            'ID': {'align': '>'},
            'Name': {},
            'Type': {},
            '#': {'align': '>'},
            'Description': {}
        }
        rows = [self._makeField(f) for f in itm.fields]
        choice_md += self._makeTable(headers, rows)
        return choice_md

    def _formatEnumerated(self, itm: definitions.Enumerated) -> str:
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        fmt = ".ID" if hasattr(itm.options, "id") else ""
        enumerated_md = f"**_Type: {itm.name} (Enumerated{fmt})_**\n\n"

        itm_fields = []
        for f in itm.fields:
            f.description = f.description[:-1] if f.description.endswith(".") else f.description
            itm_fields.append(f)

        if hasattr(itm.options, "id"):
            headers = {
                'ID': {'align': '>'},
                'Description': {}
            }
            rows = [{"ID": f.id, "Description": f"**{f.value}**::{f.description}"} for f in itm_fields]
        else:
            headers = {
                'ID': {'align': '>'},
                'Name': {},
                'Description': {}
            }
            rows = itm_fields
        enumerated_md += self._makeTable(headers, rows)
        return enumerated_md

    def _formatMap(self, itm: definitions.Map) -> str:
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        fmt = ".ID" if hasattr(itm.options, "id") else ""
        multi = itm.options.multiplicity(check=lambda x, y: x > 0 or y > 0)
        if multi:
            fmt += f"{{{multi}}}"

        map_md = f"**_Type: {itm.name} (Map{fmt})_**\n\n"
        headers = {
            'ID': {'align': '>'},
            'Name': {},
            'Type': {},
            '#': {'align': '>'},
            'Description': {}
        }
        rows = [self._makeField(f) for f in itm.fields]
        map_md += self._makeTable(headers, rows)
        return map_md

    def _formatMapOf(self, itm: definitions.MapOf) -> str:
        """
        Formats mapOf for the given schema type
        :param itm: mapOf to format
        :return: formatted mapOf
        """
        return self._formatCustom(itm)

    def _formatRecord(self, itm: definitions.Record) -> str:
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        fmt = f" /{itm.options.format}" if hasattr(itm.options, 'format') else ""
        multi = itm.options.multiplicity(check=lambda x, y: x > 0 or y > 0)
        if multi:
            fmt += f"{{{multi}}}"

        record_md = f"**_Type: {itm.name} (Record{fmt})_**\n\n"
        headers = {
            'ID': {'align': '>'},
            'Name': {},
            'Type': {},
            '#': {'align': '>'},
            'Description': {}
        }
        rows = [self._makeField(f) for f in itm.fields]
        record_md += self._makeTable(headers, rows)
        return record_md

    def _formatCustom(self, itm: definitions.CustomDefinition) -> str:
        """
        Formats custom type for the given schema type
        :param itm: custom type to format
        :return: formatted custom type
        """
        custom_md = "\n"
        headers = {
            'Type Name': {},
            'Type Definition': {},
            'Description': {}
        }
        field = self._makeField(itm)
        row = {
            'Type Name': f"**{field['name']}**",
            'Type Definition': field['type'],
            'Description': field['description']
        }

        custom_md += self._makeTable(headers, [row])
        return custom_md

    # Helper Functions
    def _makeField(self, field: Union[definitions.DefinitionBase, fields.Field]) -> Dict:
        field_dict = field.dict()
        if field.type == "MapOf":
            field_dict['type'] += f"({field.options.get('ktype', 'String')}, {field.options.get('vtype', 'String')})"
        elif field.type == "ArrayOf":
            field_dict['type'] += f"({field.options.get('vtype', 'String')})"

        opts = {} if field.type in ("Integer", "Number") else {"check": lambda x, y: x > 0 or y > 0}
        multi = field.options.multiplicity(**opts)
        if multi:
            field_dict['type'] += f"{{{multi}}}"

        field_dict['type'] += f"(%{field.options.pattern}%)" if hasattr(field.options, "pattern") else ""
        field_dict['type'] += f" /{field.options.format}" if hasattr(field.options, "format") else ""
        field_dict['type'] += " unique" if getattr(field.options, "unique", False) else ""
        if field_dict["description"].endswith("."):
            field_dict["description"] = field_dict["description"][:-1]

        return field_dict

    def _makeTable(self, headers: dict, rows: list) -> str:
        """
        Create a table using the given header and row values
        :param headers: table header names and attributes
        :param rows: row values
        :return: formatted MarkDown table
        """
        table_md = ""
        if rows:
            table_md = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=300)
            table_md.set_style(BeautifulTable.STYLE_MARKDOWN)
            table_md.column_headers = list(headers.keys())

            for row in rows:
                tmp_row = []
                for column in table_md.column_headers:
                    has_column = column in row if isinstance(row, dict) else hasattr(row, column)
                    column = column if has_column else self._table_field_headers.get(column, column)

                    if isinstance(column, str):
                        cell = row.get(column, '')
                    else:
                        cell = list(filter(None, [row.get(c, None) for c in column]))
                        cell = cell[0] if len(cell) == 1 else ''

                    if column == "options" and isinstance(cell, Options):
                        cell = cell.multiplicity(1, 1, True)
                        # TODO: More options

                    elif column == ("name", "value"):
                        cell = f"**{cell}**"
                    tmp_row.append(cell)
                tmp_row = [str(c).replace("|", "\\|") for c in tmp_row]
                table_md.append_row(tmp_row)

            table_rows = str(table_md).split("\n")
            head = dict(zip([h.strip() for h in table_rows[0].split("|")], table_rows[1].split("|")))
            alignment = [self._alignment.get(headers[k].get("align", "<"))(v) for k, v in head.items() if k]
            table_rows[1] = f"|{'|'.join(alignment)}|"
            table_md = '\n'.join(table_rows)
        return f"{table_md}\n"
