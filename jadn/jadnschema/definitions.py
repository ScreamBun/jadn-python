"""
JADN Definitions
"""
from . import utils


# Meta Ordering
META_ORDER = ('title', 'module', 'patch', 'description', 'exports', 'imports')


# Column Keys
COLUMN_KEYS = utils.FrozenDict(
    # Structures
    Structure=(
        'name',     # 0 - TNAME - Datatype name
        'type',     # 1 - TTYPE - Base type - built-in or defined
        'opts',     # 2 - TOPTS - Type options
        'desc',     # 3 - TDESC - Type description
        'fields'    # 4 - FIELDS - List of fields
    ),
    # Field Definitions
    Enum_Def=(
        'id',       # 0 - FTAG - Element ID
        'value',    # 1 - FNAME - Element name
        'desc'      # 2 - EDESC - Enumerated value description
    ),
    Gen_Def=(
        'id',       # 0 - FTAG - Element ID
        'name',     # 1 - FNAME - Element name
        'type',     # 2 - FTYPE - Datatype of field
        'opts',     # 3 - FOPTS - Field options
        'desc'      # 4 - FDESC - Field Description
    )
)

# Types
JADN_TYPES = utils.FrozenDict(
    PRIMITIVES=(
        'Binary',       # A sequence of octets. Length is the number of octets
        'Boolean',      # An element with one of two values: true or false
        'Integer',      # A positive or negative whole number
        'Number',       # A real number
        'Null',         # An unspecified or non-existent value
        'String'        # A sequence of characters, each of which has a Unicode codepoint. Length is the number of characters
    ),
    STRUCTURES=(
        'Array',        # An ordered list of labeled fields with positionally-defined semantics. Each field has a position, label, and type
        'ArrayOf',      # An ordered list of fields with the same semantics. Each field has a position and type vtype
        'Choice',       # One key and value selected from a set of named or labeled fields. The key has an id and name or label, and is mapped to a type
        'Enumerated',   # One value selected from a set of named or labeled integers
        'Map',          # An unordered map from a set of specified keys to values with semantics bound to each key. Each key has an id and name or label, and is mapped to a type
        'MapOf',        # An unordered map from a set of keys to values with the same semantics. Each key has key type ktype, and is mapped to value type vtype. Represents a map with keys that are either enumerated or are members of a well-defined category
        'Record'        # An ordered map from a list of keys with positions to values with positionally-defined semantics. Each key has a position and name, and is mapped to a type. Represents a row in a spreadsheet or database table
    )
)


# Valid Formats
FORMATS = utils.FrozenDict(
    SEMANTIC=utils.FrozenDict({
        # JSON Formats
        'date-time': str,               # RFC 3339 Section 5.6
        'date': str,                    # RFC 3339 Section 5.6
        'time': str,                    # RFC 3339 Section 5.6
        'email': str,                   # RFC 5322 Section 3.4.1
        'idn-email': str,               # RFC 6531, or email
        'hostname': str,                # RFC 1034 Section 3.1
        'idn-hostname': str,            # RFC 5890 Section 2.3.2.3, or hostname
        'ipv4': str,                    # RFC 2673 Section 3.2 "dotted-quad"
        'ipv6': str,                    # RFC 4291 Section 2.2 "IPv6 address"
        'uri': str,                     # RFC 3986
        'uri-reference': str,           # RFC 3986, or uri
        'iri': str,                     # RFC 3987
        'iri-reference': str,           # RFC 3987
        'uri-template': str,            # RFC 6570
        'json-pointer': str,            # RFC 6901 Section 5
        'relative-json-pointer': str,   # JSONP
        'regex': str,                   # ECMA 262
        # JADN Formats
        'eui': bin,                     # IEEE Extended Unique Identifier (MAC Address), EUI-48 or EUI-64 as specified in EUI
        'ipv4-addr': bin,               # IPv4 address as specified in RFC 791 Section 3.1
        'ipv6-addr': bin,               # IPv6 address as specified in RFC 8200 Section 3
        'ipv4-net': list,               # Binary IPv4 address and Integer prefix length as specified in RFC 4632 Section 3.1
        'ipv6-net': list,               # Binary IPv6 address and Integer prefix length as specified in RFC 4291 Section 2.3
        'i8': int,                      # Signed 8 bit integer, value must be between -128 and 127
        'i16': int,                     # Signed 16 bit integer, value must be between -32768 and 32767.
        'i32': int,                     # Signed 32 bit integer, value must be between ... and ...
        r'^u\d$': int,                  # Unsigned integer or bit field of <n> bits, value must be between 0 and 2^<n> - 1
    }),
    SERIALIZE=utils.FrozenDict(),
)

