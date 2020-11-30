# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .machine_vertex import MachineVertex
from .machine_edge import MachineEdge
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.overrides import overrides
from spinn_utilities.default_ordered_dict import DefaultOrderedDict
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException,
    PacmanInvalidParameterException)
from pacman.model.graphs import Graph
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import (
    AbstractMachineEdgePartition, AbstractSDRAMPartition,
    FixedRouteEdgePartition, MulticastEdgePartition)


class MachineGraph(Graph):
    """ A graph whose vertices can fit on the chips of a machine.
    """

    __slots__ = [
        # Flags to say the application level is used so all machine vertices
        # will have an application vertex
        "_application_level_used",
        # Ordered set of partitions
        "_edge_partitions",
        # A double dictionary of MULTICAST edges by their
        # application id and then their (partition name)
        "_multicast_partitions",
        # The sets of multicast edge partitions by pre-vertex
        "_multicast_edge_partitions_by_pre_vertex",
        # The sets of fixed_point edge partitions by pre-vertex
        "_fixed_route_edge_partitions_by_pre_vertex",
        # The sdram outgoing edge partitions by pre-vertex
        "_sdram_edge_partitions_by_pre_vertex",
        # The sets of multicast edge partitions by pre-vertex
        "_multicast_edge_partitions_by_post_vertex",
        # The sets of fixed_point edge partitions by pre-vertex
        "_fixed_route_edge_partitions_by_post_vertex",
        # The sdram outgoing edge partitions by pre-vertex
        "_sdram_edge_partitions_by_post_vertex",
    ]

    MISSING_APP_VERTEX_ERROR_MESSAGE = (
        "The vertex does not have an app_vertex, "
        "which is required when other app_vertices exist.")

    UNEXPECTED_APP_VERTEX_ERROR_MESSAGE = (
        "The vertex has an app_vertex, "
        "which is not allowed when others not have app_vertices.")

    def __init__(self, label, application_graph=None):
        """
        :param label: The label for the graph.
        :type label: str or None
        :param application_graph:
            The application graph that this machine graph is derived from, if
            it is derived from one at all.
        :type application_graph: ApplicationGraph or None
        """
        super(MachineGraph, self).__init__(MachineVertex, MachineEdge, label)
        if application_graph:
            application_graph.forget_machine_graph()
            # Check the first vertex added
            self._application_level_used = True
        else:
            # Must be false as there is no App_graph
            self._application_level_used = False
        self._multicast_partitions = DefaultOrderedDict(
            lambda: DefaultOrderedDict(set))
        self._edge_partitions = OrderedSet()
        self._fixed_route_edge_partitions_by_pre_vertex = (
            DefaultOrderedDict(OrderedSet))
        self._multicast_edge_partitions_by_pre_vertex = (
            DefaultOrderedDict(OrderedSet))
        self._sdram_edge_partitions_by_pre_vertex = (
            DefaultOrderedDict(OrderedSet))
        self._fixed_route_edge_partitions_by_post_vertex = (
            DefaultOrderedDict(OrderedSet))
        self._multicast_edge_partitions_by_post_vertex = (
            DefaultOrderedDict(OrderedSet))
        self._sdram_edge_partitions_by_post_vertex = (
            DefaultOrderedDict(OrderedSet))

    @overrides(Graph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):
        edge_partition = super(MachineGraph, self).add_edge(
            edge, outgoing_edge_partition_name)
        if (isinstance(edge_partition, MulticastEdgePartition)):
            if edge.pre_vertex.app_vertex:
                by_app = self._multicast_partitions[
                    edge.pre_vertex.app_vertex]
            else:
                by_app = self._multicast_partitions[
                    edge.pre_vertex]
            by_partition = by_app[outgoing_edge_partition_name]
            by_partition.add(edge.pre_vertex)
            self._multicast_edge_partitions_by_post_vertex[
                edge.post_vertex].add(edge_partition)
        elif isinstance(edge_partition, FixedRouteEdgePartition):
            self._fixed_route_edge_partitions_by_post_vertex[
                edge.post_vertex].add(edge_partition)
        elif isinstance(edge_partition, AbstractSDRAMPartition):
            self._sdram_edge_partitions_by_post_vertex[
                edge.post_vertex].add(edge_partition)
        else:
            raise NotImplementedError(
                "Unexpected edge_partition: {}".format(edge_partition))
        return edge_partition

    @property
    def multicast_partitions(self):
        """
        Returns a double dictionary of app id then
        outgoing_edge_partition_name to a set of machine_vertex that act as
        pre vertices for these multicast edges

        The app_id is normally the (machine) edge.pre_vertex.app_vertex.
        This then groups the edges which come from the same app_vertex
        If the (machine) edge.pre_vertex has no app vertex then the app_id will
        be the machine vertex which will then form its own group of 1

        :rtype: dict(ApplicationVertex, dict(str, set(MachineVertex))
        """
        return self._multicast_partitions

    @overrides(Graph.add_vertex)
    def add_vertex(self, vertex):
        super(MachineGraph, self).add_vertex(vertex)
        if self._application_level_used:
            try:
                vertex.app_vertex.remember_machine_vertex(vertex)
            except AttributeError:
                if self.n_vertices == 1:
                    self._application_level_used = False
                else:
                    raise PacmanInvalidParameterException(
                        "vertex", str(vertex),
                        self.MISSING_APP_VERTEX_ERROR_MESSAGE)
        elif vertex.app_vertex:
            raise PacmanInvalidParameterException(
                "vertex", vertex, self.UNEXPECTED_APP_VERTEX_ERROR_MESSAGE)

    @overrides(Graph.add_outgoing_edge_partition)
    def add_outgoing_edge_partition(self, edge_partition):
        # verify that this partition is suitable for this graph
        if not isinstance(edge_partition, AbstractMachineEdgePartition):
            raise PacmanInvalidParameterException(
                "outgoing_edge_partition", str(edge_partition.__class__),
                "Partitions of this graph must be an "
                "AbstractMachineEdgePartition")

        # check this partition doesn't already exist
        if edge_partition in self._edge_partitions:
            raise PacmanAlreadyExistsException(
                str(AbstractMachineEdgePartition), edge_partition)

        self._edge_partitions.add(edge_partition)
        edge_partition.register_graph_code(id(self))

        for pre_vertex in edge_partition.pre_vertices:
            key = (pre_vertex, edge_partition.identifier)
            self._outgoing_edge_partitions_by_name[key] = edge_partition
            if isinstance(edge_partition, MulticastEdgePartition):
                self._multicast_edge_partitions_by_pre_vertex[
                    pre_vertex].add(edge_partition)
            elif isinstance(edge_partition, FixedRouteEdgePartition):
                self._fixed_route_edge_partitions_by_pre_vertex[
                    pre_vertex].add(edge_partition)
            elif isinstance(edge_partition, AbstractSDRAMPartition):
                self._sdram_edge_partitions_by_pre_vertex[
                    pre_vertex].add(edge_partition)
            else:
                raise NotImplementedError(
                    "Unexpected edge_partition: {}".format(edge_partition))
        for edge in edge_partition.edges:
            self._register_edge(edge, edge_partition)

    @overrides(Graph.new_edge_partition)
    def new_edge_partition(self, name, edge):
        if edge.traffic_type == EdgeTrafficType.FIXED_ROUTE:
            return FixedRouteEdgePartition(
                identifier=name, pre_vertex=edge.pre_vertex)
        elif edge.traffic_type == EdgeTrafficType.MULTICAST:
            return MulticastEdgePartition(
                identifier=name, pre_vertex=edge.pre_vertex)
        else:
            raise PacmanInvalidParameterException(
                "edge", edge,
                "Unable to add an Edge with traffic type {} unless you first "
                "add a partition for it".format(edge.traffic_type))

    @property
    @overrides(Graph.outgoing_edge_partitions)
    def outgoing_edge_partitions(self):
        return self._edge_partitions

    @property
    @overrides(Graph.n_outgoing_edge_partitions)
    def n_outgoing_edge_partitions(self):
        return len(self._edge_partitions)

    def get_fixed_route_edge_partitions_starting_at_vertex(self, vertex):
        """ Get only the fixed_route edge partitions that start at the vertex.

        :param AbstractVertex vertex:\
             The vertex at which the edge partitions to find starts
        :rtype: iterable(FixedRouteEdgePartition)
        """
        return self._fixed_route_edge_partitions_by_pre_vertex.get(vertex, [])

    def get_multicast_edge_partitions_starting_at_vertex(self, vertex):
        """ Get only the multicast edge partitions that start at the vertex.

        :param AbstractVertex vertex:\
            The vertex at which the edge partitions to find starts
        :rtype: iterable(MulticastEdgePartition)
        """
        return self._multicast_edge_partitions_by_pre_vertex.get(vertex, [])

    def get_sdram_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the sdram edge partitions that start at the given vertex.

        :param AbstractVertex vertex:\
            The vertex at which the sdram edge partitions to find starts
        :rtype: iterable(AbstractSDRAMPartition)
        """
        return self._sdram_edge_partitions_by_pre_vertex.get(vertex, [])

    @overrides(Graph.get_outgoing_edge_partitions_starting_at_vertex)
    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        for partition in self.\
                get_fixed_route_edge_partitions_starting_at_vertex(vertex):
            yield partition
        for partition in \
                self.get_multicast_edge_partitions_starting_at_vertex(vertex):
            yield partition
        for partition in \
                self.get_sdram_edge_partitions_starting_at_vertex(vertex):
            yield partition

    def get_fixed_route_edge_partitions_ending_at_vertex(self, vertex):
        """ Get only the fixed_route edge partitions that end at the vertex.

        :param AbstractVertex vertex:\
            The vertex at which the edge partitions to find starts
        :rtype: iterable(FixedRouteEdgePartition)
        """
        return self._fixed_route_edge_partitions_by_post_vertex.get(vertex, [])

    def get_multicast_edge_partitions_ending_at_vertex(self, vertex):
        """ Get only the multicast edge partitions that end at the vertex.

        :param AbstractVertex vertex:\
            The vertex at which the edge partitions to find starts
        :rtype: iterable(MulticastEdgePartition)
        """
        return self._multicast_edge_partitions_by_post_vertex.get(vertex, [])

    def get_sdram_edge_partitions_ending_at_vertex(self, vertex):
        """ Get all the sdram edge partitions that end at the given vertex.

        :param AbstractVertex vertex:\
            The vertex at which the sdram edge partitions to find starts
        :rtype: iterable(AbstractSDRAMPartition)
        """
        return self._sdram_edge_partitions_by_post_vertex.get(vertex, [])

    def get_edge_partitions_ending_at_vertex(self, vertex):
        """ Get all the edge partitions that end at the given vertex.

        :param AbstractVertex vertex:\
            The vertex at which the sdram edge partitions to find starts
        :rtype: iterable(AbstractPartition)
        """
        for partition in \
                self.get_fixed_route_edge_partitions_ending_at_vertex(vertex):
            yield partition
        for partition in \
                self.get_multicast_edge_partitions_ending_at_vertex(vertex):
            yield partition
        for partition in \
                self.get_sdram_edge_partitions_ending_at_vertex(vertex):
            yield partition

    def clone(self, frozen=False):
        """
        Makes as shallow as possible copy of the graph.

        Vertices and edges are copied over. Partition will be new objects.

        :param application_graph: The application graph with which the clone
            should be associated
        :return: A shallow copy of this graph
        :rtype: MachineGraph
        """
        if frozen:
            new_graph = _FrozenMachineGraph(self.label)
        else:
            new_graph = MachineGraph(self.label)
        for vertex in self.vertices:
            new_graph.add_vertex(vertex)
        for outgoing_partition in \
                self.outgoing_edge_partitions:
            new_outgoing_partition = outgoing_partition.clone_without_edges()
            new_graph.add_outgoing_edge_partition(new_outgoing_partition)
            for edge in outgoing_partition.edges:
                new_graph.add_edge(edge, outgoing_partition.identifier)
        if frozen:
            new_graph.freeze()
        return new_graph


class _FrozenMachineGraph(MachineGraph):
    """ A frozen graph whose vertices can fit on the chips of a machine.
    """
    # This is declared in the same file due to the circular dependency

    __slots__ = ["__frozen"]

    def __init__(self, label):
        super(_FrozenMachineGraph, self).__init__(label)
        self.__frozen = False

    def freeze(self):
        """
        blocks any farther attempt to add to this graph

        :return:
        """
        self.__frozen = True

    @overrides(MachineGraph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):
        if self.__frozen:
            raise PacmanConfigurationException(
                "Please add edges via simulator not directly to this graph")
        super(_FrozenMachineGraph, self).add_edge(
            edge, outgoing_edge_partition_name)

    @overrides(MachineGraph.add_vertex)
    def add_vertex(self, vertex):
        if self.__frozen:
            raise PacmanConfigurationException(
                "Please add vertices via simulator not directly to this graph")
        super(_FrozenMachineGraph, self).add_vertex(vertex)

    @overrides(MachineGraph.add_outgoing_edge_partition)
    def add_outgoing_edge_partition(self, edge_partition):
        if self.__frozen:
            raise PacmanConfigurationException(
                "Please add partitions via simulator not directly to this "
                "graph")
        super(_FrozenMachineGraph, self).add_outgoing_edge_partition(
            edge_partition)
