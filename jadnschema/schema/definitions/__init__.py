"""
JADN Definition Structures
"""
from typing import Union

from .base import DefinitionBase
from .array import Array
from .arrayOf import ArrayOf
from .choice import Choice
from .enumerated import Enumerated
from .map import Map
from .mapOf import MapOf
from .record import Record
from .custom import CustomDefinition


# Helper Functions
DefinitionData = Union[Array, ArrayOf, Choice, Enumerated, Map, MapOf, Record, CustomDefinition]


def make_definition(data: Union[dict, list, DefinitionData], **kwargs) -> DefinitionData:
    """
    Create a specific definition based on the given data
    :param data: data to create a definition
    :return: created definition
    """
    data = dict(zip(DefinitionBase.__slots__, data)) if isinstance(data, list) else data
    return {
        "Array": Array,
        "ArrayOf": ArrayOf,
        "Choice": Choice,
        "Enumerated": Enumerated,
        "Map": Map,
        "MapOf": MapOf,
        "Record": Record
    }.get(data['type'], CustomDefinition)(data, **kwargs)


__all__ = [
    'DefinitionBase',
    'Array',
    'ArrayOf',
    'Choice',
    'Enumerated',
    'Map',
    'MapOf',
    'Record',
    'CustomDefinition'
]
