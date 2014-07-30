from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractConstraint(object):
    """ This represents a general constraint in PACMAN, which tells the various\
        modules what they can and can't do
    """

    def __init__(self, label):
        self._label = label

    @abstractmethod
    def is_constraint(self):
        """ Method required to ensure that this is a constraint
        
        :return: True if this is a constraint
        :rtype: bool
        """
        pass

    @property
    def label(self):
        """getter for label

        :return: string rep of the constraint
        :rtype: str
        :raise None: this does not raise any known exception
        """
        return self._label

    @classmethod
    def __subclasshook__(cls, othercls):
        """ Checks if all the abstract methods are present on the subclass
        """
        for C in cls.__mro__:
            for key in C.__dict__:
                item = C.__dict__[key]
                if hasattr(item, "__isabstractmethod__"):
                    if not any(key in B.__dict__ for B in othercls.__mro__):
                        return NotImplemented
        return True