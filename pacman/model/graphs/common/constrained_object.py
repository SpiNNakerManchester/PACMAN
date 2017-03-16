from pacman.exceptions import PacmanInvalidParameterException
from six import add_metaclass
from pacman.model.constraints.abstract_constraint \
    import AbstractConstraint
from spinn_utilities.abstract_base import AbstractBase


def _get_class_name(cls):
    return "{}.{}".format(cls.__module__, cls.__name__)


@add_metaclass(AbstractBase)
class ConstrainedObject(object):
    """ An implementation of an object which holds constraints
    """

    __slots__ = [

        # The constraints of the object
        "_constraints"
    ]

    def __init__(self, constraints=None):
        """

        :param constraints: Any initial constraints
        """

        # safety point for diamond inheritance
        if not hasattr(self, '_constraints') or self._constraints is None:
            self._constraints = set()

        # add new constraints to the set
        self.add_constraints(constraints)

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
        if constraint is None:
            raise PacmanInvalidParameterException("constraint", constraint,
                                                  "must not be None")
        if not isinstance(constraint, AbstractConstraint):
            raise PacmanInvalidParameterException(
                "constraint", constraint,
                "Must be a " + _get_class_name(AbstractConstraint))

        try:
            self._constraints.add(constraint)
        except:
            self._constraints = set()
            self._constraints.add(constraint)

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
        if constraints is not None:
            for next_constraint in constraints:
                self.add_constraint(next_constraint)

    @property
    def constraints(self):
        """ An iterable of constraints

        :return: iterable of constraints
        :rtype: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise None: Raises no known exceptions
        """
        try:
            return self._constraints
        except:
            return set()
