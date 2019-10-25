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
from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.overrides import overrides
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanInvalidParameterException, PacmanConfigurationException)
from pacman.model.graphs import AbstractEdgePartition
from pacman.model.graphs.common import ConstrainedObject

_REPR_TEMPLATE = "{}(identifier={}, edges={}, constraints={}, label={})"


@add_metaclass(AbstractBase)
class AbstractBasicEdgePartition(
        ConstrainedObject, AbstractEdgePartition):
    """ A collection of edges which start at a single vertex which have the
        same semantics and so can share a single key.
    """

    __slots__ = [
        # The partition identifier
        "_identifier",
        # The edges in the partition
        "_edges",
        # The traffic type of all the edges
        "_traffic_type",
        # The type of edges to accept
        "_allowed_edge_types",
        # The weight of traffic going down this partition
        "_traffic_weight",
        # The label of the graph
        "_label",
        # class name
        "_class_name"
    ]

    def __init__(
            self, identifier, allowed_edge_types, constraints=None,
            label=None, traffic_weight=1,
            class_name="AbstractBasicEdgePartition"):
        """
        :param identifier: The identifier of the partition
        :param allowed_edge_types: The types of edges allowed
        :param constraints: Any initial constraints
        :param label: An optional label of the partition
        :param traffic_weight: The weight of traffic going down this partition
        """
        ConstrainedObject.__init__(self, constraints)
        self._label = label
        self._identifier = identifier
        self._edges = OrderedSet()
        self._allowed_edge_types = allowed_edge_types
        self._traffic_type = None
        self._traffic_weight = traffic_weight
        self._class_name = class_name

    @property
    @overrides(AbstractEdgePartition.label)
    def label(self):
        return self._label

    @overrides(AbstractEdgePartition.add_edge)
    def add_edge(self, edge):
        # Check for an incompatible edge
        if not isinstance(edge, self._allowed_edge_types):
            raise PacmanInvalidParameterException(
                "edge", str(edge.__class__),
                "Edges of this graph must be one of the following types:"
                " {}".format(self._allowed_edge_types))

        # Check for an incompatible traffic type
        if self._traffic_type is None:
            self._traffic_type = edge.traffic_type
        elif edge.traffic_type != self._traffic_type:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same"
                " traffic_type")

        self._edges.add(edge)

    @property
    @overrides(AbstractEdgePartition.identifier)
    def identifier(self):
        return self._identifier

    @property
    @overrides(AbstractEdgePartition.edges)
    def edges(self):
        return self._edges

    @property
    @overrides(AbstractEdgePartition.n_edges)
    def n_edges(self):
        return len(self._edges)

    @property
    @overrides(AbstractEdgePartition.traffic_type)
    def traffic_type(self):
        return self._traffic_type

    @property
    @overrides(AbstractEdgePartition.traffic_weight)
    def traffic_weight(self):
        return self._traffic_weight

    def __repr__(self):
        edges = ""
        for edge in self._edges:
            if edge.label is not None:
                edges += edge.label + ","
            else:
                edges += str(edge) + ","
        return _REPR_TEMPLATE.format(
            self._class_name, self._identifier, edges, self.constraints,
            self.label)

    def __str__(self):
        return self.__repr__()

    @overrides(AbstractEdgePartition.__contains__)
    def __contains__(self, edge):
        """ Check if the edge is contained within this partition

        :param edge: the edge to search for.
        :return: boolean of true of false otherwise
        """
        return edge in self._edges
