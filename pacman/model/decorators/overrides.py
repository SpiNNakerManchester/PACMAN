class overrides(object):
    """ A decorator for indicating that a method overrides another method in\
        a super class.  This checks that the method does actually exist,
        copies the doc-string for the method, and enforces that the method\
        overridden is specified, making maintenance easier.
    """

    __slots__ = [

        # The method in the superclass that this method overrides
        "_super_class_method"
    ]

    def __init__(self, super_class_method):
        self._super_class_method = super_class_method
        if isinstance(super_class_method, property):
            self._super_class_method = super_class_method.fget

    def __call__(self, method):
        if isinstance(method, property):
            raise AttributeError(
                "Please ensure that the override decorator is the last"
                " decorator before the method declaration")
        if method.__name__ != self._super_class_method.__name__:
            raise AttributeError(
                "Super class method name {} does not match {}. "
                "Ensure override is the last decorator before the method "
                "declaration".format(
                    self._super_class_method.__name__, method.__name__))
        if (self._super_class_method.__doc__ is not None and
                method.__doc__ is None):
            method.__doc__ = self._super_class_method.__doc__
        return method
