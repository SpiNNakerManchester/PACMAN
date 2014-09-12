from abc import ABCMeta
from six import add_metaclass
from pacman.model.constraints.abstract_constraint import AbstractConstraint
from pacman.exceptions import PacmanInvalidParameterException


@add_metaclass(ABCMeta)
class AbstractConstrainedVertex(object):
    """ Represents a AbstractConstrainedVertex of a partitionable_graph, \
    which contains a number of atoms, and\
        which can be partitioned into a number of subvertices, such that the\
        total number of atoms in the subvertices adds up to the number of atoms\
        in the vertex
    """
    _non_labelled_vertex_count = 0
    
    def __init__(self, label, constraints=None):

        """
        :param label: The name of the vertex
        :type label: str
        :param constraints: The constraints of the vertex
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
                    * If the number of atoms is less than 1
        """
        if label is None:
            self._label = \
                "Population {}"\
                .format(AbstractConstrainedVertex._non_labelled_vertex_count)
            AbstractConstrainedVertex._non_labelled_vertex_count += 1
        else:
            self._label = label
        self._constraints = list()

        self.add_constraints(constraints)

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

    def add_constraint(self, constraint):
        """ Add a new constraint to the collection of constraints for the vertex

        :param constraint: constraint to add
        :type constraint:\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    constraint is not valid
        """
        if (constraint is None
                or not isinstance(constraint, AbstractConstraint)):
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
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If one of the\
                    constraints is not valid
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
        :raise pacman.exceptions.PacmanInvalidParameterException: If one of the\
                    constraints is not valid
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
