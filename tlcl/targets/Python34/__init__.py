import .. as targets import Targets as t
from ..targets import Target
from .combinator import Python34Combinator
from .parameter import Python34Parameter
from .type import Python34Type

t.add_new(name='Python3.4', description='Only tested on Python 3.4',
	combinator_cls=Python34Combinator,
	param_cls=Python34Parameter,
	type_cls=Python34Type)