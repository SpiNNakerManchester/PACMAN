from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.application.abstract_application_edge \
    import AbstractApplicationEdge
from pacman.model.graphs.common.edge_traffic_type import EdgeTrafficType
from pacman.model.graphs.machine.impl.machine_edge import \
    MachineEdge


class ApplicationEdge(AbstractApplicationEdge):
    """ A simple implementation of an application edge
    """

    __slots__ = [

        # The edge at the start of the vertex
        "_pre_vertex",

        # The edge at the end of the vertex
        "_post_vertex",

        # The type of traffic on the edge
        "_traffic_type",

        # The label of the edge
        "_label"
    ]

    def __init__(
            self, pre_vertex, post_vertex,
            traffic_type=EdgeTrafficType.MULTICAST, label=None):
        """

        :param pre_vertex: the application vertex at the start of the edge
        :type pre_vertex: \
            :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :param post_vertex: the application vertex at the end of the edge
        :type post_vertex: \
            :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :param traffic_type: The type of the traffic on the edge
        :type traffic_type:\
            :py:class:`pacman.model.graph.edge_traffic_type.EdgeTrafficType`
        :param label: The name of the edge
        :type label: str
        """
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        self._traffic_type = traffic_type
        self._label = label

    @overrides(AbstractApplicationEdge.create_machine_edge)
    def create_machine_edge(self, pre_vertex, post_vertex, label):
        return MachineEdge(pre_vertex, post_vertex, self._traffic_type,
                           label=label)

    @property
    @overrides(AbstractApplicationEdge.pre_vertex)
    def pre_vertex(self):
        return self._pre_vertex

    @property
    @overrides(AbstractApplicationEdge.post_vertex)
    def post_vertex(self):
        return self._post_vertex

    @property
    @overrides(AbstractApplicationEdge.traffic_type)
    def traffic_type(self):
        return self._traffic_type

    @property
    @overrides(AbstractApplicationEdge.label)
    def label(self):
        return self._label
