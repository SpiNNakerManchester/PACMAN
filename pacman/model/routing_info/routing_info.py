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
from typing import Dict, Iterator, Optional, Iterable, Set, TYPE_CHECKING

from pacman.exceptions import PacmanAlreadyExistsException
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from .app_vertex_routing_info import AppVertexRoutingInfo
from .machine_vertex_routing_info import MachineVertexRoutingInfo

if TYPE_CHECKING:
    from .vertex_routing_info import VertexRoutingInfo
    from pacman.model.graphs import AbstractVertex


class RoutingInfo(object):
    """
    An association of machine vertices to a non-overlapping set of keys
    and masks.
    """
    __slots__ = ("_app_info", "_mac_info")

    def __init__(self) -> None:
        # Partition information indexed by edge pre-vertex and partition ID
        # name
        self._app_info: Dict[ApplicationVertex,
                         Dict[str, AppVertexRoutingInfo]] = defaultdict(dict)
        self._mac_info: Dict[MachineVertex,
            Dict[str, MachineVertexRoutingInfo]] = defaultdict(dict)

    def add_application_info(self, info: AppVertexRoutingInfo) -> None:
        """
        Add a routing information item.

        :param info:
            The routing information item to add
        :raise PacmanAlreadyExistsException:
            If the partition is already in the set of edges
        """
        if (info.vertex in self._app_info and
                info.partition_id in self._app_info[info.vertex]):
            raise PacmanAlreadyExistsException(
                "Routing information", str(info))

        self._app_info[info.vertex][info.partition_id] = info

    def add_machine_info(self, info: MachineVertexRoutingInfo) -> None:
        """
        Add a routing information item.

        :param info:
            The routing information item to add
        :raise PacmanAlreadyExistsException:
            If the partition is already in the set of edges
        """
        if (info.vertex in self._mac_info and
                info.partition_id in self._mac_info[info.vertex]):
            raise PacmanAlreadyExistsException(
                "Routing information", str(info))

        self._mac_info[info.vertex][info.partition_id] = info

    def get_application_info(
            self, vertex: ApplicationVertex,
            partition_id: str) -> AppVertexRoutingInfo:
        """
        :param vertex: The vertex to search for
        :param partition_id:
            The ID of the partition for which to get the routing information
        :returns: Routing information for a given partition_id from a vertex.
        :raise KeyError:
            If the vertex/partition_id combination is not in the routing
            information
        """
        return self._app_info[vertex][partition_id]

    def get_machine_info(
            self, vertex: MachineVertex,
            partition_id: str) -> MachineVertexRoutingInfo:
        """
        :param vertex: The vertex to search for
        :param partition_id:
            The ID of the partition for which to get the routing information
        :returns: Routing information for a given partition_id from a vertex.
        :raise KeyError:
            If the vertex/partition_id combination is not in the routing
            information
        """
        return self._mac_info[vertex][partition_id]

    def get_application_key(
            self, vertex: ApplicationVertex, partition_id: str) -> int:
        """
        Get the first key for the partition starting at a vertex.

        :param vertex: The vertex which the partition starts at
        :param partition_id:
            The ID of the partition for which to get the routing information
        :return: The routing key of the partition
        :raise KeyError:
            If the vertex/partition_id combination is not in the routing
            information
        """
        return self._app_info[vertex][partition_id].key

    def get_machine_key(
            self, vertex: MachineVertex, partition_id: str) -> int:
        """
        Get the first key for the partition starting at a vertex.

        :param vertex: The vertex which the partition starts at
        :param partition_id:
            The ID of the partition for which to get the routing information
        :return: The routing key of the partition
        :raise KeyError:
            If the vertex/partition_id combination is not in the routing
            information
        """
        return self._mac_info[vertex][partition_id].key

    def get_application_partitions(
            self, vertex: ApplicationVertex) -> Iterable[str]:
        """
        Get the outgoing partitions from a vertex.

        :param vertex: The vertex to search for
        :returns: The partition ids for routes from this Vertex
        """
        return self._app_info[vertex].keys()

    def get_machine_partitions(
            self, vertex: MachineVertex) -> Iterable[str]:
        """
        Get the outgoing partitions from a vertex.

        :param vertex: The vertex to search for
        :returns: The partition ids for routes from this Vertex
        """
        return self._mac_info[vertex].keys()

    def has_machine_info(
            self, vertex: MachineVertex, partition_id: str) -> bool:
        """
        Check if there is routing information for a given vertex and ID.

        :param vertex: The vertex to search for
        :param partition_id:
            The ID of the partition for which to get the routing information
        :returns: True if there is a route from this vertex for this partition.
        """
        if vertex in self._mac_info:
            info = self._mac_info[vertex]
            return partition_id in info
        else:
            return False

    def check_machine_info(
            self, vertex: MachineVertex,
            allowed_partition_ids: Set[str]) -> None:
        """
        Check that the partition ids for a vertex are in the allowed set.

        :param vertex: The vertex to search for
        :param allowed_partition_ids: The allowed partition ids
        :raise KeyError: If the vertex has an unknown partition ID
        """
        if vertex in self._mac_info:
            info = self._mac_info[vertex]
            for partition_id in info:
                if partition_id not in allowed_partition_ids:
                    raise KeyError(f"Vertex {vertex} has unknown "
                                   f"partition ID {partition_id}")

    def get_single_machine_info(
            self, vertex: MachineVertex) -> Optional[VertexRoutingInfo]:
        """
        Get routing information for a given vertex.  Fails if the vertex has
        more than one outgoing partition.

        :param vertex: The vertex to search for
        :returns: The only routing from this vertex
        :raise KeyError: If the vertex has more than one outgoing partition
        """
        if vertex in self._mac_info:
            info = self._mac_info[vertex]
            if len(info) != 1:
                raise KeyError(
                    f"Vertex {vertex} has more than one outgoing partition")
            return next(iter(info.values()))
        else:
            return None

    def get_single_machine_key(
            self, vertex: MachineVertex) -> Optional[int]:
        """
        Get the first key for the partition starting at a vertex.  Fails if
        the vertex has more than one outgoing partition.

        :param vertex: The vertex which the partition starts at
        :returns: The key of the only route from this vertex
        :raise KeyError: If the vertex has more than one outgoing partition
        """
        info = self.get_single_machine_info(vertex)
        if info is None:
            return None
        return info.key

    def get_application_infos(self) -> Iterator[AppVertexRoutingInfo]:
        """
        Gets an iterator for the Application routing information.

        :return: a iterator of routing information
        """
        for vertex_info in self._app_info.values():
            for info in vertex_info.values():
                yield info

    def get_machine_infos(self) -> Iterator[MachineVertexRoutingInfo]:
        """
        Gets an iterator for the Machine routing information.

        :return: a iterator of routing information
        """
        for vertex_info in self._mac_info.values():
            for info in vertex_info.values():
                yield info
