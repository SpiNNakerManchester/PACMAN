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

from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanInvalidParameterException, PacmanConfigurationException)
from pacman.model.graphs.common import ConstrainedObject

_REPR_TEMPLATE = \
    "OutgoingEdgePartition(identifier={}, edges={}, constraints={}, label={})"


class OutgoingEdgePartition(ConstrainedObject):
    """ A collection of edges which start at a single vertex which have the
        same semantics and so can share a single key.
    """

    __slots__ = [
        # The partition identifier
        "_identifier",
        # The edges in the partition
        "_edges",
        # The vertex at the start of all the edges
        "_pre_vertex",
        # The traffic type of all the edges
        "_traffic_type",
        # The type of edges to accept
        "_allowed_edge_types",
        # The weight of traffic going down this partition
        "_traffic_weight",
        # The label of the graph
        "_label"
    ]

    def __init__(
            self, identifier, allowed_edge_types, constraints=None,
            label=None, traffic_weight=1):
        """
        :param str identifier: The identifier of the partition
        :param allowed_edge_types: The types of edges allowed
        :type allowed_edge_types: type or tuple(type, ...)
        :param list(AbstractConstraint) constraints: Any initial constraints
        :param str label: An optional label of the partition
        :param int traffic_weight:
            The weight of traffic going down this partition
        """
        super(OutgoingEdgePartition, self).__init__(constraints)
        self._label = label
        self._identifier = identifier
        self._edges = OrderedSet()
        self._allowed_edge_types = allowed_edge_types
        self._pre_vertex = None
        self._traffic_type = None
        self._traffic_weight = traffic_weight

    @property
    def label(self):
        """ The label of the outgoing edge partition.

        :rtype: str
        """
        return self._label

    def add_edge(self, edge):
        """ Add an edge to the outgoing edge partition.

        :param AbstractEdge edge: the edge to add
        :raises PacmanInvalidParameterException:
            If the starting vertex of the edge does not match that of the
            edges already in the partition
        """
        # Check for an incompatible edge
        if not isinstance(edge, self._allowed_edge_types):
            raise PacmanInvalidParameterException(
                "edge", edge.__class__,
                "Edges of this graph must be one of the following types:"
                " {}".format(self._allowed_edge_types))

        # Check for an incompatible pre vertex
        if self._pre_vertex is None:
            self._pre_vertex = edge.pre_vertex

        elif edge.pre_vertex != self._pre_vertex:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same"
                "pre_vertex")

        # Check for an incompatible traffic type
        if self._traffic_type is None:
            self._traffic_type = edge.traffic_type
        elif edge.traffic_type != self._traffic_type:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same"
                " traffic_type")

        self._edges.add(edge)

    @property
    def identifier(self):
        """ The identifier of this outgoing edge partition.

        :rtype: str
        """
        return self._identifier

    @property
    def edges(self):
        """ The edges in this outgoing edge partition.

        :rtype: iterable(AbstractEdge)
        """
        return self._edges

    @property
    def n_edges(self):
        """ The number of edges in the outgoing edge partition.

        :rtype: int
        """
        return len(self._edges)

    @property
    def pre_vertex(self):
        """ The vertex at which all edges in this outgoing edge partition\
            start.

        :rtype: AbstractVertex
        """
        return self._pre_vertex

    @property
    def traffic_type(self):
        """ The traffic type of all the edges in this outgoing edge partition.

        :rtype: EdgeTrafficType
        """
        return self._traffic_type

    @property
    def traffic_weight(self):
        """ The weight of the traffic in this outgoing edge partition compared\
            to other partitions.

        :rtype: int
        """
        return self._traffic_weight

    def __repr__(self):
        edges = ""
        for edge in self._edges:
            if edge.label is not None:
                edges += edge.label + ","
            else:
                edges += str(edge) + ","
        return _REPR_TEMPLATE.format(
            self._identifier, edges, self.constraints, self.label)

    def __str__(self):
        return self.__repr__()

    def __contains__(self, edge):
        """ Check if the edge is contained within this partition

        :param AbstractEdge edge: the edge to search for.
        :rtype: bool
        """
        return edge in self._edges
