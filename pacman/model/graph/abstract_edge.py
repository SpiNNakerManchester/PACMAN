from six import add_metaclass
from abc import ABCMeta
from abc import abstractproperty

from pacman.model.abstract_classes.abstract_has_label import AbstractHasLabel


@add_metaclass(ABCMeta)
class AbstractEdge(AbstractHasLabel):
    """ A directed edge in a graph between two vertices
    """

    @abstractproperty
    def pre_vertex(self):
        """ The vertex at the start of the edge

        :rtype: :py:class:`pacman.model.graph.abstract_vertex.AbstractVertex`
        """

    @abstractproperty
    def post_vertex(self):
        """ The vertex at the end of the edge

        :rtype: :py:class:`pacman.model.graph.abstract_vertex.AbstractVertex`
        """

    @abstractproperty
    def traffic_type(self):
        """ The traffic type of the edge

        :rtype :py:class:`pacman.model.graph.edge_traffic_type.EdgeTrafficType`
        """
