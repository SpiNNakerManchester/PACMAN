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
from typing import (
    Dict, Iterator, Optional, Iterable, Set, TYPE_CHECKING)
from pacman.exceptions import PacmanAlreadyExistsException
if TYPE_CHECKING:
    from .vertex_routing_info import VertexRoutingInfo
    from pacman.model.graphs import AbstractVertex


class RoutingInfo(object):
    """
    An association of machine vertices to a non-overlapping set of keys
    and masks.
    """
    __slots__ = ("_info", "_has_fixed_keys",
                 "_has_global_masks", "_has_shiftable_masks",
                 "_max_bits_machine", "_max_bits_atoms",
                 "_min_bits_machine_and_atoms",
                 "_size_app_part_bits", "_size_mac_atoms_bits",
                 "_target_machine_bits", "_target_atom_bits")

    def __init__(self) -> None:
        # Partition information indexed by edge pre-vertex and partition ID
        # name
        self._info: Dict[AbstractVertex,
                         Dict[str, VertexRoutingInfo]] = defaultdict(dict)
        # Temp values to avoid Optionals
        self._min_bits_machine_and_atoms = -1000
        self._max_bits_machine = -1000
        self._max_bits_atoms = -1000
        self._size_app_part_bits = -1000
        self._size_mac_atoms_bits = -1000
        self._target_machine_bits = -1000
        self._target_atom_bits = -1000
        self._has_fixed_keys = False
        self._has_shiftable_masks = True
        self._has_global_masks = True

    def add_routing_info(self, info: VertexRoutingInfo) -> None:
        """
        Add a routing information item.

        :param info:
            The routing information item to add
        :raise PacmanAlreadyExistsException:
            If the partition is already in the set of edges
        """
        if (info.vertex in self._info and
                info.partition_id in self._info[info.vertex]):
            raise PacmanAlreadyExistsException(
                "Routing information", str(info))

        self._info[info.vertex][info.partition_id] = info
        if info.has_fixed_keys:
            self._has_fixed_keys = True
        if not info.has_shiftable_masks:
            self._has_shiftable_masks = False
        if not info.has_global_masks:
            self._has_global_masks = False

    def get_info_from(
            self, vertex: AbstractVertex,
            partition_id: str) -> VertexRoutingInfo:
        """
        :param vertex: The vertex to search for
        :param partition_id:
            The ID of the partition for which to get the routing information
        :returns: Routing information for a given partition_id from a vertex.
        :raise KeyError:
            If the vertex/partition_id combination is not in the routing
            information
        """
        return self._info[vertex][partition_id]

    def get_key_from(
            self, vertex: AbstractVertex, partition_id: str) -> int:
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
        return self._info[vertex][partition_id].key

    def get_partitions_from(
            self, vertex: AbstractVertex) -> Iterable[str]:
        """
        Get the outgoing partitions from a vertex.

        :param vertex: The vertex to search for
        :returns: The partition ids for routes from this Vertex
        """
        return self._info[vertex].keys()

    def has_info_from(
            self, vertex: AbstractVertex, partition_id: str) -> bool:
        """
        Check if there is routing information for a given vertex and ID.

        :param vertex: The vertex to search for
        :param partition_id:
            The ID of the partition for which to get the routing information
        :returns: True if there is a route from this vertex for this partition.
        """
        if vertex not in self._info:
            return False
        info = self._info[vertex]
        return partition_id in info

    def check_info_from(
            self, vertex: AbstractVertex,
            allowed_partition_ids: Set[str]) -> None:
        """
        Check that the partition ids for a vertex are in the allowed set.

        :param vertex: The vertex to search for
        :param allowed_partition_ids: The allowed partition ids
        :raise KeyError: If the vertex has an unknown partition ID
        """
        if vertex not in self._info:
            return
        info = self._info[vertex]
        for partition_id in info:
            if partition_id not in allowed_partition_ids:
                raise KeyError(
                    f"Vertex {vertex} has unknown partition ID {partition_id}")

    def get_single_info_from(
            self, vertex: AbstractVertex) -> Optional[VertexRoutingInfo]:
        """
        Get routing information for a given vertex.  Fails if the vertex has
        more than one outgoing partition.

        :param vertex: The vertex to search for
        :returns: The only routing from this vertex
        :raise KeyError: If the vertex has more than one outgoing partition
        """
        if vertex not in self._info:
            return None
        info = self._info[vertex]
        if len(info) != 1:
            raise KeyError(
                f"Vertex {vertex} has more than one outgoing partition")
        return next(iter(info.values()))

    def get_single_key_from(
            self, vertex: AbstractVertex) -> Optional[int]:
        """
        Get the first key for the partition starting at a vertex.  Fails if
        the vertex has more than one outgoing partition.

        :param vertex: The vertex which the partition starts at
        :returns: The key of the only route from this vertex
        :raise KeyError: If the vertex has more than one outgoing partition
        """
        info = self.get_single_info_from(vertex)
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

    def __len__(self) -> int:
        return sum(len(v) for v in self._info.values())

    def add_zones(
            self, min_bits_machine_and_atoms: int, max_bits_machine: int,
            max_bits_atoms: int, size_app_part_bits: int,
            size_mac_atoms_bits: int, target_machine_bits: int,
            target_atom_bits: int) -> None:
        """
        Copy in the zone info from the allocator

        :param min_bits_machine_and_atoms:
        :param max_bits_machine:
        :param max_bits_atoms:
        :param size_app_part_bits:
        :param size_mac_atoms_bits:
        :param target_machine_bits:
        :param target_atom_bits:
        :return:
        """
        self._min_bits_machine_and_atoms = min_bits_machine_and_atoms
        self._max_bits_machine = max_bits_machine
        self._max_bits_atoms = max_bits_atoms
        self._size_app_part_bits = size_app_part_bits
        self._size_mac_atoms_bits = size_mac_atoms_bits
        self._target_machine_bits = target_machine_bits
        self._target_atom_bits = target_atom_bits

    @property
    def min_bits_machine_and_atoms(self) -> int:
        """
       Minimum size needed for the combined machine and atoms zone

       This is the maximum needed to represent the keys and masks
       for a single app vertex / partition ID
        """
        return self._min_bits_machine_and_atoms

    @property
    def max_bits_machine(self) -> int:
        """
        Maximum number of bits to represent the machines for any vertex
        """
        return self._max_bits_machine

    @property
    def max_bits_atoms(self) -> int:
        """
        Maximum number of bits to represent the atoms for any vertex
        """
        return self._max_bits_atoms

    @property
    def size_app_part_bits(self) -> int:
        """
        Size of the App vertex / Partition name zone
        """
        return self._size_app_part_bits

    @property
    def size_mac_atoms_bits(self) -> int:
        """
        Size of the machine and atoms part

        This will always be 32 - size_app_part_bits
        """
        return self._size_mac_atoms_bits

    @property
    def target_machine_bits(self) -> int:
        """
        Size of the machine part for vertex.

        It will be at least max_bits_machine,
        but will include any extra bits if not all bits are needed.

        It may however not be respected on vertices with a very large number
        of atoms per core.
        """
        return self._target_machine_bits

    @property
    def target_atom_bits(self) -> int:
        """
         Size of the atoms part for vertex that fit the normal case

         Ideally this will be the max_bits_atoms but may be smaller
         if there is a mix of application vertices with many outgoing
         and others with atoms per core.
         """
        return self._target_atom_bits

    @property
    def has_fixed_keys(self) -> bool:
        """
        True if ANY vertex requires fixed kleys and masks

        Fixed keys may be shiftable and even global
        """
        return self._has_fixed_keys

    @property
    def has_shiftable_masks(self) -> bool:
        """
        True if all masks in ALL infos are shiftable.

        Only fixed key vertices should have none shiftable masks
        """
        return self._has_shiftable_masks

    @property
    def has_global_masks(self) -> bool:
        """
        True if all masks in ALL infos are global ones defined by the zones

        Global masks are always shiftable.
        """
        return self._has_global_masks
