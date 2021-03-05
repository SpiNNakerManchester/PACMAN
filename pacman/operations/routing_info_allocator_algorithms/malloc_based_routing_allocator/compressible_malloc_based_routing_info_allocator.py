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
from spinn_utilities.log import FormatAdapter
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, FixedKeyFieldConstraint,
    FixedMaskConstraint, FixedKeyAndMaskConstraint,
    ContiguousKeyRangeContraint)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints, locate_constraints_of_type)
from pacman.utilities.algorithm_utilities.routing_info_allocator_utilities \
    import (
        check_types_of_edge_constraint, get_mulitcast_edge_groups)
from .utils import RoutingInfoAllocator

logger = FormatAdapter(logging.getLogger(__name__))


class CompressibleMallocBasedRoutingInfoAllocator(RoutingInfoAllocator):
    """ A Routing Info Allocation Allocator algorithm that keeps track of\
        free keys and attempts to allocate them as requested, but that also\
        looks at routing tables in an attempt to make things more compressible
    """

    __slots__ = []

    def __init__(self):
        super().__init__(0, 2 ** 32)

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

        # Get the edges grouped by those that require the same key
        (fixed_keys, _shared_keys, fixed_masks, fixed_fields, continuous,
         noncontinuous) = get_mulitcast_edge_groups(machine_graph)

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
            fixed_key_and_mask = locate_constraints_of_type(
                group.constraints, FixedKeyAndMaskConstraint)[0]

            # attempt to allocate them
            self._allocate_fixed_keys_and_masks(
                fixed_key_and_mask.keys_and_masks)

            # update the pacman data objects
            self._update_routing_objects(
                fixed_key_and_mask.keys_and_masks, group)
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
            self._update_routing_objects(keys_and_masks, group)
            continuous.remove(group)

        for group in progress.over(fixed_fields, False):
            fields = locate_constraints_of_type(
                group.constraints, FixedKeyFieldConstraint)[0].fields

            # try to allocate
            keys_and_masks = self._allocate_keys_and_masks(
                None, fields, n_keys_map.n_keys_for_partition(group))

            # update the pacman data objects
            self._update_routing_objects(keys_and_masks, group)
            continuous.remove(group)

        for group in self._group_remaining(routing_tables, continuous):
            for partition in progress.over(group, False):
                keys_and_masks = self._allocate_keys_and_masks(
                    None, None, n_keys_map.n_keys_for_partition(partition))

                # update the pacman data objects
                self._update_routing_objects(keys_and_masks, partition)

        progress.end()
        # Return the allocation (built in our utility superclass)
        return self._get_allocated_routing_info()

    def _group_remaining(self, routing_tables, continuous):
        """
        Sort the rest of the groups, using the routing tables for guidance.
        Group partitions by those which share routes in any table.

        :param MulticastRoutingTableByPartition routing_tables:
        :param list(AbstractSingleSourcePartition) continuous:
        :return: the sorted list of groups
        :rtype: list(tuple(AbstractSingleSourcePartition))
        """
        routers = sorted(
            routing_tables.get_routers(),
            reverse=True,
            key=lambda item: len(routing_tables.get_entries_for_router(*item)))
        partition_groups = OrderedDict()
        continuous = frozenset(continuous)
        for x, y in routers:

            # For all partitions that share a route in this table...
            for partitions in self.__group_partitions_by_route(
                    routing_tables.get_entries_for_router(x, y), continuous):
                found_groups = [
                    partition_groups[partition]
                    for partition in partitions
                    if partition in partition_groups]

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
        grouped_partitions = OrderedSet(
            tuple(group) for group in partition_groups.values())
        return sorted(grouped_partitions, reverse=True, key=len)

    def __group_partitions_by_route(self, routing_table, continuous):
        """
        :param routing_table:
        :type routing_table:
            dict(AbstractSingleSourcePartition,
            MulticastRoutingTableByPartitionEntry)
        :param frozenset(AbstractSingleSourcePartition) continuous:
        :rtype: ~collections.abc.Iterable(set(AbstractSingleSourcePartition))
        """
        partitions_by_route = defaultdict(OrderedSet)
        for partition, entry in routing_table.items():
            if partition in continuous:
                # Compute the spinnaker route as the hash
                entry_hash = sum(1 << i for i in entry.link_ids)
                entry_hash += sum(1 << (i + 6) for i in entry.processor_ids)
                partitions_by_route[entry_hash].add(partition)
        return partitions_by_route.values()
