

class Registry:
    """
    Registry holds a set of key, value pairs. Main intended use is to declare singletons to build a
    dependency graph or Composition root as in Dependency Injection / IOC.

    It is advised to use a single instance of Registry during an application's execution life time.
    """

    def __init__(self):
        self.d = dict()

    def add(self, key, value):
        """
        It is discouraged to replace value of keys.
        Not preferable in the use of dependency injection / inversion of control (IOC) context

        Use `replace` if required
        """
        if key in self.d:
            raise ValidationException('key already exists: {}'.format(key))

        self.d[key] = value

    def replace(self, key, value):
        self.d[key] = value

    def exists(self, key):
        return key in self.d

    def get(self, key):
        if key not in self.d:
            msg = 'key {} not found'.format(key)
            raise NotFoundException(msg)
        return self.d[key]

_registry = Registry()