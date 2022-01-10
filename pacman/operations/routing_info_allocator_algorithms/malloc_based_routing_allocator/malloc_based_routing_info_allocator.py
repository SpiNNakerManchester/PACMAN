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
from pacman.data import PacmanDataView
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, ShareKeyConstraint, FixedMaskConstraint,
    FixedKeyAndMaskConstraint, ContiguousKeyRangeContraint)
from .key_field_generator import KeyFieldGenerator
from pacman.model.routing_info import (
    RoutingInfo, BaseKeyAndMask, PartitionRoutingInfo)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints, get_key_ranges)
from pacman.utilities.algorithm_utilities import ElementAllocatorAlgorithm
from pacman.utilities.algorithm_utilities.routing_info_allocator_utilities \
    import (check_types_of_edge_constraint, get_mulitcast_edge_groups)
from pacman.exceptions import PacmanRouteInfoAllocationException
from .utils import get_possible_masks

logger = FormatAdapter(logging.getLogger(__name__))


def malloc_based_routing_info_allocator(n_keys_map):
    """
    A Routing Info Allocation Allocator algorithm that keeps track of\
        free keys and attempts to allocate them as requested.

    :param MachineGraph machine_graph:
    :param AbstractMachinePartitionNKeysMap n_keys_map:
    :rtype: RoutingInfo
    :raises PacmanRouteInfoAllocationException:
    """
    allocator = _MallocBasedRoutingInfoAllocator(n_keys_map)
    return allocator.run()


