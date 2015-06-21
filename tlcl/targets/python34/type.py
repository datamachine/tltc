from pathlib import Path

type_template="""
class {identifier}(TLType):
    def __init__({param_list}):
        {param_inits}
"""

class Python34Type:
    def __init__(self, schema, ir_type):
        self.schema = schema
        self.ir_type = ir_type
        self.outpath = Path('out/python34/types.py')

        self.identifier = 'raise NotImplemented'
        self.param_list = 'raise NotImplemented'
        self.param_inits = 'raise NotImplemented'

    def preprocess(self):
        ident = self.ir_type.identifier
        if ident.full_ident.isidentifier():
            self.identifier = ident.full_ident

    def definition(self):
        return type_template.format(**self.__dict__)
