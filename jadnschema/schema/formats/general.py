"""
JADN General Formats
"""
import re

from typing import (
    Optional,
    Union
)
from urllib.parse import urlparse
from ... import (
    exceptions,
    utils
)

GeneralFormats = {}


# Use regex from https://stackoverflow.com/questions/201323/how-to-validate-an-email-address-using-a-regular-expression
#   A more comprehensive email address validator is available at http://isemail.info/about
@utils.addKey(d=GeneralFormats)
def email(val: str) -> Optional[Exception]:
    """
    Check if valid E-Mail address - RFC 5322 Section 3.4.1
    :param val: E-Mail address to validate
    :return: given e-mail
    :raises: TypeError, ValueError
    """
    if not isinstance(val, str):
        raise TypeError(f"E-Mail given is not expected string, given {type(val)}")
    rfc5322_re = (
        r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"
        r'"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@'
        r"(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])"
        r"|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]"
        r":(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
    )
    if not re.match(rfc5322_re, val):
        return ValueError(f"E-Mail given is not valid")


@utils.addKey(d=GeneralFormats)
def uri(val: str) -> Optional[Exception]:
    """
    Check if valid URI - RFC 3986
    :param val: URI to validate
    :return: uri given
    :raises TypeError, ValueError
    """
    if not isinstance(val, str):
        return TypeError(f"URI given is not expected string, given {type(val)}")
    url_match = re.match(r"(https?:\/\/(www\.)?)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)", val)

    try:
        result = urlparse(val)
        if not all([result.scheme, result.netloc, result.path]) or url_match:
            return ValueError(f"URI given is not expected valid")
    except Exception:
        return ValueError(f"URI given is not expected valid")


try:
    import jsonpointer
except ImportError:
    pass
else:
    @utils.addKey(d=GeneralFormats, k="json-pointer")
    def json_pointer(val: str) -> Optional[Exception]:
        """
        Validate JSON Pointer - RFC 6901 Section 5
        :param val: JSON Pointer to validate
        :return: None or Exception
        """
        if not isinstance(val, str):
            raise TypeError(f"JSON Pointer given is not expected string, given {type(val)}")

        try:
            jsonpointer.JsonPointer(val)
        except Exception as e:
            return e

    # Definition taken from: https://tools.ietf.org/html/draft-handrews-relative-json-pointer-01#section-3
    @utils.addKey(d=GeneralFormats, k="relative-json-pointer")
    def relative_json_pointer(val: str) -> Optional[Exception]:
        """
        Validate Relative JSON Pointer - JSONP
        :param val: Relative JSON Pointer to validate
        :return: None or Exception
        """
        if not isinstance(val, str):
            return TypeError(f"relative json pointer given is not expected string, given {type(val)}")

        non_negative_integer, rest = [], ""
        for i, character in enumerate(val):
            if character.isdigit():
                non_negative_integer.append(character)
                continue

            if not non_negative_integer:
                return exceptions.ValidationError("invalid relative json pointer given")

            rest = val[i:]
            break
        try:
            (rest == "#") or jsonpointer.JsonPointer(rest)
        except Exception as e:
            return e


@utils.addKey(d=GeneralFormats)
def regex(val: str) -> Optional[Exception]:
    """
    Validate Regular Expression - ECMA 262
    :param val: RegEx to validate
    :return: None or Exception
    """
    if not isinstance(val, str):
        return TypeError(f"RegEx given is not expected string, given {type(val)}")

    try:
        re.compile(val)
    except Exception as e:
        return e


@utils.addKey(d=GeneralFormats, k="i8")
def bit_8(val: int) -> Optional[Exception]:
    """
    Validate 8-bit number - Signed 8 bit integer, value must be between -128 and 127
    :param val: number to validate
    :return: None or Exception
    """
    if not isinstance(val, int):
        return TypeError(f"number given is not expected integer, given {type(val)}")

    if len(f"{abs(val):b}") > 8:
        return ValueError(f"number is not 8-bit, {val}")


@utils.addKey(d=GeneralFormats, k="i16")
def bit_16(val: int) -> Optional[Exception]:
    """
    Validate 16-bit number - Signed 16 bit integer, value must be between -32768 and 62767
    :param val: number to validate
    :return: None or Exception
    """
    if not isinstance(val, int):
        return TypeError(f"number given is not expected integer, given {type(val)}")

    if len(f"{abs(val):b}") > 16:
        return ValueError(f"number is not 16-bit, {val}")


@utils.addKey(d=GeneralFormats, k="i32")
def bit_32(val: int) -> Optional[Exception]:
    """
    Validate 36-bit number - Signed 36 bit integer, value must be between -2147483648 and 2147483647
    :param val: number to validate
    :return: None or Exception
    """
    if not isinstance(val, int):
        return TypeError(f"number given is not expected integer, given {type(val)}")

    if len(f"{abs(val):b}") > 32:
        return ValueError(f"number is not 32-bit, {val}")


@utils.addKey(d=GeneralFormats, k="unsigned")
def unsigned(n: int, val: Union[bytes, int]) -> Optional[Exception]:
    """
    Validate an Unsigned integer or bit field of <n> bits, value must be between 0 and 2^<n> - 1
    :param n: max value of the integer/bytes - 2^<n> - 1
    :param val: integer/bytes to validate
    :return: None or Exception
    """
    if not isinstance(val, (bytes, int, str)):
        return TypeError(f"unsigned bytes/number given is not expected bytes/integer, given {type(val)}")

    # Maximum bytes/number
    max_val = pow(2, n) - 1

    # Unsigned Integer
    if isinstance(val, int):
        msg = "cannot be negative" if 0 > val else (f"cannot be greater than {max_val:,}" if val > max_val else None)
        return ValueError(f"unsigned integer given is invalid, {msg}") if msg else None

    # Unsigned Bytes
    val = bytes(val, "utf-8") if isinstance(val, str) else val
    if val and len(val) > max_val:
        return ValueError(f"unsigned bytes given is invalid, cannot be more than {max_val:,} bytes")


__all__ = ["GeneralFormats"]
