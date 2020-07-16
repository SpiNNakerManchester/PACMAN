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
from pacman.model.graphs.common import EdgeTrafficType
from pacman.utilities.constants import BITS_IN_KEY, FULL_MASK


def _bits_needed(size):
    """ Work out the bits needed to represent a number of values

    :param int size: The number of values to be represented
    """
    return int(math.ceil(math.log(size, 2)))


class GlobalZonedRoutingInfoAllocator(object):
    """ A routing key allocator that uses fixed zones that are the same for
        all vertices.  This will hopefully make the keys more compressible.

        Keys will have the format:
             <--- 32 bits --->
        Key: | A | M | P | X |
        Mask:|11111111111|   | (i.e. 1s covering A, M and P fields)

        A: the index of the application vertex
        M: the index of the machine vertex of the application vertex
        P: the index of the outgoing edge partition of the machine vertex
        X: space for the maximum number of keys required by any outgoing edge
           partition

        Note that this also means that all machine vertices of the same
        application vertex will have a shared key.

        The widths of the fields are determined such that every key will have
        every field in the same place in the key, and the mask is the same
        for every vertex.

    .. note::
        No special constraints are supported.  This will only work if the
        numbers above add up to 32-bits (an error will result if not).  A
        single large vertex (like a retina) and lots of small vertices (like
        a large neural network) will thus not likely work here.
    """

    __slots__ = [
        # Passed in parameters
        "__application_graph",
        "__machine_graph",
        "__n_keys_map",
        "__n_bits_partition",
        "__n_bits_machine",
        "__n_bits_atoms",
        "__n_bits_total"
    ]
    # pylint: disable=attribute-defined-outside-init

    def __call__(self, application_graph, machine_graph, n_keys_map):
        """
        :param application graph:\
            The application graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param machine_graph:\
            The machine graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param n_keys_map:\
            A map between the edges and the number of keys required by the\
            edges
        :type n_keys_map:\
            :py:class:`pacman.model.routing_info.AbstractMachinePartitionNKeysMap`
        :return: The routing information
        :rtype:\
            :py:class:`pacman.model.routing_info.PartitionRoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: \
            If something goes wrong with the allocation
        """
        self.__application_graph = application_graph
        self.__machine_graph = machine_graph
        self.__n_keys_map = n_keys_map

        # check that this algorithm supports the constraints put onto the
        # partitions
        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # Do the allocation
        self._calculate_zones()
        return self._simple_allocate()

    def _calculate_zones(self):
        """ Work out the number of bits needed to allow the mask to be the\
            same for all routing table entries

        :raises PacmanRouteInfoAllocationException:
        """
        progress = ProgressBar(
            self.__application_graph.n_vertices, "Calculating zones")

        # Over all application vertices work out:
        # - the maximum number of multicast keys sent down any outgoing edge
        #   partition
        # - the maximum number of machine vertices for any application vertex
        # - the maximum number of outgoing edge partitions that send multicast
        #   keys for any machine vertex
        # - the number of application vertices which send multicast packets
        max_partitions = 0
        max_machine_vertices = 0
        max_keys = 0
        n_app_vertices = 0
        for app_vertex in progress.over(self.__application_graph.vertices):

            # For this application vertex work out:
            # - the max number of keys sent by an outgoing edge partition of
            #   any machine vertex
            # - the maximum number of outgoing edge partitions of any machine
            #   vertex
            # - The total number of machine vertices that send multicast
            local_max_keys = 0
            app_max_partitions = 0
            n_machine_vertices = 0
            for vertex in app_vertex.machine_vertices:
                partitions = self.__machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)

                # Count only outgoing edge partitions that send multicast keys
                # for this machine vertex
                n_partitions = 0
                for partition in partitions:
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        n_keys = self.__n_keys_map.n_keys_for_partition(
                            partition)
                        local_max_keys = max(local_max_keys, n_keys)
                        n_partitions += 1
                if n_partitions > 0:
                    app_max_partitions = max(app_max_partitions, n_partitions)
                    n_machine_vertices += 1

            # Only count the number for this machine vertex if one of the
            # outgoing edge partitions sends multicast
            if local_max_keys > 0:
                max_partitions = max(max_partitions, app_max_partitions)
                max_machine_vertices = max(
                    n_machine_vertices, max_machine_vertices)
                max_keys = max(local_max_keys, max_keys)
                n_app_vertices += 1

        # Work out the number of bits needed by each part
        self.__n_bits_machine = _bits_needed(max_machine_vertices)
        self.__n_bits_partition = _bits_needed(max_partitions)
        self.__n_bits_atoms = _bits_needed(max_keys)

        # Add up the bits needed by everything below the application vertex
        self.__n_bits_total = sum((
            self.__n_bits_machine, self.__n_bits_partition,
            self.__n_bits_atoms))

        # Check the total number of bits isn't too big
        n_bits_vertices = _bits_needed(n_app_vertices)
        if (self.__n_bits_total + n_bits_vertices) > BITS_IN_KEY:
            raise PacmanRouteInfoAllocationException(
                "Unable to use GlobalZonedRoutingInfoAllocator as it needs "
                "{} + {} + {} + {} bits".format(
                    self.__n_bits_machine, self.__n_bits_partition,
                    self.__n_bits_atoms, n_bits_vertices))

    def _simple_allocate(self):
        """ Allocate the keys given the calculations done previously
        """
        progress = ProgressBar(
            self.__application_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()

        # Keep track of the application vertex keys and masks
        by_app_vertex = dict()

        # Work out the mask to use in the key and the applcation-vertex key
        mask = FULL_MASK - ((2 ** self.__n_bits_atoms) - 1)
        app_mask = FULL_MASK - ((2 ** self.__n_bits_total) - 1)

        app_index = 0
        for app_vertex in progress.over(self.__application_graph.vertices):
            machine_index = 0
            for vertex in app_vertex.machine_vertices:
                partitions = self.__machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)
                part_index = 0
                for partition in partitions:
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        # Build a key based on the indices
                        key = app_index
                        key = (key << self.__n_bits_machine) | machine_index
                        key = (key << self.__n_bits_partition) | part_index
                        key = key << self.__n_bits_atoms
                        key_and_mask = BaseKeyAndMask(base_key=key, mask=mask)
                        info = PartitionRoutingInfo([key_and_mask], partition)
                        routing_infos.add_partition_info(info)
                        part_index += 1
                if part_index > 0:
                    machine_index += 1

            # If we allocated a key for one of the machine vertices, store
            # the "application" key and mask; that is the key used by every
            # machine vertex of this application vertex.
            if machine_index > 0:
                app_key = app_index << self.__n_bits_total
                by_app_vertex[app_vertex] = BaseKeyAndMask(
                    base_key=app_key, mask=app_mask)
                app_index += 1

        return routing_infos, by_app_vertex
