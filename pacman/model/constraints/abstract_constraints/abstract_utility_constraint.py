from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.constraints.abstract_constraints.abstract_constraint \
    import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractUtilityConstraint(AbstractConstraint):
    """ A general purpose constraint not associated with any particular\
        component
    """

    def __init__(self, label):
        """

        :param label: A label for the constraint
        """
        AbstractConstraint.__init__(self, label)

    def is_constraint(self):
        return True

    @abstractmethod
    def is_utility_constraint(self):
        """ Determine if this is a placer constraint
        """
        pass
