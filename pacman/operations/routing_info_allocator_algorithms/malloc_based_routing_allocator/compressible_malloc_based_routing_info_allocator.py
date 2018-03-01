# pacman imports
from pacman.model.constraints.key_allocator_constraints\
    import AbstractKeyAllocatorConstraint, FixedKeyFieldConstraint
from pacman.model.constraints.key_allocator_constraints\
    import FixedMaskConstraint
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.constraints.key_allocator_constraints \
    import FixedKeyAndMaskConstraint, ContiguousKeyRangeContraint
from .key_field_generator import KeyFieldGenerator
from pacman.model.routing_info \
    import RoutingInfo, BaseKeyAndMask, PartitionRoutingInfo
from pacman.utilities.utility_calls import \
    check_algorithm_can_support_constraints, locate_constraints_of_type, \
    compress_from_bit_array, expand_to_bit_array
from pacman.utilities.algorithm_utilities import ElementAllocatorAlgorithm
from pacman.utilities.algorithm_utilities.routing_info_allocator_utilities \
    import check_types_of_edge_constraint, get_edge_groups
from pacman.exceptions import \
    PacmanConfigurationException, PacmanRouteInfoAllocationException

from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet

# general imports
import math
import numpy
import logging
from collections import defaultdict
from collections import OrderedDict
from spinn_utilities.log import FormatAdapter

logger = FormatAdapter(logging.getLogger(__name__))


class CompressibleMallocBasedRoutingInfoAllocator(ElementAllocatorAlgorithm):
    """ A Routing Info Allocation Allocator algorithm that keeps track of\
        free keys and attempts to allocate them as requested, but that also\
        looks at routing tables in an attempt to make things more compressible
    """

    __slots__ = []

    def __init__(self):
        super(CompressibleMallocBasedRoutingInfoAllocator, self).__init__(
            0, 2 ** 32)

    def __call__(self, machine_graph, n_keys_map, routing_tables):
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
        (fixed_keys, _shared_keys, fixed_masks, fixed_fields, flexi_fields,
         continuous, noncontinuous) = \
            get_edge_groups(machine_graph, EdgeTrafficType.MULTICAST)
        if flexi_fields:
            raise PacmanConfigurationException(
                "MallocBasedRoutingInfoAllocator does not support FlexiField")

        # Even non-continuous keys will be continuous
        for group in noncontinuous:
            continuous.add(group)

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
            for partition, entry in routing_table.iteritems():
                if partition in continuous:
                    entry_hash = sum(
                        1 << i
                        for i in entry.out_going_links)
                    entry_hash += sum(
                        1 << (i + 6)
                        for i in entry.out_going_processors)
                    partitions_by_route[entry_hash].add(partition)

            for entry_hash, partitions in partitions_by_route.iteritems():
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
            tuple(group) for group in partition_groups.itervalues()))

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
            keys_and_masks, routing_infos, group):
        # Allocate the routing information
        partition_info = PartitionRoutingInfo(keys_and_masks, group)
        routing_infos.add_partition_info(partition_info)

    @staticmethod
    def _get_key_ranges(key, mask):
        """ Get a generator of base_key, n_keys pairs that represent ranges
            allowed by the mask

        :param key: The base key
        :param mask: The mask
        """
        unwrapped_mask = expand_to_bit_array(mask)
        first_zeros = list()
        remaining_zeros = list()
        pos = len(unwrapped_mask) - 1

        # Keep the indices of the first set of zeros
        while pos >= 0 and unwrapped_mask[pos] == 0:
            first_zeros.append(pos)
            pos -= 1

        # Find all the remaining zeros
        while pos >= 0:
            if unwrapped_mask[pos] == 0:
                remaining_zeros.append(pos)
            pos -= 1

        # Loop over 2^len(remaining_zeros) to produce the base key,
        # with n_keys being 2^len(first_zeros)
        n_sets = 2 ** len(remaining_zeros)
        n_keys = 2 ** len(first_zeros)
        unwrapped_key = expand_to_bit_array(key)
        for value in xrange(n_sets):
            generated_key = numpy.copy(unwrapped_key)
            unwrapped_value = expand_to_bit_array(value)[
                -len(remaining_zeros):]
            generated_key[remaining_zeros] = unwrapped_value
            yield compress_from_bit_array(generated_key), n_keys

    @staticmethod
    def _get_possible_masks(n_keys):
        """ Get the possible masks given the number of keys

        :param n_keys: The number of keys to generate a mask for
        """

        # TODO: Generate all the masks. Currently only the obvious mask with
        # the zeros at the bottom is generated but the zeros could actually be
        # anywhere.
        n_zeros = int(math.ceil(math.log(n_keys, 2)))
        n_ones = 32 - n_zeros
        return [((1 << n_ones) - 1) << n_zeros]

    def _allocate_fixed_keys_and_masks(self, keys_and_masks, fixed_mask):
        # If there are fixed keys and masks, allocate them
        for key_and_mask in keys_and_masks:

            # If there is a fixed mask, check it doesn't clash
            if fixed_mask is not None and fixed_mask != key_and_mask.mask:
                raise PacmanRouteInfoAllocationException(
                    "Cannot meet conflicting constraints")

            # Go through the mask sets and allocate
            for key, n_keys in self._get_key_ranges(
                    key_and_mask.key, key_and_mask.mask):
                self._allocate_elements(key, n_keys)

    def _allocate_keys_and_masks(self, fixed_mask, fields, partition_n_keys):
        # If there isn't a fixed mask, generate a fixed mask based on the
        # number of keys required
        masks_available = [fixed_mask]
        if fixed_mask is None:
            masks_available = self._get_possible_masks(partition_n_keys)

        # For each usable mask, try all of the possible keys and see if a
        # match is possible
        mask_found = None
        key_found = None
        mask = None
        for mask in masks_available:
            logger.debug("Trying mask {} for {} keys",
                         hex(mask), partition_n_keys)

            key_found = None
            for key in KeyFieldGenerator(
                    mask, fields, self._free_space_tracker):
                logger.debug("Trying key {}", hex(key))

                # Check if all the key ranges can be allocated
                matched_all = True
                index = 0
                for (base_key, n_keys) in self._get_key_ranges(key, mask):
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
        # allocate them. Otherwise raise an exception
        if key_found is None or mask_found is None:
            raise PacmanRouteInfoAllocationException(
                "Could not find space to allocate keys")

        for (base_key, n_keys) in self._get_key_ranges(key_found, mask):
            self._allocate_elements(base_key, n_keys)
        # If we get here, we can assign the keys to the edges
        return [BaseKeyAndMask(base_key=key_found, mask=mask)]
