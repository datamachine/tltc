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
