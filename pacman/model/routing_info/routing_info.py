# Copyright (c) 2014 The University of Manchester
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
from typing import Dict, Iterator, Optional, TYPE_CHECKING
from pacman.exceptions import PacmanAlreadyExistsException, PacmanException
from pacman.model.graphs.abstract_supports_multiple_partitions import (
    AbstractSupportsMultiplePartitions)
if TYPE_CHECKING:
    from .vertex_routing_info import VertexRoutingInfo
    from pacman.model.graphs import AbstractVertex


class RoutingInfo(object):
    """
    An association of machine vertices to a non-overlapping set of keys
    and masks.
    """
    __slots__ = ("_info", )

    def __init__(self) -> None:
        # Partition information indexed by edge pre-vertex and partition ID
        # name
        self._info: Dict[AbstractVertex[Dict[str], VertexRoutingInfo]] = (
            defaultdict(dict))

    def add_routing_info(self, info: VertexRoutingInfo):
        """
        Add a routing information item.

        :param VertexRoutingInfo info:
            The routing information item to add
        :raise PacmanAlreadyExistsException:
            If the partition is already in the set of edges
        """
        vertex = info.vertex
        partition_id = info.partition_id
        if vertex in self._info:
            if partition_id in self._info[vertex]:
                raise PacmanAlreadyExistsException(
                    "Routing information", str(info))
        if isinstance(vertex, AbstractSupportsMultiplePartitions):
            if info.partition_id not in vertex.partition_ids_supported():
                raise PacmanException(
                    f"Unsupported partition {info.partition_id} "
                    f"expected {vertex.partition_ids_supported()}")
            self._info[vertex][partition_id] = info
        else:
            if vertex in self._info:
                raise PacmanException(
                    f"{vertex=} can not support multiple partitions")
            self._info[vertex][partition_id] = info

    def get_routing_info_from_pre_vertex(
            self, vertex: AbstractVertex,
            partition_id: str) -> Optional[VertexRoutingInfo]:
        """
        Get routing information for a given partition_id from a vertex.

        :param AbstractVertex vertex: The vertex to search for
        :param str partition_id:
            The ID of the partition for which to get the routing information
        :rtype: VertexRoutingInfo
        """
        if vertex in self._info:
            return self._info[vertex].get(partition_id)
        else:
            return None

    def get_routing_info_from_pre_single(
            self, vertex: AbstractVertex) -> Optional[VertexRoutingInfo]:
        """
        Get routing information for a given partition_id from a vertex.

        :param AbstractVertex vertex: The vertex to search for
        :param str partition_id:
            The ID of the partition for which to get the routing information
        :rtype: VertexRoutingInfo
        """
        if vertex in self._info:
            vertex_info = self._info[vertex]
            if len(vertex_info) == 1:
                return next(iter(vertex_info.values()))
            else:
                raise PacmanException(f"{vertex=} has multiple keys")
        else:
            return None

    def get_first_key_from_pre_vertex(
            self, vertex: AbstractVertex, partition_id: str) -> Optional[int]:
        """
        Get the first key for the partition starting at a vertex.

        :param AbstractVertex vertex: The vertex which the partition starts at
        :param str partition_id:
            The ID of the partition for which to get the routing information
        :return: The routing key of the partition
        :rtype: int
        """
        if vertex in self._info:
            vertex_info = self._info[vertex]
            if partition_id in vertex_info:
                return vertex_info[partition_id].key
            if isinstance(vertex, AbstractSupportsMultiplePartitions):
                if partition_id in vertex_info.partition_ids_supported():
                    return None
                raise PacmanException(
                    f"{vertex} does not support {partition_id}")
            else:
                return None

    def get_first_key_from_single_pre(
            self, vertex: AbstractVertex) -> Optional[int]:
        """
        Get the first key for the partition starting at a vertex.

        :param AbstractVertex vertex: The vertex which the partition starts at
        :return: The routing key of the partition
        :rtype: int
        """
        if vertex in self._info:
            vertex_info = self._info[vertex]
            if len(vertex_info) == 1:
                return next(iter(vertex_info.values())).key
            elif len(vertex_info) == 0:
                return None
            else:
                raise PacmanException(f"{vertex=} has multiple keys")

    def __iter__(self) -> Iterator[VertexRoutingInfo]:
        """
        Gets an iterator for the routing information.

        :return: a iterator of routing information
        """
        for vertex_info in self._info.values():
            yield from vertex_info.values()
