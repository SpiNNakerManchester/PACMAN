from collections import defaultdict

_instances = list()
_methods = defaultdict(dict)


def supports_injection(injectable_class):
    """ Indicate that the class has methods on which objects can be injected
    """
    orig_init = injectable_class.__init__

    def new_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        for method in injectable_class.__dict__.itervalues():
            if hasattr(method, "_type_to_inject"):
                _methods[injectable_class][method._type_to_inject] = method
        _instances.append(self)

    injectable_class.__init__ = new_init
    return injectable_class


def inject(type_to_inject):
    """ Marks a method as something to be called to inject an object of the\
        given type.  The type is just a name for the type, and should match up\
        at some point with some generated data

    :param type_to_inject: The type to be injected using this method
    """
    def wrap(method):
        method._type_to_inject = type_to_inject
        return method
    return wrap


def do_injection(objects_to_inject, objects_to_inject_into=None):
    """ Perform the actual injection of objects

    :param objects_to_inject:\
        The objects to be injected as a dict of type name -> object of type
    :type objects_to_inject: dict(str)->object
    :param object_to_inject_into: \
        The objects whose classes support_injection, or None to use all\
        instances that have been created
    :type objects_to_inject_into: list
    """
    injectees = objects_to_inject_into
    if objects_to_inject_into is None:
        injectees = _instances
    for obj in injectees:
        methods = _methods.get(obj.__class__, None)
        if methods is not None:
            for object_type, object_to_inject in objects_to_inject.iteritems():
                method = methods.get(object_type, None)
                if method is not None:
                    method(obj, object_to_inject)
