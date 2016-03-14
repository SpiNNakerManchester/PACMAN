from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


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