# Options
TYPE_CONFIG = dict(
    OPTIONS={
        # Structural
        '=': ('id', bool),      # If present, Enumerated values and fields of compound types are denoted by FieldID rather than FieldName
        '*': ('vtype', str),    # Value type for ArrayOf and MapOf
        '+': ('ktype', str),    # Key type for MapOf
        '$': ('enum', str),     # Enumerated type derived from the specified Array, Choice, Map or Record type
        # Validation
        '/': ('format', str),   # Semantic validation keyword
        '%': ('pattern', str),  # Regular expression used to validate a String type
        '{': ('minv', int),     # Minimum numeric value, octet or character count, or element count
        '}': ('maxv', int),     # Maximum numeric value, octet or character count, or element count
        '!': ('default', str),  # Default value for an instance of this type
    },
    SUPPORTED_OPTIONS=dict(
        # Primitives
        Binary=('minv', 'maxv', 'format'),
        Boolean=(),
        Integer=('minv', 'maxv', 'format'),
        Number=('minv', 'maxv', 'format'),
        Null=(),
        String=('minv', 'maxv', 'format', 'pattern'),
        # Structures
        Array=('minv', 'maxv', 'format'),
        ArrayOf=('minv', 'maxv', 'vtype'),
        Choice=('id', ),
        Enumerated=('id', 'enum'),
        Map=('id', 'minv', 'maxv'),
        MapOf=('ktype', 'minv', 'maxv', 'vtype'),
        Record=('minv', 'maxv')
    )
)
TYPE_CONFIG["D2S"] = {v[0]: (k, v[1]) for k, v in TYPE_CONFIG["OPTIONS"].items()}


TYPE_CONFIG = utils.toFrozen(TYPE_CONFIG)

"""
minc    maxc	Multiplicity	Description	                                Keywords
0	    1	    0..1	        No instances or one instance	            optional
1	    1	    1	            Exactly one instance	                    required
0	    0	    0..*	        Zero or more instances	                    optional, repeated
1	    0	    1..*	        At least one instance	                    required, repeated
m	    n	    m..n	        At least m but no more than n instances     required, repeated if m > 1
"""
FIELD_CONFIG = dict(
    OPTIONS={
        # Structural
        '[': ('minc', int),         # Minimum cardinality
        ']': ('maxc', int),         # Maximum cardinality
        '&': ('tfield', str),       # Field that specifies the type of this field
        '<': ('flatten', bool),     # Use FieldName as a qualifier for fields in FieldType
    }
)
FIELD_CONFIG["D2S"] = {v[0]: (k, v[1]) for k, v in FIELD_CONFIG["OPTIONS"].items()}

FIELD_CONFIG = utils.toFrozen(FIELD_CONFIG)


# Definition Utilities
def is_builtin(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin type
    :param vtype: Type
    :return: is builtin type
    """
    return vtype in JADN_TYPES.PRIMITIVES + JADN_TYPES.STRUCTURES


def is_primitive(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin primitive
    :param vtype: Type
    :return: is builtin primitive
    """
    return vtype in JADN_TYPES.PRIMITIVES


def is_structure(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin structure
    :param vtype: Type
    :return: is builtin structure
    """
    return vtype in JADN_TYPES.STRUCTURES


def is_compound(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin compound (has defined fields)
    :param vtype: Type
    :return: is builtin compound
    """
    return vtype in ('Array', 'Choice', 'Enumerated', 'Map', 'Record')


def column_index(col_type: str, col_name: str) -> int:
    """
    Get the index of hte column given the type and column name
    :param col_type: type of builtin - (Structure, Gen_Def, Enum_Def)
    :param col_name: name of column
    :return: index number of the column
    """
    if col_type not in COLUMN_KEYS:
        raise KeyError(f"{col_type} is not a valid column type")

    columns = COLUMN_KEYS[col_type]
    if col_name not in columns:
        raise KeyError(f"{col_name} is not a valid column for {col_type}")

    return columns.index(col_name)


def basetype(tt: str) -> str:
    """
    Return base type of derived subtypes
    :param tt: Type of structure/field
    :return: base type
    """
    return tt.rsplit(".")[0]  # Strip off subtype (e.g., .ID)


def multiplicity(minimum: int, maximum: int) -> str:
    if minimum == 1 and maximum == 1:
        return "1"
    return f"{minimum}..{'*' if maximum == 0 else maximum}"
