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
from pacman.utilities.constants import BITS_IN_KEY, FULL_MASK
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
        No constraints are supported, and that the number of keys
        required by each edge must be 2048 or less, and that all edges coming
        out of a vertex will be given the same key/mask assignment.

    :param ApplicationGraph application_graph:
        The application graph to allocate the routing info for
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
        :param ApplicationGraph application_graph:
        :param MachineGraph machine_graph:
        :param AbstractMachinePartitionNKeysMap n_keys_map:
        :rtype: tuple(RoutingInfo, dict(ApplicationVertex, BaseKeyAndMask))
        :raise PacmanRouteInfoAllocationException:
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

        max_app_keys_bits, key_bits_per_app = self._calculate_zones()

        return self._simple_allocate(max_app_keys_bits, key_bits_per_app)

    def _calculate_zones(self):
        """
        :return: tuple containing max app keys and a map of app to max keys
            for any given machine vertex
        :rtype: tuple(int, dict(ApplicationVertex, int))
        :raises PacmanRouteInfoAllocationException:
        """
        by_app_and_partition_name = \
            self.__machine_graph.pre_vertices_by_app_and_partition_name
        progress = ProgressBar(
            len(by_app_and_partition_name), "Calculating zones")

        # Over all application vertices work out the number of but needed for
        # partition (names)

        # For each App vertex / Partition name zone keep track of the number of
        # bites required for the mask for each machine vertex
        mask_bits_per_zone = dict()
        # maximum number of bites to represent the keys and masks
        # for a single app vertex / partition name zone
        max_zone_keys_bits = 0

        # search for size of regions
        for app_vertex in progress.over(by_app_and_partition_name):
            for partition_name, by_partition_name in \
                    by_app_and_partition_name[app_vertex].values():
                max_keys = 0
                for mac_vertex in by_partition_name.vertices:
                    partition =  self.__machine_graph.\
                        get_edges_ending_at_vertex_with_partition_name(
                        mac_vertex, partition )
                    n_keys = self.__n_keys_map.n_keys_for_partition(partition)
                    max(max_keys, n_keys)
                if max_keys > 0:
                    key_bits = self.__bits_needed(max_keys)
                    machine_bits = self.__bits_needed(len(
                        by_partition_name.vertices))
                    max_zone_keys_bits = max(
                        max_zone_keys_bits, machine_bits + key_bits)
                mask_bits_per_zone[(app_vertex, partition_name)] = key_bits

        zone_bits = self.__bits_needed(len(mask_bits_per_zone))

        if zone_bits + max_zone_keys_bits > BITS_IN_KEY:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bits".format(
                    zone_bits, max_zone_keys_bits))
        return max_zone_keys_bits, mask_bits_per_zone

    def _simple_allocate(self, max_app_keys_bits, mask_bits_map):
        """
        :param int max_app_keys_bits: max bits for app keys
        :param dict((ApplicationVertex, str),int) mask_bits_map:
            map of app vertex,name to max keys for that vertex
        :return: tuple of routing infos and map from app vertex and key masks
        :rtype: tuple(RoutingInfo, dict(ApplicationVertex,BaseKeyAndMask))
        """
        by_app_and_partition_name = \
            self.__machine_graph.pre_vertices_by_app_and_partition_name
        progress = ProgressBar(
            len(by_app_and_partition_name), "Allocating routing keys")
        routing_infos = RoutingInfo()
        by_app_vertex = dict()
        app_mask = self.__mask(max_app_keys_bits)

        zone_index = 0
        for app_vertex in progress.over(by_app_and_partition_name ):
            for partition_name, by_partition_name in \
                    by_app_and_partition_name[app_vertex].values():
                mask_bits = mask_bits_map.get(
                    (app_vertex, partition_name), None)
                if mask_bits is None:
                   continue
                app_key = zone_index << max_app_keys_bits
                machine_vertices = list(by_partition_name.vertices)
                machine_vertices.sort(lambda x: x.vertex_slice.lo_atom)
                for machine_index, vertex in enumerate(machine_vertices):
                    mask = self.__mask(mask_bits)
                    key = app_key | machine_index << mask_bits
                    key_and_mask = BaseKeyAndMask(base_key=key, mask=mask)
                    partition = self.__machine_graph. \
                        get_edges_ending_at_vertex_with_partition_name(
                        vertex, partition)
                    routing_infos.add_partition_info(
                        PartitionRoutingInfo([key_and_mask], partition))
                    # TODO what about partition ??
                by_app_vertex[app_vertex] = BaseKeyAndMask(
                    base_key=app_key, mask=app_mask)
                zone_index += 1

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

    # get delay app vertex
    delay_app_vertex = self._app_to_delay_map.get(app_edge, None)
    if delay_app_vertex is None:
        delay_app_vertex = self._create_delay_app_vertex(
            app_edge, max_delay_needed, machine_time_step,
            time_scale_factor, app_graph)
