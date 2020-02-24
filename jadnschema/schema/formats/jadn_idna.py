"""
JADN Internationalised Domain Names in Applications (IDNA) Formats
"""
import re

from typing import Optional
from .general import email
from .network import hostname
from ... import (
    exceptions,
    utils
)

IDNA_Formats = {}

try:
    # The built-in `idna` codec only implements RFC 3890, so we go elsewhere.
    import idna
except ImportError:
    # Defaults if IDNA is not installed
    IDNA_Formats.update({
        "idn-hostname": hostname,
        "idn-email": email
    })
else:
    @utils.addKey(d=IDNA_Formats, k="idn-hostname")
    def idn_hostname(val: str) -> Optional[Exception]:
        """
        Validate an IDN Hostname - RFC 5890 § 2.3.2.3
        :param val: IDN Hostname to validate
        :return: None or Exception
        """
        if not isinstance(val, str):
            return TypeError(f"idn_hostname given is not expected string, given {type(val)}")

        val = re.sub(r"^https?://", "", val)
        try:
            val = idna.encode(val)
        except idna.IDNAError as e:
            return e
        val = val.decode("utf-8") if isinstance(val, bytes) else val
        return hostname(val)


    @utils.addKey(d=IDNA_Formats, k="idn-email")
    def idn_email(val: str) -> Optional[Exception]:
        """
        Validate an IDN Email - RFC 6531
        :param val: IDN Email to validate
        :return: None or Exception
        """
        if not isinstance(val, str):
            return TypeError(f"idn_email given is not expected string, given {type(val)}")

        val = val.split("@")
        if len(val) != 2:
            return exceptions.ValidationError(f"IDN Email address invalid")

        try:
            val = b"@".join(map(idna.encode, val)).decode("utf-8")
        except idna.IDNAError as e:
            return e

        return email(val)


__all__ = ["IDNA_Formats"]
