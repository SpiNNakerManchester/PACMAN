# Copyright (c) 2019 The University of Manchester
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
    Generic, Sequence, Tuple, Type, TypeVar, Union, TYPE_CHECKING)
from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import AbstractEdgePartition
if TYPE_CHECKING:
    from .abstract_vertex import AbstractVertex  # @UnusedImport
    from .abstract_edge import AbstractEdge  # @UnusedImport
#: :meta private:
V = TypeVar("V", bound='AbstractVertex')
#: :meta private:
E = TypeVar("E", bound='AbstractEdge')


class AbstractSingleSourcePartition(
        AbstractEdgePartition, Generic[V, E], metaclass=AbstractBase):
    """
    An edge partition that has a single source vertex.
    """
    __slots__ = (
        # The vertex at the start of all the edges
        "_pre_vertex", )

    def __init__(
            self, pre_vertex: V, identifier: str,
            allowed_edge_types: Union[Type[E], Tuple[Type[E], ...]]):
        """

        :param pre_vertex: The vertex at the start of all the edges
        :param identifier: The identifier of the partition
        :param allowed_edge_types: The types of edges allowed
        """
        super().__init__(
            identifier=identifier, allowed_edge_types=allowed_edge_types)
        self._pre_vertex = pre_vertex

    @overrides(AbstractEdgePartition.add_edge)
    def add_edge(self, edge: E) -> None:
        super().add_edge(edge)
        if edge.pre_vertex != self._pre_vertex:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same pre_vertex")

    @property
    def pre_vertex(self) -> V:
        """
        The vertex at which all edges in this outgoing edge partition start.
        """
        return self._pre_vertex

    @property
    @overrides(AbstractEdgePartition.pre_vertices)
    def pre_vertices(self) -> Sequence[V]:
        return (self.pre_vertex, )