class _MallocBasedRoutingInfoAllocator(ElementAllocatorAlgorithm):
    """ A Routing Info Allocation Allocator algorithm that keeps track of\
        free keys and attempts to allocate them as requested.
    """

    __slots__ = ["_n_keys_map"]

    def __init__(self, n_keys_map):
        super().__init__(0, 2 ** 32)
        self._n_keys_map = n_keys_map

    def run(self):
        """
        :param MachineGraph machine_graph:
        :param AbstractMachinePartitionNKeysMap n_keys_map:
        :rtype: RoutingInfo
        :raises PacmanRouteInfoAllocationException:
        """
        machine_graph = PacmanDataView.get_runtime_machine_graph()
        # check that this algorithm supports the constraints
        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[
                FixedMaskConstraint,
                FixedKeyAndMaskConstraint,
                ContiguousKeyRangeContraint, ShareKeyConstraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # verify that no edge has more than 1 of a constraint ,and that
        # constraints are compatible
        check_types_of_edge_constraint(machine_graph)

        # final keys allocations
        routing_infos = RoutingInfo()

        # Get the edges grouped by those that require the same key
        (fixed_keys, shared_keys, fixed_masks, fixed_fields, continuous,
         noncontinuous) = get_mulitcast_edge_groups(machine_graph)

        # Go through the groups and allocate keys
        progress = ProgressBar(
            machine_graph.n_outgoing_edge_partitions,
            "Allocating routing keys")

        # allocate the groups that have fixed keys
        for group in progress.over(fixed_keys, False):
            self._allocate_fixed_keys(group, routing_infos)

        for group in progress.over(fixed_masks, False):
            self._allocate_fixed_masks(group, routing_infos)

        for group in progress.over(fixed_fields, False):
            self._allocate_fixed_fields(group, routing_infos)

        for group in progress.over(shared_keys, False):
            self._allocate_share_key(group, routing_infos)

        for group in continuous:
            self._allocate_other_groups(group, routing_infos, True)

        for group in noncontinuous:
            self._allocate_other_groups(group, routing_infos, False)

        progress.end()
        return routing_infos

    def __get_n_keys(self, group):
        """
        :param ConstraintGroup group:
        :rtype: int
        """
        return max(
            self._n_keys_map.n_keys_for_partition(partition)
            for partition in group)

    def _allocate_other_groups(self, group, routing_infos, continuous):
        """
        :param ConstraintGroup group:
        :param RoutingInfo routing_infos:
        :param bool continuous:
        """
        keys_and_masks = self._allocate_keys_and_masks(
            None, None, self.__get_n_keys(group),
            contiguous_keys=continuous)
        for partition in group:
            self._update_routing_objects(
                keys_and_masks, routing_infos, partition)

    def _allocate_share_key(self, group, routing_infos):
        """
        :param ConstraintGroup group:
        :param RoutingInfo routing_infos:
        """
        keys_and_masks = self._allocate_keys_and_masks(
            None, None, self.__get_n_keys(group))

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(keys_and_masks, routing_infos,
                                         partition)

    def _allocate_fixed_keys(self, group, routing_infos):
        """
        :param ConstraintGroup group:
        :param RoutingInfo routing_infos:
        """
        # Get any fixed keys and masks from the group and attempt to
        # allocate them
        fixed_key_and_mask_constraint = group.constraint

        fixed_mask = None
        self._allocate_fixed_keys_and_masks(
            fixed_key_and_mask_constraint.keys_and_masks, fixed_mask)

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(
                fixed_key_and_mask_constraint.keys_and_masks, routing_infos,
                partition)

    def _allocate_fixed_masks(self, group, routing_infos):
        """
        :param ConstraintGroup group:
        :param RoutingInfo routing_infos:
        """
        # get mask and fields if need be
        fixed_mask = group.constraint.mask

        # try to allocate
        keys_and_masks = self._allocate_keys_and_masks(
            fixed_mask, None, self.__get_n_keys(group))

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(
                keys_and_masks, routing_infos, partition)

    def _allocate_fixed_fields(self, group, routing_infos):
        """
        :param ConstraintGroup group:
        :param RoutingInfo routing_infos:
        """
        fields = group.constraint.fields

        # try to allocate
        keys_and_masks = self._allocate_keys_and_masks(
            None, fields, self.__get_n_keys(group))

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(
                keys_and_masks, routing_infos, partition)

    @staticmethod
    def _update_routing_objects(keys_and_masks, routing_infos, group):
        """
        :param iterable(BaseKeyAndMask) keys_and_masks:
        :param RoutingInfo routing_infos:
        :param ConstraintGroup group:
        """
        # Allocate the routing information
        partition_info = PartitionRoutingInfo(keys_and_masks, group)
        routing_infos.add_partition_info(partition_info)

    def _allocate_fixed_keys_and_masks(self, keys_and_masks, fixed_mask):
        """ Allocate fixed keys and masks.

        :param iterable(BaseKeyAndMask) keys_and_masks:
            the fixed keys and masks combos
        :param fixed_mask: fixed mask
        :type fixed_mask: int or None
        :rtype: None
        :raises PacmanRouteInfoAllocationException:
        """
        # If there are fixed keys and masks, allocate them
        for key_and_mask in keys_and_masks:
            # If there is a fixed mask, check it doesn't clash
            if fixed_mask is not None and fixed_mask != key_and_mask.mask:
                raise PacmanRouteInfoAllocationException(
                    "Cannot meet conflicting constraints")

            # Go through the mask sets and allocate
            for key, n_keys in get_key_ranges(
                    key_and_mask.key, key_and_mask.mask):
                self._allocate_elements(key, n_keys)

    def _allocate_keys_and_masks(self, fixed_mask, fields, partition_n_keys,
                                 contiguous_keys=True):
        """
        :param fixed_mask:
        :type fixed_mask: int or None
        :param fields:
        :type fields: iterable(Field) or None
        :param int partition_n_keys:
        :param bool contiguous_keys:
        :rtype: list(BaseKeyAndMask)
        :raises PacmanRouteInfoAllocationException:
        """
        # If there isn't a fixed mask, generate a fixed mask based
        # on the number of keys required
        masks_available = [fixed_mask]
        if fixed_mask is None:
            masks_available = get_possible_masks(
                partition_n_keys, contiguous_keys=contiguous_keys)

        # For each usable mask, try all of the possible keys and
        # see if a match is possible
        mask_found = None
        key_found = None
        mask = None
        for mask in masks_available:
            logger.debug("Trying mask {} for {} keys",
                         hex(mask), partition_n_keys)

            key_found = None
            key_generator = KeyFieldGenerator(
                mask, fields, self._free_space_tracker)
            for key in key_generator:
                logger.debug("Trying key {}", hex(key))

                # Check if all the key ranges can be allocated
                matched_all = True
                index = 0
                for (base_key, n_keys) in get_key_ranges(key, mask):
                    logger.debug("Finding slot for {}, n_keys={}",
                                 hex(base_key), n_keys)
                    index = self._find_slot(base_key, lo=index)
                    logger.debug("Slot for {} is {}", hex(base_key), index)
                    if index is None:
                        matched_all = False
                        break
                    space = self._check_allocation(index, base_key, n_keys)
                    logger.debug("Space for {} is {}", hex(base_key), space)
                    if space is None:
                        matched_all = False
                        break

                if matched_all:
                    logger.debug("Matched key {}", hex(key))
                    key_found = key
                    break

            # If we found a matching key, store the mask that worked
            if key_found is not None:
                logger.debug("Matched mask {}", hex(mask))
                mask_found = mask
                break

        # If we found a working key and mask that can be assigned,
        # Allocate them
        if key_found is not None and mask_found is not None:
            for (base_key, n_keys) in get_key_ranges(key_found, mask):
                self._allocate_elements(base_key, n_keys)

            # If we get here, we can assign the keys to the edges
            return [BaseKeyAndMask(base_key=key_found, mask=mask)]

        raise PacmanRouteInfoAllocationException(
            "Could not find space to allocate keys")
