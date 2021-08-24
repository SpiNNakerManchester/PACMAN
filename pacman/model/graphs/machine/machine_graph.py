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
from pacman.exceptions import PacmanInvalidParameterException
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
        # The sets of multicast edge partitions by pre-vertex
        "_multicast_edge_partitions_by_pre_vertex",
        # The sets of fixed_point edge partitions by pre-vertex
        "_fixed_route_edge_partitions_by_pre_vertex",
        # The sdram outgoing edge partitions by pre-vertex
        "_sdram_edge_partitions_by_pre_vertex",
        # The sdram outgoing edge partitions by pre-vertex
        "_sdram_edge_partitions_by_post_vertex",
        # The total number of outgoing edge partitions
        "_n_outgoing_edge_partitions"
    ]

    MISSING_APP_VERTEX_ERROR_MESSAGE = (
        "The vertex does not have an app_vertex, "
        "which is required when other app_vertices exist.")

    UNEXPECTED_APP_VERTEX_ERROR_MESSAGE = (
        "The vertex has an app_vertex, "
        "which is not allowed when other vertices not have app_vertices.")

    def __init__(self, label, application_graph=None):
        """
        :param label: The label for the graph.
        :type label: str or None
        :param application_graph:
            The application graph that this machine graph is derived from, if
            it is derived from one at all.
        :type application_graph: ApplicationGraph or None
        """
        super().__init__(MachineVertex, MachineEdge, label)
        if application_graph:
            application_graph.forget_machine_graph()
            # Check the first vertex added
            self._application_level_used = True
        else:
            # Must be false as there is no App_graph
            self._application_level_used = False
        self._fixed_route_edge_partitions_by_pre_vertex = (
            DefaultOrderedDict(OrderedSet))
        self._multicast_edge_partitions_by_pre_vertex = (
            DefaultOrderedDict(OrderedSet))
        self._sdram_edge_partitions_by_pre_vertex = (
            DefaultOrderedDict(OrderedSet))
        self._sdram_edge_partitions_by_post_vertex = (
            DefaultOrderedDict(OrderedSet))
        self._n_outgoing_edge_partitions = 0

    @overrides(Graph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):
        edge_partition = super().add_edge(
            edge, outgoing_edge_partition_name)
        if isinstance(edge_partition, AbstractSDRAMPartition):
            self._sdram_edge_partitions_by_post_vertex[
                edge.post_vertex].add(edge_partition)
        return edge_partition

    @overrides(Graph.add_vertex)
    def add_vertex(self, vertex):
        super().add_vertex(vertex)
        if self._application_level_used:
            try:
                vertex.app_vertex.remember_machine_vertex(vertex)
            except AttributeError as e:
                if self.n_vertices == 1:
                    self._application_level_used = False
                else:
                    raise PacmanInvalidParameterException(
                        "vertex", str(vertex),
                        self.MISSING_APP_VERTEX_ERROR_MESSAGE) from e
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

        edge_partition.register_graph_code(id(self))

        for pre_vertex in edge_partition.pre_vertices:
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

        self._n_outgoing_edge_partitions += 1

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
        for partitions in \
                self._fixed_route_edge_partitions_by_pre_vertex.values():
            for partition in partitions:
                yield partition
        for partitions in \
                self._multicast_edge_partitions_by_pre_vertex.values():
            for partition in partitions:
                yield partition
        for partitions in \
                self._sdram_edge_partitions_by_pre_vertex.values():
            for partition in partitions:
                yield partition

    @property
    @overrides(Graph.n_outgoing_edge_partitions)
    def n_outgoing_edge_partitions(self):
        return self._n_outgoing_edge_partitions

    @property
    def outgoing_multicast_edge_partitions(self):
        for partitions in \
                self._multicast_edge_partitions_by_pre_vertex.values():
            for partition in partitions:
                yield partition

    def get_fixed_route_edge_partitions_starting_at_vertex(self, vertex):
        """ Get only the fixed_route edge partitions that start at the vertex.

        :param MachineVertex vertex:
             The vertex at which the edge partitions to find starts
        :rtype: iterable(FixedRouteEdgePartition)
        """
        return self._fixed_route_edge_partitions_by_pre_vertex.get(vertex, [])

    def get_multicast_edge_partitions_starting_at_vertex(self, vertex):
        """ Get only the multicast edge partitions that start at the vertex.

        :param MachineVertex vertex:
            The vertex at which the edge partitions to find starts
        :rtype: iterable(MulticastEdgePartition)
        """
        return self._multicast_edge_partitions_by_pre_vertex.get(vertex, [])

    def get_sdram_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the SDRAM edge partitions that start at the given vertex.

        :param MachineVertex vertex:
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

    def get_sdram_edge_partitions_ending_at_vertex(self, vertex):
        """ Get all the sdram edge partitions that end at the given vertex.

        :param MachineVertex vertex:
            The vertex at which the SDRAM edge partitions to find starts
        :rtype: iterable(AbstractSDRAMPartition)
        """
        return self._sdram_edge_partitions_by_post_vertex.get(vertex, [])

    def clone(self):
        """
        Makes as shallow as possible copy of the graph.

        Vertices and edges are copied over. Partition will be new objects.

        :return: A shallow copy of this graph
        :rtype: MachineGraph
        :raises PacmanInvalidParameterException:
            If called on a none empty graph when Application Vertexes exist
        """
        new_graph = MachineGraph(self.label)
        for vertex in self.vertices:
            new_graph.add_vertex(vertex)
        for outgoing_partition in \
                self.outgoing_edge_partitions:
            new_outgoing_partition = outgoing_partition.clone_without_edges()
            new_graph.add_outgoing_edge_partition(new_outgoing_partition)
            for edge in outgoing_partition.edges:
                new_graph.add_edge(edge, outgoing_partition.identifier)
        return new_graph
