"""
JADN Field/Type Options
"""
import re

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

from . import base
from .. import exceptions


class Options(base.BaseModel):
    # Type Structural
    enum: str
    id: bool
    vtype: str
    ktype: str
    # Type Validation
    format: str
    minv: int
    maxv: int
    pattern: str
    unique: bool
    # Field
    default: str
    path: bool
    minc: int
    maxc: int
    tfield: str  # Enumerated

    # Helper Vars
    _options: Dict[str, List[str]] = {
        "field": (
            "default",
            "minc",
            "maxc",
            "path",
            "tfield"
        ),
        "type": (
            # Structural
            "enum",
            "id",
            "ktype",
            "vtype",
            # Validation
            "format",
            "pattern",
            "minv",
            "maxv",
            "unique"
        )
    }
    _boolOpts: Tuple[str] = ("id", "path", "unique")
    _ids: Dict[str, str] = {
        # Field Structural
        "!": "default",     # Reserved for default value § 3.2.2.4
        "<": "path",        # Use FieldName as a qualifier for fields in FieldType
        "[": "minc",        # Minimum cardinality
        "]": "maxc",        # Maximum cardinality
        "&": "tfield",      # Field that specifies the type of this field, value is Enumerated
        # Type Structural
        "#": "enum",        # Enumerated type derived from the specified Array, Choice, Map or Record type
        "=": "id",          # Optional-Enumerated values and fields of compound types denoted by FieldID rather than FieldName
        "+": "ktype",       # Key type for MapOf
        "*": "vtype",       # Value type for ArrayOf and MapOf
        # Type Validation
        "/": "format",      # Semantic validation keyword
        "{": "minv",        # Minimum numeric value, octet or character count, or element count
        "}": "maxv",        # Maximum numeric value, octet or character count, or element count
        "%": "pattern",     # Regular expression used to validate a String type
        "q": "unique",      # If present, an ArrayOf instance must not contain duplicate values
    }
    enum_id = [*_ids.keys()][[*_ids.values()].index("enum")]
    _validFormats: List[str] = [
        # JSON Formats
        "date-time",              # RFC 3339 § 5.6
        "date",                   # RFC 3339 § 5.6
        "time",                   # RFC 3339 § 5.6
        "email",                  # RFC 5322 § 3.4.1
        "idn-email",              # RFC 6531, or email
        "hostname",               # RFC 1034 § 3.1
        "idn-hostname",           # RFC 5890 § 2.3.2.3, or hostname
        "ipv4",                   # RFC 2673 § 3.2 "dotted-quad"
        "ipv6",                   # RFC 4291 § 2.2 "IPv6 address"
        "uri",                    # RFC 3986
        "uri-reference",          # RFC 3986, or uri
        "iri",                    # RFC 3987
        "iri-reference",          # RFC 3987
        "uri-template",           # RFC 6570
        "json-pointer",           # RFC 6901 § 5
        "relative-json-pointer",  # JSONP
        "regex",                  # ECMA 262
        # JADN Formats
        "eui",        # IEEE Extended Unique Identifier (MAC Address), EUI-48 or EUI-64 specified in EUI
        "ipv4-addr",  # IPv4 address as specified in RFC 791 § 3.1
        "ipv6-addr",  # IPv6 address as specified in RFC 8200 § 3
        "ipv4-net",   # Binary IPv4 address and Integer prefix length as specified in RFC 4632 §3.1
        "ipv6-net",   # Binary IPv6 address and Integer prefix length as specified in RFC 4291 §2.3
        "i8",         # Signed 8 bit integer, value must be between -128 and 127
        "i16",        # Signed 16 bit integer, value must be between -32768 and 32767.
        "i32",        # Signed 32 bit integer, value must be between ... and ...
        r"u\d+",      # Unsigned integer or bit field of <n> bits, value must be between 0 and 2^<n> - 1
        # Serialization
        "x",          # Binary-JSON string containing Base16 (hex) encoding of a binary value as defined in RFC 4648 § 8
        "ipv4-addr",  # Binary-JSON string containing a "dotted-quad" as specified in RFC 2673 § 3.2.
        "ipv6-addr",  # Binary-JSON string containing text representation of IPv6 address specified in RFC 4291 § 2.2
        "ipv4-net",   # Array-JSON string containing text representation of IPv4 address range specified in RFC 4632 § 3.1
        "ipv6-net"    # Array-JSON string containing text representation of IPv6 address range specified in RFC 4291 § 2.3
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
        "ArrayOf": ("minv", "maxv", "vtype", "unique"),
        "Choice": ("id", "path"),
        "Enumerated": ("id", "enum", "path"),
        "Map": ("id", "minv", "maxv", "path"),
        "MapOf": ("ktype", "minv", "maxv", "vtype"),
        "Record": ("minv", "maxv", "path")
    }

    __slots__ = tuple(o for ot in _options.values() for o in ot)

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

    def __setattr__(self, key, val):
        if key in ("ktype", "vtype") and val:
            enum = re.match(r"^[eE]num\((?P<type>[^)]*)\)$", val)
            val = f"${enum.groupdict()['type']}" if enum else val
        super.__setattr__(self, key, val)

    def schema(self, basetype: str, defname: str = None, field: bool = False) -> list:
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
                val = val.replace("_Enum-", self.enum_id) if opt == "vtype" and val.startswith("_Enum") else val
                rtn.append(f"{ids.get(opt)}{'' if opt in self._boolOpts else val}")

        return rtn

    def verify(self, basetype: str, defname: str = None, field: bool = False,
               silent: bool = False) -> Optional[List[Exception]]:
        """
        Verify the definitions are proper based on the basetype and field status
        :param basetype: base type to validate options against
        :param defname: name of definition/field to use in error message
        :param field: bool - options are field/type options
        :param silent: bool - raise or return errors
        :return: OPTIONAL(list of errors)
        """
        errors = []
        valid_opts = (*self._validOptions.get(basetype, ()), *(self._options["field"] if field else ()))
        opts = {o: getattr(self, o) for o in self.__slots__ if hasattr(self, o)}
        keys = {*opts.keys()} - {*valid_opts}
        loc = f"{defname}({basetype})" if defname else basetype

        if len(keys) > 0:
            errors.append(exceptions.OptionError(f"Extra options given for {loc} - {', '.join(keys)}"))

        elif basetype == "ArrayOf":
            keys = {"vtype"} - {*opts.keys()}
            if len(keys) != 0:
                errors.append(exceptions.OptionError(f"ArrayOf {loc} requires options: vtype"))

        elif basetype == "MapOf":
            keys = {"vtype", "ktype"} - {*opts.keys()}
            if len(keys) != 0:
                errors.append(exceptions.OptionError(f"MapOf {loc} requires options: vtype and ktype"))

        values = ("minc", "maxc") if field else ("minv", "maxv")
        minimum = getattr(self, values[0], 1)
        maximum = getattr(self, values[1], max(1, minimum))

        if maximum and maximum != 0 and maximum < minimum:
            errors.append(exceptions.OptionError(f"{values[1]} cannot be less than {values[0]}"))

        fmt = opts.get("format")
        if fmt and not any([re.match(fr"^{vf}$", fmt) for vf in self._validFormats]):
            errors.append(exceptions.OptionError(f"{basetype} {loc} specified unknown format {fmt}"))

        errors = list(filter(None, errors))
        if len(errors) > 0:
            if silent:
                return errors
            raise errors[0]

    def multiplicity(self, min_default: int = 0, max_default: int = 0, field: bool = False,
                     check: Callable[[int, int], bool] = lambda x, y: True) -> str:
        """
        Determine the multiplicity of the min/max options
        minc    maxc	Multiplicity	Description	                                Keywords
        0	    1	    0..1	        No instances or one instance	            optional
        1	    1	    1	            Exactly one instance	                    required
        0	    0	    0..*	        Zero or more instances	                    optional, repeated
        1	    0	    1..*	        At least one instance	                    required, repeated
        m	    n	    m..n	        At least m but no more than n instances     required, repeated if m > 1

        :param min_default: default value of minc/minv
        :param max_default: default value of maxc/maxv
        :param field: if option for field or type
        :param check: function for ignoring multiplicity - Fun(minimum, maximum) -> bool
        :return: options multiplicity or empty string
        """
        values = ("minc", "maxc") if field else ("minv", "maxv")
        minimum = getattr(self, values[0], min_default)
        maximum = getattr(self, values[1], max_default)
        if check(minimum, maximum):
            if minimum == 1 and maximum == 1:
                return "1"
            return f"{minimum}..{'*' if maximum == 0 else maximum}"
        return ""

    def split(self) -> Tuple["Options", "Options"]:
        field_opts = Options({f: getattr(self, f) for f in self._options["field"] if hasattr(self, f)})
        type_opts = Options({f: getattr(self, f) for f in self._options["type"] if hasattr(self, f)})
        return field_opts, type_opts


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
