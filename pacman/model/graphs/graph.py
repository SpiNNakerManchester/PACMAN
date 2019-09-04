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

try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict
from spinn_utilities.ordered_default_dict import DefaultOrderedDict
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)
from pacman.model.graphs import OutgoingEdgePartition
from pacman.model.graphs.common import ConstrainedObject


class AbstractGraph(ConstrainedObject):
    """ A graph that specifies the allowed types of the vertices and edges.
    """

    __slots__ = [
        # The classes of vertex that are allowed in this graph
        "_allowed_vertex_types",
        # The classes of edges that are allowed in this graph
        "_allowed_edge_types",
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
        # the outgoing partitions by edge
        "_outgoing_edge_partition_by_edge",
        # The label of the graph
        "_label"]

    def __init__(self, allowed_vertex_types, allowed_edge_types, label):
        """
        :param allowed_vertex_types:\
            A single or tuple of types of vertex to be allowed in the graph
        :param allowed_edge_types:\
            A single or tuple of types of edges to be allowed in the graph
        :param label: The label on the graph, or None
        """
        super(AbstractGraph, self).__init__(None)
        self._allowed_vertex_types = allowed_vertex_types
        self._allowed_edge_types = allowed_edge_types

        self._vertices = OrderedSet()
        self._outgoing_edge_partitions_by_name = OrderedDict()
        self._outgoing_edges = DefaultOrderedDict(OrderedSet)
        self._incoming_edges = DefaultOrderedDict(OrderedSet)
        self._incoming_edges_by_partition_name = DefaultOrderedDict(list)
        self._outgoing_edge_partitions_by_pre_vertex = \
            DefaultOrderedDict(OrderedSet)
        self._outgoing_edge_partition_by_edge = OrderedDict()
        self._label = label

    @property
    def label(self):
        """ The label of the graph.

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    def add_vertex(self, vertex):
        """ Add a vertex to the graph.

        :param vertex: The vertex to add
        :type vertex: :py:class:`pacman.model.graphs.AbstractVertex`
        :raises PacmanInvalidParameterException:\
            If the vertex is not of a valid type
        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        """
        if not isinstance(vertex, self._allowed_vertex_types):
            raise PacmanInvalidParameterException(
                "vertex", vertex.__class__,
                "Vertices of this graph must be one of the following types:"
                " {}".format(self._allowed_vertex_types))
        self._vertices.add(vertex)

    def add_vertices(self, vertices):
        """ Add a collection of vertices to the graph.

        :param vertices: The vertices to add
        :type vertices: \
            iterable(:py:class:`pacman.model.graphs.AbstractVertex`)
        :raises PacmanInvalidParameterException:\
            If any vertex is not of a valid type
        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        """
        for v in vertices:
            self.add_vertex(v)

    def add_edge(self, edge, outgoing_edge_partition_name):
        """ Add an edge to the graph.

        :param edge: The edge to add
        :type edge: :py:class:`pacman.model.graphs.AbstractEdge`
        :param outgoing_edge_partition_name: \
            The name of the edge partition to add the edge to; each edge\
            partition is the partition of edges that start at the same vertex
        :type outgoing_edge_partition_name: str
        :raises PacmanInvalidParameterException:\
            If the edge is not of a valid type or if edges have already been\
            added to this partition that start at a different vertex to this\
            one
        """
        # verify that the edge is one suitable for this graph
        if not isinstance(edge, self._allowed_edge_types):
            raise PacmanInvalidParameterException(
                "edge", edge.__class__,
                "Edges of this graph must be one of the following types:"
                " {}".format(self._allowed_edge_types))

        if edge.pre_vertex not in self._vertices:
            raise PacmanInvalidParameterException(
                "edge", edge.pre_vertex, "pre-vertex must be known in graph")
        if edge.post_vertex not in self._vertices:
            raise PacmanInvalidParameterException(
                "edge", edge.post_vertex, "post-vertex must be known in graph")

        # Add the edge to the partition
        partition = None
        if ((edge.pre_vertex, outgoing_edge_partition_name) not in
                self._outgoing_edge_partitions_by_name):
            partition = OutgoingEdgePartition(
                outgoing_edge_partition_name, self._allowed_edge_types)
            self._outgoing_edge_partitions_by_pre_vertex[
                edge.pre_vertex].add(partition)
            self._outgoing_edge_partitions_by_name[
                edge.pre_vertex, outgoing_edge_partition_name] = partition
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

    def add_edges(self, edges, outgoing_edge_partition_name):
        """ Add a collection of edges to the graph.

        :param edges: The edges to add
        :type edges: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        :param outgoing_edge_partition_name: \
            The name of the edge partition to add the edges to; each edge\
            partition is the partition of edges that start at the same vertex
        :type outgoing_edge_partition_name: str
        :raises PacmanInvalidParameterException:\
            If any edge is not of a valid type or if edges have already been\
            added to this partition that start at a different vertex to this\
            one
        """
        for e in edges:
            self.add_edge(e, outgoing_edge_partition_name)

    def add_outgoing_edge_partition(self, outgoing_edge_partition):
        """ Add an outgoing edge partition to the graph.

        :param outgoing_edge_partition: The outgoing edge partition to add
        :type outgoing_edge_partition:\
            :py:class:`pacman.model.graphs.OutgoingEdgePartition`
        :raises PacmanAlreadyExistsException:\
            If a partition already exists with the same pre_vertex and\
            identifier
        """
        # verify that this partition is suitable for this graph
        if not isinstance(outgoing_edge_partition, OutgoingEdgePartition):
            raise PacmanInvalidParameterException(
                "outgoing_edge_partition", outgoing_edge_partition.__class__,
                "Partitions of this graph must be one of the following types:"
                " {}".format(OutgoingEdgePartition.__class__))

        # check this partition doesn't already exist
        if ((outgoing_edge_partition.pre_vertex,
                outgoing_edge_partition.identifier) in
                self._outgoing_edge_partitions_by_name):
            raise PacmanAlreadyExistsException(
                "{}".format(OutgoingEdgePartition.__class__),
                (outgoing_edge_partition.pre_vertex,
                 outgoing_edge_partition.identifier))

        self._outgoing_edge_partitions_by_pre_vertex[
            outgoing_edge_partition.pre_vertex].add(outgoing_edge_partition)
        self._outgoing_edge_partitions_by_name[
            outgoing_edge_partition.pre_vertex,
            outgoing_edge_partition.identifier] = outgoing_edge_partition

    @property
    def vertices(self):
        """ The vertices in the graph.

        :rtype: iterable(:py:class:`pacman.model.graphs.AbstractVertex`)
        """
        return self._vertices

    @property
    def n_vertices(self):
        """ The number of vertices in the graph.

        :rtype: int
        """
        return len(self._vertices)

    @property
    def edges(self):
        """ The edges in the graph

        :rtype: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        """
        return [
            edge
            for partition in self._outgoing_edge_partitions_by_name.values()
            for edge in partition.edges]

    @property
    def outgoing_edge_partitions(self):
        """ The outgoing edge partitions in the graph.

        :rtype: iterable(:py:class:`pacman.model.graphs.OutgoingEdgePartition`)
        """
        return self._outgoing_edge_partitions_by_name.values()

    @property
    def n_outgoing_edge_partitions(self):
        """ The number of outgoing edge partitions in the graph.

        :rtype: int
        """
        return len(self._outgoing_edge_partitions_by_name)

    def get_outgoing_partition_for_edge(self, edge):
        """ Gets the outgoing partition this edge is associated with.

        :param edge: the edge to find associated partition
        :type edge: :py:class:`pacman.model.graphs.AbstractEdge`
        :return: the outgoing partition
        :rtype: :py:class:`pacman.model.graphs.OutgoingEdgePartition`
        """
        return self._outgoing_edge_partition_by_edge[edge]

    def get_edges_starting_at_vertex(self, vertex):
        """ Get all the edges that start at the given vertex.

        :param vertex: The vertex at which the edges to get start
        :type vertex: :py:class:`pacman.model.graphs.AbstractVertex`
        :rtype: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        """
        return self._outgoing_edges[vertex]

    def get_edges_ending_at_vertex(self, vertex):
        """ Get all the edges that end at the given vertex.

        :param vertex: The vertex at which the edges to get end
        :type vertex: :py:class:`pacman.model.graphs.AbstractVertex`
        :rtype: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        """
        if vertex not in self._incoming_edges:
            return []
        return self._incoming_edges[vertex]

    def get_edges_ending_at_vertex_with_partition_name(
            self, vertex, partition_name):
        """ Get all the edges that end at the given vertex, and reside in the\
            correct partition ID.

        :param vertex:  The vertex at which the edges to get end
        :type vertex: :py:class:`pacman.model.graphs.AbstractVertex`
        :param partition_name: the label for the partition
        :type partition_name: str
        :return: iterable(:py:class:`pacman.model.graphs.AbstractEdge`)
        """
        key = (vertex, partition_name)
        if key not in self._incoming_edges_by_partition_name:
            return []
        return self._incoming_edges_by_partition_name[key]

    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the edge partitions that start at the given vertex.

        :param vertex: The vertex at which the edge partitions to find starts
        :type vertex: :py:class:`pacman.model.graphs.AbstractVertex`
        :rtype: iterable(:py:class:`pacman.model.graphs.OutgoingEdgePartition`)
        """
        return self._outgoing_edge_partitions_by_pre_vertex[vertex]

    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        """ Get the given outgoing edge partition that starts at the\
            given vertex, or None if no such edge partition exists.

        :param vertex: The vertex at the start of the edges in the partition
        :type vertex: :py:class:`pacman.model.graphs.AbstractVertex`
        :param outgoing_edge_partition_name: The name of the edge partition
        :type outgoing_edge_partition_name: str
        :rtype: :py:class:`pacman.model.graphs.OutgoingEdgePartition`
        """
        return self._outgoing_edge_partitions_by_name.get(
            (vertex, outgoing_edge_partition_name), None)
