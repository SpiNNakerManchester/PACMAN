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
from pacman.utilities.utility_calls import (
    allocator_bits_needed, expand_to_bit_array, get_key_ranges)
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
        # Set of app_part indexes used by fixed
        "__ap_keys_blocked_by_fixed",
        # Size of the App vertex / Partition name zone
        "__size_app_part_bits",
        # Size of the machine and atoms part
        "__size_machine_atoms_bits",
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
        self.__size_machine_atoms_bits = -10000
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
        self.__set_fixed_used(routing_info)
        self.__calculate_machine_atoms_zones(routing_info)

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
            app_key_and_mask, part_id, m_vertex, app_key_and_mask.mask,
            m_vertex.index))
        n_bits_atoms = m_vertex.get_n_keys_for_partition(part_id)
        routing_info.add_routing_info(FixedAppVertexRoutingInfo(
            app_key_and_mask, part_id, pre,
            app_key_and_mask.mask, n_bits_atoms,
            len(pre.machine_vertices) - 1))

        atom_mask = app_key_and_mask.mask ^ FULL_MASK

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
                atom_zone = machine_mask ^ FULL_MASK
                machine_zone = machine_mask ^ app_key_and_mask.mask
            elif machine_mask != key_and_mask.mask:
                raise PacmanRouteInfoAllocationException(
                    f"For partition {part_id} {pre} has different "
                    f"machine_fixed_key_and_mask found {hex(machine_mask)} "
                    f"and {hex(key_and_mask.mask)}")


            routing_info.add_routing_info(FixedMachineVertexRoutingInfo(
                key_and_mask, part_id, m_vertex, app_key_and_mask.mask,
                m_vertex.index))
            n_bits_atoms = m_vertex.get_n_keys_for_partition(part_id)
            max_atom_bits = max(max_atom_bits, n_bits_atoms)

        assert machine_mask is not None
        routing_info.add_routing_info(FixedAppVertexRoutingInfo(
            app_key_and_mask, part_id, pre,
            machine_mask, n_bits_atoms,
            len(pre.machine_vertices) - 1))

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

    def __get_atoms_bits_based_on_fixed(
            self, routing_info: RoutingInfo) -> Optional[int]:
        atom_mask = None
        for info in routing_info:
            if atom_mask is None:
                atom_mask = info.atom_mask
            elif atom_mask != info.atom_mask:
                # mutiple masks so ignore fixed
                return None
        if atom_mask is None:
            # no fixed so nothing to set
            return None

        key_zone = self.get_key_zone(atom_mask)
        if key_zone is not None and key_zone[1] == BITS_IN_KEY - 1:
            fixed_atoms_bits = BITS_IN_KEY - key_zone[0]
        else:
            # bad zone
            return None

        if fixed_atoms_bits < self.__max_bits_atoms:
            # too small
            return None

        if self.__size_machine_atoms_bits < (
            self.__max_bits_machine + fixed_atoms_bits):
            # too big
            return None

        return fixed_atoms_bits

    def __calculate_machine_atoms_zones(
            self, routing_info: RoutingInfo) -> None:
        # use all the bits not used by the application partition and overlaps
        self.__size_machine_atoms_bits = (
                BITS_IN_KEY - self.__size_app_part_bits)

        if self.__size_machine_atoms_bits >= (
                self.__max_bits_machine + self.__max_bits_atoms):
            fixed_atoms_bits = self.__get_atoms_bits_based_on_fixed(routing_info)
            if fixed_atoms_bits is not None:
                # use a fixed atoms bits if it fits
                self.__target_atom_bits = fixed_atoms_bits
            else:
                self.__target_atom_bits = self.__max_bits_atoms
            # Add extra bits to the machine zone
            self.__target_machine_bits = (
                    self.__size_machine_atoms_bits - self.__target_atom_bits)
        else:
            # Does not fit so remove bits from the atom zone
            # Likely only a few very big machine vertices will need them
            # they will then flow into the machine zone
            self.__target_atom_bits = (
                    self.__size_machine_atoms_bits - self.__max_bits_machine)
            self.__target_machine_bits = self.__max_bits_machine

        VertexRoutingInfo.set_global_mask(
            self.__mask(self.__target_machine_bits + self.__target_atom_bits),
            self.__mask(self.__target_atom_bits))

    @classmethod
    def get_key_zone(cls, mask: int) -> Optional[Tuple[int, int]]:
        start = None
        end = None
        bits = expand_to_bit_array(mask)
        for i in range(32):
            if bits[i] == 1:
                if start is None:
                    start = i
                if end is not None:
                    return None
            else:
                if start is not None:
                    if end is None:
                        end = i - 1
        if start is not None:
            if end is None:
                end = 31

        if start is None or end is None:
            return None
        else:
            return (start, end)

    @classmethod
    def calc_overlaps(
            cls, key: int, mask: int, ap_zone: int) -> Set[int]:
        """
        Which of the top bits could be used by this key and mask

        :param key: application vertex key
        :param mask: application vertex mask
        :param ap_zone: number of bits in the application partition zone
        :return: Set of top zone values that need to be blocked.
        """
        mac_zone = BITS_IN_KEY - ap_zone
        # Get the key and mask that overlap with the A-P key and mask
        key = key >> mac_zone
        mask = mask >> mac_zone
        # Make the mask all 1s in the MSBs where it has been shifted
        mask |= (((1 << mac_zone) - 1) << ap_zone)

        blocked: Set[int] = set()
        for k, n_keys in get_key_ranges(key, mask):
            blocked.update(range(k, k + n_keys))
        return blocked

    def __set_fixed_used(self, routing_info: RoutingInfo) -> None:
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
        for pre, identifier in self.__vertex_partitions:
            if not routing_info.has_info_from(pre, identifier):
                continue
            key_and_mask = routing_info.get_info_from(pre, identifier)
            blocked = self.calc_overlaps(
                key_and_mask.key, key_and_mask.mask,
                self.__size_app_part_bits)

            if blocked:
                self.__ap_keys_blocked_by_fixed.update(blocked)

            ap_keys_available = 2**self.__size_app_part_bits
            ap_keys_available -= len(self.__ap_keys_blocked_by_fixed)
            if ap_keys_available < len(self.__vertex_partitions):
                #  Oops need more bits
                self.__size_app_part_bits += 1
                if (self.__size_app_part_bits +
                        self.__min_bits_machine_and_atoms > BITS_IN_KEY):
                    raise PacmanRouteInfoAllocationException(
                        "Unable to allocate with fixed keys")
                # clear used
                self.__ap_keys_blocked_by_fixed = set()
                # No need to clear routing_infos overlap as all will repeat
                self.__set_fixed_used(routing_info)

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
                n_bits_machine = self.__size_machine_atoms_bits - n_bits_atoms
                needed = allocator_bits_needed(len(machine_vertices))
                assert (n_bits_machine >= needed)
                overlap = True
            for machine_index, machine_vertex in enumerate(machine_vertices):
                mask = self.__mask(n_bits_atoms)
                key = app_part_index
                key = (key << n_bits_machine) | machine_index
                key = key << n_bits_atoms
                m_info: MachineVertexRoutingInfo
                if overlap:
                    key_and_mask = BaseKeyAndMask(base_key=key, mask=mask)
                    m_info = SpecificMachineVertexRoutingInfo(
                        key_and_mask, identifier, machine_vertex,
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
                    n_bits_atoms=n_bits_atoms,
                    max_machine_index=len(machine_vertices) - 1))
            else:
                routing_info.add_routing_info(GlobalAppVertexRoutingInfo(
                    app_key=key, partition_id=identifier, app_vertex=pre,
                    n_bits_atoms=n_bits_atoms,
                    max_machine_index=len(machine_vertices) - 1))
            app_part_index += 1

        routing_info.add_zones(
            self.__min_bits_machine_and_atoms,
            self.__max_bits_machine, self.__max_bits_atoms,
            self.__size_app_part_bits, self.__size_machine_atoms_bits,
            self.__target_machine_bits, self.__target_atom_bits)

    @staticmethod
    def __mask(bits: int) -> int:
        return FULL_MASK - ((2 ** bits) - 1)
