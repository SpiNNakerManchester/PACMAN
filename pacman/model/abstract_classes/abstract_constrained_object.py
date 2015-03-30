from abc import ABCMeta
from six import add_metaclass


from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.constraints.abstract_constraints.abstract_constraint \
    import AbstractConstraint


@add_metaclass(ABCMeta)
class AbstractConstrainedObject(object):

    def __init__(self, label, constraints=None):
        self._label = label
        self._constraints = list()
        self.add_constraints(constraints)

    def add_constraint(self, constraint):
        """ Add a new constraint to the collection of constraints for the vertex

        :param constraint: constraint to add
        :type constraint:\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    constraint is not valid
        """
        if (constraint is None or
                not isinstance(constraint, AbstractConstraint)):
            raise PacmanInvalidParameterException(
                "constraint", constraint, "Must be a pacman.model."
                                          "constraints.abstract_constraint."
                                          "AbstractConstraint")
        self._constraints.append(constraint)

    def add_constraints(self, constraints):
        """ Add an iterable of constraints to the collection of constraints for\
            the vertex

        :param constraints: iterable of constraints to add
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If one of \
                    the constraints is not valid
        """
        if constraints is not None:
            for next_constraint in constraints:
                self.add_constraint(next_constraint)

    def set_constraints(self, constraints):
        """ Set the constraints of the vertex to be exactly the given iterable\
            of constraints, overwriting any previously added constraints

        :param constraints: iterable of constraints to set
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If one of \
                    the constraints is not valid
        """
        self._constraints = list()
        self.add_constraints(constraints)

    @property
    def label(self):
        """ The label of the vertex

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    @property
    def constraints(self):
        """ An iterable constraints for the vertex

        :return: iterable of constraints
        :rtype: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise None: Raises no known exceptions
        """
        return self._constraints
