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

import logging
import math
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_info import (
    RoutingInfo, MachineVertexRoutingInfo, BaseKeyAndMask,
    AppVertexRoutingInfo)
from pacman.utilities.utility_calls import get_key_ranges
from pacman.exceptions import PacmanRouteInfoAllocationException,\
    PacmanInvalidParameterException
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
        "__app_graph",
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
        # Map of (partition identifier, machine_vertex) to fixed_key_and_mask
        "__fixed_partitions",
        # Set of app_part indexes used by fixed
        "__fixed_used"
    ]
    # pylint: disable=attribute-defined-outside-init

    def __call__(self, app_graph, flexible):
        """
        :param ApplicationGraph app_graph:
            The graph to allocate the routing info for
        :param bool flexible: Determines if flexible can be use.
            If False, global settings will be attempted
        :return: The routing information
        :rtype: RoutingInfo
        :raise PacmanRouteInfoAllocationException:
            If something goes wrong with the allocation
        """
        self.__app_graph = app_graph

        self.__n_bits_atoms_and_mac = 0
        self.__n_bits_machine = 0
        self.__n_bits_atoms = 0
        self.__atom_bits_per_app_part = dict()
        self.__flexible = flexible
        self.__fixed_keys = list()
        self.__fixed_partitions = dict()
        self.__fixed_used = set()

        self.__find_fixed()
        self.__calculate_zones()
        self.__check_zones()
        return self.__allocate()

    def __check_constraint_supported(self, constraint):
        if not isinstance(constraint, AbstractKeyAllocatorConstraint):
            return
        if isinstance(constraint, ContiguousKeyRangeContraint):
            return
        raise PacmanInvalidParameterException(
            "constraint", constraint, "Unsupported key allocation constraint")

    def __find_fixed(self):
        """
        Looks for FixedKeyAmdMask Constraints and keeps track of these.

        See :py:meth:`__add_fixed`
        """
        partitions = self.__app_graph.outgoing_edge_partitions
        for part in partitions:
            pre = part.pre_vertex
            # Try the application vertex
            for constraint in pre.constraints:
                if isinstance(constraint, FixedKeyAndMaskConstraint):
                    if constraint.applies_to_partition(part.identifier):
                        for vert in pre.splitter.get_out_going_vertices(
                                part.identifier):
                            self.__add_fixed(part.identifier, vert, constraint)
                        self.__add_fixed(
                            part.identifier, part.pre_vertex, constraint)
                else:
                    self.__check_constraint_supported(constraint)

            # Try the machine vertices
            for vert in pre.splitter.get_out_going_vertices(
                    part.identifier):
                for constraint in vert.constraints:
                    if isinstance(constraint, FixedKeyAndMaskConstraint):
                        if constraint.applies_to_partition(part.identifier):
                            self.__add_fixed(part.identifier, vert, constraint)
                    else:
                        self.__check_constraint_supported(constraint)

    def __add_fixed(self, part_id, vertex, constraint):
        """
        Precomputes and caches FixedKeyAndMask for easier use later

        Saves a map of partition to the constraint records these in a dict by
        Partition so they can be found easier in future passes.

        Saves a list of the keys and their n_keys so these zones can be blocked

        :param str part_id: The identifier of the partition
        :param MachineVertex vertex: The machine vertex this applies to
        :param FixedKeyAndMaskConstraint constraint:
        """
        if (part_id, vertex) in self.__fixed_partitions:
            raise PacmanInvalidParameterException(
                "constraint", constraint,
                "Multiple FixedKeyConstraints apply to the same vertex")
        self.__fixed_partitions[part_id, vertex] = constraint.keys_and_masks
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
        progress = ProgressBar(
            self.__app_graph.n_outgoing_edge_partitions, "Calculating zones")

        # search for size of regions
        partitions = self.__app_graph.outgoing_edge_partitions
        for partition in progress.over(partitions):
            splitter = partition.pre_vertex.splitter
            machine_vertices = splitter.get_out_going_vertices(
                partition.identifier)
            if not machine_vertices:
                continue
            max_keys = 0
            for machine_vertex in machine_vertices:
                if ((partition.identifier, machine_vertex) not in
                        self.__fixed_partitions):
                    n_keys = machine_vertex.get_n_keys_for_partition(
                        partition.identifier)
                    max_keys = max(max_keys, n_keys)

            if max_keys > 0:
                atom_bits = self.__bits_needed(max_keys)
                self.__n_bits_atoms = max(self.__n_bits_atoms, atom_bits)
                machine_bits = self.__bits_needed(len(machine_vertices))
                self.__n_bits_machine = max(
                    self.__n_bits_machine, machine_bits)
                self.__n_bits_atoms_and_mac = max(
                    self.__n_bits_atoms_and_mac, machine_bits + atom_bits)
                self.__atom_bits_per_app_part[partition] = atom_bits
            else:
                self.__atom_bits_per_app_part[partition] = 0

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
        progress = ProgressBar(
            self.__app_graph.n_outgoing_edge_partitions,
            "Allocating routing keys")
        routing_infos = RoutingInfo()
        partitions = self.__app_graph.outgoing_edge_partitions
        app_part_index = 0
        for partition in progress.over(partitions):
            while app_part_index in self.__fixed_used:
                app_part_index += 1
            # Get a list of machine vertices ordered by pre-slice
            splitter = partition.pre_vertex.splitter
            machine_vertices = list(splitter.get_out_going_vertices(
                partition.identifier))
            if not machine_vertices:
                continue
            machine_vertices.sort(key=lambda x: x.vertex_slice.lo_atom)
            n_bits_atoms = self.__atom_bits_per_app_part[partition]
            if self.__flexible:
                n_bits_machine = min(
                    self.__n_bits_atoms_and_mac - n_bits_atoms,
                    self.__n_bits_machine)
            else:
                if n_bits_atoms <= self.__n_bits_atoms:
                    # Ok it fits use global sizes
                    n_bits_atoms = self.__n_bits_atoms
                    n_bits_machine = self.__n_bits_machine
                else:
                    # Nope need more bits! Use the flexible approach here
                    n_bits_machine = self.__n_bits_atoms_and_mac - n_bits_atoms

            for machine_index, machine_vertex in enumerate(machine_vertices):
                key = (partition.identifier, machine_vertex)
                if key in self.__fixed_partitions:
                    # Ignore zone calculations and just use fixed
                    keys_and_masks = self.__fixed_partitions[key]
                else:
                    mask = self.__mask(n_bits_atoms)
                    key = app_part_index
                    key = (key << n_bits_machine) | machine_index
                    key = key << n_bits_atoms
                    keys_and_masks = [BaseKeyAndMask(base_key=key, mask=mask)]
                routing_infos.add_routing_info(MachineVertexRoutingInfo(
                    keys_and_masks, partition.identifier, machine_vertex,
                    machine_index))

            # Add application-level routing information
            key = (partition.identifier, partition.pre_vertex)
            if key in self.__fixed_partitions:
                keys_and_masks = self.__fixed_partitions[key]
            else:
                key = app_part_index << (n_bits_atoms + n_bits_machine)
                mask = self.__mask(n_bits_atoms + n_bits_machine)
                keys_and_masks = [BaseKeyAndMask(key, mask)]
            routing_infos.add_routing_info(AppVertexRoutingInfo(
                keys_and_masks, partition.identifier, partition.pre_vertex,
                self.__mask(n_bits_atoms), n_bits_atoms,
                len(machine_vertices) - 1))
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
        if size == 0:
            return 0
        return int(math.ceil(math.log(size, 2)))


def flexible_allocate(app_graph):
    """
    Allocated with fixed bits for the Application/Partition index but
    with the size of the atom and machine bit changing

    :param ApplicationGraph app_graph:
        The graph to allocate the routing info for
    :rtype: tuple(RoutingInfo,
        dict((ApplicationVertex, str), BaseKeyAndMask))
    :raise PacmanRouteInfoAllocationException:
    """
    # check that this algorithm supports the constraints put onto the
    # partitions

    allocator = ZonedRoutingInfoAllocator()

    return allocator(app_graph, True)


def global_allocate(app_graph):
    """
    :param ApplicationGraph app_graph:
        The graph to allocate the routing info for
    :rtype: tuple(RoutingInfo,
        dict((ApplicationVertex, str), BaseKeyAndMask))
    :raise PacmanRouteInfoAllocationException:
    """
    # check that this algorithm supports the constraints put onto the
    # partitions

    allocator = ZonedRoutingInfoAllocator()

    return allocator(app_graph, False)
