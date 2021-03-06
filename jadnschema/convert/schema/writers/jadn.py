"""
JADN to JADN
"""
from datetime import datetime

from .. import base, enums


class JADNtoJADN(base.WriterBase):
    format = "jadn"

    def dump(self, fname: str, source: str = None, comm: str = enums.CommentLevels.ALL, **kwargs) -> None:
        """
        Produce JSON schema from JADN schema and write to file provided
        :param fname: Name of file to write
        :param source: Name of the original schema file
        :param comm: Level of comments to include in converted schema
        :return: None
        """
        self._comm = comm == enums.CommentLevels.ALL
        with open(fname, "w") as f:
            if source:
                f.write(f"<!-- Generated from {source}, {datetime.ctime(datetime.now())} -->\n")
            f.write(self.dumps(self._comm))

    def dumps(self, comm: str = enums.CommentLevels.ALL, **kwargs) -> str:
        """
        Converts the JADN schema to JSON
        :param comm: Level of comments to include in converted schema
        :return: JSON schema
        """
        self._comm = comm == enums.CommentLevels.NONE
        return self._schema.schema_pretty(self._comm)
