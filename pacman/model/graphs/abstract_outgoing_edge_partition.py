from six import add_metaclass

from spinn_utilities.abstract_base import \
    AbstractBase, abstractmethod, abstractproperty


@add_metaclass(AbstractBase)
class AbstractOutgoingEdgePartition(object):
    """ A group of edges that start at the same vertex and share the same\
        semantics; used to group edges that can use the same multicast key.
    """

    __slots__ = ()

    @abstractproperty
    def label(self):
        """ The label of the outgoing edge partition.

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """

    @abstractproperty
    def constraints(self):
        """ The constraints of the outgoing edge partition.

        :rtype: iterable(:py:class:`AbstractConstraint`)
        """

    @abstractmethod
    def add_constraint(self, constraint):
        """ Add a constraint to the outgoing edge partition.

        :param constraint: The constraint to add
        :type constraint: :py:class:`AbstractConstraint`
        """

    def add_constraints(self, constraints):
        """ Add a list of constraints to the outgoing edge partition.

        :param constraints: The list of constraints to add
        :type constraints: iterable(:py:class:`AbstractConstraint`)
        """
        for constraint in constraints:
            self.add_constraint(constraint)

    @abstractmethod
    def add_edge(self, edge):
        """ Add an edge to the outgoing edge partition.

        :param edge: the edge to add
        :type edge: :py:class:`pacman.model.graphs.AbstractEdge`
        :raises pacman.exceptions.PacmanInvalidParameterException:\
            If the starting vertex of the edge does not match that of the\
            edges already in the partition
        """

    @abstractproperty
    def identifier(self):
        """ The identifier of this outgoing edge partition.

        :rtype: str
        """

    @abstractproperty
    def edges(self):
        """ The edges in this outgoing edge partition.

        :rtype: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        """

    @abstractproperty
    def n_edges(self):
        """ The number of edges in the outgoing edge partition.

        :rtype: int
        """

    @abstractproperty
    def pre_vertex(self):
        """ The vertex at which all edges in this outgoing edge partition\
            start.

        :rtype: :py:class:`pacman.model.graphs.AbstractVertex`
        """

    @abstractproperty
    def traffic_weight(self):
        """ The weight of the traffic in this outgoing edge partition compared\
            to other partitions.

        :rtype: int
        """

    @abstractproperty
    def traffic_type(self):
        """ The traffic type of all the edges in this outgoing edge partition.

        :rtype: :py:class:`pacman.model.graphs.common.EdgeTrafficType`
        """

    @abstractmethod
    def __contains__(self, edge):
        """ Determine if an edge is in the outgoing edge partition.

        :param edge: The edge to check for the existence of
        :type edge: :py:class:`pacman.model.graphs.AbstractEdge`
        """
