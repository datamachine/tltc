#!/usr/bin/env python3.4

from .ir.schema import IRSchema

if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path
    import sys
    from .targets import Targets

    parser = ArgumentParser(description='Translate a TL schema to the specified target language')
    parser.add_argument('-t', '--target', required=True, choices=Targets.available(), help='supported targets: {}'.format(', '.join(Targets.available())))
    parser.add_argument('source', nargs='?', help='TL source file')
    args = parser.parse_args(sys.argv[1:])

    schema = None
    with open(args.source, 'r') as fp:
        schema = fp.read()

    tl_schema = IRSchema(schema)
    tl_schema.generate_ir()

    target = Targets.init_target(args.target, tl_schema)
    target.translate()