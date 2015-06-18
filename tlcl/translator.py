class TLTranslator:
    def __init__(self, schema, constructors, functions, types):
        self.schema = schema
        self.constructors = constructors
        self.functions = functions
        self.types = types

    class TranslateObject(metaclass=ABCMeta):
        @abstractmethod
        def identifier(self):
            raise NotImplemented

        @abstractmethod
        def declaration(self):
            raise NotImplemented

        @abstractmethod
        def definition(self):
            raise NotImplemented

    class Type(TranslateObject):
        def __init__(self, namespace, identifier):
            self.namespace = namespace
            self.identifier = identifier
            self.ident_full = '{}.{}'.format(namespace, identifier) if namespace else identifier
            self.constructors = []

    class Parameter(TranslateObject):
        def __init__(self, _identifier, type):
            self._identifier = _identifier
            self.type = type

    class OptionalParameter(Parameter):
        @property
        def optional_parameter(self):
            return self.parameter

    class Combinator(TranslateObject):
        def __init__(self, namespace, identifier, id, optional_params, params, result_type):
            self.identifier = identifier
            self.namespace = namespace
            self.id = id
            self.optional_params = optional_params
            self.params = params
            self.result_type = result_type

    class Function(Combinator):
        @property
        def function(self):
            return self.combinator


    class Constructor(Combinator):
        @property
        def constructor(self):
            return self.combinator
        

    @abstractmethod
    def translate(self):
        raise NotImplemented