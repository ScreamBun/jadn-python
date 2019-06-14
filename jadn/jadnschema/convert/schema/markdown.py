"""
JADN to Markdown tables
"""

from datetime import datetime

from .base_dump import JADNConverterBase

from ...definitions import (
    multiplicity
)


class JADNtoMD(JADNConverterBase):
    def md_dump(self):
        """
        Convert the given JADN schema to MarkDown Tables
        :return: formatted MarkDown tables of the given JADN Schema
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
            return f'| **{k}** | {v} |'

        return '\n'.join([
            '## Schema',
            '| . | . |',
            '| ---: | :--- |',
            *[mkrow(meta, self._meta.get(meta, '')) for meta in self._meta_order]
        ]) + '\n\n'

    # Structure Formats
    def _formatArray(self, itm):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        fmt = f" /{itm.opts.format}" if "format" in itm.opts else ""
        array_md = f"**_Type: {itm.name} (Array{fmt})_**\n\n"
        headers = {
            'ID': {'align': 'r'},
            'Type': {},
            '#': {'align': 'r'},
            'Description': {}
        }
        rows = [{"id": f.id, "type": f.type, "opts": f.opts, "desc": f"{f.name}:: {f.desc}"} for f in itm.fields]

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
        fmt = ".ID" if "id" in itm.opts else ""
        choice_md = f"**_Type: {itm.name} (Choice{fmt})_**\n\n"
        headers = {
            'ID': {'align': 'r'},
            'Name': {},
            'Type': {},
            '#': {'align': 'r'},
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
        fmt = ".ID" if "id" in itm.opts else ""
        enumerated_md = f"**_Type: {itm.name} (Enumerated{fmt})_**\n\n"
        if "id" in itm.opts:
            headers = {
                'ID': {'align': 'r'},
                'Description': {}
            }
            rows = [{"ID": f.id, "Description": f"{f.value}:: {f.desc}"} for f in itm.fields]
        else:
            headers = {
                'ID': {'align': 'r'},
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
        fmt = ".ID" if "id" in itm.opts else ""
        map_md = f"**_Type: {itm.name} (Map{fmt})_**\n\n"
        headers = {
            'ID': {'align': 'r'},
            'Name': {},
            'Type': {},
            '#': {'align': 'r'},
            'Description': {}
        }
        rows = []
        for field in itm.fields:
            row = dict(field)
            if field.type == "MapOf":
                row['type'] += f"({field.opts.get('ktype', 'String')}, {field.opts.get('vtype', 'String')})"
            elif field.type == "ArrayOf":
                row['type'] += f"({field.opts.get('vtype', 'String')})"

            if "format" in field.opts:
                row['type'] += f" /{field.opts.format}"
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
        fmt = f" /{itm.opts.format}" if "format" in itm.opts else ""
        record_md = f"**_Type: {itm['name']} (Record{fmt})_**\n\n"
        headers = {
            'ID': {'align': 'r'},
            'Name': {},
            'Type': {},
            '#': {'align': 'r'},
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
            'Description': itm.desc
        }
        if itm.type == "MapOf":
            row['Type Definition'] += f"({itm.opts.get('ktype', 'String')}, {itm.opts.get('vtype', 'String')})"
        elif itm.type == "ArrayOf":
            row['Type Definition'] += f"({itm.opts.get('vtype', 'String')})"

        if "format" in itm.opts:
            row['Type Definition'] += f" /{itm.opts.format}"

        if any([v in itm.opts.keys() for v in ("minc", "maxc", "minv", "maxv")]):
            multi = ("minc", "maxc") if "minc" in itm.opts else ("minv", "maxv")
            row['Type Definition'] += f" [{multiplicity(itm.opts.get(multi[0], 1), itm.opts.get(multi[1], 1))}]"

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
        table_md = []

        # Headers
        header = []
        header_align = []
        for column, opts in headers.items():
            header.append(column)
            align = opts.get('align', 'left')
            header_align.append('---:' if align.startswith('r') else (':---:' if align.startswith('c') else ':---'))

        table_md.append(f"| {' | '.join(header)} |")
        table_md.append(f"| {' | '.join(header_align)} |")

        # Body
        for row in rows:
            tmp_row = []
            for column, opts in headers.items():
                column = column if column in row else self._table_field_headers.get(column, column)
                if isinstance(column, str):
                    cell = row.get(column, '')
                else:
                    cell = list(filter(None, [row.get(c, None) for c in column]))
                    cell = cell[0] if len(cell) == 1 else ''

                if column == "opts":
                    if isinstance(cell, dict):
                        cell = multiplicity(cell.get("minc", 1), cell.get("maxc", 1))
                        # TODO: More options
                    else:
                        print(cell)

                elif column == ("name", "value"):
                    cell = f"**{cell}**"

                tmp_str = str(cell)
                tmp_row.append(' ' if tmp_str == '' else tmp_str)

            table_md.append(f"| {' | '.join(tmp_row)} |")

        return '\n'.join(table_md) + '\n'


def md_dumps(jadn):
    """
    Produce CDDL schema from JADN schema
    :arg jadn: JADN Schema to convert
    :return: MarkDown Table schema
    """
    return JADNtoMD(jadn).md_dump()


def md_dump(jadn, fname, source=""):
    """
    Produce MarkDown tables from the given JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :param fname: Name of file to write
    :param source: Name of the original JADN schema file
    :return: None
    """
    with open(fname, "w") as f:
        if source:
            f.write(f"<!-- Generated from {source}, {datetime.ctime(datetime.now())} -->\n")
        f.write(md_dumps(jadn))
