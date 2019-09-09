"""
JADN Validation Format Functions
"""
from .general import GeneralFormats
from .jadn_idna import IDNA_Formats
from .network import NetworkFormats
from .rfc_3339 import RFC3339_Formats
from .rfc_3986 import RFC3986_Formats
from .rfc_3987 import RFC3987_Formats

ValidationFormats = {
    **GeneralFormats,
    **IDNA_Formats,
    **NetworkFormats,
    **RFC3339_Formats,
    **RFC3986_Formats,
    **RFC3987_Formats
}

__all__ = ["ValidationFormats"]
