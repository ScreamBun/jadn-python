import base64
import sys

from typing import Any, Type, Union


# Util Classes
class ObjectDict(dict):
    """
    Dictionary that acts like a object
    d = ObjectDict()

    d['key'] = 'value'
        SAME AS
    d.key = 'value'
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize an ObjectDict
        :param args: positional parameters
        :param kwargs: key/value parameters
        """
        self._hash = None
        super(ObjectDict, self).__init__(*args, **kwargs)

    def __getattr__(self, key: str) -> Any:
        """
        Get an key as if an attribute - ObjectDict.key - SAME AS - ObjectDict['key']
        :param key: key to get value of
        :return: value of given key
        """
        if key in self:
            return self[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key: str, val: Any) -> None:
        """
        Set an key as if an attribute - d.key = 'value' - SAME AS - d['key'] = 'value'
        :param key: key to create/override
        :param val: value to set
        :return: None
        """
        dict.__setitem__(self, key, val)


class FrozenDict(ObjectDict):
    """
    Immutable dictionary
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize a FrozenDict
        :param args: positional parameters
        :param kwargs: key/value parameters
        """
        super(FrozenDict, self).__init__(*args, **kwargs)

    def __hash__(self) -> int:
        """
        Create a hash for the FrozenDict
        :return: object hash
        """
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.items())))
        return self._hash

    def _immutable(self, *args, **kwargs) -> None:
        """
        Raise an error for an attempt to alter the FrozenDict
        :param args: positional args
        :param kwargs: key/value args
        :return: None
        :raise TypeError
        """
        raise TypeError('cannot change object - object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    pop = _immutable
    popitem = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable


# Util Functions
def default_encoding(itm: Any) -> Any:
    """
    Encode the given object/type to the default of the system
    :param itm: object/type to convert to the system default
    :return: system default converted object/type
    """
    if isinstance(itm, dict):
        return {toStr(k): default_encoding(v) for k, v in itm.items()}

    elif isinstance(itm, list):
        return [default_encoding(i) for i in itm]

    elif isinstance(itm, tuple):
        tmp = tuple(default_encoding(i) for i in itm)

    elif isinstance(itm, (complex, int, float, object)):
        return itm
    else:
        return toStr(itm)
    return tmp


def isBase64(sb: Union[str, bytes]) -> bool:
    """
    Determine if a given string is valid as base64
    :param sb: string to validate as base64
    :return: bool if base64
    """
    try:
        if isinstance(sb, str):
            # If there's any unicode here, an exception will be thrown and the function will return false
            sb_bytes = bytes(sb, 'ascii')
        elif isinstance(sb, bytes):
            sb_bytes = sb
        else:
            raise ValueError("Argument must be string or bytes")
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False


def toFrozen(itm: Union[dict, list, str]) -> Union[FrozenDict, str, tuple]:
    """
    Convert the given item to a frozen format
    :param itm: item to freeze
    :return: converted item as a frozen format
    """
    if isinstance(itm, dict):
        return FrozenDict({k: toFrozen(v) for k, v in itm.items()})
    if isinstance(itm, list):
        return tuple(toFrozen(i) for i in itm)

    return itm


def toThawed(itm: Union[dict, FrozenDict, tuple]) -> Union[dict, list, str]:
    """
    Convert the given item to a thawed format
    :param itm: item to thaw
    :return: converted item as a thawed format
    """
    if isinstance(itm, (dict, FrozenDict)):
        return {k: toThawed(v) for k, v in itm.items()}
    if isinstance(itm, tuple):
        return list(toThawed(i) for i in itm)

    return itm


def toStr(s: Any) -> str:
    """
    Convert a given type to a default string
    :param s: item to convert to a string
    :return: converted string
    """
    return s.decode(sys.getdefaultencoding(), 'backslashreplace') if hasattr(s, 'decode') else str(s)


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
