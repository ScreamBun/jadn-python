from .utils import FrozenDict

# Valid Message Formats for load/dump
MessageFormats = FrozenDict(
    CBOR='cbor',
    JSON='json',
    XML='xml',
    # Proto='proto',
    # Thrift='thrift',
    YAML='yaml'
)

# Valid Schema Formats for conversion
SchemaFormats = FrozenDict(
    CDDL='cddl',
    HTML='html',
    JADN='jadn',
    JAS='jas',
    MarkDown='md',
    Proto='proto',
    Relax='rng',
    Thrift='thrift',
)

# Conversion Comment Level
CommentLevels = FrozenDict(
    ALL='all',
    NONE='none'
)
