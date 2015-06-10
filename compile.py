#!/usr/bin/env python3.4

import sys
import re
from abc import ABCMeta, abstractmethod

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
#print("\n".join([name + " ::= " + item for name, item in TL.items()]))

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

#print(TL['lc-ident-ns'])
#print("\n".join([name + " ::= " + item for name, item in TL.items()]))

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

class TLParameter:
    def __init__(self, name, type):
        self.name = name
        self.type = type

class TLOptionalParameter(TLParameter):
    pass

    @abstractmethod
    def translate(self):
        raise NotImplemented

class TLType:
    def __init__(self, namespace, identifier):
        self.namespace = namespace
        self.identifier = identifier
        self.constructors = []

    def add_constructor(self, constructor):
        self.constructors.append(constructor)

class TLCombinator:
    def __init__(self, namespace, identifier, id):
        self.namespace = namespace
        self.identifier = identifier
        self.id = id
        self.optional_params = []
        self.params = []
        self.result_type = None

    def add_parameter(self, param_name, param_type):
        self.params.append(TLParameter(param_name, param_type))

    def add_optional_parameter(self, param_name, param_type):
        self.optional_params.append(TLOptionalParameter(param_name, param_type))

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
        self.types = []
        self.combinators = {}

    @property
    def functions(self):
        return [c for c_id, c in self.combinators.items() if type(c) is TLConstructor]

    @property
    def constructors(self):
        return [c for c_id, c in self.combinators.items() if type(c) is TLFunction]
        

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
                    '(?:(?P<optional_parameter_type_namespace>{lc-ident-ns})\.|)'
                    '(?P<optional_parameter_type_identifier>\S+)'
                '\}}'
            ')'.format(**TL),
            # parameter's names and types
            '(?P<parameter>'
                '(?:'
                    '(?P<parameter_identifier>\S+):'
                    '(?:(?P<parameter_type_namespace>{lc-ident-ns})\.|)'
                    '(?P<parameter_type_identifier>\S+)'
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

    def get_type(self, namespace, name, create_if_new=False):
        t = TLType(namespace, name)
        try:
            return next(filter(lambda x: x == t, self.types))
        except StopIteration:
            if create_if_new:
                self.types.append(t)
                return t
        return None

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

        t = self.get_type(groups['optional_parameter_type_namespace'], groups['optional_parameter_type_identifier'], True)
        combinator.add_optional_parameter(groups['optional_parameter_identifier'], t)
        #print('\toptpar: {optional_parameter}'.format(**groups))
        return 'combinator_optional_params', {'combinator':combinator, 'section':section}

    def _fsm_combinator_params(self, groups, section, combinator):
        if not groups['parameter']:
            return self._fsm_combinator_result_type(groups, section, combinator)

        t = self.get_type(groups['parameter_type_namespace'], groups['parameter_type_identifier'], True)
        combinator.add_parameter(groups['parameter_identifier'], t)
        #print('\tparam:  {parameter}'.format(**groups))
        return 'combinator_params', {'combinator':combinator, 'section':section}

    def _fsm_combinator_result_type(self, groups, section, combinator):
        if not groups['combinator_result_type']:
            return 'error', {'groups':groups}

        t = self.get_type(groups['combinator_result_type_namespace'], groups['combinator_result_type_identifier'], True)
        combinator.set_result_type(t)

        #print('\ttype:   {combinator_type}'.format(**groups))
        return 'combinator_end', {'section':section}

    def _fsm_combinator_end(self, groups, section):
        if not groups['combinator_end']:
            return 'error', {}

        #print()
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
        def __init__(self, tl_type):
            self.tl_type = tl_type

    class Combinator(TranslateObject):
        def __init__(self, combinator, optional_params, params, result_type):
            self.combinator = combinator
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

    class Parameter(TranslateObject):
        def __init__(self, parameter):
            self.parameter = parameter

    class OptionalParameter(Parameter):
        @property
        def optional_parameter(self):
            return self.parameter
        

    @abstractmethod
    def translate(self):
        raise NotImplemented

    @staticmethod
    def init_translator(translator_type, schema):
        # combinators = []
        # for c_id, c in schema.combinators.items():
        #     params = [translator_type.OptionalParameter(p) if type(p) is type(TLOptionalParameter) else translator_type.Parameter(p) for p in c.params]
        #     result_type = translator_type.Type(c.result_type)
        #     combinator = None

        #     if type(c) is type(TLConstructor):
        #         combinator = translator_type.Constructor(c, params, result_type)
        #     elif type(c) is type(TLFunction):
        #         combinator = translator_type.Function(c, params, result_type)
        #     else:
        #         raise Exception('invalid combinator type: {}'.format(type(c)))
        #
        #    combinators.append(combinator)

        constructors = []
        for c in schema.constructors:
            optional_params = [translator_type.OptionalParameter(op) for op in c.optional_params]
            params = [translator_type.Parameter(p) for p in c.params]
            result_type = translator_type.Type(c.result_type)
            constructor = translator_type.Constructor(c, optional_params, params, result_type)
            constructors.append(constructor)

        functions = []
        for c in schema.functions:
            optional_params = [translator_type.OptionalParameter(op) for op in c.optional_params]
            params = [translator_type.Parameter(p) for p in c.params]
            result_type = translator_type.Type(c.result_type)
            function = translator_type.Function(c, optional_params, params, result_type)
            functions.append(function)

        types = [translator_type.Type(t) for t in schema.types]

        return translator_type(schema, constructors, functions, types)

class Python3Translator(TLTranslator):
    class Type(TLTranslator.Type):
        def identifier(self):
            return self.tl_type.name

        def declaration(self):
            return self.tl_type.name

        def definition(self):
            return '\n'.join([
                'class {identifier}(TLObject):',
                '   pass',
                ''
                ]).format(identifier=self.tl_type.identifier)

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

    class Function(TLTranslator.Function):
        def identifier(self):
            return self.combinator.identifier

        def declaration(self):
            return None

        def definition(self):
            return '\n'.join([
                'class {}(TLObject):'.format(self.identifier()),
                '    id = int(\'{:x}\', 16)'.format(self.combinator.id),
                '',
                '    def __init__(self)',
                '       pass',
                '',
                '    def __call__(self):',
                '        pass',
                ''
                ])

    class Constructor(TLTranslator.Constructor):
        def identifier(self):
            return self.combinator.identifier

        def declaration(self):
            return None

        def definition(self):
            return '\n'.join([
                'class {}(TLObject):'.format(self.identifier()),
                '    id = int(\'{:x}\', 16)'.format(self.combinator.id),
                '',
                '    def __init__(self)',
                '       pass',
                '',
                '    def __call__(self):',
                '        pass',
                ''
                ])

    def define_types(self):
        print(''
            'from abc import ABCMeta, abstractmethod\n'
            '\n'
            'class TLObject(metaclass=ABCMeta):\n'
            '   @abstractmethod\n'
            '   def serialize(self):\n'
            '       raise NotImplemented\n'
            )

        for t in self.types:
            print(t.definition())

    def translate(self):
        self.define_types()


if __name__ == "__main__":
    schema = None
    with open(sys.argv[1]) as fp:
        schema = fp.read()

    #combinators = get_raw_combinators(schema)
    #types = get_all_types(combinators)

    tl_schema = TLSchema(schema)
    tl_schema.generate_intermediate_objects()

    python3_translator = TLTranslator.init_translator(Python3Translator, tl_schema)
    python3_translator.translate()