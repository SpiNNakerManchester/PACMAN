from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractOutgoingEdgePartition(object):
    """ A group of edges that start at the same vertex and share the same\
        semantics; used to group edges that can use the same multicast key
    """

    @abstractmethod
    def add_edge(self, edge):
        """ Add an edge to the partition

        :param edge: the edge to add
        :type: :py:class:`pacman.model.graph.AbstractEdge`
        :raises:\
            :py:class:`pacman.execptions.PacmanInvalidParameterException`\
            if the starting vertex of the edge does not match that of the\
            edges already in the partition
        """

    @property
    def identifier(self):
        """ The identifier of this outgoing edge partition

        :rtype: str
        """

    @property
    def edges(self):
        """ The edges in this outgoing edge partition

        :rtype: iterable of :py:class:`pacman.model.graph.AbstractEdge`
        """

    @property
    def pre_vertex(self):
        """ The vertex at which all edges in this partition start
        """

    @abstractmethod
    def __contains__(self, edge):
        """ Determine if an edge is in the partition

        :param edge: The edge to check for the existence of
        :type edge: :py:class:`pacman.model.graph.AbstractEdge`
        """
