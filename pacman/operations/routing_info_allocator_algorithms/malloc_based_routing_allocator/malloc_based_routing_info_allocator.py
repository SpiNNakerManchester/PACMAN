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

import logging
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.log import FormatAdapter
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, ShareKeyConstraint, FixedMaskConstraint,
    FixedKeyAndMaskConstraint, ContiguousKeyRangeContraint)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints)
from pacman.utilities.algorithm_utilities.routing_info_allocator_utilities \
    import (check_types_of_edge_constraint, get_mulitcast_edge_groups)
from .utils import RoutingInfoAllocator

logger = FormatAdapter(logging.getLogger(__name__))


class MallocBasedRoutingInfoAllocator(RoutingInfoAllocator):
    """ A Routing Info Allocation Allocator algorithm that keeps track of\
        free keys and attempts to allocate them as requested.
    """

    __slots__ = ["_n_keys_map"]

    def __init__(self):
        super().__init__(0, 2 ** 32)
        self._n_keys_map = None

    def __call__(self, machine_graph, n_keys_map):
        """
        :param MachineGraph machine_graph:
        :param AbstractMachinePartitionNKeysMap n_keys_map:
        :rtype: RoutingInfo
        :raises PacmanRouteInfoAllocationException:
        """
        self._n_keys_map = n_keys_map
        # check that this algorithm supports the constraints
        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[
                FixedMaskConstraint, FixedKeyAndMaskConstraint,
                ContiguousKeyRangeContraint, ShareKeyConstraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # verify that no edge has more than 1 of a constraint ,and that
        # constraints are compatible
        check_types_of_edge_constraint(machine_graph)

        # Get the edges grouped by those that require the same key
        (fixed_keys, shared_keys, fixed_masks, fixed_fields, continuous,
         noncontinuous) = get_mulitcast_edge_groups(machine_graph)

        # Go through the groups and allocate keys
        progress = ProgressBar(
            machine_graph.n_outgoing_edge_partitions,
            "Allocating routing keys")

        # allocate the groups that have fixed keys
        for group in progress.over(fixed_keys, False):
            self._allocate_fixed_keys(group)

        for group in progress.over(fixed_masks, False):
            self._allocate_fixed_masks(group)

        for group in progress.over(fixed_fields, False):
            self._allocate_fixed_fields(group)

        for group in progress.over(shared_keys, False):
            self._allocate_share_key(group)

        for group in continuous:
            self._allocate_other_groups(group, True)

        for group in noncontinuous:
            self._allocate_other_groups(group, False)

        progress.end()
        # Return the allocation (built in our utility superclass)
        return self._get_allocated_routing_info()

    def __get_n_keys(self, group):
        """
        :param ConstraintGroup group:
        :rtype: int
        """
        return max(
            self._n_keys_map.n_keys_for_partition(partition)
            for partition in group)

    def _allocate_other_groups(self, group, continuous):
        """
        :param ConstraintGroup group:
        :param bool continuous:
        """
        keys_and_masks = self._allocate_keys_and_masks(
            None, None, self.__get_n_keys(group),
            contiguous_keys=continuous)
        for partition in group:
            self._update_routing_objects(keys_and_masks, partition)

    def _allocate_share_key(self, group):
        """
        :param ConstraintGroup group:
        """
        keys_and_masks = self._allocate_keys_and_masks(
            None, None, self.__get_n_keys(group))

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(keys_and_masks, partition)

    def _allocate_fixed_keys(self, group):
        """
        :param ConstraintGroup group:
        """
        # Get any fixed keys and masks from the group and attempt to
        # allocate them
        keys_and_masks = group.constraint.keys_and_masks
        self._allocate_fixed_keys_and_masks(keys_and_masks)

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(keys_and_masks, partition)

    def _allocate_fixed_masks(self, group):
        """
        :param ConstraintGroup group:
        """
        # get mask and fields if need be
        fixed_mask = group.constraint.mask

        # try to allocate
        keys_and_masks = self._allocate_keys_and_masks(
            fixed_mask, None, self.__get_n_keys(group))

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(keys_and_masks, partition)

    def _allocate_fixed_fields(self, group):
        """
        :param ConstraintGroup group:
        """
        fields = group.constraint.fields

        # try to allocate
        keys_and_masks = self._allocate_keys_and_masks(
            None, fields, self.__get_n_keys(group))

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(keys_and_masks, partition)
