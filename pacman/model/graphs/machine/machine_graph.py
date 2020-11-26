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
from spinn_utilities.default_ordered_dict import DefaultOrderedDict
from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)
from pacman.model.graphs import OutgoingEdgePartition
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.graph import Graph


class MachineGraph(Graph):
    """ A graph whose vertices can fit on the chips of a machine.
    """

    __slots__ = [
        # A double dictionary of MULTICAST edges by their
        # application id and then their (partition name)
        "_multicast_partitions",
        # Flags to say the application level is used so all machine vertices
        # will have an application vertex
        "_application_level_used",
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
        super(MachineGraph, self).__init__(
            MachineVertex, MachineEdge, OutgoingEdgePartition, label)
        if application_graph:
            application_graph.forget_machine_graph()
            # Check the first vertex added
            self._application_level_used = True
        else:
            # Must be false as there is no App_graph
            self._application_level_used = False
        self._multicast_partitions = DefaultOrderedDict(
            lambda: DefaultOrderedDict(set))

    @overrides(Graph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):
        super(MachineGraph, self).add_edge(edge, outgoing_edge_partition_name)
        if edge.traffic_type == EdgeTrafficType.MULTICAST:
            if edge.pre_vertex.app_vertex:
                by_app = self._multicast_partitions[
                    edge.pre_vertex.app_vertex]
            else:
                by_app = self._multicast_partitions[
                    edge.pre_vertex]
            by_partition = by_app[outgoing_edge_partition_name]
            by_partition.add(edge.pre_vertex)

    @property
    def multicast_partitions(self):
        """
        Returns a double dictionary of  app id then
        outgoing_edge_partition_name to a set of machine_vertex that act as
        pre vertices for these multicast edges

        The app_id is normally the (machine) edge.pre_vertex.app_vertex.
        This then groups the edges which come from the same app_vertex
        If the (machine) edge.pre_vertex has no app vertex then the app_id will
        be the machine vertex which will then form its own group of 1

        :rtype dict(Vertex, dict(str, set(MachineVertex))
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
                        "vertex", vertex,
                        self.MISSING_APP_VERTEX_ERROR_MESSAGE)
        else:
            if vertex.app_vertex:
                raise PacmanInvalidParameterException(
                    "vertex", vertex, self.UNEXPECTED_APP_VERTEX_ERROR_MESSAGE)

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
    def add_outgoing_edge_partition(self, outgoing_edge_partition):
        if self.__frozen:
            raise PacmanConfigurationException(
                "Please add partitions via simulator not directly to this "
                "graph")
        super(_FrozenMachineGraph, self).add_outgoing_edge_partition(
            outgoing_edge_partition)
