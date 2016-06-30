from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from abc import abstractproperty


@add_metaclass(ABCMeta)
class AbstractHasConstraints(object):
    """ Represents an object with constraints
    """

    @abstractmethod
    def add_constraint(self, constraint):
        """ Add a new constraint to the collection of constraints

        :param constraint: constraint to add
        :type constraint:\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    constraint is not valid
        """

    @abstractmethod
    def add_constraints(self, constraints):
        """ Add an iterable of constraints to the collection of constraints

        :param constraints: iterable of constraints to add
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If one of \
                    the constraints is not valid
        """

    @abstractproperty
    def constraints(self):
        """ An iterable of constraints

        :return: iterable of constraints
        :rtype: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise None: Raises no known exceptions
        """
