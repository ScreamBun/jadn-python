"""
JADN to JSON Schema
"""
import json

from datetime import datetime

from .base_dump import JADNConverterBase

from ... import (
    enums,
    # jadn_utils,
    # utils
)


class JADNtoJSON(JADNConverterBase):
    _fieldMap = {
        'Binary': 'string',
        'Boolean': 'bool',
        'Integer': 'integer',
        'Number': 'number',
        'Null': 'null',
        'String': 'string'
    }

    _validationMap = {
        'b': 'binary',
        "date-time": "date-time",
        "email": "email",
        "hostname": "hostname",
        'ipv4-addr': 'ipv4',  # ipv4
        'ipv6-addr': 'ipv6',  # ipv6
        "json-pointer": "json-pointer",  # Draft 6
        "uri": "uri",
        "uri-reference": "uri-reference",  # Draft 6
        "uri-template": "uri-template",  # Draft 6
        'x': 'binary',
    }

    def json_dump(self, com=None):
        """
        Converts the JADN schema to JSON
        :param com: Level of comments to include in converted schema
        :return: JSON schema
        """
        if com:
            self.comm = com if com in enums.CommentLevels.values() else enums.CommentLevels.ALL

        json_schema = self.makeHeader()
        for struct in self._makeStructures(default={}):
            json_schema.update(struct)

        return json_schema

    def makeHeader(self):
        """
        Create the headers for the schema
        :return: header for schema
        """
        header = {
            "$schema": "http://json-schema.org/draft-07/schema#"
        }
        if 'module' in self._meta:
            header['$id'] = ('' if self._meta['module'].startswith('http') else 'http://') + self._meta['module']

        if 'title' in self._meta:
            header['title'] = self._meta['title']

        if 'description' in self._meta:
            header['description'] = self._meta['description']

        return header

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
        return {
            self.formatStr(itm.name): self._cleanEmpty({})
        }

    def _formatCustom(self, itm):
        """
        Formats custom for the given schema type
        :param itm: custom to format
        :return: formatted custom
        """
        custom_json = dict(
            type=self._fieldMap.get(itm.type, 'string'),
            description=itm.desc,
        )

        return {
            self.formatStr(itm.name): self._cleanEmpty(custom_json)
        }

    # Helper Functions
    def _get_type(self, name):
        pass

    def _cleanEmpty(self, itm):
        if isinstance(itm, dict):
            return dict((k, self._cleanEmpty(v)) for k, v in itm.items() if v or isinstance(v, bool))
        else:
            return itm


def json_dumps(jadn, comm=enums.CommentLevels.ALL):
    """
    Produce JSON schema from JADN schema
    :param jadn: JADN Schema to convert
    :param comm: Level of comments to include in converted schema
    :return: JSON schema
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
    return JADNtoJSON(jadn).json_dump(comm)


def json_dump(jadn, fname, source="", comm=enums.CommentLevels.ALL):
    """
    Produce JSON schema from JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :type jadn: str or dict
    :param fname: Name of file to write
    :tyoe fname: str
    :param source: Name of the original JADN schema file
    :type source: str
    :param comm: Level of comments to include in converted schema
    :type comm: str of enums.CommentLevel
    :return: N/A
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

    with open(fname, "w") as f:
        if source:
            f.write(f"; Generated from {source}, {datetime.ctime(datetime.now())}\n")
        f.write(json.dumps(json_dumps(jadn, comm), indent=2))
