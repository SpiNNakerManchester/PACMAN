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
from typing import Dict, Iterator, Optional, Iterable, TYPE_CHECKING
from deprecated import deprecated
from pacman.exceptions import PacmanAlreadyExistsException
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
        self._info: Dict[AbstractVertex,
                         Dict[str, VertexRoutingInfo]] = defaultdict(dict)

    def add_routing_info(self, info: VertexRoutingInfo):
        """
        Add a routing information item.

        :param VertexRoutingInfo info:
            The routing information item to add
        :raise PacmanAlreadyExistsException:
            If the partition is already in the set of edges
        """
        if (info.vertex in self._info and
                info.partition_id in self._info[info.vertex]):
            raise PacmanAlreadyExistsException(
                "Routing information", str(info))

        self._info[info.vertex][info.partition_id] = info

    @deprecated(reason="This method is unsafe, since it doesn't determine "
                       "whether the info is missing because there is no "
                       "outgoing edge, or if the outgoing edge is in another "
                       "partition and the name is wrong. "
                       "Use a combination of "
                       "get_safe_routing_info_from_pre_vertex, "
                       "get_partitions_outgoing_from_vertex, "
                       "has_routing_info_from_pre_vertex, "
                       "or get_single_routing_info_from_pre_vertex")
    def get_routing_info_from_pre_vertex(
            self, vertex: AbstractVertex,
            partition_id: str) -> Optional[VertexRoutingInfo]:
        """
        Get routing information for a given partition_id from a vertex.

        :param AbstractVertex vertex: The vertex to search for
        :param str partition_id:
            The ID of the partition for which to get the routing information
        :rtype: VertexRoutingInfo or None
        """
        # TODO: Replace (currently temporarily broken to make sure we don't
        # call it)
        raise NotImplementedError("Deprecated - shouldn't be used")
        # return self._info[vertex].get(partition_id)

    def get_safe_routing_info_from_pre_vertex(
            self, vertex: AbstractVertex,
            partition_id: str) -> VertexRoutingInfo:
        """
        Get routing information for a given partition_id from a vertex.

        :param AbstractVertex vertex: The vertex to search for
        :param str partition_id:
            The ID of the partition for which to get the routing information
        :rtype: VertexRoutingInfo
        :raise KeyError:
            If the vertex/partition_id combination is not in the routing
            information
        """
        return self._info[vertex][partition_id]

    @deprecated(reason="This method is unsafe, since it doesn't determine "
                       "whether the info is missing because there is no "
                       "outgoing edge, or if the outgoing edge is in another "
                       "partition and the name is wrong. "
                       "Use a combination of "
                       "get_safe_first_key_from_pre_vertex, "
                       "get_partitions_outgoing_from_vertex, "
                       "has_routing_info_from_pre_vertex, "
                       "or get_single_first_key_from_pre_vertex")
    def get_first_key_from_pre_vertex(
            self, vertex: AbstractVertex, partition_id: str) -> Optional[int]:
        """
        Get the first key for the partition starting at a vertex.

        :param AbstractVertex vertex: The vertex which the partition starts at
        :param str partition_id:
            The ID of the partition for which to get the routing information
        :return: The routing key of the partition
        :rtype: int or None
        """
        # TODO: Replace (currently temporarily broken to make sure we don't
        # call it)
        raise NotImplementedError("Deprecated - shouldn't be used")

        # if vertex not in self._info:
        #     return None
        # info = self._info[vertex]
        # if partition_id not in info:
        #     return None
        # return info[partition_id].key

    def get_safe_first_key_from_pre_vertex(
            self, vertex: AbstractVertex, partition_id: str) -> int:
        """
        Get the first key for the partition starting at a vertex.

        :param AbstractVertex vertex: The vertex which the partition starts at
        :param str partition_id:
            The ID of the partition for which to get the routing information
        :return: The routing key of the partition
        :rtype: int
        :raise KeyError:
            If the vertex/partition_id combination is not in the routing
            information
        """
        return self._info[vertex][partition_id].key

    def get_partitions_outgoing_from_vertex(
            self, vertex: AbstractVertex) -> Iterable[str]:
        """
        Get the outgoing partitions from a vertex.

        :param AbstractVertex vertex: The vertex to search for
        """
        return self._info[vertex].keys()

    def has_routing_info_from_pre_vertex(
            self, vertex: AbstractVertex, partition_id: str) -> bool:
        """
        Check if there is routing information for a given vertex.

        :param AbstractVertex vertex: The vertex to search for
        :param str partition_id:
            The ID of the partition for which to get the routing information
        :rtype: bool
        """
        if vertex not in self._info:
            return False
        info = self._info[vertex]
        return partition_id in info

    def get_single_routing_info_from_pre_vertex(
            self, vertex: AbstractVertex) -> Optional[VertexRoutingInfo]:
        """
        Get routing information for a given vertex.  Fails if the vertex has
        more than one outgoing partition.

        :param AbstractVertex vertex: The vertex to search for
        :rtype: VertexRoutingInfo or None
        :raise KeyError: If the vertex has more than one outgoing partition
        """
        if vertex not in self._info:
            return None
        info = self._info[vertex]
        if len(info) != 1:
            raise KeyError(
                f"Vertex {vertex} has more than one outgoing partition")
        return next(iter(info.values()))

    def get_single_first_key_from_pre_vertex(
            self, vertex: AbstractVertex) -> Optional[int]:
        """
        Get the first key for the partition starting at a vertex.  Fails if
        the vertex has more than one outgoing partition.

        :param AbstractVertex vertex: The vertex which the partition starts at
        :rtype: int or None
        :raise KeyError: If the vertex has more than one outgoing partition
        """
        info = self.get_single_routing_info_from_pre_vertex(vertex)
        if info is None:
            return None
        return info.key

    def __iter__(self) -> Iterator[VertexRoutingInfo]:
        """
        Gets an iterator for the routing information.

        :return: a iterator of routing information
        """
        for vertex_info in self._info.values():
            for info in vertex_info.values():
                yield info
