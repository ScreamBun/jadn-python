"""
JADN Exceptions
"""
from builtins import BaseException, Exception


class DuplicateError(Exception):
    """
    JADN field/type duplicated in id/name
    """


class FormatError(Exception):
    """
    JADN Syntax Error
    """


class OptionError(Exception):
    """
    JADN Field/Type option Error
    """