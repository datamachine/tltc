class Python34Identifier:
    def __init__(self, ir_ident):
        self._ir_ident = ir_ident

    def __str__(self):
        return self.py3ident

    @property
    def ir_ident(self):
        return self._ir_ident

    @property
    def py3ident(self):
        return str(self._ir_ident.ident)

    @staticmethod
    def validate(ident):
        if ident in __builtins__:
            raise Exception('ERROR: identifier "{}" conflicts with python3.4 built-in type'.format(ident))

        if not ident.isidentifier():
            raise Exception('"{}" is not a valid python3.4 identifier'.format(ident))
