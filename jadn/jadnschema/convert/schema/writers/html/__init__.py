"""
JADN to JADN IDL
"""
import json
import lesscpy
import os
import re

from datetime import datetime

from ... import WriterBase

from ..... import (
    definitions,
    schema
)


class JADNtoHTML(WriterBase):
    format = "html"

    _themeFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "theme.css")  # Default theme

    def dump(self, fname, source=None, comm=None, styles=None) -> None:
        """
        Produce JSON schema from JADN schema and write to file provided
        :param fname: Name of file to write
        :param styles: CSS or Less styles to add to the HTML
        :param source: Name of the original schema file
        :param comm: Level of comments to include in converted schema, ignored
        :return: None
        """
        with open(fname, "w") as f:
            if source:
                f.write(f"<!-- Generated from {source}, {datetime.ctime(datetime.now())} -->\n")
            f.write(self.dumps())

    def dumps(self, comm=None, styles=None) -> str:
        """
        Converts the JADN schema to HTML
        :param styles: CSS or Less styles to add to the HTML
        :param comm: Level of comments to include in converted schema, ignored
        :return: JSON schema
        """
        html = f"""<!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>{self._meta.get("module", "JADN Schema Convert")} v.{self._meta.get("version", "0.0")}</title>
                    <style type="text/css">{self._loadStyles(styles)}</style>
                </head>
                <body>
                    <div id="schema">
                        <h1>Schema</h1>
                        <div id="meta">{self.makeHeader()}</div>
                        <div id="types">
                            {"".join(self.makeStructures())}
                        </div>
                    </div>
                </body>
            </html>"""

        return self._format_html(html)

    def makeHeader(self):
        """
        Create the headers for the schema
        :return: header for schema
        """
        def mkrow(k, v):
            if type(v) is list:
                v = ", ".join(["**{}**: {}".format(*i) for i in v] if type(v[0]) is list else v) if len(v) > 0 else "N/A"
            return f"<tr><td class='h'>{k}:</td><td class='s'>{v}</td></tr>"

        meta_rows = "".join([mkrow(meta, self._meta.get(meta, "")) for meta in self._meta_order])
        return f"<table>{meta_rows}</table>"

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        """
        structure_html = "<h2>3.2 Structure Types</h2>"
        primitives = []

        for i, t in enumerate(self._types):
            if definitions.is_structure(t.type):
                structure_html += getattr(self, f"_format{t.type}", lambda *a: "<h1>OOPS</h1>")(t, i+1)
            else:
                primitives.append(t)

        rows = []
        for prim in primitives:
            fmt = f" ({prim.options.format})" if "format" in prim.options else ""
            minimum = prim.options.get("minv", 0)
            maximum = prim.options.get("maxv", 0)
            count = f" [{definitions.multiplicity(minimum, maximum)}]" if minimum > 0 or maximum > 0 else ""
            rows.append({
                **prim.dict(),
                "type": f"{prim.type}{fmt}{count}",
            })

        primitives_table = self._makeTable(
            headers=dict(
                Name={"class": "s"},
                Type={"class": "s"},
                Description={"class": "s"}
            ),
            rows=rows
        )

        primitive_html = f"<h2>3.3 Primitive Types</h2>{primitives_table}"
        return structure_html + primitive_html

    # Structure Formats
    def _formatArray(self, itm, idx):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        desc = "" if itm.description == "" else f"<h4>{itm.description}</h4>"
        array_html = f"<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>{desc}"

        array_table = self._makeTable(
            headers={
                "ID": {"class": "n"},
                "Type": {"class": "s"},
                "#": {"class": "n"},
                "Description": {"class": "s"},
            },
            rows=[{**row.dict(), 'Description': f'"{row.name}": {row.description}'} for row in itm.fields],
            caption=f"{self.formatStr(itm.name)} (Array)"
        )

        return array_html + array_table

    def _formatArrayOf(self, itm, idx):
        """
        Formats arrayOf for the given schema type
        :param itm: arrayOf to format
        :return: formatted arrayOf
        """
        desc = "" if itm.description == "" else f'<h4>{itm.description}</h4>'
        arrayOf_html = f"<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>{desc}"

        value_type = self.formatStr(itm.options.get('vtype', 'string'))
        value_count = definitions.multiplicity(itm.options.get("minv", 0), itm.options.get("maxv", 0))

        options = f"<p>{self.formatStr(itm.name)} (ArrayOf({value_type})[{value_count}])</p>"

        arrayOf_html += options
        return arrayOf_html

    def _formatChoice(self, itm, idx):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        desc = "" if itm.description == "" else f"<h4>{itm.description}</h4>"
        choice_html = f"<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>{desc}"

        choice_table = self._makeTable(
            headers={
                "ID": {"class": "n"},
                "Name": {"class": "s"},
                "Type": {"class": "s"},
                "Description": {"class": "s"},
            },
            rows=itm.fields,
            caption=f"{self.formatStr(itm.name)} (Choice{f' {json.dumps(itm.options.dict())}' if itm.options.dict().keys() else ''})"
        )

        return choice_html + choice_table

    def _formatEnumerated(self, itm, idx):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        desc = "" if itm.description == "" else f"<h4>{itm.description}</h4>"
        enum_html = f"<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>{desc}"

        if "id" in itm.options:
            headers = {"Value": {'class': 'n'}}
            rows = [{"Value": row.id, "Description": f"{row.value} -- {row.description}"} for row in itm.fields]

        else:
            headers = {"ID": {"class": "n"}, "Name": {"class": "s"}}
            rows = itm.fields

        headers["Description"] = {"class": "s"}
        enum_table = self._makeTable(
            headers=headers,
            rows=rows,
            caption=f"{self.formatStr(itm.name)} (Enumerated{'.ID' if 'id' in itm.options else ''})"
        )

        return enum_html + enum_table

    def _formatMap(self, itm, idx):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        desc = "" if itm.description == "" else f"<h4>{itm.description}</h4>"
        map_html = f"<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>{desc}"

        map_table = self._makeTable(
            headers={
                "ID": {"class": "n"},
                "Name": {"class": "s"},
                "Type": {"class": "s"},
                "#": {"class": "n"},
                "Description": {"class": "s"},
            },
            rows=itm.fields,
            caption=f"{self.formatStr(itm.name)} (Map{f' {json.dumps(itm.options.dict())}' if itm.options.dict().keys() else ''})"
        )

        return map_html + map_table

    def _formatMapOf(self, itm, idx):
        """
        Formats mapOf for the given schema type
        :param itm: mapOf to format
        :return: formatted mapOf
        """
        desc = "" if itm.description == "" else f'<h4>{itm.description}</h4>'
        mapOf_html = f"<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>{desc}"

        key_type = self.formatStr(itm.options.get('ktype', 'string'))
        value_type = self.formatStr(itm.options.get('vtype', 'string'))
        value_count = definitions.multiplicity(itm.options.get("minv", 0), itm.options.get("maxv", 0))

        options = f"<p>{self.formatStr(itm.name)} (MapOf({key_type}, {value_type})[{value_count}])</p>"

        mapOf_html += options
        return mapOf_html

    def _formatRecord(self, itm, idx):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        desc = "" if itm.description == "" else f"<h4>{itm.description}</h4>"
        record_html = f"<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>{desc}"

        record_table = self._makeTable(
            headers={
                "ID": {"class": "n"},
                "Name": {"class": "s"},
                "Type": {"class": "s"},
                "#": {"class": "n"},
                "Description": {"class": "s"},
            },
            rows=itm.fields,
            caption=f"{self.formatStr(itm.name)} (Record)"
        )

        return record_html + record_table

    # Helper Functions
    def _format_html(self, html):
        """
        Format the HTML to a predefined standard
        :param html: HTML string to format
        :return: formatted HTML
        """
        html = "".join(l.strip() for l in html.split("\n"))
        html_formatted = ""
        nested_tags = []

        tmp_format = []
        for elm in html.split("><"):
            elm = "<" + elm if not elm.startswith("<") else elm
            elm = elm + ">" if not elm.endswith(">") else elm
            tmp_format.append(elm)

        i = 0
        while i < len(tmp_format):
            line = tmp_format[i].strip()
            tag = re.sub(r"\s*?<\/?(?P<tag>[\w]+)(\s|>).*$", "\g<tag>", str(line))
            indent = "\t" * len(nested_tags)

            if tag == "style":
                styles = line[line.index(">")+1:line.rindex("<")]
                styles_formatted = self._format_css(styles)
                if styles_formatted == "":
                    html_formatted += f"{indent}{line}</style>\n"
                    i += 1
                else:
                    styles_indent = "\t" * (len(nested_tags) + 1)
                    styles = re.sub(r"^(?P<start>.)", f"{styles_indent}\g<start>", str(styles_formatted), flags=re.M)
                    html_formatted += f"{indent}{line[:line.index('>')+1]}\n{styles}\n{indent}{line[line.rindex('<'):]}\n"

            elif re.match(rf"^<{tag}.*?<\/{tag}>$", str(line)):
                html_formatted += f"{indent}{line}\n"

            elif line.startswith("<!") or line.endswith("/>"):
                html_formatted += f"{indent}{line}\n"

            elif line.endswith("</" + (nested_tags[-1] if len(nested_tags) > 0 else "") + ">"):
                nested_tags.pop()
                indent = "\t" * len(nested_tags)
                html_formatted += f"{indent}{line}\n"

            else:
                html_formatted += f"{indent}{line}\n"
                if not line.endswith(f"{tag}/>"):
                    nested_tags.append(tag)
            i += 1

        return html_formatted

    def _format_css(self, css):
        """
        Format the CSS to a predefined standard
        :param css: CSS string to format
        :return: formatted CSS
        """
        line_breaks = ("\*/", "{", "}", ";")
        css_formatted = re.sub(rf"(?P<term>{'|'.join(line_breaks)})", "\g<term>\n", css)
        css_formatted = css_formatted[:-1]

        return "\n".join(re.sub(r"\s{4}", "\t", line) for line in css_formatted.split("\n"))

    def _loadStyles(self, styles):
        """
        Load the given styles
        :param styles: the CSS or Less file location
        :return:
        """
        if styles in ["", " ", None]:  # Check if theme exists
            return open(self._themeFile, "r").read() if os.path.isfile(self._themeFile) else ""

        fname, ext = os.path.splitext(styles)
        if ext not in [".css", ".less"]:  # Check valid theme format
            raise TypeError("Styles are not in css or less format")

        if os.path.isfile(styles):
            if ext == ".css":
                return open(styles, "r").read()
            elif ext == ".less":
                return lesscpy.compile(open(styles, "r"))
            else:
                raise ValueError("The style format specified is an unknown format")
        else:
            raise IOError(f"The style file specified does not exist: {styles}")

    def _makeTable(self, headers={}, rows=[], caption=""):
        """
        Create a table using the given header and row values
        :param headers: table header names and attributes
        :param rows: row values
        :return: formatted HTML table
        """
        table_contents = []

        # Caption
        if caption not in ["", " ", None]:
            table_contents.append(f"<caption>{caption}</caption>")

        # Headers
        column_headers = []
        for column, opts in headers.items():
            attrs = " ".join(f"{arg}='{val}'" for arg, val in opts.items())
            column_headers.append(f"<th {attrs}>{column}</th>")

        table_contents.append(f"<thead><tr>{''.join(column_headers)}</tr></thead>")

        # Body
        table_body = []
        for row in rows:
            field_row = ""
            for column, opts in headers.items():
                has_column = column in row if isinstance(row, dict) else hasattr(row, column)
                column = column if has_column else self._table_field_headers.get(column, column)

                if isinstance(column, str):
                    cell = row.get(column, "")
                else:
                    cell = list(filter(None, [row.get(c, None) for c in column]))
                    cell = cell[0] if len(cell) == 1 else ""

                if column == "options" and isinstance(cell, schema.Options):
                    cell_val = definitions.multiplicity(cell.get("minc", 1), cell.get("maxc", 1))

                else:
                    tmp_str = str(cell)
                    cell_val = " " if tmp_str == "" else tmp_str

                attrs = " ".join(f"{arg}='{val}'" for arg, val in headers.get(column, {}).items())
                field_row += f"<td {attrs}>{cell_val}</td>"

            table_body.append(f"<tr>{field_row}</tr>")
        table_contents.append(f"<tbody>{''.join(table_body)}</tbody>")

        table_contents = "".join(table_contents)
        return f"<table>{table_contents}</table>"
