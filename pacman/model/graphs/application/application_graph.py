# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import defaultdict
from .application_edge import ApplicationEdge
from .application_vertex import ApplicationVertex
from .application_edge_partition import ApplicationEdgePartition
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)


class ApplicationGraph(object):
    """ An application-level abstraction of a graph.
    """

    __slots__ = [
        # The sets of edge partitions by pre-vertex
        "_outgoing_edge_partitions_by_pre_vertex",
        # The total number of outgoing edge partitions
        "_n_outgoing_edge_partitions",
        # count of vertex which had a None or already used label
        "_unlabelled_vertex_count",
        # map between labels and vertex
        "_vertex_by_label"
    ]

    def __init__(self):
        self._outgoing_edge_partitions_by_pre_vertex = defaultdict(OrderedSet)
        self._n_outgoing_edge_partitions = 0
        self._unlabelled_vertex_count = 0
        self._vertex_by_label = dict()

    def add_vertex(self, vertex):
        """ Add a vertex to the graph.

        :param ApplicationVertex vertex: The vertex to add
        :raises PacmanInvalidParameterException:
            If the vertex is not of a valid type
        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        """
        if not isinstance(vertex, ApplicationVertex):
            raise PacmanInvalidParameterException(
                "vertex", str(vertex.__class__),
                "Only an ApplicationVertex can be added")
        if not vertex.label:
            vertex.set_label(
                vertex.__class__.__name__ + "_" + self._label_postfix())
        elif vertex.label in self._vertex_by_label:
            if self._vertex_by_label[vertex.label] == vertex:
                raise PacmanAlreadyExistsException("vertex", vertex.label)
            vertex.set_label(vertex.label + self._label_postfix())
        vertex.addedToGraph()
        self._vertex_by_label[vertex.label] = vertex

    @property
    def vertices(self):
        """ The vertices in the graph.

        :rtype: iterable(AbstractVertex)
        """
        return self._vertex_by_label.values()

    def vertex_by_label(self, label):
        return self._vertex_by_label[label]

    @property
    def n_vertices(self):
        """ The number of vertices in the graph.

        :rtype: int
        """
        return len(self._vertex_by_label)

    def add_edge(self, edge, outgoing_edge_partition_name):
        """ Add an edge to the graph and its partition.

        If required and possible will create a new partition in the graph

        Returns the partition the edge was added to

        :param ApplicationEdge edge: The edge to add
        :param str outgoing_edge_partition_name:
            The name of the edge partition to add the edge to; each edge
            partition is the partition of edges that start at the same vertex
        :rtype: AbstractEdgePartition
        :raises PacmanInvalidParameterException:
            If the edge is not of a valid type or if edges have already been
            added to this partition that start at a different vertex to this
            one
        """
        self._check_edge(edge)
        # Add the edge to the partition
        partition = self.get_outgoing_edge_partition_starting_at_vertex(
            edge.pre_vertex, outgoing_edge_partition_name)
        if partition is None:
            partition = ApplicationEdgePartition(
                identifier=outgoing_edge_partition_name,
                pre_vertex=edge.pre_vertex)
            self._add_outgoing_edge_partition(partition)
        partition.add_edge(edge)
        return partition

    def _check_edge(self, edge):
        """ Add an edge to the graph.

        :param ApplicationEdge edge: The edge to add
        :raises PacmanInvalidParameterException:
            If the edge is not of a valid type or if edges have already been
            added to this partition that start at a different vertex to this
            one
        """
        # verify that the edge is one suitable for this graph
        if not isinstance(edge, ApplicationEdge):
            raise PacmanInvalidParameterException(
                "edge", edge.__class__,
                "Only ApplicationEdges can be added")

        if edge.pre_vertex.label not in self._vertex_by_label:
            raise PacmanInvalidParameterException(
                "Edge", str(edge.pre_vertex),
                "Pre-vertex must be known in graph")
        if edge.post_vertex.label not in self._vertex_by_label:
            raise PacmanInvalidParameterException(
                "Edge", str(edge.post_vertex),
                "Post-vertex must be known in graph")

    @property
    def edges(self):
        # pylint: disable=not-an-iterable
        # https://github.com/PyCQA/pylint/issues/3105
        """ The edges in the graph.

        :rtype: iterable(AbstractEdge)
        """
        return [
            edge
            for partition in self.outgoing_edge_partitions
            for edge in partition.edges]

    def _add_outgoing_edge_partition(self, edge_partition):
        """ Add an edge partition to the graph.

        Will also add any edges already in the partition as well

        :param ApplicationEdgePartition edge_partition:
        """
        self._outgoing_edge_partitions_by_pre_vertex[
            edge_partition.pre_vertex].add(edge_partition)
        self._n_outgoing_edge_partitions += 1

    @property
    def outgoing_edge_partitions(self):
        """ The edge partitions in the graph.

        :rtype: iterable(AbstractEdgePartition)
        """
        for partitions in \
                self._outgoing_edge_partitions_by_pre_vertex.values():
            for partition in partitions:
                yield partition

    @property
    def n_outgoing_edge_partitions(self):
        """ The number of outgoing edge partitions in the graph.

        :rtype: int
        """
        return self._n_outgoing_edge_partitions

    def get_outgoing_edge_partitions_starting_at_vertex(self, vertex):
        """ Get all the edge partitions that start at the given vertex.

        :param AbstractVertex vertex:
            The vertex at which the edge partitions to find starts
        :rtype: iterable(AbstractEdgePartition)
        """
        return self._outgoing_edge_partitions_by_pre_vertex[vertex]

    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex, outgoing_edge_partition_name):
        """
        Get the given outgoing edge partition that starts at the
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

    def reset(self):
        """ Reset all the application vertices.
        """
        for vertex in self.vertices:
            vertex.reset()

    def _label_postfix(self):
        self._unlabelled_vertex_count += 1
        return str(self._unlabelled_vertex_count)
