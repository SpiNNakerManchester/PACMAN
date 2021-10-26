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
from .application_edge_partition import ApplicationEdgePartition
from spinn_utilities.default_ordered_dict import DefaultOrderedDict
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)
from pacman.model.graphs.graph import Graph


class ApplicationGraph(Graph):
    """ An application-level abstraction of a graph.
    """

    __slots__ = [
        # The sets of edge partitions by pre-vertex
        "_outgoing_edge_partitions_by_pre_vertex",
    ]

    def __init__(self, label):
        """
        :param label: The label on the graph, or None
        :type label: str or None
        """
        super().__init__(ApplicationVertex, ApplicationEdge, label)
        self._outgoing_edge_partitions_by_pre_vertex = \
            DefaultOrderedDict(OrderedSet)

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

    @overrides(Graph.new_edge_partition)
    def new_edge_partition(self, name, edge):
        return ApplicationEdgePartition(
            identifier=name, pre_vertex=edge.pre_vertex)

    @overrides(Graph.add_outgoing_edge_partition)
    def add_outgoing_edge_partition(self, edge_partition):
        # verify that this partition is suitable for this graph
        if not isinstance(edge_partition, ApplicationEdgePartition):
            raise PacmanInvalidParameterException(
                "outgoing_edge_partition", edge_partition.__class__,
                "Partitions of this graph must be an ApplicationEdgePartition")

        # check this partition doesn't already exist
        key = (edge_partition.pre_vertex,
               edge_partition.identifier)
        if key in self._outgoing_edge_partitions_by_name:
            raise PacmanAlreadyExistsException(
                str(ApplicationEdgePartition), key)

        edge_partition.register_graph_code(id(self))

        self._outgoing_edge_partitions_by_pre_vertex[
            edge_partition.pre_vertex].add(edge_partition)
        self._outgoing_edge_partitions_by_name[key] = edge_partition
        for edge in edge_partition.edges:
            self._register_edge(edge, edge_partition)

    @property
    @overrides(Graph.outgoing_edge_partitions)
    def outgoing_edge_partitions(self):
        # This is based on the assumption that an Application partition is
        # always SingleSourced
        return self._outgoing_edge_partitions_by_name.values()

    @property
    @overrides(Graph.n_outgoing_edge_partitions)
    def n_outgoing_edge_partitions(self):
        # This is based on the assumption that an Application partition is
        # always SingleSourced
        return len(self._outgoing_edge_partitions_by_name)

    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the edge partitions that start at the given vertex.

        :param AbstractVertex vertex:
            The vertex at which the edge partitions to find starts
        :rtype: iterable(AbstractEdgePartition)
        """
        return self._outgoing_edge_partitions_by_pre_vertex[vertex]

    @property
    def n_machine_vertices(self):
        """
        The total number of machine vertices in the graph

        :rtpye: int
        """
        return sum(len(m.machine_vertices) for m in self.vertices)

    def clone(self):
        """
        Makes as shallow as possible copy of the graph.

        Vertices and edges are copied over. Partition will be new objects.

        :return: A shallow copy of this graph
        :rtype: ApplicationGraph
        """
        new_graph = ApplicationGraph(label=self.label)
        for vertex in self.vertices:
            new_graph.add_vertex(vertex)
        for outgoing_partition in self.outgoing_edge_partitions:
            for edge in outgoing_partition.edges:
                new_graph.add_edge(edge, outgoing_partition.identifier)
        return new_graph
