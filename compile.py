#!/usr/bin/env python3.4

import sys
import re
from abc import ABCMeta, abstractmethod
from pathlib import Path

# Character classes
TL = {}
TL['lc-letter'] = 'a-z'
TL['uc-letter'] = 'A-Z'
TL['digit'] = '0-9'
TL['hex-digit'] = '{digit}a-f'.format(**TL)
TL['underscore'] = '_'
TL['letter'] = '{lc-letter}{uc-letter}'.format(**TL)
TL['ident-char'] = '{letter}{digit}{underscore}'.format(**TL)
TL = { name: '[{}]'.format(c) for name, c in TL.items() }

# Simple identifiers and keywords:
TL['lc-ident'] = r'{lc-letter}{ident-char}*'.format(**TL)
TL['uc-ident'] = r'{uc-letter}{ident-char}*'.format(**TL)
TL['namespace-ident'] = r'{lc-ident}'.format(**TL)
TL['lc-ident-ns'] = r'(:?{namespace-ident}\.|)(:?{lc-ident})'.format(**TL)
TL['uc-ident-ns'] = r'(:?{namespace-ident}\.|)(:?{uc-ident})'.format(**TL)
TL['lc-ident-full'] = r'(:?{lc-ident-ns})#({hex-digit}{{8}})'.format(**TL)

TL['var-ident'] = r'(:?{lc-ident}|{uc-ident})'.format(**TL)
TL['boxed-type-ident'] = r'{uc-ident-ns}'.format(**TL)
TL['type-ident'] = r'(:?{boxed-type-ident}|{lc-ident-ns}|#)'.format(**TL)

# Tokens
TOKENS = {}
TOKENS['underscore'] = '_'
TOKENS['colon'] = ':'
TOKENS['semicolon'] = ';'
TOKENS['open-par'] = '('
TOKENS['close-par'] = ')'
TOKENS['open-bracket'] = '['
TOKENS['close-bracket'] = ']'
TOKENS['open-brace'] = '{'
TOKENS['close-brace'] = '}'
TOKENS['triple-minus'] = '---'
TOKENS['nat-const'] = '{digit}+'.format(**TL)
TOKENS['lc-ident-full'] = TL['lc-ident-full']
TOKENS['lc-ident'] = TL['lc-ident']
TOKENS['uc-ident-ns'] = TL['uc-ident-ns']
TOKENS['equals'] = '='
TOKENS['hash'] = '#'
TOKENS['question-mark'] = '?'
TOKENS['percent'] = '%'
TOKENS['plus'] = '+'
TOKENS['langle'] = '<'
TOKENS['rangle'] = '>'
TOKENS['comma'] = ','
TOKENS['dot'] = '.'
TOKENS['asterisk'] = '*'
TOKENS['excl-mark'] = '!'
TOKENS['Final-kw'] = 'Final'
TOKENS['New-kw'] = 'New'
TOKENS['Empty-kw'] = 'Empty'
TOKENS = {name: r'\s*{}'.format(item) for name, item in TOKENS.items()}

COMBINATOR_DECL = {}
COMBINATOR_DECL['full-combinator-id'] = '\s*{lc-ident-full}'.format(**TL)
COMBINATOR_DECL['opt-arg'] = r'\s*{{(?P<parameter>{var-ident}):(?P<type>{type-ident})}}'.format(**TL)
COMBINATOR_DECL['arg'] = r'\s{var-ident}:{var-ident}'.format(**TL)
COMBINATOR_DECL['result-type'] = r'\s*=\s*(?P<result_type>.*?)\s*;'

