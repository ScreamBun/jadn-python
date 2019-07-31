import os

from datetime import datetime

from jadnschema import (
    convert,
    jadn,
    # Enums
    CommentLevels,
)


# TODO: Add CommentLevels, requires dump.py rewrite
class Conversions(object):
    _test_dir = 'schema_gen'

    def __init__(self, schema):
        self._schema = schema
        self._base_schema = f'schema/{self._schema}.jadn'

        if not os.path.isdir(self._test_dir):
            os.makedirs(self._test_dir)

        self._schema_obj = jadn.load(self._base_schema)

    def CDDL(self):
        print("Convert: JADN --> CDDL")
        convert.cddl_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.all.cddl'), comm=CommentLevels.ALL)
        convert.cddl_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.none.cddl'), comm=CommentLevels.NONE)
        # print("Convert: CDDL --> JADN")
        # convert.cddl_load(open(os.path.join(self._test_dir, self._schema + '.all.cddl'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.cddl.jadn'))

    def HTML(self):
        print("Convert: JADN --> HMTL Tables")
        convert.html_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.html'))

    def JADN(self):
        print("Convert: JADN --> JAS")
        convert.jadn_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.all.jadn'), comm=CommentLevels.ALL)
        convert.jadn_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.none.jadn'), comm=CommentLevels.NONE)

    def JAS(self):
        print("Convert: JADN --> JAS")
        convert.jas_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.jas'))
        # print("Convert: JAS --> JADN ")
        # convert.jas_load(open(os.path.join(self._test_dir, self._schema + '.jas'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.jas.jadn'))

    def JIDL(self):
        print("Convert: JADN --> JIDL")
        convert.jidl_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.jidl'))
        # print("Convert: JIDL --> JADN")
        # with open(os.path.join(self._test_dir, self._schema + '.jidl.jadn'), "w") as f:
        #     convert.jidl_loads(open(os.path.join(self._test_dir, self._schema + '.jidl'), 'rb').read()).dump(f)

    def JSON(self):
        print("Convert: JADN --> JSON")
        convert.json_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.all.json'), comm=CommentLevels.ALL)
        convert.json_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.none.json'), comm=CommentLevels.NONE)
        # print("Convert: JSON --> JADN")
        # convert.json_load(open(os.path.join(self._test_dir, self._schema + '.all.json'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.json.jadn'))

    def MarkDown(self):
        print("Convert: JADN --> MarkDown Tables")
        convert.md_dump(schema=self._schema_obj, fname=os.path.join(self._test_dir, self._schema + '.md'))

    def ProtoBuf(self):
        print("Convert: JADN --> ProtoBuf")
        convert.proto_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.all.proto'), comm=CommentLevels.ALL)
        convert.proto_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.none.proto'), comm=CommentLevels.NONE)
        # print("Convert: ProtoBuf --> JADN")
        # convert.proto_load(open(os.path.join(self._test_dir, self._schema + '.all.proto'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.proto.jadn'))

    def Relax_NG(self):
        print("Convert: JADN --> RelaxNG")
        convert.relax_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.all.rng'), comm=CommentLevels.ALL)
        convert.relax_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.none.rng'), comm=CommentLevels.NONE)
        # print("Convert: RelaxNG --> JADN")
        # convert.relax_load(open(os.path.join(self._test_dir, self._schema + '.all.rng'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.rng.jadn'))

    def Thrift(self):
        print("Convert: JADN --> Thrift")
        convert.thrift_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.all.thrift'), comm=CommentLevels.ALL)
        convert.thrift_dump(self._schema_obj, os.path.join(self._test_dir, self._schema + '.none.thrift'), comm=CommentLevels.NONE)
        # print("Convert: Thrift --> JADN")
        # convert.thrift_load(open(os.path.join(self._test_dir, self._schema + '.all.thrift'), 'rb').read(), os.path.join(self._test_dir, self._schema + '.thrift.jadn'))

    # Tester Functions
    def Analyze(self):
        print("JADN --> Schema Analysis")
        for k, v in self._schema_obj.analyze().items():
            print(f"{k}: {v}")

    def prettyFormat(self):
        print("JADN --> Formatted JADN")
        self._schema_obj.dump(f"{self._test_dir}/{self._schema}_reorg.jadn")


if __name__ == '__main__':
    schema = 'oc2ls-v1.0-csprd03'
    # schema = 'oc2ls-v1.0-csprd03'
    conversions = Conversions(schema)
    validConvert = (
        "Analyze",
        "HTML",
        "JADN",
        "JIDL",
        "JSON",
        "MarkDown",
        "prettyFormat"
    )

    for conv in dir(conversions):
        if not conv.startswith('_') and conv in validConvert:
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
