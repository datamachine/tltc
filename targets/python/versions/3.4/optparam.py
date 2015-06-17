class OptionalParameter(TLTranslator.OptionalParameter):
    def identifier(self):
        return self._identifier

    def declaration(self):
        return self._identifier

    def definition(self):
        return self._identifier
