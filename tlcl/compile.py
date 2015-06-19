#!/usr/bin/env python3.4

from .ir.schema import TLSchema

if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path
    import sys
    from .targets import Targets as targets

    parser = ArgumentParser(description='Translate a TL schema to the specified target language')
    parser.add_argument('-t', '--target', required=True, choices=targets.available(), help='supported targets: {}'.format(', '.join(targets.available())))
    parser.add_argument('source', nargs='?', help='TL source file')
    args = parser.parse_args(sys.argv[1:])

    schema = None
    with open(args.source, 'r') as fp:
        schema = fp.read()

    tl_schema = TLSchema(schema)
    tl_schema.generate_ir()

    #print('\n'.join([str(t) for t in tl_schema.types]))

    #python3_translator = TLTranslator.init_translator(Python3Translator, tl_schema)
    #python3_translator.translate()
