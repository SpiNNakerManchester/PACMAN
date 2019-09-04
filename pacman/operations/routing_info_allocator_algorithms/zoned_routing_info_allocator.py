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

KEY_SIZE = 32


class ZonedRoutingInfoAllocator(object):
    """ An basic algorithm that can produce routing keys and masks for\
        edges in a graph based on the x,y,p of the placement\
        of the preceding vertex.

    .. note::
        No constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex will be given the same key/mask assignment.
    """
    # pylint: disable=attribute-defined-outside-init

    __slots__ = [
        # Passed in paramateres
        "__application_graph",
        "__machine_graph",
        "__n_keys_map"
    ]

    def __call__(self, application_graph, machine_graph, placements,
                 n_keys_map):
        """
        :param machine_graph:\
            The machine graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param placements: The placements of the vertices
        :type placements:\
            :py:class:`pacman.model.placements.placements.Placements`
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

        # check that this algorithm supports the constraints put onto the
        # partitions
        self.__application_graph = application_graph
        self.__machine_graph = machine_graph
        self.__n_keys_map = n_keys_map

        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        max_app_keys_bytes, max_partitions, key_bytes_per_app = \
            self._calculate_zones()

        if max_partitions == 1:
            return self._simple_allocate(max_app_keys_bytes, key_bytes_per_app)

        raise NotImplementedError()

    def _calculate_zones(self):
        max_app_keys_bytes = 0
        max_partitions = 0
        key_bytes_map = dict()

        progress = ProgressBar(
            self.__application_graph.n_vertices, "Calculating zones")
        source_zones = 0
        for app_vertex in progress.over(self.__application_graph.vertices):
            app_max_partitions = 0
            max_keys = 0
            for vertex in app_vertex.machine_vertices:
                partitions = self.__partitions(vertex)
                app_max_partitions = max(app_max_partitions, len(partitions))
                # Do we need to check type here
                for partition in partitions:
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        max_keys = max(max_keys, self.__n_keys(partition))
            if max_keys > 0:
                max_partitions = max(max_partitions, app_max_partitions)
                source_zones += app_max_partitions
                key_bytes = self.__bytes_needed(max_keys)
                machine_bytes = self.__bytes_needed(len(
                    app_vertex.machine_vertices))
                max_app_keys_bytes = max(
                    max_app_keys_bytes, machine_bytes + key_bytes)
                key_bytes_map[app_vertex] = key_bytes
        source_bytes = self.__bytes_needed(source_zones)

        if source_bytes + max_app_keys_bytes > KEY_SIZE:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bytes".format(
                    source_bytes, max_app_keys_bytes))
        return max_app_keys_bytes, max_partitions, key_bytes_map

    def _simple_allocate(self, max_app_keys_bytes, key_bytes_map):
        progress = ProgressBar(
            self.__application_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()
        by_app_vertex = dict()
        app_mask = (2 ** 32) - (2 ** max_app_keys_bytes)

        source_index = 0
        for app_vertex in progress.over(self.__application_graph.vertices):
            if app_vertex in key_bytes_map:
                key_bytes = key_bytes_map[app_vertex]
                for machine_index, vertex in enumerate(
                        app_vertex.machine_vertices):
                    partition = self.__partitions(vertex).peek()
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        mask = (2 ** 32) - (2 ** key_bytes)
                        key = source_index << max_app_keys_bytes | \
                            machine_index << key_bytes
                        keys_and_masks = list([BaseKeyAndMask(
                            base_key=key, mask=mask)])
                        info = PartitionRoutingInfo(keys_and_masks, partition)
                        routing_infos.add_partition_info(info)
            app_key = key = source_index << max_app_keys_bytes
            by_app_vertex[app_vertex] = BaseKeyAndMask(
                base_key=app_key, mask=app_mask)
            source_index += 1

        return routing_infos, by_app_vertex

    def __n_keys(self, partition):
        return self.__n_keys_map.n_keys_for_partition(partition)

    def __partitions(self, machine_vertex):
        return self.__machine_graph.\
            get_outgoing_edge_partitions_starting_at_vertex(machine_vertex)

    @staticmethod
    def __bytes_needed(size):
        return math.ceil(math.log(size, 2))
