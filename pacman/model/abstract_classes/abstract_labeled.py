from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractLabeled(object):
    """ Represents an item with a label
    """

    def __init__(self, label):
        self._label = label

    @property
    def label(self):
        """ The label of the item

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    @classmethod
    def __subclasshook__(cls, othercls):
        """ Checks if all the abstract methods are present on the subclass
        """
        has_abstract = False
        for C in cls.__mro__:
            for key in C.__dict__:
                item = C.__dict__[key]
                if hasattr(item, "__isabstractmethod__"):
                    has_abstract = True
                    if not any(key in B.__dict__ for B in othercls.__mro__):
                        return NotImplemented
        if has_abstract:
            return True
        return NotImplemented
