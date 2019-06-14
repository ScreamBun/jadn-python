import os

from datetime import datetime

from jadnschema import (
    convert,
    enums,
    jadn
)


# TODO: Add CommentLevels, requires dump.py rewrite
class Conversions(object):
    _test_dir = 'schema_gen'

    def __init__(self, schema):
        self._schema = schema
        self._base_schema = f'schema/{self._schema}.jadn'

        if not os.path.isdir(self._test_dir):
            os.makedirs(self._test_dir)

        self._schema_json = jadn.load(self._base_schema)

    def CDDL(self):
        print("Convert: JADN --> CDDL")
        convert.cddl_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.all.cddl'), comm=enums.CommentLevels.ALL)
        convert.cddl_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.none.cddl'), comm=enums.CommentLevels.NONE)
        print("Convert: CDDL --> JADN")
        convert.cddl_load(open(os.path.join(self._test_dir, self._schema + '.all.cddl'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.cddl.jadn'))

    def HTML(self):
        print("Convert: JADN --> HMTL Tables")
        convert.html_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.html'))

    def JAS(self):
        print("Convert: JADN --> JAS")
        convert.jas_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.jas'))
        print("Convert: JAS --> JADN ")
        convert.jas_load(open(os.path.join(self._test_dir, self._schema + '.jas'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.jas.jadn'))

    def JSON(self):
        print("Convert: JADN --> JSON")
        convert.json_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.all.json'), comm=enums.CommentLevels.ALL)
        convert.json_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.none.json'), comm=enums.CommentLevels.NONE)
        print("Convert: JSON --> JADN")
        convert.json_load(open(os.path.join(self._test_dir, self._schema + '.all.json'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.json.jadn'))

    def MarkDown(self):
        print("Convert: JADN --> MarkDown Tables")
        convert.md_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.md'))

    def ProtoBuf(self):
        print("Convert: JADN --> ProtoBuf")
        convert.proto_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.all.proto'), comm=enums.CommentLevels.ALL)
        convert.proto_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.none.proto'), comm=enums.CommentLevels.NONE)
        print("Convert: ProtoBuf --> JADN")
        convert.proto_load(open(os.path.join(self._test_dir, self._schema + '.all.proto'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.proto.jadn'))

    def Relax_NG(self):
        print("Convert: JADN --> RelaxNG")
        convert.relax_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.all.rng'), comm=enums.CommentLevels.ALL)
        convert.relax_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.none.rng'), comm=enums.CommentLevels.NONE)
        print("Convert: RelaxNG --> JADN")
        convert.relax_load(open(os.path.join(self._test_dir, self._schema + '.all.rng'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.rng.jadn'))

    def Thrift(self):
        print("Convert: JADN --> Thrift")
        convert.thrift_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.all.thrift'), comm=enums.CommentLevels.ALL)
        convert.thrift_dump(self._schema_json, os.path.join(self._test_dir, self._schema + '.none.thrift'), comm=enums.CommentLevels.NONE)
        print("Convert: Thrift --> JADN")
        convert.thrift_load(open(os.path.join(self._test_dir, self._schema + '.all.thrift'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.thrift.jadn'))

    def prettyFormat(self):
        print("JADN --> Formatted JADN")
        with open(f'{self._test_dir}/{self._schema}_reorg.jadn', "w") as f:
            jadn.jadn_dump(self._schema_json, f)


if __name__ == '__main__':
    schema = 'oc2ls-wd13'
    conversions = Conversions(schema)

    '''
    for conv in dir(conversions):
        if not conv.startswith('_'):
            print(f'Convert To/From: {conv}')
            t = datetime.now()
            try:
                getattr(conversions, conv)()
            except Exception as e:
                if 'parsing' in str(e):
                    print(getattr(e, 'message', e))
                else:
                    raise e
            t = datetime.now() - t
            minutes, seconds = divmod(t.total_seconds(), 60)
            print(f'{minutes}m {seconds:.4f}s\n')
    '''
    conversions.MarkDown()
