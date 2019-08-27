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
        "_application_graph",
        "_machine_graph",
        "_placements",
        "_n_keys_map",
        "_max_partions",
        "_max_app_keys_bytes",
        "_key_bytes_per_app"
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
        self._application_graph = application_graph
        self._machine_graph = machine_graph
        self._placements = placements
        self._n_keys_map = n_keys_map

        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        self._max_app_keys_bytes = 0
        self._max_partions = 0
        self._key_bytes_per_app = dict()

        self._caluculate_zones()

        if self._max_partions == 1:
            return self._simple_allocate()

        raise NotImplementedError()

    def __partitions(self, machine_vertex):
        return self._machine_graph.\
            get_outgoing_edge_partitions_starting_at_vertex(machine_vertex)

    def _caluculate_zones(self):
        progress = ProgressBar(
            self._application_graph.n_vertices, "Calculating zones")
        source_zones = 0
        for app_vertex in progress.over(self._application_graph.vertices):
            app_max_partions = 0
            machine_vertices = app_vertex.machine_vertices
            max_keys = 0
            for vertex in machine_vertices:
                partitions = self.__partitions(vertex)
                app_max_partions = max(app_max_partions, len(partitions))
                # Do we need to check type here
                for partition in partitions:
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        n_keys = self._n_keys_map.n_keys_for_partition(
                            partition)
                        max_keys = max(max_keys, n_keys)
            if max_keys > 0:
                self._max_partions = max(self._max_partions, app_max_partions)
                source_zones += app_max_partions
                key_bytes = self.__bytes_needed(max_keys)
                machine_bytes = self.__bytes_needed(len(machine_vertices))
                self._max_app_keys_bytes = max(
                    self._max_app_keys_bytes, machine_bytes + key_bytes)
                self._key_bytes_per_app[app_vertex] = key_bytes
        source_bytes = self.__bytes_needed(source_zones)

        if source_bytes + self._max_app_keys_bytes > KEY_SIZE:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bytes".format(
                    source_bytes, self._max_app_keys_bytes))

    def _simple_allocate(self):
        progress = ProgressBar(
            self._application_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()
        by_app_vertex = dict()
        app_mask = 2 ** 32 - 2 ** self._max_app_keys_bytes

        source_index = 0
        for app_vertex in progress.over(self._application_graph.vertices):
            if app_vertex in self._key_bytes_per_app:
                key_bytes = self._key_bytes_per_app[app_vertex]
                for vertex in app_vertex.machine_vertices:
                    machine_index = vertex.index
                    partitions = self.__partitions(vertex)
                    partition = partitions.peek()
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        mask = 2 ** 32 - 2 ** key_bytes
                        key = source_index << self._max_app_keys_bytes | \
                            machine_index << key_bytes
                        keys_and_masks = list([BaseKeyAndMask(
                            base_key=key, mask=mask)])
                        info = PartitionRoutingInfo(keys_and_masks, partition)
                        routing_infos.add_partition_info(info)
            app_key = key = source_index << self._max_app_keys_bytes
            by_app_vertex[app_vertex] = BaseKeyAndMask(
                base_key=app_key, mask=app_mask)
            source_index += 1

        return routing_infos, by_app_vertex

    def __bytes_needed(self, size):
        return math.ceil(math.log(size, 2))
