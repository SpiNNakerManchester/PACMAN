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

from .application_edge import ApplicationEdge
from .application_vertex import ApplicationVertex
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.graph import Graph
from pacman.model.graphs import OutgoingEdgePartition


class ApplicationGraph(Graph):
    """ An application-level abstraction of a graph.
    """

    __slots__ = []

    def __init__(self, label):
        """
        :param label: The label on the graph, or None
        :type label: str or None
        """
        super(ApplicationGraph, self).__init__(
            ApplicationVertex, ApplicationEdge, OutgoingEdgePartition, label)

    def forget_machine_graph(self):
        """ Forget the whole mapping from this graph to an application graph.
        """
        for v in self.vertices:
            v.forget_machine_vertices()
        for e in self.edges:
            e.forget_machine_edges()

    def forget_machine_edges(self):
        """ Ensure that all application edges in this graph forget what
            machine edges they map to. The mapping of vertices is unaffected.
        """
        for e in self.edges:
            e.forget_machine_edges()

    def clone(self, frozen=False):
        """
        Makes as shallow as possible copy of the graph.

        Vertices and edges are copied over. Partition will be new objects.

        :return: A shallow copy of this graph
        :rtype: ApplicationGraph
        """
        if frozen:
            new_graph = _FrozenApplicationGraph(label=self.label)
        else:
            new_graph = ApplicationGraph(label=self.label)
        for vertex in self.vertices:
            new_graph.add_vertex(vertex)
        for outgoing_partition in \
                self.outgoing_edge_partitions:
            for edge in outgoing_partition.edges:
                new_graph.add_edge(edge, outgoing_partition.identifier)
        if frozen:
            new_graph.freeze()
        return new_graph


class _FrozenApplicationGraph(ApplicationGraph):
    """ A frozen application-level abstraction of a graph.
    """
    # This is declared in the same file due to the circular dependency

    __slots__ = ["__frozen"]

    def __init__(self, label):
        """
        :param label: The label on the graph, or None
        :type label: str or None
        """
        super(_FrozenApplicationGraph, self).__init__(label)
        self.__frozen = False

    def freeze(self):
        """
        blocks any farther attempt to add to this graph

        :return:
        """
        self.__frozen = True

    @overrides(ApplicationGraph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):
        if self.__frozen:
            raise PacmanConfigurationException(
                "Please add edges via simulator not directly to this graph")
        super(_FrozenApplicationGraph, self).add_edge(
            edge, outgoing_edge_partition_name)

    @overrides(ApplicationGraph.add_vertex)
    def add_vertex(self, vertex):
        if self.__frozen:
            raise PacmanConfigurationException(
                "Please add vertices via simulator not directly to this graph")
        super(_FrozenApplicationGraph, self).add_vertex(vertex)

    @overrides(ApplicationGraph.add_outgoing_edge_partition)
    def add_outgoing_edge_partition(self, outgoing_edge_partition):
        if self.__frozen:
            raise PacmanConfigurationException(
                "Please add partitions via simulator not directly to this "
                "graph")
        super(_FrozenApplicationGraph, self).add_outgoing_edge_partition(
            outgoing_edge_partition)
