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
        def __init__(self, _identifier, type):
            self._identifier = _identifier
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
    type_template="""
class {identifier}(TLType):
    def __init__({param_list}):
        {param_inits}
"""

    class Type(TLTranslator.Type):
        def identifier(self):
            return self.identifier

        def declaration(self):
            return self.identifier

        def definition(self):
            member_vars = []
            for c in self.constructors:
                member_vars += [p.identifier() for p in c.params if p.identifier() and p.identifier() not in member_vars]
            if not member_vars:
                member_vars = ['combinator_id']
            param_list = ', '.join(['self'] + member_vars)
            param_inits = '\n'.join([''] + ['        self.{0} = {0}'.format(m) for m in member_vars])
            if not param_inits:
                param_inits = 'pass'
            return Python3Translator.type_template.format(
                identifier=self.identifier,
                param_list=param_list,
                param_inits=param_inits)

    class OptionalParameter(TLTranslator.OptionalParameter):
        def identifier(self):
            return self._identifier

        def declaration(self):
            return self._identifier

        def definition(self):
            return self._identifier

    class Parameter(TLTranslator.Parameter):
        def identifier(self):
            return self._identifier

        def declaration(self):
            return self._identifier

        def definition(self):
            return self._identifier

    combinator_template="""
class {identifier}({base_class}):
    id = {hex_id}

    @staticmethod
    def new({params}):
        return {result_type_identifer}({type_init_args})

    @staticmethod
    def serialize(obj):
        return {serialize}

    @staticmethod
    def deserialize(io_bytes):
        return {identifier}.new(...)
"""

    class Constructor(TLTranslator.Constructor):
        def identifier(self):
            return self.combinator.identifier

        def declaration(self):
            return None

        def definition(self):
            param_identifiers = [p.identifier() for p in self.params if p.identifier()]
            params = ', '.join(param_identifiers)
            type_init_args = ', '.join(['{}.id'.format(self.identifier)] + param_identifiers)
            serialize = ' + '.join(['struct.pack(\'!i\', id)'] + ['{}.serialize()'.format(p) for p in param_identifiers])
            return Python3Translator.combinator_template.format(
                identifier=self.identifier,
                base_class='TLConstructor',
                hex_id=self.id,
                params=params,
                result_type_identifer=self.result_type.identifier,
                type_init_args=type_init_args,
                serialize=serialize)

    class Function(TLTranslator.Function):
        def identifier(self):
            return self.identifier

        def declaration(self):
            return None

        def definition(self):
            param_identifiers = [p.identifier() for p in self.params if p.identifier()]
            params = ','.join(param_identifiers)
            type_init_args = ', '.join(['{}.id'.format(self.identifier)] + param_identifiers)
            serialize = ' + '.join(['struct.pack(\'!i\', id)'] + ['{}.serialize()'.format(p) for p in param_identifiers])
            return Python3Translator.combinator_template.format(
                identifier=self.identifier,
                base_class='TLFunction',
                hex_id=self.id,
                params=params,
                result_type_identifer=self.result_type.identifier,
                type_init_args=type_init_args,
                serialize=serialize)

    builtin_templates = []
    builtin_templates += [
"""
from abc import ABCMeta, abstractmethod
from collections import abc
from numbers import Integral

class TLType(metaclass=ABCMeta):
    @abstractmethod
    def serialize(obj):
        raise NotImplemented

    @abstractmethod
    def deserialize(self, obj, bytes_io):
        raise NotImplemented
"""]

    builtin_templates += [
"""
class TLCombinator(metaclass=ABCMeta):
    combinators = {}

    @staticmethod
    def add_combinator(combinator_type):
        TLCombinator.combinators[combinator.id] = combinator_type

    @staticmethod
    @abstractmethod
    def serialize(obj):
        raise NotImplemented

    @staticmethod
    @abstractmethod
    def deserialize(self, obj, bytes_io):
        raise NotImplemented
"""
]

    builtin_templates += [
"""
class TLConstructor(TLCombinator):
    pass
"""
]

    builtin_templates += [
"""
class TLFunction(TLCombinator):
    pass
"""
]

    builtin_templates += [
"""
class Int(numbers.Integral, TLType):
    def __init__(self, _int):
        self._int = int(_int)

    def serialize(obj):
        pass

    def deserialize(io_string):
        pass

    """
    numbers.Integral abstract methods
    """
    def default_integral_override(name):
        def integral_override(self, *args, **kwargs):
            return Int(getattr(self._int, name)(*args, **kwargs))
        return integral_override

    def __int__(self):
        return self._int

for abstract_method in Int.__abstractmethods__:
    setattr(Int, abstract_method, Int.default_integral_override(abstract_method))
Int.__abstractmethods__ = frozenset()
"""
]

    builtin_templates += [
"""
class Long(TLType):
    def __init__(self, _long):
        self._long = int(_long)

    def __getattr__(self, name):
        return getattr(self._long, name)

    def serialize(obj):
        pass

    def deserialize(io_string):
        pass
"""
]

    builtin_templates += [
"""
class Bool(TLType):
    def __init__(self, _bool):
        self._bool = bool(_bool)

    def __getattr__(self, name):
        return getattr(self._bool, name)

    def serialize(obj):
        pass

    def deserialize(io_string):
        pass
"""
]

    def define_builtins(self):
        for t in Python3Translator.builtin_templates:
            print(t)

    def define_types(self):
        for typename, t in self.types.items():
            print(t.definition())

    def define_constructors(self):
        for c in self.constructors:
            print(c.definition())

    def define_functions(self):
        for f in self.functions:
            print(f.definition())

    def translate(self):
        self.define_builtins()
        #self.define_types()
        #self.define_constructors()
        #self.define_functions()


if __name__ == "__main__":
    schema = None
    with open(sys.argv[1]) as fp:
        schema = fp.read()

    tl_schema = TLSchema(schema)
    tl_schema.generate_intermediate_objects()

    python3_translator = TLTranslator.init_translator(Python3Translator, tl_schema)
    python3_translator.translate()
