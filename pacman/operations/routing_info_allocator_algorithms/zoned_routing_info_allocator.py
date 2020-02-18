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

from pacman.utilities.constants import BITS_IN_KEY, FULL_MASK
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_info import (
    RoutingInfo, PartitionRoutingInfo, BaseKeyAndMask)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints)
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, ContiguousKeyRangeContraint)
from pacman.model.graphs.common import EdgeTrafficType


class ZonedRoutingInfoAllocator(object):
    """ An basic algorithm that can produce routing keys and masks for\
        edges in a graph based on the x,y,p of the placement\
        of the preceding vertex.

    .. note::
        No constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex will be given the same key/mask assignment.
    """

    MAX_PARTITIONS_SUPPORTED = 1

    def __call__(
            self, application_graph, graph_mapper, machine_graph, n_keys_map):
        """
        :param machine_graph:\
            The machine graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param n_keys_map:\
            A map between the edges and the number of keys required by the\
            edges
        :type n_keys_map:\
            :py:class:`pacman.model.routing_info.AbstractMachinePartitionNKeysMap`
        :param graph_mapper: map between graphs
        :type graph_mapper:\
            :py:class:`pacman.model.graphs.common.graph_mapper.GraphMapper`
        :return: The routing information
        :rtype:\
            :py:class:`pacman.model.routing_info.PartitionRoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: \
            If something goes wrong with the allocation
        """

        # check that this algorithm supports the constraints put onto the
        # partitions

        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        max_app_keys_bits, key_bits_per_app = self._calculate_zones(
                application_graph, graph_mapper, machine_graph, n_keys_map)

        return self._simple_allocate(
            max_app_keys_bits, key_bits_per_app, application_graph,
            graph_mapper, machine_graph)

    def _calculate_zones(
            self, application_graph, graph_mapper, machine_graph, n_keys_map):
        """
        :param machine_graph:\
            The machine graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param n_keys_map:\
            A map between the edges and the number of keys required by the\
            edges
        :type n_keys_map:\
            :py:class:`pacman.model.routing_info.AbstractMachinePartitionNKeysMap`
        :param graph_mapper: map between graphs
        :type graph_mapper:\
            :py:class:`pacman.model.graphs.common.graph_mapper.GraphMapper`
        :return: tuple containing max app keys and a map of app to max keys\
         for any given machine vertex
         :rtype: tuple of (int, dict(app vertex) : int)
        """
        progress = ProgressBar(
            application_graph.n_vertices, "Calculating zones")
        # holders
        max_app_keys_bits = 0
        source_zones = 0
        max_partitions = 0
        key_bits_per_app = dict()

        # search for size of regions
        for app_vertex in progress.over(application_graph.vertices):
            app_max_partitions = 0
            machine_vertices = graph_mapper.get_machine_vertices(
                app_vertex)
            max_keys = 0
            for vertex in machine_vertices:
                partitions = machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)
                app_max_partitions = max(app_max_partitions, len(partitions))
                # Do we need to check type here
                for partition in partitions:
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        n_keys = n_keys_map.n_keys_for_partition(
                            partition)
                        max_keys = max(max_keys, n_keys)
            if max_keys > 0:
                max_partitions = max(max_partitions, app_max_partitions)
                source_zones += app_max_partitions
                key_bits = self._bits_needed(max_keys)
                machine_bits = self._bits_needed(len(machine_vertices))
                max_app_keys_bits = max(
                    max_app_keys_bits, machine_bits + key_bits)
                key_bits_per_app[app_vertex] = key_bits
        source_bits = self._bits_needed(source_zones)

        if source_bits + max_app_keys_bits > BITS_IN_KEY:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bites".format(
                    source_bits, max_app_keys_bits))

        if max_partitions > self.MAX_PARTITIONS_SUPPORTED:
            raise NotImplementedError()

        return max_app_keys_bits, key_bits_per_app

    @staticmethod
    def _simple_allocate(
            max_app_keys_bits, key_bits_per_app, application_graph,
            graph_mapper, machine_graph):
        """

        :param max_app_keys_bits: max bits for app keys
        :type max_app_keys_bits: int
        :param key_bits_per_app: map of app to max keys for any given \
        machine vertex
        :type key_bits_per_app: dict of [app vertex] to int
        :param machine_graph:\
            The machine graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param n_keys_map:\
            A map between the edges and the number of keys required by the\
            edges
        :type n_keys_map:\
            :py:class:`pacman.model.routing_info.AbstractMachinePartitionNKeysMap`
        :param graph_mapper: map between graphs
        :type graph_mapper:\
            :py:class:`pacman.model.graphs.common.graph_mapper.GraphMapper`
        :return: tuple of routing infos and map from app vertex and key masks
        """
        progress = ProgressBar(
            application_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()
        by_app_vertex = dict()
        app_mask = FULL_MASK - ((2 ** max_app_keys_bits) - 1)
        source_index = 0
        for app_vertex in progress.over(application_graph.vertices):
            if app_vertex in key_bits_per_app:
                machine_vertices = graph_mapper.get_machine_vertices(
                    app_vertex)
                key_bites = key_bits_per_app[app_vertex]
                for machine_index, vertex in enumerate(machine_vertices):
                    partitions = (
                        machine_graph.
                        get_outgoing_edge_partitions_starting_at_vertex(
                            vertex))
                    partition = partitions.peek()
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        mask = FULL_MASK - ((2 ** key_bites) - 1)
                        key = (source_index << max_app_keys_bits |
                               machine_index << key_bites)
                        key_and_mask = BaseKeyAndMask(base_key=key, mask=mask)
                        info = PartitionRoutingInfo([key_and_mask], partition)
                        routing_infos.add_partition_info(info)
                app_key = source_index << max_app_keys_bits
                by_app_vertex[app_vertex] = BaseKeyAndMask(
                    base_key=app_key, mask=app_mask)
                source_index += 1

        return routing_infos, by_app_vertex

    @staticmethod
    def _bits_needed(size):
        return int(math.ceil(math.log(size, 2)))
