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

    :param MachineGraph machine_graph:
        The machine graph to allocate the routing info for
    :param AbstractMachinePartitionNKeysMap n_keys_map:
        A map between the edges and the number of keys required by the
        edges
    :return: The routing information
    :rtype: tuple(RoutingInfo, dict(ApplicationVertex, BaseKeyAndMask))
    :raise PacmanRouteInfoAllocationException:
        If something goes wrong with the allocation
    """

    __slots__ = [
        # Passed in parameters
        "__application_graph",
        "__machine_graph",
        "__n_keys_map"
    ]
    # pylint: disable=attribute-defined-outside-init

    def __call__(self, application_graph, machine_graph, n_keys_map):
        """
        :param MachineGraph machine_graph:
            The machine graph to allocate the routing info for
        :param AbstractMachinePartitionNKeysMap n_keys_map:
            A map between the edges and the number of keys required by the
            edges
        :return: The routing information
        :rtype: tuple(RoutingInfo, dict(ApplicationVertex,BaseKeyAndMask))
        :raise PacmanRouteInfoAllocationException:
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

        max_partitions, max_app_keys_bits, key_bits_per_app = \
            self._caluculate_zones()
        if max_partitions != 1:
            raise NotImplementedError()

        return self._simple_allocate(max_app_keys_bits, key_bits_per_app)

    def _caluculate_zones(self):
        """
        :rtype: tuple(int, int, dict(ApplicationVertex,int))
        :raises PacmanRouteInfoAllocationException:
        """
        progress = ProgressBar(
            self.__application_graph.n_vertices, "Calculating zones")
        max_app_keys_bits = 0
        source_zones = 0
        max_partitions = 0
        key_bits_per_app = dict()
        for app_vertex in progress.over(self.__application_graph.vertices):
            app_max_partitions = 0
            max_keys = 0
            for vertex in app_vertex.machine_vertices:
                partitions = self.__machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)
                app_max_partitions = max(app_max_partitions, len(partitions))
                max_keys = max(max_keys, max(
                    (self.__n_keys_map.n_keys_for_partition(partition)
                     for partition in partitions
                     if partition.traffic_type == EdgeTrafficType.MULTICAST),
                    default=0))
            if max_keys > 0:
                max_partitions = max(max_partitions, app_max_partitions)
                source_zones += app_max_partitions
                key_bits = self.__bits_needed(max_keys)
                machine_bits = self.__bits_needed(len(
                    app_vertex.machine_vertices))
                max_app_keys_bits = max(
                    max_app_keys_bits, machine_bits + key_bits)
                key_bits_per_app[app_vertex] = key_bits
        source_bits = self.__bits_needed(source_zones)

        if source_bits + max_app_keys_bits > KEY_SIZE:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bits".format(
                    source_bits, max_app_keys_bits))
        return max_partitions, max_app_keys_bits, key_bits_per_app

    def _simple_allocate(self, max_app_keys_bits, key_bits_map):
        """
        :param int max_app_keys_bits:
        :param dict(ApplicationVertex,int) key_bits_map:
        :rtype: tuple(RoutingInfo, dict(ApplicationVertex,BaseKeyAndMask))
        """
        progress = ProgressBar(
            self.__application_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()
        by_app_vertex = dict()
        app_mask = self.__mask(max_app_keys_bits)

        for source_index, app_vertex in progress.over(
                enumerate(self.__application_graph.vertices)):
            app_key = source_index << max_app_keys_bits
            if app_vertex in key_bits_map:
                key_bits = key_bits_map[app_vertex]
                for machine_index, vertex in enumerate(
                        app_vertex.machine_vertices):
                    partitions = self.__machine_graph. \
                        get_outgoing_edge_partitions_starting_at_vertex(vertex)
                    partition = partitions.peek()
                    if partition.traffic_type == EdgeTrafficType.MULTICAST:
                        mask = self.__mask(key_bits)
                        key = app_key | machine_index << key_bits
                        key_and_mask = BaseKeyAndMask(base_key=key, mask=mask)
                        routing_infos.add_partition_info(
                            PartitionRoutingInfo([key_and_mask], partition))
            by_app_vertex[app_vertex] = BaseKeyAndMask(
                base_key=app_key, mask=app_mask)

        return routing_infos, by_app_vertex

    @staticmethod
    def __mask(bits):
        """
        :param int bits:
        :rtype int:
        """
        return (2 ** 32) - (2 ** bits)

    @staticmethod
    def __bits_needed(size):
        """
        :param int size:
        :rtype: int
        """
        return math.ceil(math.log(size, 2))
