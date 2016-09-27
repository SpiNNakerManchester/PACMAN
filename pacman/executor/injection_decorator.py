from collections import defaultdict
from functools import wraps
import inspect

_instances = list()
_methods = defaultdict(dict)
_injectables = None


class InjectionException(Exception):
    """ Raised when there is an error with injection
    """


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

        @wraps(method)
        def wrapper(obj, arg):
            method(obj, arg)
            if arg is not None:
                wrapper._called = True

        wrapper._type_to_inject = type_to_inject
        wrapper._called = False
        return wrapper
    return wrap


def requires_injection(types_required):
    """ Indicates that injection of the given types is required before this\
        method is called; an Exception is raised if the types have not been\
        injected

    :param types_required: A list of types that must have been injected
    :type types_required: list of str
    """
    def wrap(wrapped_method):

        @wraps(wrapped_method)
        def wrapper(obj, *args, **kwargs):
            methods = dict()
            for cls in obj.__class__.__mro__:
                cls_methods = _methods.get(cls, {})
                methods.update(cls_methods)
            for object_type in types_required:
                method = methods.get(object_type, None)
                if method is None:
                    raise InjectionException(
                        "No injector for type {} for object {}"
                        .format(object_type, obj))
                if not method._called:
                    raise InjectionException(
                        "Type {} has not been injected for object {}"
                        .format(object_type, obj))
            return wrapped_method(obj, *args, **kwargs)
        return wrapper
    return wrap


def inject_items(types):
    """ Indicates values that need to be injected into the method

    :param types: A dict of method argument name to type name to be injected
    """
    def wrap(wrapped_method):

        @wraps(wrapped_method)
        def wrapper(obj, *args, **kwargs):

            method_args = inspect.getargspec(wrapped_method)
            for type_arg in types:
                if type_arg not in method_args.args:
                    raise InjectionException(
                        "Argument {} does not exist for method {} of"
                        " {}".format(
                            type_arg, wrapped_method.__name__,
                            obj.__class__))

            if _injectables is None:
                raise InjectionException(
                    "No injectable objects have been provided")
            new_args = dict(kwargs)
            for arg, arg_type in types.iteritems():
                if arg_type not in _injectables:
                    raise InjectionException(
                        "Cannot find object of type {} to inject into"
                        " method {} of {}".format(
                            arg_type, wrapped_method.__name__, obj.__class__))
                value = _injectables.get(arg_type, None)
                if arg in new_args:
                    raise InjectionException(
                        "Argument {} was already provided to"
                        " method {} of {}".format(
                            arg, wrapped_method.__name, obj.__class__))
                new_args[arg] = value
            return wrapped_method(obj, *args, **new_args)
        return wrapper
    return wrap


def provide_injectables(injectables):
    """ Set the objects from which values should be injected into methods

    :param injectables: A dict of type to value
    """
    global _injectables
    if _injectables is not None:
        raise InjectionException("Injectables have already been defined")
    _injectables = injectables


def clear_injectables():
    """ Clear the current set of injectables
    """
    global _injectables
    _injectables = None


def do_injection(objects_to_inject, objects_to_inject_into=None):
    """ Perform the actual injection of objects

    :param objects_to_inject:\
        The objects to be injected as a dict of type name -> object of type
    :type objects_to_inject: dict(str)->object
    :param objects_to_inject_into: \
        The objects whose classes support_injection, or None to use all\
        instances that have been created
    :type objects_to_inject_into: list
    """
    injectees = objects_to_inject_into
    if objects_to_inject_into is None:
        injectees = _instances
    for obj in injectees:
        methods = dict()
        for cls in obj.__class__.__mro__:
            cls_methods = _methods.get(cls, {})
            methods.update(cls_methods)
        if methods is not None:
            for object_type, object_to_inject in objects_to_inject.iteritems():
                method = methods.get(object_type, None)
                if method is not None:
                    method(obj, object_to_inject)
