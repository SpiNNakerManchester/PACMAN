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
from typing import (
    Collection, Generic, Tuple, Type, TypeVar, Union, TYPE_CHECKING)
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import (
    PacmanInvalidParameterException, PacmanAlreadyExistsException)
if TYPE_CHECKING:
    from .abstract_edge import AbstractEdge  # @UnusedImport
    from .abstract_vertex import AbstractVertex
#: :meta private:
E = TypeVar("E", bound='AbstractEdge')


class AbstractEdgePartition(Generic[E], metaclass=AbstractBase):
    """
    A collection of edges which start at a single vertex which have the
    same semantics and so can share a single key or block of SDRAM
    (depending on edge type).
    """

    __slots__ = (
        # The partition identifier
        "_identifier",
        # The edges in the partition
        "_edges",
        # The type of edges to accept
        "_allowed_edge_types")

    def __init__(self, identifier: str,
                 allowed_edge_types: Union[Type[E], Tuple[Type[E], ...]]):
        """
        :param identifier: The identifier of the partition
        :param allowed_edge_types: The types of edges allowed
        """
        self._identifier = identifier
        self._allowed_edge_types = allowed_edge_types
        self._edges: OrderedSet[E] = OrderedSet()

    def add_edge(self, edge: E) -> None:
        """
        Add an edge to the edge partition.

        :param edge: the edge to add
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
    def identifier(self) -> str:
        """
        The identifier of this edge partition.
        """
        return self._identifier

    @property
    def edges(self) -> Collection[E]:
        """
        The edges in this edge partition.

        .. note::
            The order in which the edges are added is preserved for when they
            are requested later. If not, please talk to the software team.
        """
        return self._edges

    @property
    def n_edges(self) -> int:
        """
        The number of edges in the edge partition.
        """
        return len(self._edges)

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(identifier={self.identifier}"
                f", n_edges={self.n_edges})")

    def __str__(self) -> str:
        return self.__repr__()

    def __contains__(self, edge: AbstractEdge) -> bool:
        """
        Check if the edge is contained within this partition.

        :param edge: the edge to search for.
        """
        return edge in self._edges

    @property
    @abstractmethod
    def pre_vertices(self) -> Collection[AbstractVertex]:
        """
        The vertices associated with this partition.

        .. note::
            Most edge partitions will be
            :py:class:`AbstractSingleSourcePartition`
            and therefore provide the ``pre_vertex`` method.

        """
        raise NotImplementedError
