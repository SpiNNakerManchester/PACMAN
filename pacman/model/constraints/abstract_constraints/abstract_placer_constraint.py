from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.constraints.abstract_constraints.abstract_constraint \
    import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractPlacerConstraint(AbstractConstraint):
    """ A constraint that will be used by the placer
    """

    def __init__(self, label):
        """

        :param label: A label for the constraint
        """
        AbstractConstraint.__init__(self, label)

    def is_constraint(self):
        return True

    @abstractmethod
    def is_placer_constraint(self):
        """ Determine if this is a placer constraint
        """
        pass

    @abstractmethod
    def rank(self):
        """ Relative importance of this constraint to other placement\
            constraints
        :return: The rank of the constraint, between 0 (least important)\
                    and sys.maxint (most important)
        :rtype: int
        :raise None: does not raise any known exception
        """
