# Copyright (c) 2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
import logging
import math
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_info import (
    RoutingInfo, PartitionRoutingInfo, BaseKeyAndMask)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints, get_key_ranges)
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, ContiguousKeyRangeContraint,
    FixedKeyAndMaskConstraint)
from pacman.utilities.constants import BITS_IN_KEY, FULL_MASK

logger = FormatAdapter(logging.getLogger(__name__))


class ZonedRoutingInfoAllocator(object):
    """ A routing key allocator that uses fixed zones that are the same for\
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

        In "global" mode the widths of the fields are predetermined and fixed
        such that every key will have every field in the same place in the key,
        and the mask is the same for every vertex.
        The global approach is particularly sensitive to the one large and
        many small vertices limit.

        In "flexible" mode the size of the ``M`` and ``X`` will change for each
        application/partition. Every vertex for a application/partition pair
        but different pairs may have different masks.
        This should result in less gaps between the machine vertexes.
        Even in none Flexible mode if the sizes are too big to keep ``M`` and
        ``X`` the same size they will be allowed to change for those vertexes
        will a very high number of atoms.
    """

    __slots__ = [
        # Passed in parameters
        "__machine_graph",
        "__n_keys_map",
        # For each App vertex / Partition name zone keep track of the number of
        # bites required for the mask for each machine vertex
        "__atom_bits_per_app_part",
        # maximum number of bites to represent the keys and masks
        # for a single app vertex / partition name zone
        "__n_bits_atoms_and_mac",
        # Maximum number pf bit to represent the machine assuming global
        "__n_bits_machine",
        # Maximum number pf bit to represent the machine assuming global
        "__n_bits_atoms",
        # Flag to say operating in flexible mode
        "__flexible",
        # List of (key, n_keys) needed for fixed
        "__fixed_keys",
        # Map of partition to fixed_+key_and_mask
        "__fixed_partitions",
        # Set of app_part indexes used by fixed
        "__fixed_used"
    ]
    # pylint: disable=attribute-defined-outside-init

    def __call__(self, machine_graph, n_keys_map, flexible):
        """
        :param MachineGraph machine_graph:
            The machine graph to allocate the routing info for
        :param AbstractMachinePartitionNKeysMap n_keys_map:
            A map between the edges and the number of keys required by the
            edges
        :param bool flexible: Determines if flexible can be use.
            If False, global settings will be attempted
        :return: The routing information
        :rtype: RoutingInfo
        :raise PacmanRouteInfoAllocationException:
            If something goes wrong with the allocation
        """
        # check that this algorithm supports the constraints put onto the
        # partitions
        self.__machine_graph = machine_graph
        self.__n_keys_map = n_keys_map
        self.__n_bits_atoms_and_mac = 0
        self.__n_bits_machine = 0
        self.__n_bits_atoms = 0
        self.__atom_bits_per_app_part = dict()
        self.__flexible = flexible
        self.__fixed_keys = list()
        self.__fixed_partitions = dict()
        self.__fixed_used = set()

        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[
                ContiguousKeyRangeContraint, FixedKeyAndMaskConstraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        self.__find_fixed()
        self.__calculate_zones()
        self.__check_zones()
        return self.__allocate()

    def __find_fixed(self):
        """
        Looks for FixedKeyAmdMask Constraints and keeps track of these.

        See :py:meth:`__add_fixed`
        """
        multicast_partitions = self.__machine_graph.multicast_partitions
        for app_id in multicast_partitions:
            # multicast_partitions is a map of app_id to paritition_vertices
            # paritition_vertices is a map of partition(name) to set(vertex)
            by_app = multicast_partitions[app_id]
            for partition_name, paritition_vertices in by_app.items():
                for mac_vertex in paritition_vertices:
                    partition = self.__machine_graph.\
                        get_outgoing_edge_partition_starting_at_vertex(
                            mac_vertex, partition_name)
                    for constraint in partition.constraints:
                        if isinstance(constraint, FixedKeyAndMaskConstraint):
                            self.__add_fixed(partition, constraint)

    def __add_fixed(self, partition, constraint):
        """
        Precomputes and caches FixedKeyAndMask for easier use later

        Saves a map of partition to the constraint records these in a dict by
        Partition so they can be found easier in future passes.

        Saves a list of the keys and their n_keys so these zones can be blocked

        :param pacman.model.graphs.OutgoingEdgePartition partition:
        :param FixedKeyAndMaskConstraint constraint:
        """
        self.__fixed_partitions[partition] = constraint.keys_and_masks
        for key_and_mask in constraint.keys_and_masks:
            # Go through the mask sets and save keys and n_keys
            for key, n_keys in get_key_ranges(
                    key_and_mask.key, key_and_mask.mask):
                self.__fixed_keys.append((key, n_keys))

    def __calculate_zones(self):
        """
        Computes the size for the zones.

        .. note::
            Even Partitions with FixedKeysAndMasks a included here.
            This does waste a little space.
            However makes this and the allocate code slightly simpler
            It also keeps the ``AP`` zone working for these partitions too

        :raises PacmanRouteInfoAllocationException:
        """
        multicast_partitions = self.__machine_graph.multicast_partitions
        progress = ProgressBar(
            len(multicast_partitions), "Calculating zones")

        # search for size of regions
        for app_id in progress.over(multicast_partitions):
            by_app = multicast_partitions[app_id]
            for partition_name, paritition_vertices in by_app.items():
                max_keys = 0
                for mac_vertex in paritition_vertices:
                    partition = self.__machine_graph.\
                        get_outgoing_edge_partition_starting_at_vertex(
                            mac_vertex, partition_name)
                    if partition not in self.__fixed_partitions:
                        n_keys = self.__n_keys_map.n_keys_for_partition(
                            partition)
                        max_keys = max(max_keys, n_keys)
                if max_keys > 0:
                    atom_bits = self.__bits_needed(max_keys)
                    self.__n_bits_atoms = max(self.__n_bits_atoms, atom_bits)
                    machine_bits = self.__bits_needed(len(paritition_vertices))
                    self.__n_bits_machine = max(
                        self.__n_bits_machine, machine_bits)
                    self.__n_bits_atoms_and_mac = max(
                        self.__n_bits_atoms_and_mac, machine_bits + atom_bits)
                    self.__atom_bits_per_app_part[
                        (app_id, partition_name)] = atom_bits
                else:
                    self.__atom_bits_per_app_part[(app_id, partition_name)] = 0

    def __check_zones(self):
        # See if it could fit even before considerding fixed
        app_part_bits = self.__bits_needed(len(self.__atom_bits_per_app_part))
        if app_part_bits + self.__n_bits_atoms_and_mac > BITS_IN_KEY:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bits".format(
                    app_part_bits, self.__n_bits_atoms_and_mac))

        # Reserve fixed and check it still works
        self.__set_fixed_used()
        app_part_bits = self.__bits_needed(
            len(self.__atom_bits_per_app_part) + len(self.__fixed_used))
        if app_part_bits + self.__n_bits_atoms_and_mac > BITS_IN_KEY:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bits".format(
                    app_part_bits, self.__n_bits_atoms_and_mac))

        if not self.__flexible:
            # If using global see if the fixed M and X zones are too big
            if app_part_bits + self.__n_bits_machine + self.__n_bits_atoms > \
                    BITS_IN_KEY:
                # We know from above test that all will fit if flexible
                # Reduce the suggested size of n_bits_atoms
                self.__n_bits_atoms = \
                    BITS_IN_KEY - app_part_bits - self.__n_bits_machine
                self.__n_bits_atoms_and_mac = BITS_IN_KEY - app_part_bits
                logger.warning(
                    "The ZonedRoutingInfoAllocator could not use the global "
                    "approach for all vertexes.")
            else:
                # Set the size of atoms and machine for biggest of each
                self.__n_bits_atoms_and_mac = \
                    self.__n_bits_machine + self.__n_bits_atoms

    def __set_fixed_used(self):
        """
        Block the use of ``AP`` indexes that would clash with fixed keys
        """
        self.__fixed_used = set()
        bucket_size = 2 ** self.__n_bits_atoms_and_mac
        for (key, n_keys) in self.__fixed_keys:
            start = key // bucket_size
            end = (key + n_keys) // bucket_size
            for i in range(start, end + 1):
                self.__fixed_used.add(i)

    def __allocate(self):
        multicast_partitions = self.__machine_graph.multicast_partitions
        progress = ProgressBar(
            len(multicast_partitions), "Allocating routing keys")
        routing_infos = RoutingInfo()
        app_part_index = 0
        for app_id in progress.over(multicast_partitions):
            while app_part_index in self.__fixed_used:
                app_part_index += 1
            for partition_name, paritition_vertices in \
                    multicast_partitions[app_id].items():
                # convert set to a list and sort by slice
                machine_vertices = list(paritition_vertices)
                machine_vertices.sort(key=lambda x: x.vertex_slice.lo_atom)
                n_bits_atoms = self.__atom_bits_per_app_part[
                    (app_id, partition_name)]
                if self.__flexible:
                    n_bits_machine = self.__n_bits_atoms_and_mac - n_bits_atoms
                else:
                    if n_bits_atoms <= self.__n_bits_atoms:
                        # Ok it fits use global sizes
                        n_bits_atoms = self.__n_bits_atoms
                        n_bits_machine = self.__n_bits_machine
                    else:
                        # Nope need more bits! Use the flexible approach here
                        n_bits_machine = \
                            self.__n_bits_atoms_and_mac - n_bits_atoms

                for machine_index, vertex in enumerate(machine_vertices):
                    partition = self.__machine_graph.\
                        get_outgoing_edge_partition_starting_at_vertex(
                            vertex, partition_name)
                    if partition in self.__fixed_partitions:
                        # Ignore zone calculations and just use fixed
                        keys_and_masks = self.__fixed_partitions[partition]
                    else:
                        mask = self.__mask(n_bits_atoms)
                        key = app_part_index
                        key = (key << n_bits_machine) | machine_index
                        key = key << n_bits_atoms
                        keys_and_masks = [BaseKeyAndMask(
                            base_key=key, mask=mask)]
                    routing_infos.add_partition_info(
                        PartitionRoutingInfo(keys_and_masks, partition))
                app_part_index += 1

        return routing_infos

    @staticmethod
    def __mask(bits):
        """
        :param int bits:
        :rtype int:
        """
        return FULL_MASK - ((2 ** bits) - 1)

    @staticmethod
    def __bits_needed(size):
        """
        :param int size:
        :rtype: int
        """
        return int(math.ceil(math.log(size, 2)))


