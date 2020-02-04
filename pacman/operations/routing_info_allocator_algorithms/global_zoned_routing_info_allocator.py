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

KEY_SIZE = 32


class GlobalZonedRoutingInfoAllocator(object):
    """ A routing key allocator that uses fixed zones that are the same for\
        all vertices

    .. note::
        No constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex will be given the same key/mask assignment.
    """

    __slots__ = [
        # Passed in parameters
        "_application_graph",
        "_graph_mapper",
        "_machine_graph",
        "_placements",
        "_n_keys_map",
        "_n_bits_partition",
        "_n_bits_machine",
        "_n_bits_atoms"
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

        self._calculate_zones()
        return self._simple_allocate()

    def _calculate_zones(self):
        progress = ProgressBar(
            self._application_graph.n_vertices, "Calculating zones")
        max_partitions = 0
        max_machine_vertices = 0
        max_keys = 0
        n_app_vertices = 0

        for app_vertex in progress.over(self._application_graph.vertices):
            app_max_partitions = 0
            machine_vertices = self._graph_mapper.get_machine_vertices(
                app_vertex)
            n_machine_vertices = 0
            for vertex in machine_vertices:
                partitions = self._machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)
                n_partitions = 0
                local_max_keys = 0
                for partition in partitions:
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        n_keys = self._n_keys_map.n_keys_for_partition(
                            partition)
                        local_max_keys = max(local_max_keys, n_keys)
                        n_partitions += 1
                app_max_partitions = max(app_max_partitions, n_partitions)
                n_machine_vertices += 1
            if local_max_keys > 0:
                max_partitions = max(max_partitions, app_max_partitions)
                max_machine_vertices = max(
                    n_machine_vertices, max_machine_vertices)
                max_keys = max(local_max_keys, max_keys)
                n_app_vertices += 1

        self._n_bits_machine = self._bites_needed(max_machine_vertices)
        self._n_bits_partition = self._bites_needed(max_partitions)
        self._n_bits_atoms = self._bites_needed(max_keys)
        n_bits_vertices = self._bites_needed(n_app_vertices)

        if sum((self._n_bits_machine,
                self._n_bits_partition,
                self._n_bits_atoms,
                n_bits_vertices)) > KEY_SIZE:
            raise PacmanRouteInfoAllocationException(
                "Unable to use GlobalZonedRoutingInfoAllocator as it needs "
                "{} + {} + {} + {} bits".format(
                    self._n_bits_machine, self._n_bits_partition,
                    self._n_bits_atoms, n_bits_vertices))
        return max_partitions

    def _simple_allocate(self):
        progress = ProgressBar(
            self._application_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()
        by_app_vertex = dict()
        mask = 0xFFFFFFFF - ((2 ** self._n_bits_atoms) - 1)
        app_bits = (
            self._n_bits_atoms + self._n_bits_machine + self._n_bits_partition)
        app_mask = 0xFFFFFFFF - ((2 ** app_bits) - 1)
        app_index = 0
        for app_vertex in progress.over(self._application_graph.vertices):
            machine_vertices = self._graph_mapper.get_machine_vertices(
                app_vertex)
            machine_index = 0
            for vertex in machine_vertices:
                partitions = self._machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)
                part_index = 0
                for partition in partitions:
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        key = app_index
                        key = (key << self._n_bits_machine) | machine_index
                        key = (key << self._n_bits_partition) | part_index
                        key = key << self._n_bits_atoms
                        key_and_mask = BaseKeyAndMask(
                            base_key=key, mask=mask)
                        info = PartitionRoutingInfo(
                            [key_and_mask], partition)
                        routing_infos.add_partition_info(info)
                        part_index += 1
                if part_index > 0:
                    machine_index += 1
            if machine_index > 0:
                app_key = app_index << (self._n_bits_machine +
                                        self._n_bits_partition +
                                        self._n_bits_atoms)
                by_app_vertex[app_vertex] = BaseKeyAndMask(
                    base_key=app_key, mask=app_mask)
                app_index += 1

        return routing_infos, by_app_vertex

    def _bites_needed(self, size):
        return int(math.ceil(math.log(size, 2)))
