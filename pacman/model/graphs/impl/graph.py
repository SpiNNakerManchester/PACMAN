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
from pacman.model.graphs.abstract_costed_partition import \
    AbstractCostedPartition
from pacman.model.graphs.abstract_sdram_partition import AbstractSDRAMPartition

try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
from spinn_utilities.overrides import overrides
from spinn_utilities.ordered_default_dict import DefaultOrderedDict
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)
from pacman.model.graphs import AbstractGraph, AbstractMultiplePartition, \
    AbstractSingleSourcePartition
from pacman.model.graphs.common import ConstrainedObject
from .outgoing_edge_partition import OutgoingEdgePartition


class Graph(ConstrainedObject, AbstractGraph):
    """ A graph implementation that specifies the allowed types of the\
        vertices and edges.
    """

    __slots__ = [
        # The classes of vertex that are allowed in this graph
        "_allowed_vertex_types",
        # The classes of outgoing edge partition that are allowed in this
        # graph
        "_allowed_partition_types",
        # The vertices of the graph
        "_vertices",
        # The outgoing edge partitions of the graph by name
        "_outgoing_edge_partitions_by_name",
        # The outgoing edges by pre-vertex
        "_outgoing_edges",
        # The incoming edges by post-vertex
        "_incoming_edges",
        # map between incoming edges and their associated partitions
        "_incoming_edges_by_partition_name",
        # The outgoing edge partitions by pre-vertex
        "_outgoing_edge_partitions_by_pre_vertex",
        # The sdram outgoing edge partitions by pre-vertex
        "_outgoing_costed_edge_partitions_by_pre_vertex",
        # the outgoing partitions by edge
        "_outgoing_edge_partition_by_edge",
        # The label of the graph
        "_label",
        # map between labels and vertex
        "_vertex_by_label",
        # count of vertex which had a None or already used label
        "_none_labelled_vertex_count",
    ]

    def __init__(self, allowed_vertex_types, allowed_partition_types, label):
        """
        :param allowed_vertex_types:\
            A single or tuple of types of vertex to be allowed in the graph
        :param allowed_partition_types:\
            A single or tuple of types of partitions to be allowed in the graph
        :param label: The label on the graph, or None
        """
        super(Graph, self).__init__(None)
        self._allowed_vertex_types = allowed_vertex_types
        self._allowed_partition_types = allowed_partition_types
        self._vertices = []
        self._vertex_by_label = dict()
        self._none_labelled_vertex_count = 0
        self._outgoing_edge_partitions_by_name = OrderedDict()
        self._outgoing_edges = DefaultOrderedDict(OrderedSet)
        self._incoming_edges = DefaultOrderedDict(OrderedSet)
        self._incoming_edges_by_partition_name = DefaultOrderedDict(list)
        self._outgoing_edge_partitions_by_pre_vertex = \
            DefaultOrderedDict(OrderedSet)
        self._outgoing_costed_edge_partitions_by_pre_vertex = \
            DefaultOrderedDict(OrderedSet)
        self._outgoing_edge_partition_by_edge = OrderedDict()
        self._label = label

    @property
    @overrides(AbstractGraph.label)
    def label(self):
        return self._label

    def _label_postfix(self):
        self._none_labelled_vertex_count += 1
        return str(self._none_labelled_vertex_count)

    @overrides(AbstractGraph.add_vertex)
    def add_vertex(self, vertex):
        if not isinstance(vertex, self._allowed_vertex_types):
            raise PacmanInvalidParameterException(
                "vertex", str(vertex.__class__),
                "Vertices of this graph must be one of the following types:"
                " {}".format(self._allowed_vertex_types))
        if not vertex.label:
            vertex.set_label(
                vertex.__class__.__name__ + "_" + self._label_postfix())
        elif vertex.label in self._vertex_by_label:
            if self._vertex_by_label[vertex.label] == vertex:
                raise PacmanAlreadyExistsException("vertex", vertex.label)
            vertex.set_label(vertex.label + self._label_postfix())
        vertex.addedToGraph()
        self._vertices.append(vertex)
        self._vertex_by_label[vertex.label] = vertex

    @overrides(AbstractGraph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):

        if edge.pre_vertex not in self._vertices:
            raise PacmanInvalidParameterException(
                "edge", str(edge.pre_vertex),
                "pre-vertex must be known in graph")
        if edge.post_vertex not in self._vertices:
            raise PacmanInvalidParameterException(
                "edge", str(edge.post_vertex),
                "post-vertex must be known in graph")

        # Add the edge to the partition
        if ((edge.pre_vertex, outgoing_edge_partition_name) not in
                self._outgoing_edge_partitions_by_name):
            raise PacmanInvalidParameterException(
                "vertex and partition name",
                str((edge.pre_vertex, outgoing_edge_partition_name)),
                "No outgoing partition for vertex {} with name "
                "{} exists".format(
                    edge.pre_vertex, outgoing_edge_partition_name))
        else:
            partition = self._outgoing_edge_partitions_by_name[
                edge.pre_vertex, outgoing_edge_partition_name]
        partition.add_edge(edge)

        # Add the edge to the indices
        self._outgoing_edges[edge.pre_vertex].add(edge)
        self._incoming_edges_by_partition_name[
            (edge.post_vertex, outgoing_edge_partition_name)].append(edge)
        self._incoming_edges[edge.post_vertex].add(edge)
        self._outgoing_edge_partition_by_edge[edge] = partition

    @overrides(AbstractGraph.add_outgoing_edge_partition)
    def add_outgoing_edge_partition(self, outgoing_edge_partition):

        # verify that this partition is suitable for this graph
        if not isinstance(
                outgoing_edge_partition, self._allowed_partition_types):
            raise PacmanInvalidParameterException(
                "outgoing_edge_partition", outgoing_edge_partition.__class__,
                "Partitions of this graph must be one of the following types:"
                " {}".format(self._allowed_partition_types))

        # check if its a single pre or multiple pre
        if isinstance(outgoing_edge_partition, AbstractSingleSourcePartition):
            pre_vertices = [outgoing_edge_partition.pre_vertex]
        elif isinstance(outgoing_edge_partition, AbstractMultiplePartition):
            pre_vertices = outgoing_edge_partition.pre_vertices
        else:
            raise PacmanInvalidParameterException(
                "outgoing_edge_partition", outgoing_edge_partition.__class__,
                "The graph does not know how to handle outgoing partitions"
                " which are not of types [single source, multiple]")

        for pre_vertex in pre_vertices:
            # check this partition doesn't already exist
            if ((pre_vertex, outgoing_edge_partition.identifier) in
                    self._outgoing_edge_partitions_by_name):
                raise PacmanAlreadyExistsException(
                    "{}".format(OutgoingEdgePartition.__class__),
                    str((pre_vertex, outgoing_edge_partition.identifier)))

        if isinstance(outgoing_edge_partition, AbstractCostedPartition):
            for pre_vertex in pre_vertices:
                self._outgoing_costed_edge_partitions_by_pre_vertex[
                    pre_vertex].add(outgoing_edge_partition)
        else:
            for pre_vertex in pre_vertices:
                self._outgoing_edge_partitions_by_pre_vertex[pre_vertex].add(
                    outgoing_edge_partition)

        for pre_vertex in pre_vertices:
            self._outgoing_edge_partitions_by_name[
                pre_vertex, outgoing_edge_partition.identifier] = (
                    outgoing_edge_partition)

    def outgoing_partition_exists(self, pre_vertex, identifier):
        return ((pre_vertex, identifier) in
                self._outgoing_edge_partitions_by_name)

    @property
    @overrides(AbstractGraph.vertices)
    def vertices(self):
        return self._vertices

    def vertex_by_label(self, label):
        return self._vertex_by_label[label]

    @property
    @overrides(AbstractGraph.n_vertices)
    def n_vertices(self):
        return len(self._vertices)

    @property
    @overrides(AbstractGraph.edges)
    def edges(self):
        return [
            edge
            for partition in self._outgoing_edge_partitions_by_name.values()
            for edge in partition.edges]

    @property
    @overrides(AbstractGraph.outgoing_edge_partitions)
    def outgoing_edge_partitions(self):
        data = OrderedSet()
        for element in self._outgoing_edge_partitions_by_name.values():
            data.add(element)
        return data

    @property
    @overrides(AbstractGraph.n_outgoing_edge_partitions)
    def n_outgoing_edge_partitions(self):
        return len(self._outgoing_edge_partitions_by_name)

    @overrides(AbstractGraph.get_outgoing_partition_for_edge)
    def get_outgoing_partition_for_edge(self, edge):
        return self._outgoing_edge_partition_by_edge[edge]

    @overrides(AbstractGraph.get_edges_starting_at_vertex)
    def get_edges_starting_at_vertex(self, vertex):
        return self._outgoing_edges[vertex]

    @overrides(AbstractGraph.get_edges_ending_at_vertex)
    def get_edges_ending_at_vertex(self, vertex):
        if vertex not in self._incoming_edges:
            return []
        return self._incoming_edges[vertex]

    @overrides(AbstractGraph.get_edges_ending_at_vertex_with_partition_name)
    def get_edges_ending_at_vertex_with_partition_name(
            self, vertex, partition_name):
        key = (vertex, partition_name)
        if key not in self._incoming_edges_by_partition_name:
            return []
        return self._incoming_edges_by_partition_name[key]

    @overrides(AbstractGraph.get_outgoing_edge_partitions_starting_at_vertex)
    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        return self._outgoing_edge_partitions_by_pre_vertex[vertex]

    @overrides(AbstractGraph.get_costed_edge_partitions_starting_at_vertex)
    def get_costed_edge_partitions_starting_at_vertex(self, vertex):
        return self._outgoing_costed_edge_partitions_by_pre_vertex[vertex]

    @overrides(AbstractGraph.get_outgoing_edge_partition_starting_at_vertex)
    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        return self._outgoing_edge_partitions_by_name.get(
            (vertex, outgoing_edge_partition_name), None)
