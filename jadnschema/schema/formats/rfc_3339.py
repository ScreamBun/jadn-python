"""
JADN RFC3339 Formats
"""
from typing import Optional

from ... import utils

RFC3339_Formats = {}

try:
    import strict_rfc3339
except ImportError:
    pass
else:
    @utils.addKey(d=RFC3339_Formats, k="date-time")
    def datetime(val: str) -> Optional[Exception]:
        """
        Validate a datetime - RFC 3339 § 5.6
        :param val: DateTime instance to validate
        :return: None or Exception
        """
        if not isinstance(val, str):
            return TypeError(f"datetime given is not expected string, given {type(val)}")

        try:
            strict_rfc3339.validate_rfc3339(val)
        except Exception as e:  # pylint: disable=broad-except
            # TODO: change to better exception
            return e


    @utils.addKey(d=RFC3339_Formats)
    def date(val: str) -> Optional[Exception]:
        """
        Validate a date - RFC 3339 § 5.6
        :param val: Date instance to validate
        :return: None or Exception
        """
        if not isinstance(val, str):
            return TypeError(f"date given is not expected string, given {type(val)}")
        try:
            datetime(f"{val}T00:00:00")
        except Exception as e:  # pylint: disable=broad-except
            # TODO: change to better exception
            return e


    @utils.addKey(d=RFC3339_Formats)
    def time(val: str) -> Optional[Exception]:
        """
        Validate a time - RFC 3339 § 5.6
        :param val: Time instance to validate
        :return: None or Exception
        """
        if not isinstance(val, str):
            return TypeError(f"time given is not expected string, given {type(val)}")
        try:
            datetime(f"1970-01-01T{val}")
        except Exception as e:  # pylint: disable=broad-except
            # TODO: change to better exception
            return e


__all__ = ["RFC3339_Formats"]
