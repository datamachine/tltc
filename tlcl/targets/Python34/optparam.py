from tlcl.translate.optparam import TLOptionalParameter

class Python34OptionalParameter(TLOptionalParameter):
    def identifier(self):
        return self._identifier

    def declaration(self):
        return self._identifier

    def definition(self):
        return self._identifier
