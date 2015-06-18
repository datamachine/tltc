class Python34Parameter(TLTranslator.Parameter):
    def identifier(self):
        return self._identifier

    def declaration(self):
        return self._identifier

    def definition(self):
        return self._identifier
