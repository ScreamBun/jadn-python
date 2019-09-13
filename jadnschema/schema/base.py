"""
JADN Base Model
"""
import re

from typeguard import check_type
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union
)


ModelData = Union[dict, list, "BaseModel"]

'''
class MetaModel(ABCMeta):
    def __new__(mcs, name, bases, namespace):
        fields: Dict[str, ModelData] = {}
        validators: Dict[str, Callable] = {}

        new_namespace = {
            '__config__': None,
            '__fields__': fields,

            **{n: v for n, v in namespace.items() if n not in fields}
        }
        print(f"namespace - {new_namespace.keys()}")
        return super().__new__(mcs, name, bases, new_namespace)
'''


class BaseModel(object):
    _iter_idx: int

    # Helper Variables
    _config: "Schema"
    _jadn_types: Dict[str, Tuple[str]] = {
        "Simple": (
            "Binary",       # A sequence of octets. Length is the number of octets
            "Boolean",      # An element with one of two values: true or false
            "Integer",      # A positive or negative whole number
            "Number",       # A real number
            "Null",         # An unspecified or non-existent value
            "String",       # A sequence of characters, each of which has a Unicode codepoint. Length is the number of characters
        ),
        "Selector": (
            "Choice",      # One key and value selected from a set of named or labeled fields. The key has an id and name or label, and is mapped to a type
            "Enumerated",  # One value selected from a set of named or labeled integers
        ),
        "Compound": (
            "Array",        # An ordered list of labeled fields with positionally-defined semantics. Each field has a position, label, and type
            "ArrayOf",       # An ordered list of fields with the same semantics. Each field has a position and type vtype
            "Map",          # An unordered map from a set of specified keys to values with semantics bound to each key. Each key has an id and name or label, and is mapped to a type
            "MapOf",        # An unordered map from a set of keys of the same type to values with the same semantics. Each key has key type ktype, and is mapped to value type vtype
            "Record"        # An ordered map from a list of keys with positions to values with positionally-defined semantics. Each key has a position and name, and is mapped to a type. Represents a row in a spreadsheet or database table
        )
    }
    _schema_types: Set[str] = {t for jt in _jadn_types.values() for t in jt}

    def __init__(self, data: ModelData, **kwargs):
        if data:
            values, errs = init_model(self, data, **kwargs)
            if errs:
                raise errs[0]
        else:
            values = {}

        values.update({k: v for k, v in kwargs.items() if k in self.__slots__})
        values, errs = init_model(self, values, **kwargs)

        for k, v in values.items():
            setattr(self, k, v)

    def __setattr__(self, key, val):
        if key in self.__slots__ or key.startswith("_"):
            if hasattr(self, f"check_{key}"):
                val = getattr(self, f"check_{key}")(val)
            check_type(key, val, self.__annotations__.get(key, Any))
            super(BaseModel, self).__setattr__(key, val)
        else:
            raise AttributeError(f"{self.__class__.__name__}.{key} is not a valid attribute that can be set by a user")

    def __iter__(self):
        self._iter_idx = 0
        return getattr(self, self.__slots__[self._iter_idx])

    def __next__(self):
        if self._iter_idx < len(self.__slots__):
            self._iter_idx += 1
            return getattr(self, self.__slots__[self._iter_idx])
        else:
            raise StopIteration

    def __contains__(self, key):
        return key in self.__slots__ and hasattr(self, key)

    def __hash__(self) -> int:
        return hash(self.__repr__())

    def dict(self) -> dict:
        """
        Create a dictionary od hte current object
        :return: dict value of the object
        """
        return {attr: getattr(self, attr) for attr in self.__slots__ if hasattr(self, attr)}

    def get(self, attr: str, default: Any = None):
        """
        Emulate a dictionary get method
        :param attr: attribute to get the value
        :param default: default value if attribute does not exist
        :return: value of attribute/default/None
        """
        return getattr(self, attr, default) if attr in self.__slots__ else default

    def items(self) -> tuple:
        """
        Emulate a dictionary items method
        :return: tuple of tuples - (KEY, VALUE)
        """
        return tuple((k, v) for k, v in self.dict().items())

    def keys(self) -> tuple:
        """
        Emulate a dictionary keys method
        :return: tuple of valid attributes of the class
        """
        return tuple(attr for attr in self.__slots__ if hasattr(self, attr))

    # Helper functions


def init_model(model: BaseModel, input_data: ModelData, silent: bool = True, **kwargs) -> Tuple[dict, Optional[List[Exception]]]:
    """
    Validate data against a model
    :param model: model class the data is being validated against
    :param input_data: data to validate
    :param silent: bool - raise or return errors
    :return: validated fields, OPTIONAL(ERRORS)
    """
    model_class = model.__class__.__name__
    input_data = dict(zip(model.__slots__, input_data)) if isinstance(input_data, list) else input_data
    basetype = input_data.get("type")
    fields = {k: v for k, v in kwargs.items() if re.match(r"^_[^_]", k)}
    errors = []

    if model_class == "Schema":
        if "meta" in input_data and isinstance(input_data.get("meta"), dict):
            from .schema import Meta
            input_data["meta"] = Meta(input_data["meta"])

        if "types" in input_data and isinstance(input_data.get("types"), list):
            from .definitions import make_definition
            input_data["types"] = {t[0]: make_definition(t, **kwargs) for t in input_data.get("types", [])}

    elif model_class == "Meta":
        if "config" in input_data and isinstance(input_data.get("config"), dict):
            from .schema import Config
            input_data["config"] = Config(input_data["config"])

    else:
        if "options" in input_data and isinstance(input_data.get("options"), list):
            from .options import Options
            try:
                input_data["options"] = Options(input_data["options"])
            except Exception as e:
                if silent:
                    errors.append(e)
                else:
                    raise e

        if "fields" in input_data and isinstance(input_data.get("fields"), list):
            from .fields import EnumeratedField, Field
            field = EnumeratedField if basetype == "Enumerated" else Field
            input_data["fields"] = [field(f, **kwargs) for f in input_data["fields"]]

    for var, val in input_data.items():
        inst = model.__annotations__.get(var)
        try:
            if var not in model.__slots__:
                raise KeyError(f"{model_class} has extra keys - {var}")
            check_type(var, val, inst)
        except Exception as e:
            if silent:
                errors.append(e)
            else:
                raise e
        fields[var] = val

    return fields, errors
