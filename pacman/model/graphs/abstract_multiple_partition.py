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
from typing import Collection, Dict, Generic, Tuple, Type, TypeVar, Union
from collections import defaultdict
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException, PacmanValueError
from pacman.model.graphs import (
    AbstractVertex, AbstractEdge, AbstractEdgePartition)
#: :meta private:
V = TypeVar("V", bound=AbstractVertex)
#: :meta private:
E = TypeVar("E", bound=AbstractEdge)


class AbstractMultiplePartition(AbstractEdgePartition[E], Generic[V, E]):
    """
    An edge partition that has multiple source vertices.
    """
    __slots__ = (
        # the vertices which send through this partition.
        "_pre_vertices",
        # the destinations of this outgoing partition.
        "_destinations")

    def __init__(
            self, pre_vertices: Collection[V], identifier: str,
            allowed_edge_types: Union[Type[E], Tuple[Type[E], ...]]):
        super().__init__(
            identifier=identifier, allowed_edge_types=allowed_edge_types)
        self._pre_vertices: Dict[V, OrderedSet[E]] = dict()
        self._destinations: Dict[V, OrderedSet[E]] = defaultdict(OrderedSet)

        # hard code dict of lists so that only these are acceptable.
        for pre_vertex in pre_vertices:
            self._pre_vertices[pre_vertex] = OrderedSet()

        # handle clones
        if len(self._pre_vertices.keys()) != len(pre_vertices):
            raise PacmanConfigurationException(
                "There were clones in your list of acceptable pre vertices")

    @overrides(AbstractEdgePartition.add_edge)
    def add_edge(self, edge: E) -> None:
        # safety checks
        if edge.pre_vertex not in self._pre_vertices:
            raise PacmanValueError(
                f"The edge {edge} is not allowed in this outgoing partition")

        super().add_edge(edge)

        # update
        self._pre_vertices[edge.pre_vertex].add(edge)
        self._destinations[edge.post_vertex].add(edge)

    @property
    @overrides(AbstractEdgePartition.pre_vertices)
    def pre_vertices(self) -> Collection[V]:
        return self._pre_vertices.keys()
