from spinn_utilities.overrides import overrides
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs import AbstractEdge
from pacman.model.resources import ResourceContainer


class MachineEdge(AbstractEdge):
    """ A simple implementation of a machine edge.
    """

    __slots__ = [
        # The vertex at the start of the edge
        "_pre_vertex",

        # The vertex at the end of the edge
        "_post_vertex",

        # The type of traffic for this edge
        "_traffic_type",

        # The traffic weight of the edge
        "_traffic_weight",

        # The label of the edge
        "_label"
    ]

    def __init__(
            self, pre_vertex, post_vertex,
            traffic_type=EdgeTrafficType.MULTICAST, label=None,
            traffic_weight=1):
        """
        :param pre_vertex: the vertex at the start of the edge
        :type pre_vertex:\
            :py:class:`pacman.model.graphs.machine.MachineVertex`
        :param post_vertex: the vertex at the end of the edge
        :type post_vertex:\
            :py:class:`pacman.model.graphs.machine.MachineVertex`
        :param traffic_type: The type of traffic that this edge will carry
        :type traffic_type:\
            :py:class:`pacman.model.graphs.common.EdgeTrafficType`
        :param label: The name of the edge
        :type label: str
        :param traffic_weight:\
            the optional weight of traffic expected to travel down this edge\
            relative to other edges (default is 1)
        :type traffic_weight: int
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        self._traffic_type = traffic_type
        self._traffic_weight = traffic_weight

    @property
    @overrides(AbstractEdge.label)
    def label(self):
        return self._label

    @property
    @overrides(AbstractEdge.pre_vertex)
    def pre_vertex(self):
        return self._pre_vertex

    @property
    @overrides(AbstractEdge.post_vertex)
    def post_vertex(self):
        return self._post_vertex

    @property
    @overrides(AbstractEdge.traffic_type)
    def traffic_type(self):
        return self._traffic_type

    @property
    def traffic_weight(self):
        """ The amount of traffic expected to go down this edge relative to
            other edges
        """
        return self._traffic_weight

    @property
    def resources_required(self):
        """ The resources required by this edge. This represents shared\
            resources between source and target vertices, which has\
            implications in placement.

            This is designed to be overridden by an edge that has such\
            requirements that are not accounted for elsewhere.  The default\
            implementation assumes no resources are consumed by edges.

        :rtype: :py:class:`pacman.model.resources.ResourceContainer`
        """
        return ResourceContainer()

    def __repr__(self):
        return (
            "MachineEdge(pre_vertex={}, post_vertex={}, "
            "traffic_type={}, label={}, traffic_weight={})".format(
                self._pre_vertex, self._post_vertex, self._traffic_type,
                self.label, self._traffic_weight))
