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

import logging
from typing import Dict, Iterable, List, Optional, Set, Tuple
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet
from pacman.model.routing_info import (
    RoutingInfo, BaseKeyAndMask,
    FixedAppVertexRoutingInfo, FixedMachineVertexRoutingInfo,
    GlobalAppVertexRoutingInfo, GlobalMachineVertexRoutingInfo,
    MachineVertexRoutingInfo,
    SpecificAppVertexRoutingInfo, SpecificMachineVertexRoutingInfo,
    VertexRoutingInfo)
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from pacman.utilities.utility_calls import allocator_bits_needed
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.utilities.constants import BITS_IN_KEY, FULL_MASK
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    get_app_partitions)
_XAlloc = Iterable[Tuple[ApplicationVertex, str]]
logger = FormatAdapter(logging.getLogger(__name__))


class ZonedRoutingInfoAllocator(object):
    """
    A routing key allocator that uses fixed zones that are the same for
    all vertices.  This will hopefully make the keys more compressible.

    Keys will have the format::

              <--- 32 bits --->
        Key:  | A | P | M | X |
        Mask: |11111111111|   | (i.e. 1s covering A, P and M fields)

    Field ``A``:
        The index of the application vertex.
    Field ``P``:
        The index of the name of outgoing edge partition of the vertex.
    Field ``M``:
        The index of the machine vertex of the application vertex.
    Field ``X``:
        Space for the maximum number of keys required by any outgoing edge
        partition.

    The ``A`` and ``P`` are combined into a single index (``AP``) so that
    applications with multiple partitions use multiple entries
    while ones with only 1 use just one.

    The split between the ``AP`` bit and other parts is always fixed
    This also means that all machine vertices of the same
    application vertex and partition will have a shared key.

    The split between the ``M`` and ``X`` may vary depending on how the
    allocator is called.

    In normal mode the widths of the fields are predetermined and fixed
    such that every key will have every field in the same place in the key,
    and the mask is the same for every vertex.

    The AP part will be as small as possible represent all AP Keys.
    If there are fixed keys using the higher bits this may increase.
    The atoms zone will be large enough for the vertex with the most atoms.
    The remaining bits will be the machine zone.

    In some cases, when there is a mix of
    machine vertices with a large number of atoms (ex. retinas)
    and application vertices with a large number of machine vertices,
    a global split of machine zone and atom zone will not fit.
    In These case the target machine size will be big enough for
    application vertices with a large number of machine vertices
    with the remaining bits being the target atom zone.
    Most vertices will be able to use this split.
    The few vertices with a large number of atoms will then not respect the
    split between machine and atoms zones.
    """

    __slots__ = (
        # A list of vertices and partitions to allocate
        "__vertex_partitions",
        # For each App vertex / Partition name zone keep track of the number of
        # bites required for the mask for each machine vertex
        "__atom_bits_per_app_part",
        # Minimum size needed for the combined machine and atoms zone
        # This is the maximum needed to represent the keys and masks
        # for a single app vertex / partition ID
        "__min_bits_machine_and_atoms",
        # Maximum number of bits to represent the machines for any vertex
        "__max_bits_machine",
        # Maximum number of bits to represent the atoms for any vertex
        "__max_bits_atoms",
        # Needed size of the App vertex / Partition name zone
        "__size_app_part_bits",
        # Set of app_part indexes used by fixed
        "__ap_keys_blocked_by_fixed",
        # The size of the App vertex / Partition name zone
        "__target_app_bits",
        # Size of the machine part for vertex that fit the normal case
        "__target_machine_bits",
        # Size of the atoms part for vertex that fit the normal case
        "__target_atom_bits"
    )

    def __init__(self) -> None:
        # Storage objects to be filled
        self.__vertex_partitions: OrderedSet[
            Tuple[ApplicationVertex, str]] = OrderedSet()
        self.__atom_bits_per_app_part: Dict[
            Tuple[ApplicationVertex, str], int] = dict()
        self.__ap_keys_blocked_by_fixed: Set[int] = set()

        # Start at with values for an empty graph then as needed
        self.__min_bits_machine_and_atoms = 0
        self.__max_bits_machine = 0
        self.__max_bits_atoms = 0

        # temp values to init without optional
        self.__size_app_part_bits = -10000
        self.__target_app_bits = -10000
        self.__target_machine_bits = -10000
        self.__target_atom_bits = -10000

    def allocate(self) -> RoutingInfo:
        """
        Perform routing information allocation.

        :return: The routing information
        :raise PacmanRouteInfoAllocationException:
            If something goes wrong with the allocation
        """
        self.__vertex_partitions = OrderedSet(
            (p.pre_vertex, p.identifier)
            for p in get_app_partitions())

        routing_info = RoutingInfo()
        self.__allocate_fixed(routing_info)
        self.__calculate_zone_sizes_needed(routing_info)
        self.__set_target_zones(routing_info)
        self.__set_fixed_used(routing_info)
        self.__allocate(routing_info)
        return routing_info

    def __check_no_fixed(
            self, pre: ApplicationVertex, identifier: str) -> None:
        for vert in pre.splitter.get_out_going_vertices(identifier):
            key_and_mask = pre.get_machine_fixed_key_and_mask(
                vert, identifier)
            if key_and_mask is not None:
                raise PacmanRouteInfoAllocationException(
                    f"For partition {identifier} {pre} has no fixed key,"
                    f" but {vert} has fixed key {key_and_mask}")

    def __allocate_one_fixed(
            self, pre: ApplicationVertex, part_id: str,
            app_key_and_mask: BaseKeyAndMask, m_vertex: MachineVertex,
            routing_info: RoutingInfo) -> None:
        key_and_mask = pre.get_machine_fixed_key_and_mask(m_vertex, part_id)
        if key_and_mask is not None:
            if key_and_mask != app_key_and_mask:
                raise PacmanRouteInfoAllocationException(
                    f"For partition {part_id} {pre} has fixed key "
                    f"{app_key_and_mask} while only outgoing machine vertex"
                    f" has {key_and_mask}")
        routing_info.add_routing_info(FixedMachineVertexRoutingInfo(
            app_key_and_mask, part_id, m_vertex, app_key_and_mask,
            m_vertex.index))
        routing_info.add_routing_info(FixedAppVertexRoutingInfo(
            app_key_and_mask, part_id, pre,
            app_key_and_mask.mask,
            len(pre.machine_vertices) - 1))

    def __allocate_many_fixed(
            self, pre: ApplicationVertex, part_id: str,
            app_key_and_mask: BaseKeyAndMask, outgoing: List[MachineVertex],
            routing_info: RoutingInfo) -> None:
        max_atom_bits = 0
        machine_mask: Optional[int] = None
        for m_vertex in outgoing:
            key_and_mask = pre.get_machine_fixed_key_and_mask(
                m_vertex, part_id)

            if key_and_mask is None:
                raise PacmanRouteInfoAllocationException(
                    f"For partition {part_id} {pre} has fixed key "
                    f"{app_key_and_mask} "
                    f"while outgoing {m_vertex} has no fixed key")
            if (key_and_mask.key & app_key_and_mask.mask !=
                    app_key_and_mask.key):
                raise PacmanRouteInfoAllocationException(
                    f"For partition {part_id} {pre} has fixed key "
                    f"{app_key_and_mask} "
                    f"while outgoing {m_vertex} has {key_and_mask}"
                    f"these do not align")

            if machine_mask is None:
                machine_mask = key_and_mask.mask
            elif machine_mask != key_and_mask.mask:
                raise PacmanRouteInfoAllocationException(
                    f"For partition {part_id} {pre} has different "
                    f"machine_fixed_key_and_mask found {hex(machine_mask)} "
                    f"and {hex(key_and_mask.mask)}")

            routing_info.add_routing_info(FixedMachineVertexRoutingInfo(
                key_and_mask, part_id, m_vertex, app_key_and_mask,
                m_vertex.index))
            n_bits_atoms = m_vertex.get_n_keys_for_partition(part_id)
            max_atom_bits = max(max_atom_bits, n_bits_atoms)

        assert machine_mask is not None
        routing_info.add_routing_info(FixedAppVertexRoutingInfo(
            app_key_and_mask, part_id, pre,
            machine_mask, len(pre.machine_vertices) - 1))

    def __allocate_fixed(self, routing_info: RoutingInfo) -> None:
        for pre, part_id in self.__vertex_partitions:
            app_key_and_mask = pre.get_fixed_key_and_mask(part_id)
            if app_key_and_mask is None:
                self.__check_no_fixed(pre, part_id)
            else:
                outgoing = list(
                    pre.splitter.get_out_going_vertices(part_id))
                if len(outgoing) == 1:
                    self.__allocate_one_fixed(pre, part_id, app_key_and_mask,
                                              outgoing[0], routing_info)
                elif len(outgoing) > 1:
                    self.__allocate_many_fixed(pre, part_id, app_key_and_mask,
                                               outgoing, routing_info)
                else:
                    raise PacmanRouteInfoAllocationException(
                        "Application {pre} has fixed key {key_and_mask} for "
                        "partition {identifier} but no out_going_vertices")

    def __calculate_zone_sizes_needed(
            self, routing_info: RoutingInfo) -> None:
        """
        Computes the size for the zones.

        """
        self.__size_app_part_bits = allocator_bits_needed(
            len(self.__vertex_partitions))

        progress = ProgressBar(
            len(self.__vertex_partitions), "Calculating zones")
        for pre, identifier in progress.over(self.__vertex_partitions):
            if routing_info.has_info_from(pre, identifier):
                continue
            max_keys = 0
            machine_vertices = pre.splitter.get_out_going_vertices(identifier)
            for m_vtx in machine_vertices:
                max_keys = max(max_keys, m_vtx.get_n_keys_for_partition(
                    identifier))

            if max_keys > 0:
                atom_bits = allocator_bits_needed(max_keys)
                self.__max_bits_atoms = max(self.__max_bits_atoms, atom_bits)
                machine_bits = allocator_bits_needed(len(machine_vertices))
                self.__max_bits_machine = max(
                    self.__max_bits_machine, machine_bits)
                self.__min_bits_machine_and_atoms = max(
                    self.__min_bits_machine_and_atoms,
                    machine_bits + atom_bits)
                self.__atom_bits_per_app_part[pre, identifier] = atom_bits
            else:
                self.__atom_bits_per_app_part[pre, identifier] = 0

        # See if it could fit even before considering fixed
        if (self.__size_app_part_bits + self.__min_bits_machine_and_atoms >
                BITS_IN_KEY):
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator as it needs "
                "{self.__size_app_part_bits} bits for application keys + "
                f"{self.__min_bits_machine_and_atoms} "
                f"for machine and atom bits")

    def __set_target_zones(self, routing_info: RoutingInfo) -> None:
        min_fix_app = self.__size_app_part_bits
        max_fix_app = BITS_IN_KEY - self.__min_bits_machine_and_atoms
        for info in routing_info:
            if isinstance(info, FixedMachineVertexRoutingInfo):
                v_min, v_max = info.get_atom_bits_needed_range()
                if v_min > max_fix_app:
                    raise PacmanRouteInfoAllocationException(
                        f"Vertex {info.vertex} fixed keys requires at least "
                        f"{v_min} app bits but max allowed if {max_fix_app}")
                min_fix_app = max(min_fix_app, v_min)
                if v_max < min_fix_app:
                    raise PacmanRouteInfoAllocationException(
                        f"Vertex {info.vertex} fixed keys requires at most "
                        f"{v_max} app bits but min allowed if {min_fix_app}")
                max_fix_app = min(max_fix_app, v_max)
        if min_fix_app > max_fix_app:
            raise PacmanRouteInfoAllocationException(
                "There is no n_atom_bit which works for for all fixed")

        self.__target_app_bits = (
                BITS_IN_KEY - self.__max_bits_machine - self.__max_bits_atoms)
        if self.__target_app_bits > max_fix_app:
            self.__target_app_bits = max_fix_app
        if self.__target_app_bits < min_fix_app:
            self.__target_app_bits = min_fix_app

        if (self.__target_app_bits + self.__min_bits_machine_and_atoms
                > BITS_IN_KEY):
            raise PacmanRouteInfoAllocationException(
                "Unable to find a number of atom bits that works with fixed")

        self.__target_machine_bits = self.__max_bits_machine
        self.__target_atom_bits = (BITS_IN_KEY - self.__target_app_bits -
                                   self.__target_machine_bits)

        VertexRoutingInfo.set_global_mask(
            self.__mask(self.__target_machine_bits + self.__target_atom_bits),
            self.__mask(self.__target_atom_bits))

    def __set_fixed_used(self, routing_info: RoutingInfo) -> None:
        for pre, identifier in self.__vertex_partitions:
            if not routing_info.has_info_from(pre, identifier):
                continue
            key_and_mask = routing_info.get_info_from(pre, identifier)
            # Get the key and mask that overlap with the A-P key and mask
            blocked = key_and_mask.key >> self.__target_app_bits
            self.__ap_keys_blocked_by_fixed.add(blocked)

    def __allocate(self, routing_info: RoutingInfo) -> None:
        progress = ProgressBar(
            len(self.__vertex_partitions), "Allocating routing keys")
        app_part_index = 0
        for pre, identifier in progress.over(self.__vertex_partitions):
            if routing_info.has_info_from(pre, identifier):
                continue
            # Get a list of machine vertices ordered by pre-slice
            splitter = pre.splitter
            machine_vertices = list(splitter.get_out_going_vertices(
                identifier))
            if not machine_vertices:
                continue

            n_bits_atoms = self.__atom_bits_per_app_part[pre, identifier]
            while app_part_index in self.__ap_keys_blocked_by_fixed:
                app_part_index += 1

            machine_vertices.sort(key=lambda x: x.vertex_slice.lo_atom)
            if n_bits_atoms <= self.__target_atom_bits:
                # OK it fits use global sizes
                n_bits_machine = self.__target_machine_bits
                n_bits_atoms = self.__target_atom_bits
                overlap = False
            else:
                n_bits_machine = allocator_bits_needed(len(machine_vertices))
                assert (self.__target_app_bits + n_bits_machine +
                        n_bits_atoms <= BITS_IN_KEY)
                n_bits_machine = (
                        BITS_IN_KEY - self.__target_app_bits - n_bits_atoms)
                overlap = True
            for machine_index, machine_vertex in enumerate(machine_vertices):
                mask = self.__mask(n_bits_atoms)
                key = app_part_index
                key = (key << n_bits_machine) | machine_index
                key = key << n_bits_atoms
                m_info: MachineVertexRoutingInfo
                if overlap:
                    m_info = SpecificMachineVertexRoutingInfo(
                        key, mask, identifier, machine_vertex,
                        machine_index)
                else:
                    m_info = GlobalMachineVertexRoutingInfo(
                        key, identifier, machine_vertex,
                        machine_index)
                routing_info.add_routing_info(m_info)

            # Add application-level routing information
            key = app_part_index << (n_bits_atoms + n_bits_machine)
            if overlap:
                routing_info.add_routing_info(SpecificAppVertexRoutingInfo(
                    app_key=key, partition_id=identifier, app_vertex=pre,
                    machine_mask=self.__mask(n_bits_atoms),
                    max_machine_index=len(machine_vertices) - 1))
            else:
                routing_info.add_routing_info(GlobalAppVertexRoutingInfo(
                    app_key=key, partition_id=identifier, app_vertex=pre,
                    max_machine_index=len(machine_vertices) - 1))
            app_part_index += 1

        routing_info.add_zones(
            self.__min_bits_machine_and_atoms,
            self.__max_bits_machine, self.__max_bits_atoms,
            self.__size_app_part_bits,
            self.__target_app_bits, self.__target_machine_bits,
            self.__target_atom_bits)

    @staticmethod
    def __mask(bits: int) -> int:
        return FULL_MASK - ((2 ** bits) - 1)
