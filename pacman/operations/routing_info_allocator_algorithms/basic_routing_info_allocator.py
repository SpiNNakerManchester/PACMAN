# Copyright (c) 2017-2019 The University of Manchester
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

from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_info import (
    RoutingInfo, PartitionRoutingInfo, BaseKeyAndMask)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints)
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, ContiguousKeyRangeContraint)

MAX_KEYS_SUPPORTED = 2048
MASK = 0xFFFFF800


class BasicRoutingInfoAllocator(object):
    """ An basic algorithm that can produce routing keys and masks for\
        edges in a graph based on the x,y,p of the placement\
        of the preceding vertex.

    .. note::
        No constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex will be given the same key/mask assignment.

    """

    __slots__ = []

    def __call__(self, machine_graph, placements, n_keys_map):
        """
        :param MachineGraph machine_graph:
            The machine graph to allocate the routing info for
        :param Placements placements: The placements of the vertices
        :param AbstractMachinePartitionNKeysMap n_keys_map:
            A map between the edges and the number of keys required by the
            edges
        :return: The routing information
        :rtype: PartitionRoutingInfo
        :raise PacmanRouteInfoAllocationException:
            If something goes wrong with the allocation
        """

        # check that this algorithm supports the constraints put onto the
        # partitions
        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # take each edge and create keys from its placement
        progress = ProgressBar(
            machine_graph.n_vertices, "Allocating routing keys")
        routing_infos = RoutingInfo()
        for vertex in progress.over(machine_graph.vertices):
            for partition in machine_graph.\
                    get_multicast_edge_partitions_starting_at_vertex(vertex):
                routing_infos.add_partition_info(
                    self._allocate_key_for_partition(
                        partition, vertex, placements, n_keys_map))
        return routing_infos

    def _allocate_key_for_partition(
            self, partition, vertex, placements, n_keys_map):
        """
        :param AbstractSingleSourcePartition partition:
        :param MachineVertex vertex:
        :param Placements placements:
        :param AbstractMachinePartitionNKeysMap n_keys_map:
        :rtype: PartitionRoutingInfo
        :raises PacmanRouteInfoAllocationException:
        """
        n_keys = n_keys_map.n_keys_for_partition(partition)
        if n_keys > MAX_KEYS_SUPPORTED:
            raise PacmanRouteInfoAllocationException(
                "This routing info allocator can only support up to {} keys "
                "for any given edge; cannot therefore allocate keys to {}, "
                "which is requesting {} keys".format(
                    MAX_KEYS_SUPPORTED, partition, n_keys))

        placement = placements.get_placement_of_vertex(vertex)
        if placement is None:
            raise PacmanRouteInfoAllocationException(
                "The vertex '{}' has no placement".format(vertex))

        keys_and_masks = list([BaseKeyAndMask(
            base_key=self._get_key_from_placement(placement), mask=MASK)])
        return PartitionRoutingInfo(keys_and_masks, partition)

    @staticmethod
    def _get_key_from_placement(placement):
        """ Return a key given a placement

        :param Placement placement: the associated placement
        :return: The key
        :rtype: int
        """
        return placement.x << 24 | placement.y << 16 | placement.p << 11
