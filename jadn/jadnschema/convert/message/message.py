import os

from functools import partial
from typing import Union

from .conversions import Conversions

from ... import enums


class Message(object):
    """
    Load and dump a message to other formats
    """

    def __init__(self, msg: Union[str, bytes, dict], fmt: str = enums.MessageFormats.JSON):
        """
        :param msg: message to load
        :param fmt: format of the message to load
        """
        self._fmt = fmt
        if self._fmt in enums.MessageFormats.values():
            self._msg = self._load(msg) if isinstance(msg, str) and os.path.isfile(msg) else self._load(msg)
        else:
            raise ValueError("Message format is not known")

        for k, v in Conversions.items():
            if 'dump' in v:
                setattr(self, f'{k}_dump', partial(v['dump'], self._msg))
            if 'dumps' in v:
                setattr(self, f'{k}_dumps', partial(v['dumps'], self._msg))

    def dump(self, fname: str):
        """
        Dump the message in json format
        :param fname: file name to write to
        :return: None
        """
        json_conv = Conversions.get(enums.MessageFormats.JSON)
        if json_conv:
            if 'dump' in json_conv:
                json_conv['dump'](self._msg, fname)

    def dumps(self):
        """
        Dump the message in json format
        :return: json formatted message
        """
        json_conv = Conversions.get(enums.MessageFormats.JSON)
        if json_conv:
            if 'dumps' in json_conv:
                json_conv['dumps'](self._msg)

    # Helper Functions
    def _load(self, fname):
        if self._fmt not in Conversions:
            raise ValueError("Message format is not known")
        with open(fname, 'rb') as f:
            return Conversions[self._fmt].load(f)

    def _loads(self, val):
        if self._fmt not in Conversions:
            raise ValueError("Message format is not known")
        return Conversions[self._fmt].loads(f)
