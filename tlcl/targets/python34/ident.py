class Python34Identifier:
    def __init__(self, ir_ident):
        self._ir_ident = ir_ident

    def __str__(self):
        return self._ir_ident.ident

    @property
    def ir_ident(self):
        return self._ir_ident
    