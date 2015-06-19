#!/usr/bin/env python3.4

import sys
import re
from abc import ABCMeta, abstractmethod
from pathlib import Path





from .syntax.tlsyntax import TLSyntax
from .translate.type import *

class TLParameter:
    def __init__(self, identifier, type_namespace, type_identifier):
        self.identifier = identifier
        self.type_namespace = type_namespace
        self.type_identifier = type_identifier

class TLOptionalParameter(TLParameter):
    pass

class TLCombinator:
    def __init__(self, namespace, identifier, id):
        self.namespace = namespace
        self.identifier = identifier
        self.id = id
        self.optional_params = []
        self.params = []
        self.result_type = None

    def add_parameter(self, identifier, type_namespace, type_identifier):
        self.params.append(TLParameter(identifier, type_namespace, type_identifier))

    def add_optional_parameter(self, identifier, type_namespace, type_identifier):
        self.optional_params.append(TLOptionalParameter(identifier, type_namespace, type_identifier))

    def set_result_type(self, result_type):
        self.result_type = result_type

class TLConstructor(TLCombinator):
    pass

class TLFunction(TLCombinator):
    pass

class TLSchema:
    def __init__(self, schema):
        self.schema = schema
        self._construct_iter_expressions()
        self.types = {}
        self.combinators = {}

    @property
    def functions(self):
        return [c for c_id, c in self.combinators.items() if type(c) is TLFunction]

    @property
    def constructors(self):
        return [c for c_id, c in self.combinators.items() if type(c) is TLConstructor]

    def constructors_with_type(self, namespace, identifer):
        return [c for c in self.constructors if c.result_type.namespace == namespace and c.result_type.identifier == identifier]

    def _construct_iter_expressions(self):
        tokens = [
            # constructor's full identifier
            '(?P<combinator>'
                '(?:(?P<combinator_namespace>{lc-ident-ns})\.|)'
                '(?P<combinator_identifier>\S+)'
                '#(?P<combinator_id>{hex-digit}+)'
            ')'.format(**TLSyntax.TL),
            # optional parameter names and types
            '(?P<optional_parameter>'
                    '(?P<optional_parameter_identifier>\S+):'
                    '(?P<optional_parameter_type>'
                        '(?:(?P<optional_parameter_type_namespace>{lc-ident-ns})\.|)'
                        '(?P<optional_parameter_type_identifier>\S+)'
                    ')'
                '\}}'
            ')'.format(**TLSyntax.TL),
            # parameter's names and types
            '(?P<parameter>'
                '(?:'
                    '(?P<parameter_identifier>\S+):'
                    '(?P<parameter_type>'
                        '(?:(?P<parameter_type_namespace>{lc-ident-ns})\.|)'
                        '(?P<parameter_type_identifier>\S+)'
                    ')'
                ')'
                '|(?P<parameter_nat>'
                    '#'
                ')'
                '|\[\s+'
                    '(?P<parameter_multiplicity>\S+)'
                  '\s+\]'
            ')'.format(**TLSyntax.TL),

            # get the combinator's Type
            '=\s*'
            '(?P<combinator_result_type>'
                '(?:(?P<combinator_result_type_namespace>{lc-ident-ns})\.|)'
                '(?P<combinator_result_type_identifier>[^;]+)'
            ')'.format(**TLSyntax.TL),

            # end of constructor
            '(?P<combinator_end>;)',

            # start the function section
            '(?P<start_functions>{triple-minus}functions{triple-minus})'.format(**TLSyntax.TL),

            # start the types section
            '(?P<start_types>{triple-minus}types{triple-minus})'.format(**TLSyntax.TL),

            # catch anything else
            '(?P<invalid_syntax>\S+)'
        ]
        self.iter_expr = '(?:{})'.format('|'.join(tokens))
        self.iter_prog = re.compile(self.iter_expr)

    def _fsm_combinators(self, groups, section):
        if section == 'constructors' and groups['start_functions']:
            return 'combinators', {'section':'functions'}

        if not groups['combinator']:
            return 'error', {'groups': groups}

        combinator_namespace = groups['combinator_namespace']
        combinator_identifier = groups['combinator_identifier']
        combinator_id = int(groups['combinator_id'], 16)

        if combinator_id in self.combinators:
            raise Exception('Combinator already exists with id: {}'.format(combinator_id))

        if section not in ['functions', 'constructors']:
            return 'error', {'groups', groups}

        combinator_cls = TLConstructor if section == 'constructors' else TLFunction

        combinator = combinator_cls(combinator_namespace, combinator_identifier, combinator_id)

        self.combinators[combinator.id] = combinator
        return 'combinator_optional_params', {'combinator': combinator, 'section':section}

    def _fsm_combinator_optional_params(self, groups, section, combinator):
        if not groups['optional_parameter']:
            return self._fsm_combinator_params(groups, section, combinator)


        t = self.types.get(groups['optional_parameter_type'], None)
        if not t:
            t = TLType(groups['optional_parameter_type_namespace'], groups['optional_parameter_type_identifier'])
            self.types[groups['optional_parameter_type']] = t

        combinator.add_optional_parameter(groups['optional_parameter_identifier'], groups['optional_parameter_type_namespace'], groups['optional_parameter_type_identifier'])

        return 'combinator_optional_params', {'combinator':combinator, 'section':section}

    def _fsm_combinator_params(self, groups, section, combinator):
        if not groups['parameter']:
            return self._fsm_combinator_result_type(groups, section, combinator)

        t = self.types.get(groups['parameter_type'], None)
        if not t:
            t = TLType(groups['parameter_type_namespace'], groups['parameter_type_identifier'])
            self.types[groups['parameter_type']] = t

        combinator.add_parameter(groups['parameter_identifier'], groups['parameter_type_namespace'], groups['parameter_type_identifier'])

        return 'combinator_params', {'combinator':combinator, 'section':section}

    def _fsm_combinator_result_type(self, groups, section, combinator):
        if not groups['combinator_result_type']:
            return 'error', {'groups':groups}

        t = self.types.get(groups['combinator_result_type'], None)
        if not t:
            t = TLType(groups['combinator_result_type_namespace'], groups['combinator_result_type_identifier'])
            self.types[groups['combinator_result_type']] = t
        combinator.set_result_type(t)

        return 'combinator_end', {'section':section}

    def _fsm_combinator_end(self, groups, section):
        if not groups['combinator_end']:
            return 'error', {}

        return 'combinators', {'section':section}

    def _fsm_error(self, matches, **kwargs):
        print('_fsm_error')
        print('ERROR:\t{}:\t{}'.format(matches, kwargs))
        return 'quit', {}

    def generate_intermediate_objects(self):
        self.combinators = {}
        schema_iter = self.iter_prog.finditer(self.schema)
        kwargs = {'section': 'constructors'}
        state = 'combinators'
        for i in schema_iter:
            func = getattr(self, '_fsm_{}'.format(state))
            state, kwargs = func(i.groupdict(), **kwargs)

            if state == 'quit':
                return _fsm_error(i, kwargs)

    @staticmethod
    def init_translator(translator_type, schema):
        types = {key:translator_type.Type(t.namespace, t.identifier) for key, t in schema.types.items()}
        constructors = []
        for c in schema.constructors:
            optional_params = [translator_type.OptionalParameter(op.identifier, translator_type.Type(op.type_namespace, op.type_identifier)) for op in c.optional_params]
            params = [translator_type.Parameter(p.identifier, translator_type.Type(p.type_namespace, p.type_identifier)) for p in c.params]
            result_type = types[c.result_type.ident_full]
            constructor = translator_type.Constructor(c.namespace, c.identifier, c.id, optional_params, params, result_type)
            constructors.append(constructor)
            result_type.constructors.append(constructor)

        functions = []
        for c in schema.functions:
            optional_params = [translator_type.OptionalParameter(op.identifier, translator_type.Type(op.type_namespace, op.type_identifier)) for op in c.optional_params]
            params = [translator_type.Parameter(p.identifier, translator_type.Type(p.type_namespace, p.type_identifier)) for p in c.params]
            result_type = types[c.result_type.ident_full]
            function = translator_type.Function(c.namespace, c.identifier, c.id, optional_params, params, result_type)
            functions.append(function)

        return translator_type(schema, constructors, functions, types)

if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path
    import sys
    from .targets import AVAILABLE_TARGETS

    parser = ArgumentParser(description='Translate a TL schema to the specified target language')
    parser.add_argument('-t', '--target', required=True, choices=AVAILABLE_TARGETS.keys(), help='supported targets: {}'.format(', '.join(AVAILABLE_TARGETS.keys())))
    parser.add_argument('source', nargs='?', help='TL source file')
    args = parser.parse_args(sys.argv[1:])

    schema = None
    with open(args.source, 'r') as fp:
        schema = fp.read()

    tl_schema = TLSchema(schema)
    tl_schema.generate_intermediate_objects()

    #python3_translator = TLTranslator.init_translator(Python3Translator, tl_schema)
    #python3_translator.translate()
