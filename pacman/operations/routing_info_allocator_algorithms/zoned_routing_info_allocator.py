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

    __slots__ = [
        # Passed in paramateres
        "_application_graph",
        "_graph_mapper",
        "_machine_graph",
        "_placements",
        "_n_keys_map",
        "_max_app_keys_bites",
        "_key_bites_per_app"
    ]
    # pylint: disable=attribute-defined-outside-init

    def __call__(self, application_graph, graph_mapper, machine_graph,
                 placements, n_keys_map):
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
        self._graph_mapper = graph_mapper
        self._machine_graph = machine_graph
        self._placements = placements
        self._n_keys_map = n_keys_map

        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        if self._caluculate_zones() != 1:
            raise NotImplementedError()

        return self._simple_allocate()

    def _caluculate_zones(self):
        progress = ProgressBar(
            self._application_graph.n_vertices, "Calculating zones")
        self._max_app_keys_bites = 0
        source_zones = 0
        max_partitions = 0
        self._key_bites_per_app = dict()
        for app_vertex in progress.over(self._application_graph.vertices):
            app_max_partitions = 0
            machine_vertices = self._graph_mapper.get_machine_vertices(
                app_vertex)
            max_keys = 0
            for vertex in machine_vertices:
                partitions = self._machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)
                app_max_partitions = max(app_max_partitions, len(partitions))
                # Do we need to check type here
                for partition in partitions:
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        n_keys = self._n_keys_map.n_keys_for_partition(
                            partition)
                        max_keys = max(max_keys, n_keys)
            if max_keys > 0:
                max_partitions = max(max_partitions, app_max_partitions)
                source_zones += app_max_partitions
                key_bites = self._bites_needed(max_keys)
                machine_bites = self._bites_needed(len(machine_vertices))
                self._max_app_keys_bites = max(
                    self._max_app_keys_bites, machine_bites + key_bites)
                self._key_bites_per_app[app_vertex] = key_bites
        source_bites = self._bites_needed(source_zones)

        if source_bites + self._max_app_keys_bites > KEY_SIZE:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bites".format(
                    source_bites, self._max_app_keys_bites))
        return max_partitions

    def _simple_allocate(self):
        progress = ProgressBar(
            self._application_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()
        by_app_vertex = dict()
        app_mask = 2 ** 32 - 2 ** self._max_app_keys_bites

        for source_index, app_vertex in progress.over(
                enumerate(self._application_graph.vertices)):
            machine_vertices = self._graph_mapper.get_machine_vertices(
                app_vertex)
            if app_vertex in self._key_bites_per_app:
                key_bites = self._key_bites_per_app[app_vertex]
                for machine_index, vertex in enumerate(machine_vertices):
                    partitions = self._machine_graph. \
                        get_outgoing_edge_partitions_starting_at_vertex(vertex)
                    partition = partitions.peek()
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        mask = 2 ** 32 - 2 ** key_bites
                        key = source_index << self._max_app_keys_bites | \
                            machine_index << key_bites
                        key_and_mask = BaseKeyAndMask(base_key=key, mask=mask)
                        info = PartitionRoutingInfo([key_and_mask], partition)
                        routing_infos.add_partition_info(info)
            app_key = source_index << self._max_app_keys_bites
            by_app_vertex[app_vertex] = BaseKeyAndMask(
                base_key=app_key, mask=app_mask)

        return routing_infos, by_app_vertex

    def _bites_needed(self, size):
        return math.ceil(math.log(size, 2))
