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
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.graphs.common import ConstrainedObject

_REPR_TEMPLATE = "{}(identifier={}, edges={}, constraints={}, label={})"


@add_metaclass(AbstractBase)
class AbstractEdgePartition(ConstrainedObject):
    """ A collection of edges which start at a single vertex which have the
        same semantics and so can share a single key.
    """

    __slots__ = [
        # The partition identifier
        "_identifier",
        # The edges in the partition
        "_edges",
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
            label=None, traffic_weight=1, class_name="AbstractEdgePartition"):
        """
        :param str identifier: The identifier of the partition
        :param allowed_edge_types: The types of edges allowed
        :type allowed_edge_types: type or tuple(type, ...)
        :param iterable(AbstractConstraint) constraints:
            Any initial constraints
        :param str label: An optional label of the partition
        :param int traffic_weight:
            The weight of traffic going down this partition
        """
        ConstrainedObject.__init__(self, constraints)
        self._label = label
        self._identifier = identifier
        self._edges = OrderedSet()
        self._allowed_edge_types = allowed_edge_types
        self._traffic_weight = traffic_weight
        self._class_name = class_name

    @property
    def label(self):
        """ The label of the edge partition.

        :rtype: str
        """
        return self._label

    def add_edge(self, edge):
        """ Add an edge to the edge partition.

        :param AbstractEdge edge: the edge to add
        :raises PacmanInvalidParameterException:
            If the edge does not belong in this edge partition
        """
        # Check for an incompatible edge
        if not isinstance(edge, self._allowed_edge_types):
            raise PacmanInvalidParameterException(
                "edge", str(edge.__class__),
                "Edges of this graph must be one of the following types:"
                " {}".format(self._allowed_edge_types))
        self._edges.add(edge)

    @property
    def identifier(self):
        """ The identifier of this edge partition.

        :rtype: str
        """
        return self._identifier

    @property
    def edges(self):
        """ The edges in this edge partition.

        :rtype: iterable(AbstractEdge)
        """
        return self._edges

    @property
    def n_edges(self):
        """ The number of edges in the edge partition.

        :rtype: int
        """
        return len(self._edges)

    @property
    def traffic_weight(self):
        """ The weight of the traffic in this edge partition compared to\
            other partitions.

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
            self._class_name, self._identifier, edges, self.constraints,
            self.label)

    def __str__(self):
        return self.__repr__()

    def __contains__(self, edge):
        """ Check if the edge is contained within this partition

        :param AbstractEdge edge: the edge to search for.
        :rtype: bool
        """
        return edge in self._edges

    @abstractmethod
    def clone_for_graph_move(self):
        """ Make a copy of this edge partition for insertion into another \
            graph.

        :return: The copied edge partition.
        """

    @abstractproperty
    def pre_vertices(self):
        """
        Proivdes the vertice(s) associated with this partition

        Note: Most edge prtitions will be AbstractSingleSourcePartition and
            therefor provide the pre_vertex method.

        :rtype: iter(AbstractVertex)
        """
