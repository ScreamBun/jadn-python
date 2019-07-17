"""
JADN to Markdown tables
"""
from beautifultable import BeautifulTable
from datetime import datetime

from .. import WriterBase

from .... import (
    definitions,
    schema
)


class JADNtoMD(WriterBase):
    format = "md"

    _alignment = {
        "^": lambda a: f":{a[1:-1]}:",
        "<": lambda a: f":{a[1:]}",
        ">": lambda a: f"{a[:-1]}:",
    }

    def dump(self, fname, source="", comm=None):
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
            f.write(self.dumps(comm))

    def dumps(self, comm=None):
        """
        Convert the given JADN schema to MarkDown Tables
        :param comm: Level of comments to include in converted schema, ignored
        :return: formatted MarkDown tables of the given Schema
        """
        return self.makeHeader() + "\n".join(self._makeStructures(default=""))

    def makeHeader(self):
        """
        Create the headers for the schema
        :return: header for schema
        """
        def mkrow(k, v):
            if isinstance(v, (list, tuple)):
                v = ", ".join([f"**{i[0]}** {i[1]}" for i in v] if isinstance(v[0], (list, tuple)) else v)
            return {".": f"**{k}:**", "..": v}

        headers = {
            ".": {'align': ">"},
            "..": {}
        }
        meta_table = self._makeTable(headers, [mkrow(meta, self._meta.get(meta, '')) for meta in self._meta_order])
        meta_table = str(meta_table).replace(" .. ", " .  ")

        return f"## Schema\n{meta_table}\n"

    # Structure Formats
    def _formatArray(self, itm):
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
        rows = [{"id": f.id, "type": f.type, "options": f.options, "description": f"**{f.name}** - {f.description}"} for f in itm.fields]

        array_md += self._makeTable(headers, rows)
        return array_md

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
        fmt = ".ID" if hasattr(itm.options, "id") else ""
        choice_md = f"**_Type: {itm.name} (Choice{fmt})_**\n\n"
        headers = {
            'ID': {'align': '>'},
            'Name': {},
            'Type': {},
            '#': {'align': '>'},
            'Description': {}
        }
        choice_md += self._makeTable(headers, itm.fields)
        return choice_md

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        fmt = ".ID" if hasattr(itm.options, "id") else ""
        enumerated_md = f"**_Type: {itm.name} (Enumerated{fmt})_**\n\n"
        if hasattr(itm.options, "id"):
            headers = {
                'ID': {'align': '>'},
                'Description': {}
            }
            rows = [{"ID": f.id, "Description": f"**{f.value}** - {f.description}"} for f in itm.fields]
        else:
            headers = {
                'ID': {'align': '>'},
                'Name': {},
                'Description': {}
            }
            rows = itm.fields
        enumerated_md += self._makeTable(headers, rows)
        return enumerated_md

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        fmt = ".ID" if hasattr(itm.options, "id") else ""
        minv = itm.options.get('minv', 0)
        maxv = itm.options.get('maxv', 0)
        if minv != 0 or maxv != 0:
            fmt += f"{{{definitions.multiplicity(minv, maxv)}}}"

        map_md = f"**_Type: {itm.name} (Map{fmt})_**\n\n"
        headers = {
            'ID': {'align': '>'},
            'Name': {},
            'Type': {},
            '#': {'align': '>'},
            'Description': {}
        }
        rows = []
        for field in itm.fields:
            row = field.dict()
            if field.type == "MapOf":
                row['type'] += f"({field.options.get('ktype', 'String')}, {field.options.get('vtype', 'String')})"
            elif field.type == "ArrayOf":
                row['type'] += f"({field.options.get('vtype', 'String')})"

            if hasattr(field.options, "format"):
                row['type'] += f" /{field.options.format}"
            rows.append(row)

        map_md += self._makeTable(headers, rows)
        return map_md

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
        fmt = f" /{itm.options.format}" if hasattr(itm.options, 'format') else ""
        minv = itm.options.get('minv', 0)
        maxv = itm.options.get('maxv', 0)
        if minv != 0 or maxv != 0:
            fmt += f"{{{definitions.multiplicity(minv, maxv)}}}"

        record_md = f"**_Type: {itm.name} (Record{fmt})_**\n\n"
        headers = {
            'ID': {'align': '>'},
            'Name': {},
            'Type': {},
            '#': {'align': '>'},
            'Description': {}
        }
        record_md += self._makeTable(headers, itm.fields)
        return record_md

    def _formatCustom(self, itm):
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
        row = {
            'Type Name': f"**{itm.name}**",
            'Type Definition': itm.type,
            'Description': itm.description
        }
        if itm.type == "MapOf":
            row['Type Definition'] += f"({itm.options.get('ktype', 'String')}, {itm.options.get('vtype', 'String')})"
        elif itm.type == "ArrayOf":
            row['Type Definition'] += f"({itm.options.get('vtype', 'String')})"

        if hasattr(itm.options, "format"):
            row['Type Definition'] += f" /{itm.options.format}"

        if any([hasattr(itm.options, v) for v in ("minc", "maxc", "minv", "maxv")]):
            multi = ("minc", "maxc") if hasattr(itm.options, "minc") else ("minv", "maxv")
            minimum = itm.options.get(multi[0], 1)
            maximum = itm.options.get(multi[1], 1)
            row['Type Definition'] += f"{{{definitions.multiplicity(minimum, maximum)}}}"

        custom_md += self._makeTable(headers, [row])
        return custom_md

    # Helper Functions
    def _makeTable(self, headers={}, rows=[]):
        """
        Create a table using the given header and row values
        :param headers: table header names and attributes
        :param rows: row values
        :return: formatted MarkDown table
        """
        table_md = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=250)
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

                if column == "options" and isinstance(cell, schema.Options):
                    cell = definitions.multiplicity(cell.get("minc", 1), cell.get("maxc", 1))
                    # TODO: More options

                elif column == ("name", "value"):
                    cell = f"**{cell}**"
                tmp_row.append(cell)
            table_md.append_row(tmp_row)

        table_rows = str(table_md).split("\n")
        head = dict(zip([h.strip() for h in table_rows[0].split("|")], table_rows[1].split("|")))
        alignment = [self._alignment.get(headers[k].get("align", "<"))(v)  for k, v in head.items() if k]
        table_rows[1] = f"|{'|'.join(alignment)}|"
        table_md = '\n'.join(table_rows)
        return f"{table_md}\n"
