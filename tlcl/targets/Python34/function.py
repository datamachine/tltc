class Python34Function(TLTranslator.Function):
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