def flexible_allocate(machine_graph, n_keys_map):
    """
    Allocated with fixed bits for the Application/Partition index but
    with the size of the atom and machine bit changing

    :param MachineGraph machine_graph:
        The machine graph to allocate the routing info for
    :param AbstractMachinePartitionNKeysMap n_keys_map:
        A map between the edges and the number of keys required by the
        edges
    :rtype: tuple(RoutingInfo,
        dict((ApplicationVertex, str), BaseKeyAndMask))
    :raise PacmanRouteInfoAllocationException:
    """
    # check that this algorithm supports the constraints put onto the
    # partitions

    allocator = ZonedRoutingInfoAllocator()

    return allocator(machine_graph, n_keys_map, True)


def global_allocate(machine_graph, n_keys_map):
    """
    :param MachineGraph machine_graph:
        The machine graph to allocate the routing info for
    :param AbstractMachinePartitionNKeysMap n_keys_map:
        A map between the edges and the number of keys required by the
        edges
    :rtype: tuple(RoutingInfo,
        dict((ApplicationVertex, str), BaseKeyAndMask))
    :raise PacmanRouteInfoAllocationException:
    """
    # check that this algorithm supports the constraints put onto the
    # partitions

    allocator = ZonedRoutingInfoAllocator()

    return allocator(machine_graph, n_keys_map, False)
