from spinn_utilities.overrides import overrides
from pacman.model.graphs import AbstractEdge
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import MachineEdge
from pacman.model.resources import ResourceContainer


class ApplicationEdge(AbstractEdge):
    """ A simple implementation of an application edge.
    """

    __slots__ = [
        # The edge at the start of the vertex
        "_pre_vertex",

        # The edge at the end of the vertex
        "_post_vertex",

        # The type of traffic on the edge
        "_traffic_type",

        # Machine edge type
        "_machine_edge_type",

        # The label
        "_label"
    ]

    def __init__(
            self, pre_vertex, post_vertex,
            traffic_type=EdgeTrafficType.MULTICAST, label=None,
            machine_edge_type=MachineEdge):
        """
        :param pre_vertex: the application vertex at the start of the edge
        :type pre_vertex: \
            :py:class:`pacman.model.graphs.application.ApplicationVertex`
        :param post_vertex: the application vertex at the end of the edge
        :type post_vertex: \
            :py:class:`pacman.model.graphs.application.ApplicationVertex`
        :param traffic_type: The type of the traffic on the edge
        :type traffic_type:\
            :py:class:`pacman.model.graphs.common.EdgeTrafficType`
        :param label: The name of the edge
        :type label: str
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        self._traffic_type = traffic_type
        self._machine_edge_type = machine_edge_type

    @property
    @overrides(AbstractEdge.label)
    def label(self):
        return self._label

    def create_machine_edge(self, pre_vertex, post_vertex, label):
        """ Create a machine edge between two machine vertices

        :param pre_vertex: The machine vertex at the start of the edge
        :type pre_vertex:\
            :py:class:`pacman.model.graphs.machine.MachineVertex`
        :param post_vertex: The machine vertex at the end of the edge
        :type post_vertex:\
            :py:class:`pacman.model.graphs.machine.MachineVertex`
        :param label: label of the edge
        :type label: str
        :return: The created machine edge
        :rtype:\
            :py:class:`pacman.model.graphs.machine.MachineEdge`
        """
        return self._machine_edge_type(
            pre_vertex, post_vertex, self._traffic_type, label=label)

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

    def get_resources_used_by_atoms(self, pre_vertex_slice, post_vertex_slice):
        """ Get the resources used by the edge from a range of atoms in the\
            pre-vertex to a range of atoms in the post-vertex.  This\
            represents shared resources between source and target vertices,\
            which has implications in placement.

            This is designed to be overridden by an edge that has such\
            requirements that are not accounted for elsewhere.  The default\
            implementation assumes no resources are consumed by edges.

        :param pre_vertex_slice: The slice of the pre-vertex being considered
        :type pre_vertex_slice: :py:class:`pacman.model.graphs.common.Slice`
        :param post_vertex_slice: The slice of the post-vertex being considered
        :type post_vertex_slice: :py:class:`pacman.model.graphs.common.Slice`
        :rtype: :py:class:`pacman.model.resources.ResourceContainer`
        """
        return ResourceContainer()
