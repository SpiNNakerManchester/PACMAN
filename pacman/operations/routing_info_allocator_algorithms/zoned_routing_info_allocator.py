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
import math
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_info import (
    RoutingInfo, PartitionRoutingInfo, BaseKeyAndMask)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints)
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, ContiguousKeyRangeContraint)
from pacman.utilities.constants import BITS_IN_KEY, FULL_MASK


class ZonedRoutingInfoAllocator(object):
    """ A routing key allocator that uses fixed zones that are the same for
        all vertices.  This will hopefully make the keys more compressible.

        Keys will have the format:
              <--- 32 bits --->
        Key:  | AP | M | X |
        Mask: |11111111111|   | (i.e. 1s covering AP and M fields)

        A: the index of the application vertex
        P: the index of the name of outgoing edge partition of the vertex.
        M: the index of the machine vertex of the application vertex
        X: space for the maximum number of keys required by any outgoing edge
           partition

        The A and P are combined into a single index so that applications with
        multiple partitions use multiple entries
        while ones with only 1 use just one.

        The split between the AP bit and other parts is always fixed
        This also means that all machine vertices of the same
        application vertex and partition will have a shared key.

        The split between the M and X may vary depending on how the allocator
        is called.

        In "global" mode he widths of the fields are pre determined and fixed
        such that every key will have every field in the same place in the key,
        and the mask is the same for every vertex.
         The global approach is pariticularly sensitive to the one large and
         many small verticies limit.

        In "flexible" mode the size of the M and X will change for each
        application/partition. Ever vertext for a application/partition pair
        but different pairs may have different masks.
        This should result in less gaps between the machine vertexes.


    .. note::
        No special constraints (except ContiguousKeyRangeContraint) are
        supported.  This will only work if the numbers above add up to 32-bits
        (an error will result if not).  A single large vertex (like a retina)
        and lots of small vertices (like a large neural network)
        will thus not likely work here.

    :param MachineGraph machine_graph:
        The machine graph to allocate the routing info for
    :param AbstractMachinePartitionNKeysMap n_keys_map:
        A map between the edges and the number of keys required by the
        edges
    :return: The routing information
    :rtype: tuple(RoutingInfo, dict((ApplicationVertex, str), BaseKeyAndMask))
    :raise PacmanRouteInfoAllocationException:
        If something goes wrong with the allocation
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
        "__flexible"
    ]
    # pylint: disable=attribute-defined-outside-init

    def __init__(self, machine_graph, n_keys_map, flexible):
        """
        :param MachineGraph machine_graph:
            The machine graph to allocate the routing info for
        :param AbstractMachinePartitionNKeysMap n_keys_map:
            A map between the edges and the number of keys required by the
            edges
        :param bool flexible: Dettermines if flexible can be use.
            If False global settings will be attempted
        :raise PacmanRouteInfoAllocationException:
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

        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.multicast_partitions.keys(),
            supported_constraints=[ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

    def _calculate_zones(self):
        """
        :raises PacmanRouteInfoAllocationException:
        """
        by_app_and_partition_name = \
            self.__machine_graph.multicast_partitions
        progress = ProgressBar(
            len(by_app_and_partition_name), "Calculating zones")

        # search for size of regions
        for app_vertex in progress.over(by_app_and_partition_name):
            by_app = by_app_and_partition_name[app_vertex]
            for partition_name, by_partition_name in by_app.items():
                max_keys = 0
                for mac_vertex in by_partition_name:
                    partition = self.__machine_graph.\
                        get_outgoing_edge_partition_starting_at_vertex(
                            mac_vertex, partition_name)
                    n_keys = self.__n_keys_map.n_keys_for_partition(partition)
                    max_keys = max(max_keys, n_keys)
                if max_keys > 0:
                    atom_bits = self.__bits_needed(max_keys)
                    self.__n_bits_atoms = max(self.__n_bits_atoms, atom_bits)
                    machine_bits = self.__bits_needed(len(by_partition_name))
                    self.__n_bits_machine = max(
                        self.__n_bits_machine, machine_bits)
                    self.__n_bits_atoms_and_mac = max(
                        self.__n_bits_atoms_and_mac, machine_bits + atom_bits)
                    self.__atom_bits_per_app_part[
                        (app_vertex, partition_name)] = atom_bits

        app_part_bits = self.__bits_needed(len(self.__atom_bits_per_app_part))

        if app_part_bits + self.__n_bits_atoms_and_mac > BITS_IN_KEY:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bits".format(
                    app_part_bits, self.__n_bits_atoms_and_mac))

        if not self.__flexible:
            if app_part_bits + self.__n_bits_machine + self.__n_bits_atoms > \
                    BITS_IN_KEY:
                # We know from above test that all will fit if flexible
                # Reduce the suggested size of n_bits_atoms
                self.__n_bits_atoms = \
                    BITS_IN_KEY - app_part_bits - self.__n_bits_machine
                self.__n_bits_atoms_and_mac = BITS_IN_KEY - app_part_bits
            else:
                # Set the size of atoms and machine for biggest of each
                self.__n_bits_atoms_and_mac = \
                    self.__n_bits_machine + self.__n_bits_atoms

    def _simple_allocate(self):
        """
        :param dict((ApplicationVertex, str),int) mask_bits_map:
            map of app vertex,name to max keys for that vertex
        :return: tuple of routing infos and map from app vertex and key masks
        :rtype: tuple(RoutingInfo,
            dict((ApplicationVertex, str), BaseKeyAndMask))
        """
        by_app_and_partition_name = \
            self.__machine_graph.multicast_partitions
        progress = ProgressBar(
            len(by_app_and_partition_name), "Allocating routing keys")
        routing_infos = RoutingInfo()
        by_app_vertex = dict()
        app_mask = self.__mask(self.__n_bits_atoms_and_mac)
        app_part_index = 0
        for app_vertex in progress.over(by_app_and_partition_name):
            for partition_name, by_partition_name in \
                    by_app_and_partition_name[app_vertex].items():
                machine_vertices = list(by_partition_name)
                machine_vertices.sort(key=lambda x: x.vertex_slice.lo_atom)
                if self.__flexible:
                    n_bits_atoms = self.__atom_bits_per_app_part[
                        (app_vertex, partition_name)]
                    n_bits_machine = self.__n_bits_atoms_and_mac - n_bits_atoms
                else:
                    n_bits_atoms = self.__atom_bits_per_app_part[
                        (app_vertex, partition_name)]
                    print(self.__atom_bits_per_app_part)
                    if n_bits_atoms < self.__n_bits_atoms:
                        # Ok it fits use global sizes
                        n_bits_atoms = self.__n_bits_atoms
                        n_bits_machine = self.__n_bits_machine
                    else:
                        # Nope need more use that so adjust n_bits_machine down
                        n_bits_machine = \
                            self.__n_bits_atoms_and_mac - n_bits_atoms

                for machine_index, vertex in enumerate(machine_vertices):
                    mask = self.__mask(n_bits_atoms)
                    key = app_part_index
                    key = (key << n_bits_machine) | machine_index
                    key = key << n_bits_atoms
                    key_and_mask = BaseKeyAndMask(base_key=key, mask=mask)
                    partition = self.__machine_graph.\
                        get_outgoing_edge_partition_starting_at_vertex(
                            vertex, partition_name)
                    routing_infos.add_partition_info(
                        PartitionRoutingInfo([key_and_mask], partition))

                app_key = app_part_index << self.__n_bits_atoms_and_mac
                by_app_vertex[(app_vertex, partition_name)] = BaseKeyAndMask(
                    base_key=app_key, mask=app_mask)
                app_part_index += 1

        return routing_infos, by_app_vertex

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
    Allocated with fixed bits for the Application/Paritition index but
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

    allocator = ZonedRoutingInfoAllocator(machine_graph, n_keys_map, True)

    allocator._calculate_zones()

    return allocator._simple_allocate()


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

    allocator = ZonedRoutingInfoAllocator(machine_graph, n_keys_map, False)

    allocator._calculate_zones()

    return allocator._simple_allocate()
