"""
JADN Network Formats
"""
import ipaddress
import re

from typing import (
    Optional,
    Union
)
from .constants import HOSTNAME_MAX_LENGTH
from ... import (
    utils
)

NetworkFormats = {}


# From https://stackoverflow.com/questions/2532053/validate-a-hostname-string
@utils.addKey(d=NetworkFormats)
def hostname(val: str) -> Optional[Exception]:
    """
    Check if valid Hostname - RFC 1034 § 3.1
    :param val: Hostname to validate
    :return: given hostname
    :raises: TypeError, ValueError
    """
    if not isinstance(val, str):
        return TypeError(f"Hostname given is not expected string, given {type(val)}")

    # Copy & strip exactly one dot from the right, if present
    val = val[:-1] if val.endswith(".") else val[:]
    if len(val) < 1:
        return ValueError(f'Hostname is not a valid length, minimum 1 character')

    if len(val) > HOSTNAME_MAX_LENGTH:
        return ValueError(f'Hostname is not a valid length, exceeds {HOSTNAME_MAX_LENGTH} characters')

    allowed = re.compile("(?!-)[A-Z0-9-]{1,63}(?<!-)$", re.IGNORECASE)
    if not all(allowed.match(x) for x in val.split(".")):
        return ValueError(f"Hostname given is not valid")


@utils.addKey(d=NetworkFormats, k="ipv4")
def IPv4(val: str) -> Optional[Exception]:
    """
    RFC 2673 § 3.2# "dotted-quad"
    :param val: IPv6 Address to validate
    :return: None or Exception
    """
    if not isinstance(val, str):
        return TypeError(f"IPv4 given is not expected string, given {type(val)}")

    try:
        ipaddress.IPv4Address(val)
    except ipaddress.AddressValueError as e:
        return e


#
@utils.addKey(d=NetworkFormats, k="ipv6")
def IPv6(val: str) -> Optional[Exception]:
    """
    RFC 4291 § 2.2 "IPv6 address"
    :param val: IPv6 Address to validate
    :return: None or Exception
    """
    if not isinstance(val, str):
        return TypeError(f"IPv6 address given is not expected string, given {type(val)}")

    try:
        ipaddress.IPv6Address(val)
    except ipaddress.AddressValueError as e:
        return e


try:
    import netaddr
except ImportError:
    pass
else:
    @utils.addKey(d=NetworkFormats, k="eui")
    def EUI(val: Union[bytes, str]) -> Optional[Exception]:
        """
        IEEE Extended Unique Identifier (MAC Address), EUI-48 or EUI-64
        :param val: EUI to validate
        :return: None or Exception
        """
        if not isinstance(val, (bytes, str)):
            return TypeError(f"EUI is not expected type, given {type(val)}")

        val = val if isinstance(val, str) else val.decode("utf-8")
        try:
            netaddr.EUI(val)
        except (netaddr.core.AddrFormatError, ValueError) as e:
            return e


# How to validate??
@utils.addKey(d=NetworkFormats, k="ipv4-addr")
def IPv4_Address(val: str) -> Optional[Exception]:
    """
    IPv4 address as specified in RFC 791 § 3.1
    :param val: IPv4 Address to validate
    :return: None or Exception
    """
    # Convert val to bytes


# How to validate??
@utils.addKey(d=NetworkFormats, k="ipv6-addr")
def IPv6_Address(val: str) -> Optional[Exception]:
    """
    IPv6 address as specified in RFC 8200 § 3
    :param val: IPv4 Address to validate
    :return: None or Exception
    """
    # Convert val to bytes


@utils.addKey(d=NetworkFormats, k="ipv4-net")
def IPv4_Network(val: Union[list, str, tuple]) -> Optional[Exception]:
    """
    Binary IPv4 address and Integer prefix length as specified in RFC 4632 § 3.1
    :param val: IPv4 network address to validate
    :return: None or exception
    """
    if not isinstance(val, (list, str, tuple)):
        return TypeError(f"IPv4 Network is not expected type, given {type(val)}")

    val = val if isinstance(val, (list, tuple)) else val.split("/")
    if len(val) == 1:
        return IPv4(val[0])

    if len(val) != 2:
        return ValueError(f"IPv6 Network is not 2 values, given {len(val)}")

    val = "/".join(map(str, val))
    try:
        ipaddress.IPv4Network(val, strict=False)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
        return e


@utils.addKey(d=NetworkFormats, k="ipv6-net")
def IPv6_Network(val: Union[list, str, tuple]) -> Optional[Exception]:
    """
    Binary IPv6 address and Integer prefix length as specified in RFC 4291 § 2.3
    :param val: IPv6 network address to validate
    :return: None or exception
    """
    if not isinstance(val, (list, str, tuple)):
        return TypeError(f"IPv6 Network is not expected type, given {type(val)}")

    val = val if isinstance(val, (list, tuple)) else val.split("/")
    if len(val) == 1:
        return IPv6(val[0])

    if len(val) != 2:
        return ValueError(f"IPv6 Network is not 2 values, given {len(val)}")

    val = "/".join(map(str, val))
    try:
        ipaddress.IPv6Network(val, strict=False)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
        return e


__all__ = ["NetworkFormats"]
