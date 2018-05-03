from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.log import FormatAdapter

# pacman imports
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.constraints.key_allocator_constraints\
    import AbstractKeyAllocatorConstraint, ShareKeyConstraint
from pacman.model.constraints.key_allocator_constraints\
    import FixedMaskConstraint, FixedKeyAndMaskConstraint
from pacman.model.constraints.key_allocator_constraints \
    import ContiguousKeyRangeContraint
from pacman.operations.routing_info_allocator_algorithms\
    .malloc_based_routing_allocator.key_field_generator \
    import KeyFieldGenerator
from pacman.model.routing_info \
    import RoutingInfo, BaseKeyAndMask, PartitionRoutingInfo
from pacman.utilities.utility_calls import \
    check_algorithm_can_support_constraints
from pacman.utilities.algorithm_utilities import ElementAllocatorAlgorithm
from pacman.utilities.algorithm_utilities import \
    routing_info_allocator_utilities as utilities
from pacman.exceptions \
    import PacmanConfigurationException, PacmanRouteInfoAllocationException

# general imports
import math
import logging

logger = FormatAdapter(logging.getLogger(__name__))


class MallocBasedRoutingInfoAllocator(ElementAllocatorAlgorithm):
    """ A Routing Info Allocation Allocator algorithm that keeps track of\
        free keys and attempts to allocate them as requested
    """

    __slots__ = []

    def __init__(self):
        super(MallocBasedRoutingInfoAllocator, self).__init__(
            [(0, 2 ** 32)])

    def __call__(self, machine_graph, n_keys_map, graph_mapper=None):
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
        utilities.check_types_of_edge_constraint(machine_graph)

        # final keys allocations
        routing_infos = RoutingInfo()

        # Get the edges grouped by those that require the same key
        (fixed_keys, shared_keys, fixed_masks, fixed_fields, flexi_fields,
         continuous, noncontinuous) = utilities.get_edge_groups(
             machine_graph, EdgeTrafficType.MULTICAST)

        # Even non-continuous keys will be continuous
        for group in noncontinuous:
            continuous.append(group)

        # Go through the groups and allocate keys
        progress = ProgressBar(
            machine_graph.n_outgoing_edge_partitions,
            "Allocating routing keys")

        # allocate the groups that have fixed keys
        for group in progress.over(fixed_keys, False):
            self._allocate_fixed_keys(group, routing_infos)

        for group in progress.over(fixed_masks, False):
            self._allocate_fixed_masks(group, n_keys_map, routing_infos)

        for group in progress.over(fixed_fields, False):
            self._allocate_fixed_fields(group, n_keys_map, routing_infos)

        if flexi_fields:
            raise PacmanConfigurationException(
                "MallocBasedRoutingInfoAllocator does not support FlexiField")

        for group in progress.over(shared_keys, False):
            self._allocate_share_key(group, routing_infos, n_keys_map)

        for group in continuous:
            self._allocate_continuous_groups(group, routing_infos, n_keys_map)

        progress.end()
        return routing_infos

    def _get_n_keys(self, group, n_keys_map):
        return max(
            n_keys_map.n_keys_for_partition(partition) for partition in group)

    def _allocate_continuous_groups(self, group, routing_infos, n_keys_map):
        keys_and_masks = self._allocate_keys_and_masks(
            None, None, self._get_n_keys(group, n_keys_map))
        for partition in group:
            self._update_routing_objects(
                keys_and_masks, routing_infos, partition)

    def _allocate_share_key(self, group, routing_infos, n_keys_map):
        keys_and_masks = self._allocate_keys_and_masks(
            None, None, self._get_n_keys(group, n_keys_map))

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(keys_and_masks, routing_infos,
                                         partition)

    def _allocate_fixed_keys(self, group, routing_infos):
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

    def _allocate_fixed_masks(self, group, n_keys_map, routing_infos):

        # get mask and fields if need be
        fixed_mask = group.constraint.mask

        # try to allocate
        keys_and_masks = self._allocate_keys_and_masks(
            fixed_mask, None, self._get_n_keys(group, n_keys_map))

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(
                keys_and_masks, routing_infos, partition)

    def _allocate_fixed_fields(self, group, n_keys_map, routing_infos):
        fields = group.constraint.fields

        # try to allocate
        keys_and_masks = self._allocate_keys_and_masks(
            None, fields, self._get_n_keys(group, n_keys_map))

        for partition in group:
            # update the pacman data objects
            self._update_routing_objects(
                keys_and_masks, routing_infos, partition)

    @staticmethod
    def _update_routing_objects(
            keys_and_masks, routing_infos, group):
        # Allocate the routing information
        partition_info = PartitionRoutingInfo(keys_and_masks, group)
        routing_infos.add_partition_info(partition_info)

    @staticmethod
    def _get_possible_masks(n_keys):
        """ Get the possible masks given the number of keys

        :param n_keys: The number of keys to generate a mask for
        """
        # TODO: Generate all the masks. Currently only the obvious mask with
        # the zeros at the bottom is generated but the zeros could actually be
        # anywhere
        n_zeros = int(math.ceil(math.log(n_keys, 2)))
        n_ones = 32 - n_zeros
        return [(((1 << n_ones) - 1) << n_zeros)]

    def _allocate_fixed_keys_and_masks(self, keys_and_masks, fixed_mask):
        """ allocate fixed keys and masks

        :param keys_and_masks: the fixed keys and masks combos
        :param fixed_mask: fixed mask
        :type fixed_mask: None or FixedMask object
        :rtype: None
        """
        # If there are fixed keys and masks, allocate them
        for key_and_mask in keys_and_masks:
            # If there is a fixed mask, check it doesn't clash
            if fixed_mask is not None and fixed_mask != key_and_mask.mask:
                raise PacmanRouteInfoAllocationException(
                    "Cannot meet conflicting constraints")

            # Go through the mask sets and allocate
            for key, n_keys in utilities.generate_key_ranges_from_mask(
                    key_and_mask.key, key_and_mask.mask):
                self.allocate_elements(key, n_keys)

    def _allocate_keys_and_masks(self, fixed_mask, fields, partition_n_keys):
        # If there isn't a fixed mask, generate a fixed mask based
        # on the number of keys required
        masks_available = [fixed_mask]
        if fixed_mask is None:
            masks_available = self._get_possible_masks(partition_n_keys)

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
                for (base_key, n_keys) in \
                        utilities.generate_key_ranges_from_mask(key, mask):
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
            for (base_key, n_keys) in utilities.generate_key_ranges_from_mask(
                    key_found, mask):
                self.allocate_elements(base_key, n_keys)

            # If we get here, we can assign the keys to the edges
            return [BaseKeyAndMask(base_key=key_found, mask=mask)]

        raise PacmanRouteInfoAllocationException(
            "Could not find space to allocate keys")
