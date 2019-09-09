"""
JADN RFC3987 Formats
"""
from typing import Optional

from ... import (
    exceptions,
    utils
)

RFC3986_Formats = {}


try:
    import rfc3986
except ImportError:
    pass
else:
    @utils.addKey(d=RFC3986_Formats, k="uri")
    def uri(val: str) -> Optional[Exception]:
        """
        Validate an URI - RFC 3987
        :param val: URI instance to validate
        :return: None or Exception
        """
        if not isinstance(val, str):
            return TypeError(f"uri given is not expected string, given {type(val)}")

        try:
            rfc3986.urlparse(val)
        except exceptions as e:
            return e


    @utils.addKey(d=RFC3986_Formats, k="uri-reference")
    def uri_reference(val: str) -> Optional[Exception]:
        """
        Validate an URI-Reference - RFC 3987
        :param val: URI-Reference instance to validate
        :return: None or Exception
        """
        if not isinstance(val, str):
            return TypeError(f"uri-reference given is not expected string, given {type(val)}")

        try:
            rfc3986.uri_reference(val)
        except exceptions as e:
            return e

__all__ = ["RFC3986_Formats"]
