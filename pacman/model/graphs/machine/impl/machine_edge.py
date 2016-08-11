from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.common.edge_traffic_type import EdgeTrafficType
from pacman.model.graphs.machine.abstract_machine_edge \
    import AbstractMachineEdge


class MachineEdge(AbstractMachineEdge):
    """ A simple implementation of a machine edge
    """

    __slots__ = [

        # The vertex at the start of the edge
        "_pre_vertex",

        # The vertex at the end of the edge
        "_post_vertex",

        # The type of traffic for this edge
        "_traffic_type",

        # The label of the edge
        "_label",

        # The traffic weight of the edge
        "_traffic_weight"
    ]

    def __init__(
            self, pre_vertex, post_vertex,
            traffic_type=EdgeTrafficType.MULTICAST, label=None,
            traffic_weight=1):
        """

        :param pre_vertex: the vertex at the start of the edge
        :type pre_vertex:\
            :py:class:`pacman.model.graphs.machine.abstract_machine_vertex.AbstractMachineVertex`
        :param post_vertex: the vertex at the end of the edge
        :type post_vertex:\
            :py:class:`pacman.model.graphs.machine.abstract_machine_vertex.AbstractMachineVertex`
        :param traffic_type: The type of traffic that this edge will carry
        :type traffic_type:\
            :py:class:`pacman.model.graphs.common.edge_traffic_type.EdgeTrafficType`
        :param label: The name of the edge
        :type label: str
        :param traffic_weight:\
            the optional weight of traffic expected to travel down this edge\
            relative to other edges (default is 1)
        :type traffic_weight: int
        """
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        self._traffic_type = traffic_type
        self._label = label
        self._traffic_weight = traffic_weight
        AbstractMachineEdge.__init__(self)

    @property
    @overrides(AbstractMachineEdge.pre_vertex)
    def pre_vertex(self):
        return self._pre_vertex

    @property
    @overrides(AbstractMachineEdge.post_vertex)
    def post_vertex(self):
        return self._post_vertex

    @property
    @overrides(AbstractMachineEdge.traffic_type)
    def traffic_type(self):
        return self._traffic_type

    @property
    @overrides(AbstractMachineEdge.label)
    def label(self):
        return self._label

    @property
    @overrides(AbstractMachineEdge.traffic_weight)
    def traffic_weight(self):
        return self._traffic_weight

    @overrides(AbstractMachineEdge.model_name)
    def model_name(self):
        return "MachineEdge"

    def __repr__(self):
        return "SimpleMachineEdge(pre_vertex={}, post_vertex={}, " \
               "traffic_type={}, label={}, traffic_weight={})".format(
                self._pre_vertex, self._post_vertex, self._traffic_type,
                self._label, self._traffic_weight)
