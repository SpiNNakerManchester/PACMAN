# Copyright (c) 2017-2022 The University of Manchester
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

from collections import defaultdict
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)
from pacman.model.graphs.common import ConstrainedObject


class Graph(ConstrainedObject, metaclass=AbstractBase):
    """ A graph that specifies the allowed types of the vertices and edges.
    """

    __slots__ = [
        # The classes of vertex that are allowed in this graph
        "_allowed_vertex_types",
        # The classes of edges that are allowed in this graph
        "_allowed_edge_types",
        # The vertices of the graph
        "_vertices",
        # The incoming edges by post-vertex
        "_incoming_edges",
        # The label of the graph
        "_label",
        # map between labels and vertex
        "_vertex_by_label",
        # count of vertex which had a None or already used label
        "_unlabelled_vertex_count"]

    def __init__(self, allowed_vertex_types, allowed_edge_types, label):
        """
        :param allowed_vertex_types:
            A single or tuple of types of vertex to be allowed in the graph
        :type allowed_vertex_types: type or tuple(type, ...)
        :param allowed_edge_types:
            A single or tuple of types of edges to be allowed in the graph
        :type allowed_edge_types: type or tuple(type, ...)
        :param label: The label on the graph, or None
        :type label: str or None
        """
        super().__init__(None)
        self._allowed_vertex_types = allowed_vertex_types
        self._allowed_edge_types = allowed_edge_types
        self._vertices = []
        self._vertex_by_label = dict()
        self._unlabelled_vertex_count = 0
        self._incoming_edges = defaultdict(OrderedSet)
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
        """ Add an edge to the graph and its partition

        If required and possible will create a new partition in the graph

        Returns the partition the edge was added to

        :param AbstractEdge edge: The edge to add
        :param str outgoing_edge_partition_name:
            The name of the edge partition to add the edge to; each edge
            partition is the partition of edges that start at the same vertex
        :rtype: AbstractEdgePartition
        :raises PacmanInvalidParameterException:
            If the edge is not of a valid type or if edges have already been
            added to this partition that start at a different vertex to this
            one
        """
        # Add the edge to the partition
        partition = self.get_outgoing_edge_partition_starting_at_vertex(
            edge.pre_vertex, outgoing_edge_partition_name)
        if partition is None:
            partition = self.new_edge_partition(
                outgoing_edge_partition_name, edge)
            self.add_outgoing_edge_partition(partition)
        self._register_edge(edge, partition)
        partition.add_edge(edge, id(self))
        return partition

    def _register_edge(self, edge, partition):
        """ Add an edge to the graph.

        :param AbstractEdge edge: The edge to add
        :param AbstractEdgePartition partition:
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
                "Edge", str(edge.pre_vertex),
                "Pre-vertex must be known in graph")
        if edge.post_vertex.label not in self._vertex_by_label:
            raise PacmanInvalidParameterException(
                "Edge", str(edge.post_vertex),
                "Post-vertex must be known in graph")

        # Add the edge to the indices
        self._incoming_edges[edge.post_vertex].add(edge)

    @abstractmethod
    def new_edge_partition(self, name, edge):
        """ How we create a new :py:class:`AbstractSingleSourcePartition` in \
            the first place. Uses the first/only element in the allowed \
            partition types argument to the graph's constructor.

        Called from :py:meth:`~add_edge`.
        Can be overridden if different arguments should be passed.

        :param str name: The identifier of the partition
        :param AbstractEdge edge: An edge for the partition
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

    @abstractmethod
    def add_outgoing_edge_partition(self, edge_partition):
        """ Add an edge partition to the graph.

        Will also add any edges already in the partition as well

        :param AbstractEdgePartition edge_partition: The edge partition to add
        :raises PacmanAlreadyExistsException:
            If a partition already exists with the same pre_vertex and
            identifier
        """

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
        # pylint: disable=not-an-iterable
        # https://github.com/PyCQA/pylint/issues/3105
        """ The edges in the graph

        :rtype: iterable(AbstractEdge)
        """
        return [
            edge
            for partition in self.outgoing_edge_partitions
            for edge in partition.edges]

    @abstractproperty
    def outgoing_edge_partitions(self):
        """ The edge partitions in the graph.

        :rtype: iterable(AbstractEdgePartition)
        """

    @abstractproperty
    def n_outgoing_edge_partitions(self):
        """ The number of outgoing edge partitions in the graph.

        :rtype: int
        """

    def get_edges_starting_at_vertex(self, vertex):
        """ Get all the edges that start at the given vertex.

        :param AbstractVertex vertex:
            The vertex at which the edges to get start
        :rtype: iterable(AbstractEdge)
        """
        parts = self.get_outgoing_edge_partitions_starting_at_vertex(vertex)
        for partition in parts:
            for edge in partition.edges:
                yield edge

    def get_edges_ending_at_vertex(self, vertex):
        """ Get all the edges that end at the given vertex.

        :param AbstractVertex vertex:
            The vertex at which the edges to get end
        :rtype: iterable(AbstractEdge)
        """
        if vertex not in self._incoming_edges:
            return []
        return self._incoming_edges[vertex]

    @abstractmethod
    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the edge partitions that start at the given vertex.

        :param AbstractVertex vertex:
            The vertex at which the edge partitions to find starts
        :rtype: iterable(AbstractEdgePartition)
        """

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
        # In general, very few partitions start at a given vertex, so iteration
        # isn't going to be as onerous as it looks
        parts = self.get_outgoing_edge_partitions_starting_at_vertex(vertex)
        for partition in parts:
            if partition.identifier == outgoing_edge_partition_name:
                return partition
        return None
