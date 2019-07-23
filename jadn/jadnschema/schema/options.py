"""
JADN Field/Type Options
"""
from typeguard import check_type
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union
)

from .base import BaseModel
from .exceptions import OptionError


class Options(BaseModel):
    # Type Structural
    id: bool
    vtype: str
    ktype: str
    enum: str
    # Type Validation
    format: str
    pattern: str
    minv: int
    maxv: int
    # Field
    minc: int
    maxc: int
    tfield: str  # Enumerated
    flatten: bool
    default: str

    __slots__ = ("id", "ktype", "vtype", "enum", "format", "pattern", "minv", "maxv", "minc", "maxc", "tfield", "flatten", "default")

    _fieldOpts: Tuple[str] = ("minc", "maxc", "tfield", "flatten", "default")

    _boolOpts: Tuple[str] = ("id", "flatten")

    _ids: Dict[str, str] = {
        # Type Structural
        "=": "id",          # If present, Enumerated values and fields of compound types are denoted by FieldID rather than FieldName
        "+": "ktype",       # Key type for MapOf
        "*": "vtype",       # Value type for ArrayOf and MapOf
        "$": "enum",        # Enumerated type derived from the specified Array, Choice, Map or Record type
        # Type Validation
        "/": "format",      # Semantic validation keyword
        "%": "pattern",     # Regular expression used to validate a String type
        "{": "minv",        # Minimum numeric value, octet or character count, or element count
        "}": "maxv",        # Maximum numeric value, octet or character count, or element count
        # Field Structural
        "[": "minc",        # Minimum cardinality
        "]": "maxc",        # Maximum cardinality
        "&": "tfield",      # Field that specifies the type of this field, value is Enumerated
        "<": "flatten",     # Use FieldName as a qualifier for fields in FieldType
        "!": "default",     # Reserved for default value Section 3.2.2.4
    }

    _validFormats: List[str] = [
        # JSON Formats
        'date-time',                # RFC 3339 Section 5.6
        'date',                     # RFC 3339 Section 5.6
        'time',                     # RFC 3339 Section 5.6
        'email',                    # RFC 5322 Section 3.4.1
        'idn-email',                # RFC 6531, or email
        'hostname',                 # RFC 1034 Section 3.1
        'idn-hostname',             # RFC 5890 Section 2.3.2.3, or hostname
        'ipv4',                     # RFC 2673 Section 3.2 "dotted-quad"
        'ipv6',                     # RFC 4291 Section 2.2 "IPv6 address"
        'uri',                      # RFC 3986
        'uri-reference',            # RFC 3986, or uri
        'iri',                      # RFC 3987
        'iri-reference',            # RFC 3987
        'uri-template',             # RFC 6570
        'json-pointer',             # RFC 6901 Section 5
        'relative-json-pointer',    # JSONP
        'regex',                    # ECMA 262
        # JADN Formats
        'eui',                      # IEEE Extended Unique Identifier (MAC Address), EUI-48 or EUI-64 as specified in EUI
        'ipv4-addr',                # IPv4 address as specified in RFC 791 Section 3.1
        'ipv6-addr',                # IPv6 address as specified in RFC 8200 Section 3
        'ipv4-net',                 # Binary IPv4 address and Integer prefix length as specified in RFC 4632 Section 3.1
        'ipv6-net',                 # Binary IPv6 address and Integer prefix length as specified in RFC 4291 Section 2.3
        'i8',                       # Signed 8 bit integer, value must be between -128 and 127
        'i16',                      # Signed 16 bit integer, value must be between -32768 and 32767.
        'i32',                      # Signed 32 bit integer, value must be between ... and ...
        r'^u\d+$',                  # Unsigned integer or bit field of <n> bits, value must be between 0 and 2^<n> - 1
        # Serialization
        'x',                        # Binary - JSON string containing Base16 (hex) encoding of a binary value as defined in RFC 4648 Section 8. Note that the Base16 alphabet does not include lower-case letters.
        'ipv4-addr',                # Binary - JSON string containing a "dotted-quad" as specified in RFC 2673 Section 3.2.
        'ipv6-addr',                # Binary - JSON string containing the text representation of an IPv6 address as specified in RFC 4291 Section 2.2.
        'ipv4-net',                 # Array - JSON string containing the text representation of an IPv4 address range as specified in RFC 4632 Section 3.1.
        'ipv6-net'                  # Array - JSON string containing the text representation of an IPv6 address range as specified in RFC 4291 Section 2.3.'
    ]

    _validOptions: Dict[str, Tuple[str]] = {
        # Primitives
        "Binary": ("format", "minv", "maxv"),
        "Boolean": (),
        "Integer": ("format", "minv", "maxv"),
        "Number": ("format", "minv", "maxv"),
        "Null": (),
        "String": ("format", "minv", "maxv", "pattern"),
        # Structures
        "Array": ("format", "minv", "maxv"),
        "ArrayOf": ("minv", "maxv", "vtype"),
        "Choice": ("id", ),
        "Enumerated": ("id", "enum"),
        "Map": ("id", "minv", "maxv"),
        "MapOf": ("ktype", "minv", "maxv", "vtype"),
        "Record": ("minv", "maxv")
    }

    def __init__(self, data: Union[dict, list, "Options"] = None, **kwargs):
        if isinstance(data, list):
            tmp = {}
            for o in data:
                opt = self._ids.get(o[0], None)
                if opt:
                    inst = self.__annotations__.get(opt)
                    val = safe_cast(o[1:], inst)
                    check_type(opt, val, inst)
                    tmp[opt] = True if inst == bool else val
            data = tmp

        super(Options, self).__init__(data, **kwargs)

    def schema(self,  basetype: str, defname: str = None, field: bool = False) -> list:
        """
        Format the options into valid JADN format
        :return: JADN formatted options
        """
        self.verify(basetype, defname, field)
        ids = {v: k for k, v in self._ids.items()}
        rtn = []
        for opt in self.__slots__:
            val = getattr(self, opt, None)
            if val is not None:
                rtn.append(f"{ids.get(opt)}{'' if opt in self._boolOpts else val}")

        return rtn

    def verify(self, basetype: str, defname: str = None, field: bool = False, silent: bool = False) -> Optional[List[Exception]]:
        """
        Verify the definitions are proper based on the basetype and field status
        :param basetype: base type to validate options against
        :param defname: name of definition/field to use in error message
        :param field: bool - options are field/type options
        :param silent: bool - raise or return errors
        :return: OPTIONAL(list of errors)
        """
        errors = []
        valid_opts = (*self._validOptions.get(basetype, ()), *(self._fieldOpts if field else ()))
        opts = {o: getattr(self, o) for o in self.__slots__ if hasattr(self, o)}
        keys = {*opts.keys()} - {*valid_opts}
        loc = f"{defname}({basetype})" if defname else basetype

        if len(keys) > 0:
            errors.append(OptionError(f"Extra options given for {loc} - {', '.join(keys)}"))
        elif basetype == "ArrayOf":
            keys = {"vtype"} - {*opts.keys()}
            if len(keys) != 0:
                errors.append(OptionError(f"ArrayOf {loc} requires options: vtype"))
        elif basetype == "MapOf":
            keys = {"vtype", "ktype"} - {*opts.keys()}
            if len(keys) != 0:
                errors.append(OptionError(f"MapOf {loc} requires options: vtype and ktype"))

        values = ("minc", "maxc") if field else ("minv", "maxv")
        minimum = getattr(self, values[0], 1)
        maximum = getattr(self, values[1], max(1, minimum))

        if maximum != 0 and maximum < minimum:
            errors.append(OptionError(f"{values[1]} cannot be less than {values[0]}"))

        fmt = opts.get("format")
        if fmt and fmt not in self._validFormats:
            errors.append(OptionError(f"{basetype} {loc} specified unknown format {fmt}"))

        errors = list(filter(None, errors))
        if len(errors) > 0:
            if silent:
                return errors
            else:
                raise errors[0]

    def multiplicity(self, min_default: int = 0, max_default: int = 0, field: bool = False, check: Callable[[int, int], bool] = lambda x, y: True) -> str:
        """
        Determine the multiplicity of the min/max options
        :param min_default: default value of minc/minv
        :param max_default: default value of maxc/maxv
        :param field: if option for field or type
        :param check: function for ignoring multiplicity - Fun(minimum, maximum) -> bool
        :return: options multiplicity or empty string
        """
        """
        minc    maxc	Multiplicity	Description	                                Keywords
        0	    1	    0..1	        No instances or one instance	            optional
        1	    1	    1	            Exactly one instance	                    required
        0	    0	    0..*	        Zero or more instances	                    optional, repeated
        1	    0	    1..*	        At least one instance	                    required, repeated
        m	    n	    m..n	        At least m but no more than n instances     required, repeated if m > 1
        """
        values = ("minc", "maxc") if field else ("minv", "maxv")
        minimum = getattr(self, values[0], min_default)
        maximum = getattr(self, values[1], max_default)
        if check(minimum, maximum):
            if minimum == 1 and maximum == 1:
                return "1"
            return f"{minimum}..{'*' if maximum == 0 else maximum}"
        return ""


# Helper Functions
def safe_cast(val: Any, to_type: Type, default: Any = None) -> Any:
    """
    Cast the given value to the goven type safely without an exception being thrown
    :param val: value to cast
    :param to_type: type to cast as
    :param default: default value if casting fails
    :return: casted value or given default/None
    """
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default
