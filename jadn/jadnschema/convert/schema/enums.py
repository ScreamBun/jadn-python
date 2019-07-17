from ...utils import FrozenDict

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
