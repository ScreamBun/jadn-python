import os

from functools import partial
from typing import Union

from .serializations import serializations

from ...utils import FrozenDict

MessageFormats = FrozenDict({s.upper(): s for s in {*serializations.encode}.union({**serializations.decode})})


class Message:
    """
    Load and dump a message to other formats
    """

    def __init__(self, msg: Union[str, bytes, dict], fmt: str = MessageFormats.JSON):
        """
        :param msg: message to load
        :param fmt: format of the message to load
        """
        self._fmt = fmt if fmt in MessageFormats.values() else MessageFormats.JSON
        self._msg = self._load(msg) if isinstance(msg, str) and os.path.isfile(msg) else self._loads(msg)

        for msgFmt in MessageFormats.values():
            setattr(self, f'{msgFmt}_dump', partial(self.dump, fmt=msgFmt))
            setattr(self, f'{msgFmt}_dumps', partial(self.dumps, fmt=msgFmt))

    def dump(self, fname: str, fmt: str = MessageFormats.JSON):
        """
        Dump the message in the specified format to the file given
        :param fname: file name to write to
        :param fmt: format to write
        :return: None
        """
        msg = self.dumps(fmt)
        with open(fname, 'wb' if isinstance(msg, (bytes, bytearray)) else 'w') as f:
            f.write(msg)

    def dumps(self, fmt: str = MessageFormats.JSON):
        """
        Dump the message in the specified format
        :param fmt: format to write
        :return: json formatted message
        """
        return serializations.encode.get(fmt)(self._msg)

    # Helper Functions
    def _load(self, fname):
        with open(fname, 'rb') as f:
            return serializations.decode.get(self._fmt)(f.read())

    def _loads(self, val):
        if isinstance(val, dict):
            return val
        return serializations.decode.get(self._fmt)(val)
