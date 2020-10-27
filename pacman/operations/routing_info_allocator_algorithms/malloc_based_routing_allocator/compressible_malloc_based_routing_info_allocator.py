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

from collections import defaultdict, OrderedDict
import logging
from six import iteritems, itervalues
from spinn_utilities.log import FormatAdapter
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, FixedKeyFieldConstraint,
    FixedMaskConstraint, FixedKeyAndMaskConstraint,
    ContiguousKeyRangeContraint)
from pacman.model.graphs.common import EdgeTrafficType
from .key_field_generator import KeyFieldGenerator
from pacman.model.routing_info import (
    RoutingInfo, BaseKeyAndMask, PartitionRoutingInfo)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints, locate_constraints_of_type,
    get_key_ranges)
from pacman.utilities.algorithm_utilities import ElementAllocatorAlgorithm
from pacman.utilities.algorithm_utilities.routing_info_allocator_utilities \
    import (check_types_of_edge_constraint, get_edge_groups)
from pacman.exceptions import PacmanRouteInfoAllocationException
from .utils import get_possible_masks

logger = FormatAdapter(logging.getLogger(__name__))


class CompressibleMallocBasedRoutingInfoAllocator(ElementAllocatorAlgorithm):
    """ A Routing Info Allocation Allocator algorithm that keeps track of
        free keys and attempts to allocate them as requested, but that also
        looks at routing tables in an attempt to make things more compressible

    :param MachineGraph machine_graph:
    :param AbstractMachinePartitionNKeysMap n_keys_map:
    :param MulticastRoutingTableByPartition routing_tables:
    :rtype: RoutingInfo
    """

    __slots__ = []

    def __init__(self):
        super(CompressibleMallocBasedRoutingInfoAllocator, self).__init__(
            0, 2 ** 32)

    def __call__(self, machine_graph, n_keys_map, routing_tables):
        """
        :param MachineGraph machine_graph:
        :param AbstractMachinePartitionNKeysMap n_keys_map:
        :param MulticastRoutingTableByPartition routing_tables:
        :rtype: RoutingInfo
        """
        # check that this algorithm supports the constraints
        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[
                FixedMaskConstraint,
                FixedKeyAndMaskConstraint,
                ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # verify that no edge has more than 1 of a constraint ,and that
        # constraints are compatible
        check_types_of_edge_constraint(machine_graph)

        routing_infos = RoutingInfo()

        # Get the edges grouped by those that require the same key
        (fixed_keys, _shared_keys, fixed_masks, fixed_fields, continuous,
         noncontinuous) = \
            get_edge_groups(machine_graph, EdgeTrafficType.MULTICAST)

        # Even non-continuous keys will be continuous
        continuous.extend(noncontinuous)

        # Go through the groups and allocate keys
        progress = ProgressBar(
            machine_graph.n_outgoing_edge_partitions,
            "Allocating routing keys")

        # allocate the groups that have fixed keys
        for group in progress.over(fixed_keys, False):
            # Get any fixed keys and masks from the group and attempt to
            # allocate them
            fixed_mask = None
            fixed_key_and_mask_constraint = locate_constraints_of_type(
                group.constraints, FixedKeyAndMaskConstraint)[0]

            # attempt to allocate them
            self._allocate_fixed_keys_and_masks(
                fixed_key_and_mask_constraint.keys_and_masks, fixed_mask)

            # update the pacman data objects
            self._update_routing_objects(
                fixed_key_and_mask_constraint.keys_and_masks, routing_infos,
                group)
            continuous.remove(group)

        for group in progress.over(fixed_masks, False):
            # get mask and fields if need be
            fixed_mask = locate_constraints_of_type(
                group.constraints, FixedMaskConstraint)[0].mask

            fields = None
            if group in fixed_fields:
                fields = locate_constraints_of_type(
                    group.constraints, FixedKeyFieldConstraint)[0].fields
                fixed_fields.remove(group)

            # try to allocate
            keys_and_masks = self._allocate_keys_and_masks(
                fixed_mask, fields, n_keys_map.n_keys_for_partition(group))

            # update the pacman data objects
            self._update_routing_objects(keys_and_masks, routing_infos, group)
            continuous.remove(group)

        for group in progress.over(fixed_fields, False):
            fields = locate_constraints_of_type(
                group.constraints, FixedKeyFieldConstraint)[0].fields

            # try to allocate
            keys_and_masks = self._allocate_keys_and_masks(
                None, fields, n_keys_map.n_keys_for_partition(group))

            # update the pacman data objects
            self._update_routing_objects(keys_and_masks, routing_infos, group)
            continuous.remove(group)

        # Sort the rest of the groups, using the routing tables for guidance
        # Group partitions by those which share routes in any table
        partition_groups = OrderedDict()
        routers = reversed(sorted(
            routing_tables.get_routers(),
            key=lambda item: len(routing_tables.get_entries_for_router(
                item[0], item[1]))))
        for x, y in routers:

            # Find all partitions that share a route in this table
            partitions_by_route = defaultdict(OrderedSet)
            routing_table = routing_tables.get_entries_for_router(x, y)
            for partition, entry in iteritems(routing_table):
                if partition in continuous:
                    entry_hash = sum(
                        1 << i
                        for i in entry.link_ids)
                    entry_hash += sum(
                        1 << (i + 6)
                        for i in entry.processor_ids)
                    partitions_by_route[entry_hash].add(partition)

            for entry_hash, partitions in iteritems(partitions_by_route):
                found_groups = list()
                for partition in partitions:
                    if partition in partition_groups:
                        found_groups.append(partition_groups[partition])

                if not found_groups:
                    # If no group was found, create a new one
                    for partition in partitions:
                        partition_groups[partition] = partitions

                elif len(found_groups) == 1:
                    # If a single other group was found, merge it
                    for partition in partitions:
                        found_groups[0].add(partition)
                        partition_groups[partition] = found_groups[0]

                else:
                    # Merge the groups
                    new_group = partitions
                    for group in found_groups:
                        for partition in group:
                            new_group.add(partition)
                    for partition in new_group:
                        partition_groups[partition] = new_group

        # Sort partitions by largest group
        continuous = list(OrderedSet(
            tuple(group) for group in itervalues(partition_groups)))

        for group in reversed(sorted(continuous, key=len)):
            for partition in progress.over(group, False):
                keys_and_masks = self._allocate_keys_and_masks(
                    None, None, n_keys_map.n_keys_for_partition(partition))

                # update the pacman data objects
                self._update_routing_objects(
                    keys_and_masks, routing_infos, partition)

        progress.end()
        return routing_infos

    @staticmethod
    def _update_routing_objects(
            keys_and_masks, routing_infos, partition):
        """
        :param iterable(BaseKeyAndMask) keys_and_masks:
        :param RoutingInfo routing_infos:
        :param OutgoingEdgePartition partition:
        """
        # Allocate the routing information
        partition_info = PartitionRoutingInfo(keys_and_masks, partition)
        routing_infos.add_partition_info(partition_info)

    def _allocate_fixed_keys_and_masks(self, keys_and_masks, fixed_mask):
        """ Allocate fixed keys and masks

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
