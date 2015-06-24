from collections import OrderedDict
from pprint import PrettyPrinter

pp = PrettyPrinter(indent=2)

# Character classes
_CHARACTER_CLASSES = OrderedDict()
_CHARACTER_CLASSES['_lc-letter'] = 'a-z'
_CHARACTER_CLASSES['_uc-letter'] = 'A-Z'
_CHARACTER_CLASSES['_digit'] = '0-9'
_CHARACTER_CLASSES['_hex-digit'] = '{_digit}a-f'
_CHARACTER_CLASSES['_underscore'] = '_'
_CHARACTER_CLASSES['_letter'] = '{_lc-letter}{_uc-letter}'
_CHARACTER_CLASSES['_ident-char'] = '{_letter}{_digit}{_underscore}'
_CHARACTER_CLASSES['lc-letter'] = '[{_lc-letter}]'
_CHARACTER_CLASSES['uc-letter'] = '[{_uc-letter}]'
_CHARACTER_CLASSES['digit'] = '[{_digit}]'
_CHARACTER_CLASSES['hex-digit'] = '[{_hex-digit}]'
_CHARACTER_CLASSES['underscore'] = '[{_underscore}]'
_CHARACTER_CLASSES['letter'] = '[{_letter}]'
_CHARACTER_CLASSES['ident-char'] = '[{_ident-char}]'

# Simple identifiers and keywords:
_SIMPLE_IDENTS_AND_KEYWORDS = OrderedDict()
_SIMPLE_IDENTS_AND_KEYWORDS['lc-ident'] = r'{lc-letter}{ident-char}*'
_SIMPLE_IDENTS_AND_KEYWORDS['uc-ident'] = r'{uc-letter}{ident-char}*'
_SIMPLE_IDENTS_AND_KEYWORDS['namespace-ident'] = r'{lc-ident}'
_SIMPLE_IDENTS_AND_KEYWORDS['lc-ident-ns'] = r'(:?{namespace-ident}\.|){lc-ident}'
_SIMPLE_IDENTS_AND_KEYWORDS['uc-ident-ns'] = r'(:?{namespace-ident}\.|){uc-ident}'
_SIMPLE_IDENTS_AND_KEYWORDS['lc-ident-full'] = r'{lc-ident-ns}#{hex-digit}{{1,8}}'

# TODO, These do not belon in this category
_SIMPLE_IDENTS_AND_KEYWORDS['var-ident'] = r'(:?{lc-ident}|{uc-ident})'
_SIMPLE_IDENTS_AND_KEYWORDS['boxed-type-ident'] = r'{uc-ident-ns}'
_SIMPLE_IDENTS_AND_KEYWORDS['type-ident'] = r'(:?{boxed-type-ident}|{lc-ident-ns}|#)'

# Tokens
_TOKENS = OrderedDict()
_TOKENS['underscore'] = '_'
_TOKENS['colon'] = ':'
_TOKENS['semicolon'] = ';'
_TOKENS['open-par'] = '\('
_TOKENS['close-par'] = '\)'
_TOKENS['open-bracket'] = '['
_TOKENS['close-bracket'] = ']'
_TOKENS['open-brace'] = '{{'
_TOKENS['close-brace'] = '}}'
_TOKENS['triple-minus'] = '---'
_TOKENS['nat-const'] = '{digit}+'
_TOKENS['lc-ident-full'] = '{lc-ident-full}'
_TOKENS['lc-ident'] = '{lc-ident}'
_TOKENS['uc-ident-ns'] = '{uc-ident-ns}'
_TOKENS['equals'] = '='
_TOKENS['hash'] = '#'
_TOKENS['question-mark'] = '\?'
_TOKENS['percent'] = '%'
_TOKENS['plus'] = '\+'
_TOKENS['langle'] = '<'
_TOKENS['rangle'] = '>'
_TOKENS['comma'] = ','
_TOKENS['dot'] = '\.'
_TOKENS['asterisk'] = '\*'
_TOKENS['excl-mark'] = '\!'
_TOKENS['Final-kw'] = 'Final'
_TOKENS['New-kw'] = 'New'
_TOKENS['Empty-kw'] = 'Empty'

COMBINATOR_DECL = {}
COMBINATOR_DECL['full-combinator-id'] = '\s*{lc-ident-full}'
COMBINATOR_DECL['opt-arg'] = '\\{{(?P<parameter>{var-ident}):(?P<type>{type-ident})\\}}'
COMBINATOR_DECL['arg'] = r'\s{var-ident}:{var-ident}'
COMBINATOR_DECL['result-type'] = r'=\s*(?P<result_type>.*?)\s*;'

