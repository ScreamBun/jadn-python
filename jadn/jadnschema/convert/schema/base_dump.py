"""
Base JADN Schema Converter
"""
import json
import os
import re

from typing import Callable, Union

from ... import (
    enums,
    definitions,
    jadn,
    utils
)


class JADNConverterBase(object):
    """
    Base JADN Converter
    """
    _indent = ' ' * 4

    _escape_chars = ('-', ' ')

    _meta_order = definitions.META_ORDER

    _space_start = re.compile(r"^\s+", re.MULTILINE)

    _table_field_headers = utils.FrozenDict({
        '#': 'opts',
        'Description': 'desc',
        'ID': 'id',
        'Name': ('name', 'value'),
        'Type': 'type',
        'Value': 'value'
    })

    def __init__(self, schema: Union[dict, str], comm=enums.CommentLevels.ALL):
        """
        Schema Converter Init
        :param schema: str or dict of the JADN schema
        :param comm: Comment level
        """
        if isinstance(schema, str):
            if os.path.isfile(schema):
                with open(schema, 'rb') as f:
                    schema = json.load(f)
            else:
                schema = json.loads(schema)
        elif isinstance(schema, dict):
            pass
        else:
            raise TypeError('JADN improperly formatted')

        schema = utils.toFrozen(jadn.jadn_idx2key(schema, True))
        self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        self._meta = schema.get('meta', {})
        self._types = []
        self._custom = []
        self._customFields = {}

        for type_def in schema.get('types', []):
            self._customFields[type_def.name] = type_def.type
            self._types.append(type_def)

    def _makeStructures(self, default=None):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype list
        """
        structs = []
        for t in self._types:
            df = getattr(self, f"_format{t.type if definitions.is_structure(t.type) else 'Custom'}", None)
            structs.append(df(t) if df else default)

        return structs

    # Helper Functions
    def formatStr(self, s: str) -> str:
        """
        Formats the string for use in schema
        :param s: string to format
        :return: formatted string
        """
        escape_chars = list(filter(None, self._escape_chars))
        if s == '*':
            return 'unknown'
        elif len(escape_chars) > 0:
            return re.compile(rf"[{''.join(escape_chars)}]").sub('_', s)
        else:
            return s

    def _is_optional(self, opts: dict) -> bool:
        """
        Check if the field is optional
        :param opts: field options
        :return: bool - optional
        """
        return opts.get('minc', 1) == 0

    def _is_array(self, opts: dict) -> bool:
        """
        Check if the field is an array
        :param opts: field options
        :return: bool - optional
        """
        if 'ktype' in opts or 'vtype' in opts:
            return False

        return opts.get('maxc', 1) != 1
