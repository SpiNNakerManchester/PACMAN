from six import add_metaclass

from spinn_utilities.abstract_base import \
    AbstractBase, abstractmethod, abstractproperty


@add_metaclass(AbstractBase)
class AbstractOutgoingEdgePartition(object):
    """ A group of edges that start at the same vertex and share the same\
        semantics; used to group edges that can use the same multicast key
    """

    __slots__ = ()

    @abstractproperty
    def label(self):
        """ The label of the item

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
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

    @abstractmethod
    def add_edge(self, edge):
        """ Add an edge to the partition

        :param edge: the edge to add
        :type edge: :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        :raises pacman.exceptions.PacmanInvalidParameterException:\
            If the starting vertex of the edge does not match that of the\
            edges already in the partition
        """

    @abstractproperty
    def identifier(self):
        """ The identifier of this outgoing edge partition

        :rtype: str
        """

    @abstractproperty
    def edges(self):
        """ The edges in this outgoing edge partition

        :rtype:\
            iterable of\
            :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        """

    @abstractproperty
    def n_edges(self):
        """ The number of edges in the partition

        :rtype: int
        """

    @abstractproperty
    def pre_vertex(self):
        """ The vertex at which all edges in this partition start

        :rtype: :py:class:`pacman.model.graphs.abstract_vertex.AbstractVertex`
        """

    @abstractproperty
    def traffic_weight(self):
        """ The weight of the traffic in this partition compared to other\
            partitions

        :rtype: int
        """

    @abstractproperty
    def traffic_type(self):
        """ The traffic type of all the edges in this partition

        :rtype:\
            :py:class:`pacman.model.graphs.common.edge_traffic_type.EdgeTrafficType`
        """

    @abstractmethod
    def __contains__(self, edge):
        """ Determine if an edge is in the partition

        :param edge: The edge to check for the existence of
        :type edge: :py:class:`pacman.model.graphs.abstract_edge.AbstractEdge`
        """
