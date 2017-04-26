from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractproperty
from spinn_utilities.abstract_base import abstractmethod


@add_metaclass(AbstractBase)
class AbstractVertex(object):
    """ A vertex in a graph
    """

    __slots__ = ()

    @abstractproperty
    def label(self):
        """ The label of the vertex

        :rtype: str
        """

    @abstractproperty
    def constraints(self):
        """ The constraints of the vertex

        :rtype: iterable of :py:class:`AbstractConstraint`
        """

    @abstractmethod
    def add_constraint(self, constraint):
        """ Add a constraint

        :param constraint: The constraint to add
        :type constraint: :py:class:`AbstractConstraint`
        """

    def add_constraints(self, constraints):
        """ Add a list of constraints

        :param constraints: The list of constraints to add
        :type constraints: list of :py:class:`AbstractConstraint`
        """
        for constraint in constraints:
            self.add_constraint(constraint)
