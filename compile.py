#!/usr/bin/env python3.4

import sys
import re

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

def strip_comments(schema):
    return re.sub('^\s*//.*$', '\n', schema, flags=re.MULTILINE)

def remove_excess_whitespace(schema):
    return re.sub('\s+', ' ', schema)

def get_constructors(schema):
    while schema:
        constructor = {'opt_args': [], 'arg': []}

        print()
        # get the namespace, identifier, and name (i.e. crc32)
        match = re.match(COMBINATOR_DECL['full-combinator-id'], schema)
        for key, item in match.groupdict().items():
            constructor[key] = item
        schema = schema[match.span()[1]:]

        print(constructor)

        # vector is built in type, ignore this for now
        if constructor['identifier'] == 'vector':
            match = re.match('.*?;', schema)
            print(match)
            schema = schema[match.span()[1]:]
            continue

        # get the optional arguments
        match = re.match(COMBINATOR_DECL['opt-arg'], schema)
        while match:
            opt_arg = match.groupdict()
            constructor['opt_args'] += [opt_arg]
            schema = schema[match.span()[1]:]
            match = re.match(COMBINATOR_DECL['opt-arg'], schema)
            print(constructor)

        # get the args
        match = re.match(COMBINATOR_DECL['arg'], schema)
        if match:
            arg = match.groupdict()
            args += [{arg['identifier']:arg['type']}]
            schema = schema[match.span()[1]:]

        print(constructor)
        # get result type
        match = re.match(COMBINATOR_DECL['result-type'], schema)
        constructor['result_type'] = match.groupdict()['result_type']
        schema = schema[match.span()[1]:]

        print(constructor)
    #print("\n".join([str(m.groupdict()) for m in matches]))
    return ''

def get_raw_combinators(schema):
    schema = strip_comments(schema)
    schema = remove_excess_whitespace(schema)
    return re.findall(r'(.*?;|---.*?---)', schema)
 
def get_combinator_iter(combinator):
    expr = '(?:{}|{}|{})'.format(
        # get the combinator's name and id(crc32) number
        '(?P<name>\S*)#(?P<id>[0-9a-f])',        
        # get the parameters' names and types
        '(?P<param>[^\s\{]*):(?P<param_type>[^\s\}]*)',
        # get the combinator's result type
        '=\s*(?P<type>.*?);'
    )

    #'(?:(?P<name>\S*)#(?P<id>[0-9a-f])|(?P<param>[^\s\{]*):(?P<arg>[^\s\}]*)|=\s*(?P<result_type>.*?);)'

    return re.finditer(expr, combinator)

def get_all_types(combinators):
    types = set()
    for c in combinators:
        #m = re.match('^.*?=\s*(.*)\s*;', c)
        for i in get_combinator_iter(c):
            groups = i.groupdict()
            if groups['type']:
                types.add(groups['type'])
            if (groups['param_type']):
                types.add(groups['param_type'])
    return types

class TLParameter:
    def __init__(self, name, type):
        self.name = name
        self.type = type

class TLOptionalParameter(TLParameter):
    pass

class TLType:
    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name
        self.constructors = []

    def add_constructor(self, constructor):
        self.constructors.append(constructor)

    def __eq__(self, other):
        return (type(other) == type(self) 
            and other.namespace == self.namespace 
            and other.name == self.name)

class TLCombinator:
    def __init__(self, namespace, name, id):
        self.namespace = namespace
        self.name = name
        self.id = int(id, 16)
        self.params = []

    def add_parameter(self, name, type):
        self.paramters.append(TLParameter(name, Type))

    def add_optional_parameter(self, name, type):
        self.paramters.append(TLOptionalParameter(name, Type))

    def __eq__(self, other):
        return self.id == other.id

class TLConstructor(TLCombinator):
    pass

class TLFunction(TLCombinator):
    pass

class TLSchema:
    def __init__(self, schema):
        self.schema = schema
        self._construct_iter_expressions()
        self.types = []
        self.combinators = []

    def _construct_iter_expressions(self):
        tokens = [
            # constructor's full identifier
            '(?P<new_combinator>'
                '(?P<fullname>'
                    '(?:(?P<namespace>{lc-ident-ns})\.|)(?P<name>\S+)'
                ')'
                '#(?P<id>{hex-digit}{{8}})'
            ')'.format(**TL),
            # optional parameter names and types
            '(?P<add_optional_paramer>\{{(?P<opt_param_name>\S+):'
                '(?:(?P<opt_param_namespace>{lc-ident-ns})\.|)(?P<opt_param_typename>\S+)\}})'.format(**TL),
            # parameter's names and types
            '(?P<add_param>(?P<param_name>[^\{\s]+):(?P<param_type>[^\}\s]+))',
            # end of constructor
            '(?P<end_combinator>;)',

            # start the function section
            '(?P<start_functions>{triple-minus}functions{triple-minus})'.format(**TOKENS),

            # start the types section
            '(?P<start_types>{triple-minus}types{triple-minus})'.format(**TOKENS)
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

    def _fsm_start(self, schema_iter):
        return 'constructor_section', {}

    def _fsm_constructor_section(self, schema_iter, **kwargs):
        groups = next(schema_iter).groupdict()
        if groups['new_combinator']:
            return 'new_constructor', {
                'namespace': groups['namespace'],
                'name': groups['name'],
                'id': groups['id'],
            }
        elif groups['start_functions']:
            return 'functions', {}

        return 'error', {}

    def _fsm_new_constructor(self, schema_iter, namespace, name, id):
        constructor = TLConstructor(namespace, name, id)

        if constructor in self.combinators:
            raise Exception('Combinator already exists with id: {}'.format(id))

        self.combinators.append(constructor)

        return 'get_optional_args', {'constructor': constructor}

    def _fsm_get_optional_args(self, schema_iter, constructor):
        groups = next(schema_iter).groupdict()
        if groups['add_optional_paramer']:
            print(groups)
            if groups['opt_param_type'] not in self.types:
                pass

        return 'end', {}

    def _fsm_functions(self, schema_iter):
        return 'end', {}

    def generate_objects(self):
        self.combinators = []
        schema_iter = self.iter_prog.finditer(self.schema)
        try:
            kwargs = {}
            state = 'start' 
            while state not in ['end', 'error'] :
                func = getattr(self, '_fsm_{state}'.format(state=state))
                state, kwargs = func(schema_iter, **kwargs)
        except StopIteration:
            pass


if __name__ == "__main__":
    schema = None
    with open(sys.argv[1]) as fp:
        schema = fp.read()

    #combinators = get_raw_combinators(schema)
    #types = get_all_types(combinators)

    tl_schema = TLSchema(schema)
    tl_schema.generate_objects()
    #print(schema)


    #print("\n".join(raw_combs))
