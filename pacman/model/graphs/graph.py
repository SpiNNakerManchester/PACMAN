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

from collections import OrderedDict
from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.default_ordered_dict import DefaultOrderedDict
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)
from .abstract_edge_partition import AbstractEdgePartition
from .abstract_multiple_partition import AbstractMultiplePartition
from .abstract_single_source_partition import AbstractSingleSourcePartition
from .abstract_edge import AbstractEdge
from .abstract_vertex import AbstractVertex
from pacman.model.graphs.common import ConstrainedObject


@add_metaclass(AbstractBase)
class Graph(ConstrainedObject):
    """ A graph that specifies the allowed types of the vertices and edges.
    """

    __slots__ = [
        # The classes of vertex that are allowed in this graph
        "_allowed_vertex_types",
        # The classes of edges that are allowed in this graph
        "_allowed_edge_types",
        # The vertices of the graph
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
        # the outgoing partitions by edge
        "_outgoing_edge_partition_by_edge",
        # The sdram outgoing edge partitions by pre-vertex
        "_outgoing_sdram_edge_partitions_by_pre_vertex",
        # The label of the graph
        "_label",
        # map between labels and vertex
        "_vertex_by_label",
        # count of vertex which had a None or already used label
        "_unlabelled_vertex_count"]

    def __init__(self, allowed_vertex_types, allowed_edge_types,
                 allowed_partition_types, label):
        """
        :param allowed_vertex_types:
            A single or tuple of types of vertex to be allowed in the graph
        :type allowed_vertex_types: type or tuple(type, ...)
        :param allowed_edge_types:
            A single or tuple of types of edges to be allowed in the graph
        :type allowed_edge_types: type or tuple(type, ...)
        :param allowed_partition_types:
            A single or tuple of types of partitions to be allowed in the
            graph
        :type allowed_partition_types: type or tuple(type, ...)
        :param label: The label on the graph, or None
        :type label: str or None
        """
        super(Graph, self).__init__(None)
        self._allowed_vertex_types = allowed_vertex_types
        self._allowed_edge_types = allowed_edge_types
        self._allowed_partition_types = allowed_partition_types
        self._vertices = []
        self._vertex_by_label = dict()
        self._unlabelled_vertex_count = 0
        self._outgoing_edge_partitions_by_name = OrderedDict()
        self._outgoing_edges = DefaultOrderedDict(OrderedSet)
        self._incoming_edges = DefaultOrderedDict(OrderedSet)
        self._incoming_edges_by_partition_name = DefaultOrderedDict(list)
        self._outgoing_edge_partitions_by_pre_vertex = \
            DefaultOrderedDict(OrderedSet)
        self._outgoing_sdram_edge_partitions_by_pre_vertex = \
            DefaultOrderedDict(OrderedSet)
        self._outgoing_edge_partition_by_edge = OrderedDict()
        self._label = label

    @property
    def label(self):
        """ The label of the graph.

        :rtype: str
        """
        return self._label

    def _label_postfix(self):
        self._unlabelled_vertex_count += 1
        return str(self._unlabelled_vertex_count)

    def add_vertex(self, vertex):
        """ Add a vertex to the graph.

        :param AbstractVertex vertex: The vertex to add
        :raises PacmanInvalidParameterException:
            If the vertex is not of a valid type
        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        """
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

    def add_vertices(self, vertices):
        """ Add a collection of vertices to the graph.

        :param iterable(AbstractVertex) vertices: The vertices to add
        :raises PacmanInvalidParameterException:
            If any vertex is not of a valid type
        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        """
        for v in vertices:
            self.add_vertex(v)

    def add_edge(self, edge, outgoing_edge_partition_name):
        """ Add an edge to the graph.

        :param AbstractEdge edge: The edge to add
        :param str outgoing_edge_partition_name:
            The name of the edge partition to add the edge to; each edge
            partition is the partition of edges that start at the same vertex
        :raises PacmanInvalidParameterException:
            If the edge is not of a valid type or if edges have already been
            added to this partition that start at a different vertex to this
            one
        """
        # verify that the edge is one suitable for this graph
        if not isinstance(edge, self._allowed_edge_types):
            raise PacmanInvalidParameterException(
                "edge", edge.__class__,
                "Edges of this graph must be one of the following types:"
                " {}".format(self._allowed_edge_types))

        if edge.pre_vertex.label not in self._vertex_by_label:
            raise PacmanInvalidParameterException(
                "edge", str(edge.pre_vertex),
                "pre-vertex must be known in graph")
        if edge.post_vertex.label not in self._vertex_by_label:
            raise PacmanInvalidParameterException(
                "edge", str(edge.post_vertex),
                "post-vertex must be known in graph")

        # Add the edge to the partition
        key = (edge.pre_vertex, outgoing_edge_partition_name)
        partition = self._outgoing_edge_partitions_by_name.get(key, None)
        if partition is None:
            partition = self.new_edge_partition(
                outgoing_edge_partition_name, edge.pre_vertex)
            self._outgoing_edge_partitions_by_pre_vertex[edge.pre_vertex].add(
                partition)
            self._outgoing_edge_partitions_by_name[key] = partition
        partition.add_edge(edge)

        # Add the edge to the indices
        self._outgoing_edges[edge.pre_vertex].add(edge)
        self._incoming_edges_by_partition_name[
            edge.post_vertex, outgoing_edge_partition_name].append(edge)
        self._incoming_edges[edge.post_vertex].add(edge)
        if edge in self._outgoing_edge_partition_by_edge:
            raise PacmanAlreadyExistsException("edge", edge)
        self._outgoing_edge_partition_by_edge[edge] = partition

    @abstractmethod
    def new_edge_partition(self, name, pre_vertex):
        """ How we create a new :py:class:`AbstractSingleSourcePartition` in \
            the first place. Uses the first/only element in the allowed \
            partition types argument to the graph's constructor.

        Called from :py:method:`~add_edge`.
        Can be overridden if different arguments should be passed.

        :param str name: The identifier of the partition
        :param AbstractVertex pre_vertex:
            The starting vertex for the partition
        :return: the new edge partition
        :rtype: AbstractSingleSourcePartition
        """

    def add_edges(self, edges, outgoing_edge_partition_name):
        """ Add a collection of edges to the graph.

        :param iterable(AbstractEdge) edges: The edges to add
        :param str outgoing_edge_partition_name:
            The name of the edge partition to add the edges to; each edge
            partition is the partition of edges that start at the same vertex
        :raises PacmanInvalidParameterException:
            If any edge is not of a valid type or if edges have already been
            added to this partition that start at a different vertex to this
            one
        """
        for e in edges:
            self.add_edge(e, outgoing_edge_partition_name)

    def add_outgoing_edge_partition(self, edge_partition):
        """ Add an edge partition to the graph.

        :param AbstractEdgePartition edge_partition:
            The edge partition to add
        :raises PacmanAlreadyExistsException:
            If a partition already exists with the same pre_vertex and
            identifier
        """
        # verify that this partition is suitable for this graph
        if not isinstance(edge_partition, self._allowed_partition_types):
            raise PacmanInvalidParameterException(
                "outgoing_edge_partition", str(edge_partition.__class__),
                "Partitions of this graph must be one of the following types:"
                " {}".format(self._allowed_partition_types))

        # check if its a single pre or multiple pre
        if isinstance(edge_partition, AbstractSingleSourcePartition):
            pre_vertices = [edge_partition.pre_vertex]
        elif isinstance(edge_partition, AbstractMultiplePartition):
            pre_vertices = edge_partition.pre_vertices
        else:
            raise PacmanInvalidParameterException(
                "outgoing_edge_partition", str(edge_partition.__class__),
                "The graph does not know how to handle outgoing partitions "
                "that are not of types [single source, multiple]")

        for pre_vertex in pre_vertices:
            # check this partition doesn't already exist
            if ((pre_vertex, edge_partition.identifier) in
                    self._outgoing_edge_partitions_by_name):
                raise PacmanAlreadyExistsException(
                    str(AbstractEdgePartition.__class__),
                    str(pre_vertex, edge_partition.identifier))
        from pacman.model.graphs.machine import AbstractSDRAMPartition
        if (isinstance(edge_partition, AbstractSDRAMPartition)):
            for pre_vertex in pre_vertices:
                self._outgoing_sdram_edge_partitions_by_pre_vertex[
                    pre_vertex].add(edge_partition)
        else:
            for pre_vertex in pre_vertices:
                self._outgoing_edge_partitions_by_pre_vertex[pre_vertex].add(
                    edge_partition)

        for pre_vertex in pre_vertices:
            self._outgoing_edge_partitions_by_name[
                pre_vertex, edge_partition.identifier] = edge_partition

    @property
    def vertices(self):
        """ The vertices in the graph.

        :rtype: iterable(AbstractVertex)
        """
        return self._vertices

    def vertex_by_label(self, label):
        return self._vertex_by_label[label]

    @property
    def n_vertices(self):
        """ The number of vertices in the graph.

        :rtype: int
        """
        return len(self._vertices)

    @property
    def edges(self):
        """ The edges in the graph

        :rtype: iterable(AbstractEdge)
        """
        return [
            edge
            for partition in self._outgoing_edge_partitions_by_name.values()
            for edge in partition.edges]

    @property
    def outgoing_edge_partitions(self):
        """ The edge partitions in the graph.

        :rtype: iterable(AbstractEdgePartition)
        """
        seen = set()
        for element in self._outgoing_edge_partitions_by_name.values():
            if element not in seen:
                yield element
                seen.add(element)

    @property
    def n_outgoing_edge_partitions(self):
        """ The number of outgoing edge partitions in the graph.

        :rtype: int
        """
        return len(self._outgoing_edge_partitions_by_name)

    def get_outgoing_partition_for_edge(self, edge):
        """ Gets the partition this edge is associated with.

        :param AbstractEdge edge: the edge to find associated partition
        :rtype: AbstractEdgePartition
        """
        return self._outgoing_edge_partition_by_edge[edge]

    def get_edges_starting_at_vertex(self, vertex):
        """ Get all the edges that start at the given vertex.

        :param AbstractVertex vertex:
            The vertex at which the edges to get start
        :rtype: iterable(AbstractEdge)
        """
        return self._outgoing_edges[vertex]

    def get_edges_ending_at_vertex(self, vertex):
        """ Get all the edges that end at the given vertex.

        :param AbstractVertex vertex:
            The vertex at which the edges to get end
        :rtype: iterable(AbstractEdge)
        """
        if vertex not in self._incoming_edges:
            return []
        return self._incoming_edges[vertex]

    def get_edges_ending_at_vertex_with_partition_name(
            self, vertex, partition_name):
        """ Get all the edges that end at the given vertex, and reside in the
            correct partition ID.

        :param AbstractVertex vertex: The vertex at which the edges to get end
        :param str partition_name: the label for the partition
        :return: iterable(AbstractEdge)
        """
        key = (vertex, partition_name)
        if key not in self._incoming_edges_by_partition_name:
            return []
        return self._incoming_edges_by_partition_name[key]

    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the edge partitions that start at the given vertex.

        :param AbstractVertex vertex:
            The vertex at which the edge partitions to find starts
        :rtype: iterable(AbstractEdgePartition)
        """
        return self._outgoing_edge_partitions_by_pre_vertex[vertex]

    def get_sdram_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the sdram edge partitions that start at the given vertex.

        :param AbstractVertex vertex:
            The vertex at which the sdram edge partitions to find starts
        :rtype: iterable(AbstractSDRAMPartition)
        """
        return self._outgoing_sdram_edge_partitions_by_pre_vertex[vertex]

    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        """ Get the given outgoing edge partition that starts at the
            given vertex, or `None` if no such edge partition exists.

        :param AbstractVertex vertex:
            The vertex at the start of the edges in the partition
        :param str outgoing_edge_partition_name:
            The name of the edge partition
        :return: the named edge partition, or None if no such partition exists
        :rtype: AbstractEdgePartition or None
        """
        return self._outgoing_edge_partitions_by_name.get(
            (vertex, outgoing_edge_partition_name), None)

    def __contains__(self, value):
        """ Determines if a value is an object that is in the graph.

        :param value: The object to see if it is in the graph
        :type value: AbstractVertex or AbstractEdge or AbstractEdgePartition
        :return: True if the value is in the graph, False otherwise
        :rtype: bool
        """
        if isinstance(value, AbstractEdgePartition):
            return value in self._outgoing_edge_partitions_by_name.values()
        elif isinstance(value, AbstractEdge):
            return value in self._outgoing_edge_partition_by_edge
        elif isinstance(value, AbstractVertex):
            return value in self._vertices
        return False
