"""
Message Conversion functions
"""
import cbor2
import collections
import json
import xmltodict
import yaml

from dicttoxml import dicttoxml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from ... import (
    utils
)


def _xml_root(msg):
    if 'message' in msg:
        return msg.get('message', {})
    elif 'response' in msg:
        return msg.get('response', {})
    elif 'action' in msg:
        return 'message'
    elif 'status' in msg:
        return 'response'


def _xml_to_dict(xml):
    tmp = {}
    for k, v in xml.items():
        a = k[1:] if k.startswith("@") else k
        tmp[a] = _xml_to_dict(v) if isinstance(v, collections.OrderedDict) else v
    return tmp


"""
Conversions Docs
    FORMAT = {
        dump - convert a dict to FORMAT
        dumps - convert a dict to FORMAT and write it to a file
        load - load FORMAT from a str/bytestring and convert to a dict
        loads - load FORMAT from a file and convert it to a dict
    }
"""
Conversions = utils.FrozenDict(
    cbor=utils.FrozenDict(
        dump=lambda v, f: cbor2.dump(v, f),
        dumps=lambda v: cbor2.dumps(v),
        load=lambda f: cbor2.load(f),
        loads=lambda v: cbor2.loads(v),
    ),
    json=utils.FrozenDict(
        dump=lambda v, f: json.dump(v, f),
        dumps=lambda v: json.dumps(v),
        load=lambda f: json.load(f),
        loads=lambda v: json.loads(v),
    ),
    xml=utils.FrozenDict(
        dump=lambda v, f: f.write(dicttoxml(v, custom_root=_xml_root(v), attr_type=False)),
        dumps=lambda v: dicttoxml(v, custom_root=_xml_root(v), attr_type=False),
        load=lambda f: _xml_root(_xml_to_dict(xmltodict.parse(f.read()))),
        loads=lambda v: _xml_root(_xml_to_dict(xmltodict.parse(v))),
    ),
    yaml=utils.FrozenDict(
        dump=lambda v, f: f.write(yaml.dump(v, Dumper=Dumper)),
        dumps=lambda v: yaml.dump(v, Dumper=Dumper),
        load=lambda f: yaml.load(f.read(), Loader=Loader),
        loads=lambda v: yaml.load(v, Loader=Loader),
    )
)