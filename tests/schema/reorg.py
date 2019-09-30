import json
import numbers
import os

from typing import Union

base = os.path.dirname(os.path.abspath(__file__))


def dumps(schema: Union[dict, float, int, str, tuple], indent: int = 2, _level: int = 0) -> str:
    """
    Properly format a JADN schema
    :param schema: Schema to format
    :param indent: spaces to indent
    :param _level: current indent level
    :return: Formatted JADN schema
    """
    schema = schema if _level == 0 and isinstance(schema, dict) else schema
    _indent = indent - 1 if indent % 2 == 1 else indent
    _indent += (_level * 2)
    ind, ind_e = " " * _indent, " " * (_indent - 2)

    if isinstance(schema, dict):
        lines = f",\n".join(f"{ind}\"{k}\": {dumps(schema[k], indent, _level + 1)}" for k in schema)
        return f"{{\n{lines}\n{ind_e}}}"

    elif isinstance(schema, (list, tuple)):
        nested = schema and isinstance(schema[0], (list, tuple))
        lvl = _level + 1 if nested and isinstance(schema[-1], (list, tuple)) else _level
        lines = [dumps(val, indent, lvl) for val in schema]
        if nested:
            return f"[\n{ind}" + f",\n{ind}".join(lines) + f"\n{ind_e}]"
        return f"[{', '.join(lines)}]"

    elif isinstance(schema, (numbers.Number, str)):
        return json.dumps(schema)
    else:
        return "???"


if __name__ == "__main__":
    for file in os.listdir(base):
        if file.endswith(".jadn"):
            print(file)
            with open(os.path.join(base, file), "r+") as f:
                cont = json.load(f)
                f.seek(0)
                f.write(dumps(cont))
