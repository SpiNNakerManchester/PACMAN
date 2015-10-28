"""
MallocBasedRoutingInfoAllocator
"""

# pacman imports
from pacman.model.constraints.abstract_constraints\
    .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_field_constraint import \
    KeyAllocatorFixedFieldConstraint
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_fixed_mask_constraint import KeyAllocatorFixedMaskConstraint
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from pacman.operations.routing_info_allocator_algorithms\
    .malloc_based_routing_allocator.key_field_generator \
    import KeyFieldGenerator
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_fixed_key_and_mask_constraint \
    import KeyAllocatorFixedKeyAndMaskConstraint
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities.element_allocator_algorithm import \
    ElementAllocatorAlgorithm
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from pacman.utilities.algorithm_utilities import \
    routing_info_allocator_utilities
from pacman import exceptions

# general imports
import math
import numpy
import logging
logger = logging.getLogger(__name__)


class MallocBasedRoutingInfoAllocator(ElementAllocatorAlgorithm):
    """ A Routing Info Allocation Allocator algorithm that keeps track of
        free keys and attempts to allocate them as requested
    """

    def __init__(self):
        ElementAllocatorAlgorithm.__init__(self, 0, math.pow(2, 32))

    def __call__(self, subgraph, n_keys_map, routing_paths):

        # check that this algorithm supports the constraints
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=subgraph.partitions,
            supported_constraints=[
                KeyAllocatorFixedMaskConstraint,
                KeyAllocatorFixedKeyAndMaskConstraint,
                KeyAllocatorContiguousRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        # verify that no edge has more than 1 of a constraint ,and that
        # constraints are compatible
        routing_info_allocator_utilities.\
            check_types_of_edge_constraint(subgraph)

        routing_tables = MulticastRoutingTables()
        routing_infos = RoutingInfo()
        
        # Get the partitioned edges grouped by those that require the same key
        (fixed_key_groups, fixed_mask_groups, fixed_field_groups,
         flexi_field_groups, continious_groups, none_continious_groups) = \
            routing_info_allocator_utilities.get_edge_groups(subgraph)

        # warn users that none continious keys are going to work in
        # continious mode
        for group in none_continious_groups:
            logger.warning(
                "The subvertex {} has a set of edges {} "
                "which has not been requested to have continous keys. The "
                "algorithm will anyway allocate keys in a continious"
                " manner.".format(group[0].pre_subvertex, group))
            continious_groups.append(group)

        # Go through the groups and allocate keys
        progress_bar = ProgressBar(
            len(subgraph.partitions), "Allocating routing keys")

        # allocate the groups that have fixed keys
        for group in fixed_key_groups:  # fixed keys groups

            # check n keys consistent through partition
            routing_info_allocator_utilities.\
                check_n_keys_are_same_through_partition(group, n_keys_map)

            # Get any fixed keys and masks from the group and attempt to
            # allocate them
            fixed_mask = None
            fixed_key_and_mask_constraint = \
                utility_calls.locate_constraints_of_type(
                    group.constraints, KeyAllocatorFixedKeyAndMaskConstraint)[0]

            # attempt to allocate them
            self._allocate_fixed_keys_and_masks(
                fixed_key_and_mask_constraint.keys_and_masks, fixed_mask)

            # update the pacman data objects
            self._update_routing_objects(
                fixed_key_and_mask_constraint.keys_and_masks, routing_infos,
                routing_paths, group, routing_tables)

            continious_groups.remove(group)

            progress_bar.update()

        for group in fixed_mask_groups:  # fixed mask groups

            # check n keys consistent through partition
            routing_info_allocator_utilities.\
                check_n_keys_are_same_through_partition(group, n_keys_map)

            # get mask and fields if need be
            fixed_mask = utility_calls.locate_constraints_of_type(
                group.constraints, KeyAllocatorFixedMaskConstraint)[0].mask

            fields = None
            if group in fixed_field_groups:
                fields = utility_calls.locate_constraints_of_type(
                    group.constraints,
                    KeyAllocatorFixedFieldConstraint)[0].fields
                fixed_field_groups.remove(group)

            # try to allocate
            keys_and_masks = self._allocate_keys_and_masks(
                fixed_mask, fields,
                n_keys_map.n_keys_for_partitioned_edge(group.edges[0]))

            # update the pacman data objects
            self._update_routing_objects(
                keys_and_masks, routing_infos, routing_paths, group,
                routing_tables)

            continious_groups.remove(group)

            progress_bar.update()

        for group in fixed_field_groups:
            fields = utility_calls.locate_constraints_of_type(
                group.constraints,
                KeyAllocatorFixedFieldConstraint)[0].fields
            # try to allocate
            keys_and_masks = self._allocate_keys_and_masks(
                None, fields,
                n_keys_map.n_keys_for_partitioned_edge(group.edges[0]))

            # update the pacman data objects
            self._update_routing_objects(
                keys_and_masks, routing_infos, routing_paths, group,
                routing_tables)

            continious_groups.remove(group)

            progress_bar.update()

        for group in flexi_field_groups:
            raise exceptions.PacmanConfigurationException(
                "I cant handle these. please fix and try again")

        for group in continious_groups:
            keys_and_masks = self._allocate_keys_and_masks(
                None, None,
                n_keys_map.n_keys_for_partitioned_edge(group.edges[0]))

            # update the pacman data objects
            self._update_routing_objects(
                keys_and_masks, routing_infos, routing_paths, group,
                routing_tables)


        progress_bar.end()
        return {'routing_infos': routing_infos,
                'routing_tables': routing_tables}

    @staticmethod
    def _update_routing_objects(
            keys_and_masks, routing_infos, routing_paths, group,
            routing_tables):
        """

        :param keys_and_masks:
        :param routing_infos:
        :param routing_paths:
        :param group:
        :param routing_tables:
        :return:
        """

        # Allocate the routing information
        for edge in group.edges:
            subedge_info = SubedgeRoutingInfo(keys_and_masks, edge)
            routing_infos.add_subedge_info(subedge_info)

            # update routing tables with entries
            routing_info_allocator_utilities.add_routing_key_entries(
                routing_paths, subedge_info, edge, routing_tables)

    @staticmethod
    def _get_key_ranges(key, mask):
        """ Get a generator of base_key, n_keys pairs that represent ranges
            allowed by the mask

        :param key: The base key
        :param mask: The mask
        """
        unwrapped_mask = utility_calls.expand_to_bit_array(mask)
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
        unwrapped_key = utility_calls.expand_to_bit_array(key)
        for value in xrange(n_sets):
            generated_key = numpy.copy(unwrapped_key)
            unwrapped_value = utility_calls.expand_to_bit_array(value)[
                -len(remaining_zeros):]
            generated_key[remaining_zeros] = unwrapped_value
            yield utility_calls.compress_from_bit_array(generated_key), n_keys

    @staticmethod
    def _get_possible_masks(n_keys):
        """ Get the possible masks given the number of keys

        :param n_keys: The number of keys to generate a mask for
        """

        # TODO: Generate all the masks - currently only the obvious
        # mask with the zeros at the bottom is generated but the zeros
        # could actually be anywhere
        n_zeros = int(math.ceil(math.log(n_keys, 2)))
        n_ones = 32 - n_zeros
        return [(((1 << n_ones) - 1) << n_zeros)]

    def _allocate_fixed_keys_and_masks(self, keys_and_masks, fixed_mask):

        # If there are fixed keys and masks, allocate them
        for key_and_mask in keys_and_masks:

            # If there is a fixed mask, check it doesn't clash
            if fixed_mask is not None and fixed_mask != key_and_mask.mask:
                raise exceptions.PacmanRouteInfoAllocationException(
                    "Cannot meet conflicting constraints")

            # Go through the mask sets and allocate
            for key, n_keys in self._get_key_ranges(
                    key_and_mask.key, key_and_mask.mask):
                self._allocate_elements(key, n_keys)

    def _allocate_keys_and_masks(self, fixed_mask, fields, edge_n_keys):

        # If there isn't a fixed mask, generate a fixed mask based
        # on the number of keys required
        masks_available = [fixed_mask]
        if fixed_mask is None:
            masks_available = self._get_possible_masks(edge_n_keys)

        # For each usable mask, try all of the possible keys and
        # see if a match is possible
        mask_found = None
        key_found = None
        mask = None
        for mask in masks_available:

            logger.debug("Trying mask {} for {} keys".format(hex(mask),
                                                             edge_n_keys))

            key_found = None
            key_generator = KeyFieldGenerator(mask, fields,
                                              self._free_space_tracker)
            for key in key_generator:

                logger.debug("Trying key {}".format(hex(key)))

                # Check if all the key ranges can be allocated
                matched_all = True
                index = 0
                for (base_key, n_keys) in self._get_key_ranges(key, mask):
                    logger.debug("Finding slot for {}, n_keys={}".format(
                        hex(base_key), n_keys))
                    index = self._find_slot(base_key, lo=index)
                    logger.debug("Slot for {} is {}".format(
                        hex(base_key), index))
                    if index is None:
                        matched_all = False
                        break
                    space = self._check_allocation(index, base_key,
                                                   n_keys)
                    logger.debug("Space for {} is {}".format(
                        hex(base_key), space))
                    if space is None:
                        matched_all = False
                        break

                if matched_all:
                    logger.debug("Matched key {}".format(hex(key)))
                    key_found = key
                    break

            # If we found a matching key, store the mask that worked
            if key_found is not None:
                logger.debug("Matched mask {}".format(hex(mask)))
                mask_found = mask
                break

        # If we found a working key and mask that can be assigned,
        # Allocate them
        if key_found is not None and mask_found is not None:
            for (base_key, n_keys) in self._get_key_ranges(
                    key_found, mask):
                self._allocate_elements(base_key, n_keys)

            # If we get here, we can assign the keys to the edges
            keys_and_masks = list([BaseKeyAndMask(base_key=key_found,
                                                  mask=mask)])
            return keys_and_masks

        raise exceptions.PacmanRouteInfoAllocationException(
            "Could not find space to allocate keys")

    def _allocate_flexi_fields(self, fields, n_keys):
        """

        :param fields:
        :param n_keys:
        :return:
        """
        # If there isn't a fixed mask, generate a fixed mask based
        # on the number of keys required
        masks_available = self._get_possible_masks(n_keys)

        # For each usable mask, try all of the possible keys and
        # see if a match is possible
        mask_found = None
        key_found = None
        mask = None
        for mask in masks_available:

            logger.debug(
                "Trying mask {} for {} keys".format(hex(mask), n_keys))

            key_found = None
            key_generator = KeyFlexiFieldGenerator(mask, fields,
                                                   self._free_space_tracker)
            for key in key_generator:

                logger.debug("Trying key {}".format(hex(key)))

                # Check if all the key ranges can be allocated
                matched_all = True
                index = 0
                for (base_key, n_keys) in self._get_key_ranges(key, mask):
                    logger.debug("Finding slot for {}, n_keys={}".format(
                        hex(base_key), n_keys))
                    index = self._find_slot(base_key, lo=index)
                    logger.debug("Slot for {} is {}".format(
                        hex(base_key), index))
                    if index is None:
                        matched_all = False
                        break
                    space = self._check_allocation(index, base_key,
                                                   n_keys)
                    logger.debug("Space for {} is {}".format(
                        hex(base_key), space))
                    if space is None:
                        matched_all = False
                        break

                if matched_all:
                    logger.debug("Matched key {}".format(hex(key)))
                    key_found = key
                    break

            # If we found a matching key, store the mask that worked
            if key_found is not None:
                logger.debug("Matched mask {}".format(hex(mask)))
                mask_found = mask
                break

        # If we found a working key and mask that can be assigned,
        # Allocate them
        if key_found is not None and mask_found is not None:
            for (base_key, n_keys) in self._get_key_ranges(
                    key_found, mask):
                self._allocate_elements(base_key, n_keys)

            # If we get here, we can assign the keys to the edges
            keys_and_masks = list([BaseKeyAndMask(base_key=key_found,
                                                  mask=mask)])
            return keys_and_masks

        raise exceptions.PacmanRouteInfoAllocationException(
            "Could not find space to allocate keys")

