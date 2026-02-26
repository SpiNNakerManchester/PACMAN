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
from typing import Dict, Iterable, Set, Tuple, cast
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet
from pacman.model.routing_info import (
    RoutingInfo, MachineVertexRoutingInfo, BaseKeyAndMask,
    AppVertexRoutingInfo)
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from pacman.utilities.utility_calls import (
    get_key_ranges, allocator_bits_needed)
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
        # maximum number of bites to represent the keys and masks
        # for a single app vertex / partition name zone
        # This is therefor the minimum size for the combine zone
        "__min_bits_atoms_and_mac",
        # Maximum number of bits to represent the machine for any vertex
        "__max_bits_machine",
        # Maximum number of bits to represent the atoms for any vertex
        "__max_bits_atoms",
        # Map of (partition identifier, machine_vertex) to fixed_key_and_mask
        "__fixed_partitions",
        # Set of app_part indexes used by fixed
        "__fixed_used",
        # Size of the App vertex / Partition name zone
        "__size_app_part_bits",
        # Size of the machine and atoms part
        "__size_mac_atoms_bits",
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
        self.__fixed_partitions: Dict[
            Tuple[str, AbstractVertex], BaseKeyAndMask] = dict()
        self.__fixed_used: Set[int] = set()

        # Start at with values for an empty graph then as needed
        self.__min_bits_atoms_and_mac = 0
        self.__max_bits_machine = 0
        self.__max_bits_atoms = 0

        # temp values to init without optional
        self.__size_app_part_bits = -10000
        self.__size_mac_atoms_bits = -10000
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

        routing_infos = RoutingInfo()
        self.__find_fixed()
        self.__calculate_zones()
        self.__check_zones(routing_infos)

        self.__allocate(routing_infos)
        return routing_infos

    def __find_fixed(self) -> None:
        """
        Looks for FixedKeyAmdMask Constraints and keeps track of these.

        See :py:meth:`__add_fixed`
        """
        for pre, identifier in self.__vertex_partitions:
            app_key_and_mask = pre.get_fixed_key_and_mask(identifier)
            is_fixed_m_key = False
            is_unfixed_m_key = False
            outgoing = list(pre.splitter.get_out_going_vertices(identifier))
            for vert in outgoing:
                key_and_mask = pre.get_machine_fixed_key_and_mask(
                    vert, identifier)
                if key_and_mask is not None:
                    if is_unfixed_m_key:
                        raise PacmanRouteInfoAllocationException(
                            "A fixed key has been found for one machine vertex"
                            f" but not for all machine vertices of {pre}")
                    is_fixed_m_key = True
                    if app_key_and_mask is None:
                        raise PacmanRouteInfoAllocationException(
                            "No application fixed key found, but machine "
                            f"fixed key {key_and_mask} found on vertex {pre}, "
                            f"machine vertex {vert}, partition {identifier}")
                    if (key_and_mask.key & app_key_and_mask.mask !=
                            app_key_and_mask.key):
                        raise PacmanRouteInfoAllocationException(
                            f"For application vertex {pre}, the fixed key for "
                            f"machine vertex {vert} of {key_and_mask} does "
                            f"not align with the app key {app_key_and_mask}")
                    self.__fixed_partitions[identifier, vert] = key_and_mask
                else:
                    if is_fixed_m_key:
                        raise PacmanRouteInfoAllocationException(
                            "A fixed key has been found for one machine vertex"
                            f" but not for all machine vertices of {pre}")
                    is_unfixed_m_key = True

            if app_key_and_mask is not None:
                if not is_fixed_m_key:
                    if len(outgoing) > 1:
                        raise PacmanRouteInfoAllocationException(
                            f"On {pre} only a fixed app key has been provided,"
                            " but there is more than one machine vertex.")
                    # pylint:disable=undefined-loop-variable
                    self.__fixed_partitions[
                        identifier, vert] = app_key_and_mask
                self.__fixed_partitions[identifier, pre] = app_key_and_mask

    def __calculate_zones(self):
        """
        Computes the size for the zones.

        """
        self.__size_app_part_bits =  allocator_bits_needed(
            len(self.__vertex_partitions))

        progress = ProgressBar(
            len(self.__vertex_partitions), "Calculating zones")
        for pre, identifier in progress.over(self.__vertex_partitions):
            max_keys = 0
            machine_vertices = pre.splitter.get_out_going_vertices(identifier)
            for m_vtx in machine_vertices:
                max_keys = max(max_keys, m_vtx.get_n_keys_for_partition(
                    identifier))

            if max_keys > 0:
                atom_bits = allocator_bits_needed(max_keys)
                if (identifier, pre) not in self.__fixed_partitions:
                    self.__max_bits_atoms = max(self.__max_bits_atoms, atom_bits)
                    machine_bits = allocator_bits_needed(len(machine_vertices))
                    self.__max_bits_machine = max(
                        self.__max_bits_machine, machine_bits)
                    self.__min_bits_atoms_and_mac = max(
                        self.__min_bits_atoms_and_mac, machine_bits + atom_bits)
                self.__atom_bits_per_app_part[pre, identifier] = atom_bits
            else:
                self.__atom_bits_per_app_part[pre, identifier] = 0

    def __check_zones(self, routing_infos: RoutingInfo) -> None:
        # See if it could fit even before considering fixed
        if (self.__size_app_part_bits + self.__min_bits_atoms_and_mac >
                BITS_IN_KEY):
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                f"different allocator as it needs {self.__app_part_bits} + "
                f"{self.__min_bits_atoms_and_mac} bits")

        # Reserve fixed and check it still works
        self.__set_fixed_used(routing_infos)

        self.__size_mac_atoms_bits = (
                BITS_IN_KEY - self.__size_app_part_bits)
        if self.__size_mac_atoms_bits >= (self.__max_bits_machine + self.__max_bits_atoms):
            self.__target_atom_bits = self.__max_bits_atoms
            self.__target_machine_bits = (
                    self.__size_mac_atoms_bits - self.__max_bits_atoms)
        else:
            self.__target_atom_bits = (
                    self.__size_mac_atoms_bits - self.__max_bits_machine)
            self.__target_machine_bits = self.__max_bits_machine

    def __set_fixed_used(self, routing_infos: RoutingInfo) -> None:
        """
        Block the use of ``AP`` indexes that would clash with fixed keys
        """
        # The idea below is to generate all combinations of the A-P keys that
        # overlap with one of the fixed keys and masks. Example:
        # | A | P | M | X |
        # |1111000|0000000| (1)
        # |1111111|1100000| (2)
        # |1010110|0000000| (3)
        # Case (1): the mask of the key is all within A and P, so it will
        #           generate 16 AP values which need to be blocked out
        # Case (2): the mask of the key goes beyond A and P, so it will
        #           generate only one AP value that can't be used
        # Case (3): the mask that overlaps AP is complex; all possible
        #           combinations of AP within the 0s of the mask will be
        #           blocked from use
        for (partition_id, vertex), key_and_mask in self.__fixed_partitions.items():
            # Get the key and mask that overlap with the A-P key and mask
            key = key_and_mask.key >> self.__min_bits_atoms_and_mac
            mask = key_and_mask.mask >> self.__min_bits_atoms_and_mac

            # Make the mask all 1s in the MSBs where it has been shifted
            mask |= (((1 << self.__min_bits_atoms_and_mac) - 1) <<
                     self.__size_app_part_bits)

            # Generate all possible combinations of keys for the remaining
            # mask
            overlap = False
            for k, n_keys in get_key_ranges(key, mask):
                self.__fixed_used.update(range(k, k + n_keys))
                overlap = True

            if overlap:
                routing_infos.add_overlap(partition_id, vertex)
                # for one app one outgoing the outgoing may not have fixed keys
                if isinstance(vertex, ApplicationVertex):
                    outgoing = list(
                        vertex.splitter.get_out_going_vertices(partition_id))
                    if len(outgoing) == 0:
                        routing_infos.add_overlap(partition_id, outgoing)

            ap_keys_available = 2**self.__size_app_part_bits
            ap_keys_available -= len(self.__fixed_used)
            if ap_keys_available < len(self.__vertex_partitions):
                #  Oops need more bits
                self.__size_app_part_bits += 1
                if (self.__size_app_part_bits + self.__min_bits_atoms_and_mac >
                        BITS_IN_KEY):
                    raise PacmanRouteInfoAllocationException(
                        "Unable to allocate with fixed keys")
                # clear used
                self.__fixed_used = set()
                # No need to clear routing_infos overlap as all will repeat
                self.__set_fixed_used(routing_infos)

    def __allocate_all_fixed(self,  routing_infos: RoutingInfo) -> None:
        progress = ProgressBar(
            len(self.__fixed_partitions), "Allocating routing keys")
        for (part_id, vertex), key_and_mask in progress.over(
                self.__fixed_partitions.items()):
            if isinstance(vertex, ApplicationVertex):
                n_bits_atoms = self.__atom_bits_per_app_part[vertex, part_id]
                routing_infos.add_routing_info(AppVertexRoutingInfo(
                    key_and_mask, part_id, vertex,
                    self.__mask(n_bits_atoms), n_bits_atoms,
                    len(vertex.machine_vertices)-1))
            elif isinstance(vertex, MachineVertex):
                routing_infos.add_routing_info(MachineVertexRoutingInfo(
                    key_and_mask, part_id, vertex, vertex.index))

    def __allocate(self, routing_infos: RoutingInfo) -> None:
        progress = ProgressBar(
            len(self.__vertex_partitions), "Allocating routing keys")
        app_part_index = 0
        for pre, identifier in progress.over(self.__vertex_partitions):
            # Get a list of machine vertices ordered by pre-slice
            splitter = pre.splitter
            machine_vertices = list(splitter.get_out_going_vertices(
                identifier))
            if not machine_vertices:
                continue

            n_bits_atoms = self.__atom_bits_per_app_part[pre, identifier]

            id_mv =(identifier, machine_vertices[0])
            fixed = id_mv in self.__fixed_partitions

            if fixed:
                for machine_index, machine_vertex in enumerate(
                        machine_vertices):
                    id_mv = (identifier, machine_vertex)
                    key_and_mask = self.__fixed_partitions[id_mv]
                    routing_infos.add_routing_info(MachineVertexRoutingInfo(
                        key_and_mask, identifier, machine_vertex,
                        machine_index))

            else:
                while app_part_index in self.__fixed_used:
                        app_part_index += 1

                machine_vertices.sort(key=lambda x: x.vertex_slice.lo_atom)
                if n_bits_atoms <= self.__target_atom_bits:
                    # OK it fits use global sizes
                    n_bits_machine = self.__target_machine_bits
                    n_bits_atoms = self.__target_atom_bits
                else:
                    n_bits_machine = self.__size_mac_atoms_bits - n_bits_atoms
                    needed = allocator_bits_needed(len(machine_vertices))
                    assert (n_bits_machine >= needed)

                for machine_index, machine_vertex in enumerate(machine_vertices):
                    mask = self.__mask(n_bits_atoms)
                    key = app_part_index
                    key = (key << n_bits_machine) | machine_index
                    key = key << n_bits_atoms
                    key_and_mask = BaseKeyAndMask(base_key=key, mask=mask)
                    routing_infos.add_routing_info(MachineVertexRoutingInfo(
                        key_and_mask, identifier, machine_vertex,
                        machine_index))

            # Add application-level routing information
            id_pr = (identifier, pre)
            if id_pr in self.__fixed_partitions:
                key_and_mask = self.__fixed_partitions[id_pr]
            else:
                key = app_part_index << (n_bits_atoms + n_bits_machine)
                mask = self.__mask(n_bits_atoms + n_bits_machine)
                key_and_mask = BaseKeyAndMask(key, mask)
            routing_infos.add_routing_info(AppVertexRoutingInfo(
                key_and_mask, identifier, pre,
                self.__mask(n_bits_atoms), n_bits_atoms,
                len(machine_vertices) - 1))
            app_part_index += 1

        return routing_infos

    @staticmethod
    def __mask(bits: int) -> int:
        return FULL_MASK - ((2 ** bits) - 1)
