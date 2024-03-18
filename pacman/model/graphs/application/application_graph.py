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
from __future__ import annotations
from collections import defaultdict
from typing import Dict, Iterable, Optional, Sequence, cast

from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)

from .application_edge import ApplicationEdge
from .application_edge_partition import ApplicationEdgePartition
from .application_vertex import ApplicationVertex


class ApplicationGraph(object):
    """
    An application-level abstraction of a graph.
    """

    __slots__ = (
        # The sets of edge partitions by pre-vertex
        "_outgoing_edge_partitions_by_pre_vertex",
        # The total number of outgoing edge partitions
        "_n_outgoing_edge_partitions",
        # count of vertex which had a None or already used label
        "_unlabelled_vertex_count",
        # map between labels and vertex
        "_vertex_by_label")

    def __init__(self) -> None:
        self._outgoing_edge_partitions_by_pre_vertex: Dict[
            ApplicationVertex,
            OrderedSet[ApplicationEdgePartition]] = defaultdict(OrderedSet)
        self._n_outgoing_edge_partitions = 0
        self._unlabelled_vertex_count = 0
        self._vertex_by_label: Dict[str, ApplicationVertex] = dict()

    def add_vertex(self, vertex: ApplicationVertex):
        """
        Add a vertex to the graph.

        :param ~pacman.model.graphs.application.ApplicationVertex vertex:
            The vertex to add
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
        vertex.set_added_to_graph()
        self._vertex_by_label[cast(str, vertex.label)] = vertex

    @property
    def vertices(self) -> Iterable[ApplicationVertex]:
        """
        The vertices in the graph.

        :rtype: iterable(~pacman.model.graphs.AbstractVertex)
        """
        return self._vertex_by_label.values()

    def vertex_by_label(self, label: str) -> ApplicationVertex:
        """
        Looks up a vertex in the graph based on the label

        :param str label:
        :rtype: ApplicationVertex
        """
        return self._vertex_by_label[label]

    @property
    def n_vertices(self) -> int:
        """
        The number of vertices in the graph.

        :rtype: int
        """
        return len(self._vertex_by_label)

    def add_edge(
            self, edge: ApplicationEdge,
            outgoing_edge_partition_name: str) -> ApplicationEdgePartition:
        """
        Add an edge to the graph and its partition.

        If required and possible will create a new partition in the graph

        :param ~pacman.model.graphs.application.ApplicationEdge edge:
            The edge to add
        :param str outgoing_edge_partition_name:
            The name of the edge partition to add the edge to; each edge
            partition is the partition of edges that start at the same vertex
        :return: The partition the edge was added to.
        :rtype: ~pacman.model.graphs.AbstractEdgePartition
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

    def _check_edge(self, edge: ApplicationEdge):
        """
        Add an edge to the graph.

        :param ~pacman.model.graphs.application.ApplicationEdge edge:
            The edge to add
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
    def edges(self) -> Sequence[ApplicationEdge]:
        # pylint: disable=not-an-iterable
        # https://github.com/PyCQA/pylint/issues/3105
        """
        The edges in the graph.

        :rtype: iterable(~pacman.model.graphs.application.ApplicationEdge)
        """
        return [
            cast(ApplicationEdge, edge)
            for partition in self.outgoing_edge_partitions
            for edge in partition.edges]

    def _add_outgoing_edge_partition(
            self, edge_partition: ApplicationEdgePartition):
        """
        Add an edge partition to the graph.

        Will also add any edges already in the partition as well

        :param edge_partition:
        :type edge_partition:
            ~pacman.model.graphs.application.ApplicationEdgePartition
        """
        self._outgoing_edge_partitions_by_pre_vertex[
            edge_partition.pre_vertex].add(edge_partition)
        self._n_outgoing_edge_partitions += 1

    @property
    def outgoing_edge_partitions(self) -> Iterable[ApplicationEdgePartition]:
        """
        The edge partitions in the graph.

        :rtype: iterable(~pacman.model.graphs.AbstractEdgePartition)
        """
        for partitions in \
                self._outgoing_edge_partitions_by_pre_vertex.values():
            yield from partitions

    @property
    def n_outgoing_edge_partitions(self) -> int:
        """
        The number of outgoing edge partitions in the graph.

        :rtype: int
        """
        return self._n_outgoing_edge_partitions

    def get_outgoing_edge_partitions_starting_at_vertex(
            self, vertex: ApplicationVertex) -> Iterable[
                ApplicationEdgePartition]:
        """
        Get all the edge partitions that start at the given vertex.

        :param ~pacman.model.graphs.AbstractVertex vertex:
            The vertex at which the edge partitions to find starts
        :rtype: iterable(~pacman.model.graphs.AbstractEdgePartition)
        """
        return self._outgoing_edge_partitions_by_pre_vertex[vertex]

    def get_outgoing_edge_partition_starting_at_vertex(
            self, vertex: ApplicationVertex,
            outgoing_edge_partition_name: str) -> Optional[
                ApplicationEdgePartition]:
        """
        Get the given outgoing edge partition that starts at the
        given vertex, or `None` if no such edge partition exists.

        :param ~pacman.model.graphs.AbstractVertex vertex:
            The vertex at the start of the edges in the partition
        :param str outgoing_edge_partition_name:
            The name of the edge partition
        :return:
            The named edge partition, or `None` if no such partition exists
        :rtype: ~pacman.model.graphs.AbstractEdgePartition or None
        """
        # In general, very few partitions start at a given vertex, so iteration
        # isn't going to be as onerous as it looks
        parts = self.get_outgoing_edge_partitions_starting_at_vertex(vertex)
        for partition in parts:
            if partition.identifier == outgoing_edge_partition_name:
                return partition
        return None

    def reset(self) -> None:
        """
        Reset all the application vertices.
        """
        for vertex in self.vertices:
            vertex.reset()

    def _label_postfix(self) -> str:
        self._unlabelled_vertex_count += 1
        return str(self._unlabelled_vertex_count)
