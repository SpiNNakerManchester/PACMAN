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
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanInvalidParameterException, PacmanAlreadyExistsException)


class AbstractEdgePartition(object, metaclass=AbstractBase):
    """
    A collection of edges which start at a single vertex which have the
    same semantics and so can share a single key or block of SDRAM
    (depending on edge type).
    """

    __slots__ = [
        # The partition identifier
        "_identifier",
        # The edges in the partition
        "_edges",
        # The type of edges to accept
        "_allowed_edge_types"
    ]

    def __init__(
            self, identifier, allowed_edge_types):
        """
        :param str identifier: The identifier of the partition
        :param allowed_edge_types: The types of edges allowed
        :type allowed_edge_types: type or tuple(type, ...)
        :param str label: An optional label of the partition
        """
        self._identifier = identifier
        self._allowed_edge_types = allowed_edge_types
        self._edges = OrderedSet()

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
                f" {self._allowed_edge_types}")
        if edge in self._edges:
            raise PacmanAlreadyExistsException("Edge", edge)
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

        .. note::
            The order in which the edges are added is preserved for when they
            are requested later. If not, please talk to the software team.

        :rtype: iterable(AbstractEdge)
        """
        return self._edges

    @property
    def n_edges(self):
        """ The number of edges in the edge partition.

        :rtype: int
        """
        return len(self._edges)

    def __repr__(self):
        return (f"{self.__class__.__name__}(identifier={self.identifier}"
                f", n_edges={self.n_edges})")

    def __str__(self):
        return self.__repr__()

    def __contains__(self, edge):
        """ Check if the edge is contained within this partition.

        :param AbstractEdge edge: the edge to search for.
        :rtype: bool
        """
        return edge in self._edges

    @abstractproperty
    def pre_vertices(self):
        """
        Provides the vertices associated with this partition.

        .. note::
            Most edge partitions will be
            :py:class:`AbstractSingleSourcePartition`
            and therefore provide the ``pre_vertex`` method.

        :rtype: iter(AbstractVertex)
        """
