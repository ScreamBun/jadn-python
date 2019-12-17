from jadnschema import jadn

schema = f'schema/oc2ls-v1.0-wd14_update.jadn'

cmd = {
    "action": "allow",
    "target": {
        # "idn_email_addr": "用户@例子.广告"  # (Chinese, Unicode)
        # "idn_email_addr": "अजय@डाटा.भारत"  # (Hindi, Unicode)
        # "idn_email_addr": "квіточка@пошта.укр"  # (Ukrainian, Unicode)
        # "idn_email_addr": "θσερ@εχαμπλε.ψομ"  # (Greek, Unicode)
        # "idn_email_addr": "Dörte@Sörensen.example.com"  # (German, Unicode)
        # "idn_email_addr": "коля@пример.рф"  # (Russian, Unicode)
        "ipv4_connection": {"src_addr": "172.20.0.100", "src_port": 65539}
        # "device": {"hostname": "test.example.com", "device_id": "device"}
    },
    "args": {
        "start_time": 1533144553,  # 2018-08-01T17:29:13.150Z
        "stop_time": 1533155353,  # 2018-08-01T20:29:13.150Z
        "duration": 0,
        "response_requested": "ack"
    },
    # "actuator": {"endpoint": {"asset_id": "endpoint6.example.com"}}
}
rsp = {
    "status": 200,
    "status_text": "string",
    "results": {
        # "x-command": {"ref": "INTERNALREFERENCEVALUEABC123"}
        "pairs": {"scan": ["file"], "query": ["features"]}
    }
}


if __name__ == '__main__':
    schema_obj = jadn.load(schema)

    for k, v in schema_obj.analyze().items():
        print(f"{k}: {v}")
    print("")

    # for t, d in schema_obj.types.items():
    #     print(f"{t} - {d}")

    # Validate
    print("\nValidate (specific)")
    print(f"\n\"OpenC2-Command\" - {cmd}")
    print("Invalid" if schema_obj.validate_as(cmd, "OpenC2-Command") else "Valid")
    print(f"\n\"OpenC2-Response\" - {rsp}")
    print("Invalid" if schema_obj.validate_as(rsp, "OpenC2-Response") else "Valid")

    print("\n\nValidate (generic)")
    print(f"\n{cmd}")
    print("Invalid" if schema_obj.validate(cmd) else "Valid")
    print(f"\n{rsp}")
    print("Invalid" if schema_obj.validate(rsp) else "Valid")

    # print(f"\n{schema_obj.dumps()}")

