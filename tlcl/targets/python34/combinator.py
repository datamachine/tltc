lscombinator_template="""
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

class Python34Combinator:
    __slots__ = ['namespace_ident', 'ident', 'optargs', 'args', 'result_type']

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