class TLType:
    def __init__(self, namespace, identifier):
        self.namespace = namespace
        self.identifier = identifier
        self.ident_full = '{}.{}'.format(namespace, identifier) if namespace else identifier

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
            ')'.format(**TL),
            # optional parameter names and types
            '(?P<optional_parameter>'
                    '(?P<optional_parameter_identifier>\S+):'
                    '(?P<optional_parameter_type>'
                        '(?:(?P<optional_parameter_type_namespace>{lc-ident-ns})\.|)'
                        '(?P<optional_parameter_type_identifier>\S+)'
                    ')'
                '\}}'
            ')'.format(**TL),
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
            ')'.format(**TL),

            # get the combinator's Type
            '=\s*'
            '(?P<combinator_result_type>'
                '(?:(?P<combinator_result_type_namespace>{lc-ident-ns})\.|)'
                '(?P<combinator_result_type_identifier>[^;]+)'
            ')'.format(**TL),

            # end of constructor
            '(?P<combinator_end>;)',

            # start the function section
            '(?P<start_functions>{triple-minus}functions{triple-minus})'.format(**TOKENS),

            # start the types section
            '(?P<start_types>{triple-minus}types{triple-minus})'.format(**TOKENS),

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

        if groups['combinator_id'] in self.combinators:
            raise Exception('Combinator already exists with id: {}'.format(groups['combinator_id']))

        combinator = None
        if section == 'constructors':
            combinator = TLConstructor(groups['combinator_namespace'], groups['combinator_identifier'], groups['combinator_id'])
        elif section == 'functions':
            combinator = TLFunction(groups['combinator_namespace'], groups['combinator_identifier'], groups['combinator_id'])
        else:
            return 'error', {'groups', groups}

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

class TLTranslator:
    def __init__(self, schema, constructors, functions, types):
        self.schema = schema
        self.constructors = constructors
        self.functions = functions
        self.types = types

    class TranslateObject(metaclass=ABCMeta):
        @abstractmethod
        def identifier(self):
            raise NotImplemented

        @abstractmethod
        def declaration(self):
            raise NotImplemented

        @abstractmethod
        def definition(self):
            raise NotImplemented

    class Type(TranslateObject):
        def __init__(self, namespace, identifier):
            self.namespace = namespace
            self.identifier = identifier
            self.ident_full = '{}.{}'.format(namespace, identifier) if namespace else identifier
            self.constructors = []

    class Parameter(TranslateObject):
        def __init__(self, identifier, type):
            self.identifier = identifier
            self.type = type

    class OptionalParameter(Parameter):
        @property
        def optional_parameter(self):
            return self.parameter

    class Combinator(TranslateObject):
        def __init__(self, namespace, identifier, id, optional_params, params, result_type):
            self.identifier = identifier
            self.namespace = namespace
            self.id = id
            self.optional_params = optional_params
            self.params = params
            self.result_type = result_type

    class Function(Combinator):
        @property
        def function(self):
            return self.combinator


    class Constructor(Combinator):
        @property
        def constructor(self):
            return self.combinator
        

    @abstractmethod
    def translate(self):
        raise NotImplemented

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

