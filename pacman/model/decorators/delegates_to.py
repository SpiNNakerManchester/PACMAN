from functools import wraps
import inspect


class delegates_to(object):
    """ Delegate this call to another object

    """

    def __init__(self, variable_name, method_to_call):
        """
        :param variable_name:\
            The name of the variable to delegate to e.g.\ if there is a\
            variable self._delegate, this would be "delegate"
        :param method_to_call:\
            The method to call in the delegate class.  Must match the name and\
            arguments of the method being decorated.  This can also be a\
            property, in which case the decorated argument should *not* be\
            a property; it will inherit it's property status from the delegate
        """
        self._variable_name = variable_name
        self._method_to_call = method_to_call

    def __call__(self, method):

        method_to_call = self._method_to_call
        is_property = False
        method_setter = None
        if isinstance(self._method_to_call, property):
            method_to_call = self._method_to_call.fget
            method_setter = self._method_to_call.fset
            is_property = True

        # Check and fail if this is a property
        if isinstance(method, property):
            raise AttributeError(
                "Please ensure that the delegates_to decorator is the last"
                " decorator before the method declaration")

        # Check that the name matches
        if method.__name__ != method_to_call.__name__:
            raise AttributeError(
                "Delegate method name {} does not match {}. "
                "Ensure delegates_to is the last decorator before the method "
                "declaration".format(
                    method_to_call.__name__, method.__name__))

        # Check that the arguments match (except for __init__ as this might
        # take extra arguments or pass arguments not specified)
        if method.__name__ != "__init__":
            method_args = inspect.getargspec(method)
            delegate_args = inspect.getargspec(method_to_call)
            if len(method_args.args) != len(delegate_args.args):
                raise AttributeError(
                    "Method has {} arguments but delegate method has {}"
                    " arguments".format(
                        len(method_args.args), len(delegate_args.args)))
            for arg, delegate_arg in zip(method_args.args, delegate_args.args):
                if arg != delegate_arg:
                    raise AttributeError(
                        "Missing argument {}".format(delegate_arg))
            if ((method_args.defaults is None and
                delegate_args.defaults is not None) or
                (method_args.defaults is not None and
                    delegate_args.defaults is None) or
                    (method_args.defaults is not None and
                        delegate_args.defaults is not None and
                        len(method_args.defaults) !=
                        len(delegate_args.defaults))):
                raise AttributeError(
                    "Default arguments don't match delegate method")

        if (method_to_call.__doc__ is not None and
                method.__doc__ is None):
            method.__doc__ = method_to_call.__doc__

        @wraps(method)
        def execute_delegate(obj, *args, **kwargs):
            delegate = getattr(obj, self._variable_name)
            return method_to_call(delegate, *args, **kwargs)

        if is_property:
            if method_setter is not None:

                def execute_delegate_setter(obj, *args, **kwargs):
                    delegate = getattr(obj, self._variable_name)
                    return method_setter(delegate, *args, **kwargs)

                return property(execute_delegate, execute_delegate_setter)

            return property(execute_delegate)

        return execute_delegate
