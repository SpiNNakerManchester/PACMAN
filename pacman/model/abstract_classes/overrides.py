class overrides(object):
    """ A decorator for indicating that a method overrides another method in\
        a super class.  This checks that the method does actually exist,
        copies the doc-string for the method, and enforces that the method\
        overridden is specified, making maintenance easier.
    """

    def __init__(self, super_class):
        self._super_class = super_class

    def __call__(self, method):
        super_attr = getattr(self._super_class, method.__name__)
        if super_attr.__doc__ is not None and not method.__doc__:
            method.__doc__ = super_attr.__doc__
        return method
