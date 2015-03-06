from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
from inspect import isabstract


@add_metaclass(ABCMeta)
class AbstractConstraint(object):
    """ This represents a general constraint in PACMAN, which tells the \
        various modules what they can and can't do
    """

    def __init__(self, label):
        """

        :param label: A label for the constraint
        """
        self._label = label

    @property
    def label(self):
        """ The label of the constraint

        :return: string representation of the constraint
        :rtype: str
        """
        return self._label

    @abstractmethod
    def is_constraint(self):
        """ Determine if this is a constraint - for is_instance to work\
            correctly
        """
        pass

    @classmethod
    def __subclasshook__(cls, othercls):
        """ Checks if all the abstract methods are present on the subclass

            is only here for duck typing
        """
        if not isabstract(cls) and not isabstract(othercls):
            return NotImplemented
        for C in cls.__mro__:
            for key in C.__dict__:
                item = C.__dict__[key]
                if hasattr(item, "__isabstractmethod__"):
                    if not any(key in B.__dict__ for B in othercls.__mro__):
                        return NotImplemented
        return True