class Python3Translator(TLTranslator):
    class Type(TLTranslator.Type):
        def identifier(self):
            return self.identifier

        def declaration(self):
            return self.identifier

        def definition(self):
            member_vars = []
            for c in self.constructors:
                member_vars += [p.identifier for p in c.params if p.identifier and p.identifier not in member_vars]
            init_params = ', '.join(['self'] + member_vars)
            init_member_vars = '\n'.join(['        self.{0} = {0}'.format(m) for m in member_vars])
            if not init_member_vars:
                init_member_vars = '        pass'
            return '\n'.join([
                'class {identifier}(TLType):',
                '    def __init__({})'.format(init_params),
                '{}'.format(init_member_vars),
                ''
                ]).format(identifier=self.identifier)

    class OptionalParameter(TLTranslator.OptionalParameter):
        def identifier(self):
            return self.parameter.name

        def declaration(self):
            return self.parameter.name

        def definition(self):
            return self.parameter.name

    class Parameter(TLTranslator.Parameter):
        def identifier(self):
            return self.parameter.name

        def declaration(self):
            return self.parameter.name

        def definition(self):
            return self.parameter.name

    class Constructor(TLTranslator.Constructor):
        def identifier(self):
            return self.combinator.identifier

        def declaration(self):
            return None

        def definition(self):
            param_identifier = [p.identifier for p in self.params if p.identifier]
            param_inits = '\n'.join('        {0} = {1}({0})'.format(p.identifier, p.type.identifier) for p in self.params)
            serialize_return = ' + '.join(['struct.pack(!\'i\', id)'] + ['{}.serialize()'.format(p) for p in param_identifier])
            return '\n'.join([
                'class {}(TLConstructor):'.format(self.identifier),
                '    id = 0x{}'.format(self.id),
                '',
                '    @staticmethod',
                '    def new({}):'.format(', '.join(['self'] + param_identifier)),
                '{}'.format(param_inits),
                '',
                '        return {}({})'.format(self.result_type.identifier, ', '.join(param_identifier)),
                '',
                '    @staticmethod',
                '    def serialize(obj):',
                '        return {}'.format(serialize_return),
                '',
                '    @staticmethod',
                '    def deserialize(io_bytes):',
                '        return {}.new({})'.format(self.identifier, '...'),
                '',
                ])

    class Function(TLTranslator.Function):
        def identifier(self):
            return self.identifier

        def declaration(self):
            return None

        def definition(self):
            param_identifier = [p.identifier for p in self.params if p.identifier]
            param_inits = '\n'.join('        {0} = {1}({0})'.format(p.identifier, p.type.identifier) for p in self.params)
            serialize_return = ' + '.join(['struct.pack(!\'i\', id)'] + ['{}.serialize()'.format(p) for p in param_identifier])
            return '\n'.join([
                'class {}(TLFunction):'.format(self.identifier),
                '    id = 0x{}'.format(self.id),
                '',
                '    @staticmethod',
                '    def new({}):'.format(', '.join(['self'] + param_identifier)),
                '{}'.format(param_inits),
                '',
                '        return {}({})'.format(self.result_type.identifier, ', '.join(param_identifier)),
                '',
                '    @staticmethod',
                '    def serialize(obj):',
                '        return {}'.format(serialize_return),
                '',
                '    @staticmethod',
                '    def deserialize(io_bytes):',
                '        return {}.new({})'.format(self.identifier, '...'),
                '',
                ])

    def define_types(self):
        print('\n'.join([
            'from abc import ABCMeta, abstractmethod',
            '',
            'class TLObject(metaclass=ABCMeta):',
            '    @staticmethod',
            '    @abstractmethod',
            '    def serialize(obj):',
            '        raise NotImplemented',
            '',
            '    @staticmethod',
            '    @abstractmethod',
            '    def deserialize(self, obj, bytes_io):',
            '        raise NotImplemented',
            ''
            ])
        )


        print('\n'.join([
            'class TLCombinator(TLObject):',
            '',
            '    combinators = {}',
            '',
            '    def __init__(self):',
            '        combinators[self.id] = self',
            ''
            ])
        )

        print('\n'.join([
            'class TLConstructor(TLCombinator):',
            '    pass',
            ''
            ])
        )

        print('\n'.join([
            'class TLFunction(TLCombinator):',
            '    pass',
            ''
            ])
        )

        for typename, t in self.types.items():
            print(t.definition())

    def define_constructors(self):
        for c in self.constructors:
            print(c.definition())

    def define_functions(self):
        for f in self.functions:
            print(f.definition())

    def translate(self):
        self.define_types()
        self.define_constructors()
        self.define_functions()


if __name__ == "__main__":
    schema = None
    with open(sys.argv[1]) as fp:
        schema = fp.read()

    tl_schema = TLSchema(schema)
    tl_schema.generate_intermediate_objects()

    python3_translator = TLTranslator.init_translator(Python3Translator, tl_schema)
    python3_translator.translate()
