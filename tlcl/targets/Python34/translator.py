class Python34Translator(TLTranslator):
    def define_builtins(self):
        pass

    def define_types(self):
        for typename, t in self.types.items():
            print(t.definition())

    def define_constructors(self):
        for c in self.constructors:
            print(c.definition())

    def define_functions(self):
        for f in self.functions:
            print(f.definition())

    def translate(self):
        self.define_builtins()
        #self.define_types()
        #self.define_constructors()
        #self.define_functions()