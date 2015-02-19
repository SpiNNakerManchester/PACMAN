from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.constraints.abstract_constraint import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractKeyAllocatorConstraint(AbstractConstraint):
    """ A constraint on key allocation
    """

    def __init__(self, label):
        AbstractConstraint.__init__(self, label)

    def is_constraint(self):
        return True

    @abstractmethod
    def is_key_allocator_constraint(self):
        """ Determine if this is a key allocator constraint
        """
        pass
