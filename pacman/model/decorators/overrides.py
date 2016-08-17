import inspect


class overrides(object):
    """ A decorator for indicating that a method overrides another method in\
        a super class.  This checks that the method does actually exist,
        copies the doc-string for the method, and enforces that the method\
        overridden is specified, making maintenance easier.
    """

    __slots__ = [

        # The method in the superclass that this method overrides
        "_super_class_method",

        # True if the doc string is to be extended, False to set if not set
        "_extend_doc",

        # Any additional arguments required by the subclass method
        "_additional_arguments"
    ]

    def __init__(
            self, super_class_method, extend_doc=True,
            additional_arguments=None):
        """

        :param super_class_method: The method to override in the superclass
        :param extend_doc:\
            True the method doc string should be appended to the super-method\
            doc string, False if the documentation should be set to the\
            super-method doc string only if there isn't a doc string already
        :param additional_arguments:\
            Additional arguments taken by the subclass method over the\
            superclass method e.g. that are to be injected
        """
        self._super_class_method = super_class_method
        self._extend_doc = extend_doc
        self._additional_arguments = additional_arguments
        if additional_arguments is None:
            self._additional_arguments = {}
        if isinstance(super_class_method, property):
            self._super_class_method = super_class_method.fget

    def __call__(self, method):

        # Check and fail if this is a property
        if isinstance(method, property):
            raise AttributeError(
                "Please ensure that the override decorator is the last"
                " decorator before the method declaration")

        # Check that the name matches
        if method.__name__ != self._super_class_method.__name__:
            raise AttributeError(
                "Super class method name {} does not match {}. "
                "Ensure override is the last decorator before the method "
                "declaration".format(
                    self._super_class_method.__name__, method.__name__))

        # Check that the arguments match (except for __init__ as this might
        # take extra arguments or pass arguments not specified)
        if method.__name__ != "__init__":
            method_args = inspect.getargspec(method)
            super_args = inspect.getargspec(self._super_class_method)
            all_args = [
                arg for arg in method_args.args
                if arg not in self._additional_arguments
            ]
            default_args = None
            if method_args.defaults is not None:
                default_args = [
                    arg for arg in method_args.defaults
                    if arg not in self._additional_arguments
                ]
            if len(all_args) != len(super_args.args):
                raise AttributeError(
                    "Method has {} arguments but super class method has {}"
                    " arguments".format(
                        len(method_args.args), len(super_args.args)))
            for arg, super_arg in zip(all_args, super_args.args):
                if arg != super_arg:
                    raise AttributeError(
                        "Missing argument {}".format(super_arg))
            if ((default_args is None and
                super_args.defaults is not None) or
                (default_args is not None and
                    super_args.defaults is None) or
                    (default_args is not None and
                        super_args.defaults is not None and
                        len(default_args) !=
                        len(super_args.defaults))):
                raise AttributeError(
                    "Default arguments don't match super class method")

        if (self._super_class_method.__doc__ is not None and
                method.__doc__ is None):
            method.__doc__ = self._super_class_method.__doc__
        elif (self._extend_doc and
                self._super_class_method.__doc__ is not None):
            method.__doc__ = (
                self._super_class_method.__doc__ +
                method.__doc__
            )
        return method
