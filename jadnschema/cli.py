import argparse
import json
import os
import sys

from . import base
from .convert.message import Message, MessageFormats


def schema_file(path: str) -> dict:
    """
    Load a JADN schema file
    :param path: path to JADN schema
    :return: loaded JADN schema as a dictionary
    """
    ext = os.path.splitext(path)[1]

    if ext == '.jadn':
        try:
            with open(path, "rb") as f:
                return dict(
                    path=path,
                    schema=json.load(f)  # jadn.jadn_load(path)
                )
        except (IOError, TypeError, ValueError):
            pass

    raise TypeError("Invalid instance given")


def instance_file(path: str) -> dict:
    """
    load a JADN message file
    :param path: path to message file
    :return: loaded message file as a Message object
    """
    ext = os.path.splitext(path)[1]
    ext = ext[1:]

    if ext in MessageFormats.values():
        try:
            return dict(
                path=path,
                instance=Message(path, ext)
            )
        except (IOError, TypeError, ValueError):
            pass

    raise TypeError("Invalid schema given")


parser = argparse.ArgumentParser(description="JADN Schema Validation CLI")

parser.add_argument(
    "schema",
    help="JADN Schema to validate with (i.e. filename.jadn)",
    type=schema_file
)

parser.add_argument(
    "-i", "--instance",
    action="append",
    dest="instance",
    help=f"instance to validate (filename.[{','.join(MessageFormats.values())}]) (May be specified multiple times)",
    type=instance_file
)


def run(args: dict, stdout=sys.stdout, stderr=sys.stderr) -> None:
    schema = base.validate_schema(args.get('schema', {}).get('schema', {}))

    if schema and isinstance(schema, list):
        for err in schema:
            stderr.write(f'{err}\n')
        sys.exit(1)
    elif schema:
        stdout.write(f"Valid schema at {args.get('schema', {}).get('path', '')}\n")

    if len(args['instance']) > 0:
        for instance in args['instance']:
            paths = instance.get('path', ''), args.get('schema', {}).get('path', '')
            stdout.write(f"\nValidating instance at {paths[0]} using schema at {paths[1]}\n")
            val_msg = base.validate_instance(schema, instance.get('instance', {}))
            if isinstance(val_msg, list):
                for err in val_msg:
                    stdout.write(f"{err}\n")
            elif isinstance(val_msg, tuple):
                stdout.write(f"Instance '{instance.get('path', '')}' is valid as {val_msg[1]}\n")


def main(args: list) -> None:
    args = args or sys.argv[1:]
    arguments = vars(parser.parse_args(args=args or ["--help"]))
    sys.exit(run(args=arguments))
