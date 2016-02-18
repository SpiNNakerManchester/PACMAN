"""
VertexBasedRoutingInfoAllocator
"""

# pacman imports
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_contiguous_range_constraint import \
    KeyAllocatorContiguousRangeContraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_field_constraint import \
    KeyAllocatorFixedFieldConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_key_and_mask_constraint import \
    KeyAllocatorFixedKeyAndMaskConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_mask_constraint import \
    KeyAllocatorFixedMaskConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_flexi_field_constraint import \
    KeyAllocatorFlexiFieldConstraint
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.partition_routing_info import PartitionRoutingInfo
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities import \
    routing_info_allocator_utilities
from pacman import exceptions
from pacman.operations.routing_info_allocator_algorithms\
    .field_based_routing_allocator.rigs_bitfield import RigsBitField \
    as BitField
from pacman.utilities.utility_objs.flexi_field \
    import FlexiField, SUPPORTED_TAGS
from spinn_machine.progress_bar import ProgressBar
from pacman.utilities.algorithm_utilities import feild_based_system_utilities\
    as field_utilities

# general imports
import math

# hard coded values
APPLICATION_MASK_BIT = 0

# flag for usage for detecting the application field
APPLICATION_DIVIDER_FIELD_NAME = "APPLICATION_DIVIDER"


class VertexBasedRoutingInfoAllocator(object):
    """
    VertexBasedRoutingInfoAllocator
    """

    def __init__(self):
        # separate holders for the application flag if needed
        self._fixed_key_application_field_value = None
        self._fixed_mask_application_field_value = None
        self._flexi_field_application_field_values = dict()
        self._fixed_field_application_field_value = None

        # mapper between fields and constraints based data
        # TODO FIX THIS BIT OF HORRIBLE CODE USAGE
        self._field_mapper = dict()

    def __call__(self, partitionable_graph, graph_mapper, partitioned_graph,
                 n_keys_map):
        """

        :param partitionable_graph: The partitionable graph object
        :param graph_mapper: the mapping between the partitionable and
         partitioned graph
        :param partitioned_graph: the partitioned graph
        :param n_keys_map: the mapping between edges and n keys
        :return: routing infos objects and the routing tables for the
        spinnaker machine
        """
        progress_bar = ProgressBar(len(partitioned_graph.partitions) * 3,
                                   "Allocating routing keys")

        # ensure groups are stable and correct
        self._determine_groups(
            partitioned_graph, graph_mapper, partitionable_graph, n_keys_map,
            progress_bar)

        # define the key space
        bit_field_space = BitField(32)
        field_positions = set()

        # locate however many types of constraints there are
        seen_fields = field_utilities.deduce_types(partitioned_graph)
        progress_bar.update(len(partitioned_graph.partitions))

        if len(seen_fields) > 1:
            self._adds_application_field_to_the_fields(seen_fields)

        # handle the application space
        self._create_application_space_in_the_bit_field_space(
            bit_field_space, seen_fields, field_positions)

        # assign fields to positions in the space. if shits going to hit the
        # fan, its here
        bit_field_space.assign_fields()

        # get positions of the flexi fields:
        self._assign_flexi_field_positions(
            bit_field_space, seen_fields, field_positions)

        # create routing_info_allocator
        routing_info = RoutingInfo()
        routing_tables = MulticastRoutingTables()
        seen_mask_instances = 0

        # extract keys and masks for each edge from the bitfield
        for partition in partitioned_graph.partitions:
            # get keys and masks
            keys_and_masks, seen_mask_instances = \
                self._extract_keys_and_masks_from_bit_field(
                    partition, bit_field_space, n_keys_map, seen_mask_instances)

            # update routing info for each edge in the partition
            partition_info = PartitionRoutingInfo(keys_and_masks, partition)
            routing_info.add_partition_info(partition_info)

            # update the progress bar again
            progress_bar.update()
        progress_bar.end()

        return {'routing_infos': routing_info,
                'fields': field_positions}

    def _assign_flexi_field_positions(
            self, bit_field_space, seen_fields, field_positions):
        """
        searches though seen fields and if there's a flexi field
        :param bit_field_space: the bit field space system
        :param seen_fields: the fields been seen
        :param field_positions: the set of fields that have been allocated
        over the entire key space
        :return: None
        """

        # locate the application field if it exists
        application_field, application_field_spare_values = \
            self._locate_application_field(seen_fields)

        for field in seen_fields:
            if (field != field_utilities.TYPES_OF_FIELDS.FIXED_MASK.name and
                    field != field_utilities.TYPES_OF_FIELDS.FIXED_KEY.name and
                    field != field_utilities.TYPES_OF_FIELDS.FIXED_FIELD.name):
                if application_field is None:
                    field_positions = \
                        self._assign_flexi_field_positions_recursive(
                            bit_field_space, field, seen_fields,
                            field_positions)
                else:
                    inputs = dict()
                    inputs[APPLICATION_DIVIDER_FIELD_NAME] = \
                        self._flexi_field_application_field_values[field]
                    this_bit_field_space = bit_field_space(**inputs)
                    field_positions = \
                        self._assign_flexi_field_positions_recursive(
                            this_bit_field_space, field, seen_fields,
                            field_positions)

    def _assign_flexi_field_positions_recursive(
            self, bit_field_space, field, fields, field_positions):
        bit_field_field = bit_field_space.get_field(field)
        low = bit_field_field.start_at
        hi = low + bit_field_field.length
        field_positions.add((hi, low))

        for field_instance in fields[field]:
            # only carry on if there's more to create
            if len(fields[field][field_instance]) > 0:
                inputs = dict()
                inputs[field] = field_instance.value
                this_bit_field_space = bit_field_space(**inputs)

                # deal with next level hierarchy
                for nested_field in fields[field][field_instance]:
                    new_field_positions = \
                        self._assign_flexi_field_positions_recursive(
                            this_bit_field_space, nested_field,
                            fields[field][field_instance], field_positions)
                    for field_position in new_field_positions:
                        field_positions.add(field_position)
        return field_positions

    def _adds_application_field_to_the_fields(self, seen_fields):
        """
        tries to determine what the field spaces and values are for the
        application field needed to separate the different hierarchy fields and
        adds it to the fields in current existence.
        :param seen_fields: the types of fields needed to get this simulation
        operating correctly
        :return: None
        """

        application_field = None
        success = False

        required_bits = int(math.ceil(math.log(len(seen_fields), 2)))
        if field_utilities.TYPES_OF_FIELDS.FIXED_KEY.name in seen_fields:
            success = self._fixed_key_application_field_allocation(
                seen_fields, required_bits)
        else:
            if field_utilities.TYPES_OF_FIELDS.FIXED_MASK.name in seen_fields:
                success = self._fixed_mask_application_field_allocation(
                    seen_fields, application_field, required_bits)
        return success

    def _fixed_key_application_field_allocation(
            self, seen_fields, required_bits):
        """

        :param seen_fields:
        :param required_bits:
        :return:
        """
        fixed_keys = seen_fields[field_utilities.TYPES_OF_FIELDS.FIXED_KEY.name]
        if len(fixed_keys) == 1:
            found = False
            searching = True

            # generate the bit generator for the fixed key
            fixed_key = fixed_keys[0]
            fields = field_utilities.convert_mask_into_fields(fixed_key.mask)
            bit_generator = self._generate_bits_that_satisfy_constraints(
                fields, required_bits)

            # search for a set of bits which will work for the fixed key and
            # any fixed masks that exist
            while searching:

                # use the fixed mask functionality to generate the fields for
                #  the fixed key
                application_field, new_fields = \
                    self._update_fixed_mask_field_set(
                        bit_generator, fixed_key.key)
                seen_fields[field_utilities.TYPES_OF_FIELDS.FIXED_KEY.name] \
                    = list()
                seen_fields[field_utilities.TYPES_OF_FIELDS.FIXED_KEY.name]\
                    .append((fixed_key, new_fields))

                # if there's fixed masks as well, ensure they work with the
                field_name = field_utilities.TYPES_OF_FIELDS.FIXED_MASK.name
                if field_name in seen_fields:
                    success = self._fixed_mask_application_field_allocation(
                        seen_fields, application_field, required_bits)
                    if success:
                        searching = False
                        found = True
                else:
                    searching = False
                    found = True
            return found
        else:  # more than 1 fixed key exists

            # generate the  bit generator for the first key, as this is the
            # premise of all the other keys to meet
            found = False
            searching = True
            new_fixed_keys = list()

            # generate the bit generator for the fixed key
            fixed_key = fixed_keys[0]
            fields = field_utilities.convert_mask_into_fields(fixed_key.mask)
            bit_generator = self._generate_bits_that_satisfy_constraints(
                fields, required_bits)

            # search till we find a application field which meets all
            # requirements
            while searching:
                application_field, new_fields = \
                    self._update_fixed_mask_field_set(bit_generator)

                # check that all the other fields can meet the value for this
                # field's application field value
                valid = True
                for fixed_key_index in range(1, len(fixed_keys)):
                    fixed_key = fixed_keys[fixed_key_index]
                    fields = \
                        field_utilities.convert_mask_into_fields(fixed_key.mask)
                    application_field_value = \
                        self._determine_fixed_mask_application_field_value(
                            fields[0].value, application_field.hi,
                            application_field.lo)
                    if application_field_value != application_field.value:
                        valid = False

                # if valid, update all fields
                if valid:
                    # set the first one which has had its already generated
                    new_fixed_keys.append((fixed_keys[0], new_fields))

                    # set the rest of the fields which need computing
                    for fixed_key_index in range(1, len(fixed_keys)):
                        fixed_key = fixed_keys[fixed_key_index]
                        fields = field_utilities.convert_mask_into_fields(
                            fixed_key.mask)
                        # create new fields
                        new_fields = self.\
                            _adjust_fixed_mask_fields_for_application_field(
                                fields[0].value, application_field.hi,
                                application_field.value)

                        # update the fields for this fixed mask
                        new_fixed_keys.append((fixed_key, new_fields))

                    field_name = field_utilities.TYPES_OF_FIELDS.FIXED_MASK.name
                    if field_name in seen_fields:
                        success = self._fixed_mask_application_field_allocation(
                            seen_fields, application_field, required_bits)
                        if success:
                            searching = False
                            found = True

                            # update the fixed keys fields
                            seen_fields[field_utilities.TYPES_OF_FIELDS.
                                        FIXED_KEY.name] = new_fixed_keys
                    else:
                        searching = False
                        found = True

                        # update the fixed keys fields
                        seen_fields[field_utilities.TYPES_OF_FIELDS.
                                    FIXED_KEY.name] = new_fixed_keys
            return found

    def _fixed_mask_application_field_allocation(
            self, seen_fields, application_field, required_bits):
        """

        :param seen_fields:
        :param application_field:
        :param required_bits:
        :return: bool true if it was able to adjust to the field,
        false otherwise
        """
        fixed_mask_masks = \
            seen_fields[field_utilities.TYPES_OF_FIELDS.FIXED_MASK.name]
        if len(fixed_mask_masks) > 1:

            # generate the  bit generator for the first field, as this is the
            # premise of all the other fields to meet
            keys = list(fixed_mask_masks.keys)
            fields = fixed_mask_masks[keys[0]]
            searching = True
            found = False
            bit_generator = self._generate_bits_that_satisfy_constraints(
                fields, required_bits)

            # search till we find a application field which meets all
            # requirements
            while searching:
                application_field, new_fields = \
                    self._update_fixed_mask_field_set(bit_generator)

                # check that all the other fields can meet the value for this
                # field's application field value
                valid = True
                keys = list(fixed_mask_masks.keys)
                no_keys = len(keys)
                for field_key_index in range(1, no_keys):
                    fields = fixed_mask_masks[keys[field_key_index]]
                    application_field_value = \
                        self._determine_fixed_mask_application_field_value(
                            fields[0].value, application_field.hi,
                            application_field.lo)
                    if application_field_value != application_field.value:
                        valid = False

                # if valid, update all fields
                if valid:

                    # set the first one which has had its already generated
                    keys = list(fixed_mask_masks.keys())
                    fixed_mask_masks[keys[0]] = new_fields

                    # set the rest of the fields which need computing
                    for field_key_index in range(1, no_keys):
                        fields = fixed_mask_masks[keys[field_key_index]]

                        # create new fields
                        new_fields = self.\
                            _adjust_fixed_mask_fields_for_application_field(
                                fields[0].value, application_field.hi,
                                application_field.value)

                        # update the fields for this fixed mask
                        fixed_mask_masks[keys[field_key_index]] = new_fields

                    # update searcher to state that we'vefound what
                    #  we've been looking for
                    searching = False
                    found = True

            # if exited but not found a solution, tell parent function
            if not found:
                return False

        else:  # one fixed mask field
            if application_field is None:  # no fixed keys seen
                keys = list(fixed_mask_masks.keys())
                fields = fixed_mask_masks[keys[0]]
                bit_generator = \
                    self._generate_bits_that_satisfy_constraints(
                        fields, required_bits)
                _, new_fields = \
                    self._update_fixed_mask_field_set(bit_generator)

                # update the seen fields object with new fields
                keys = list(fixed_mask_masks.keys())
                fixed_mask_masks[keys[0]] = new_fields

            else:  # fixed key seen so application field exists
                keys = list(fixed_mask_masks.keys())
                fields = fixed_mask_masks[keys[0]]

                # get the application field value for a application field
                application_field_value = \
                    self._determine_fixed_mask_application_field_value(
                        fields[0].value, application_field.hi,
                        application_field.lo)

                # check that the application for the fixed mask is different
                # than the fixed key mask, if not return false stating it could
                # not carry on with this application field
                if application_field_value == application_field.value:
                    return False

                # create new fields
                new_fields = \
                    self._adjust_fixed_mask_fields_for_application_field(
                        fields[0].value, application_field.hi,
                        application_field_value)

                # update the fields for this fixed mask
                keys = list(fixed_mask_masks.keys())
                fixed_mask_masks[keys[0]] = new_fields

        # state that we did fix the fixed mask stuff with this application field
        return True

    def _update_fixed_mask_field_set(self, bit_generator, fixed_key=None):
        """
        updates the first mask's field set so that it has a application field
        with the correct value and the odl fields are adjusted to take into
        account the loss of a number of bits
        :param bit_generator: the generator which can provide different sets
        of bits usable for the application field
        :return: the application field that was created
        """
        # get next attempt
        (bit_hi, bit_lo, original_mask) = bit_generator.next()

        # determine value of the application field
        if fixed_key is None:
            application_field_value = \
                self._determine_fixed_mask_application_field_value(
                    original_mask, bit_hi, bit_lo)
        else:
            application_field_value = \
                self._determine_fixed_mask_application_field_value(
                    fixed_key, bit_hi, bit_lo)

        # adjust the fields to reflect new application field scopes
        fields = self._adjust_fixed_mask_fields_for_application_field(
            original_mask, bit_hi, application_field_value)

        # locate the application field bit in the new fields and adjust the
        # tags to be routing, name to APPLICATION_DIVIDER_FIELD_NAME and the
        #  value to the located application value
        distance_in_bits = bit_hi - bit_lo
        application_field = None
        if distance_in_bits == 1:
            for field in fields:
                if field.hi == bit_hi and field.lo == bit_hi:
                    field.value = application_field_value
                    field.tag = SUPPORTED_TAGS.ROUTING.name
                    field.name = APPLICATION_DIVIDER_FIELD_NAME
                    application_field = field
        else:
            for field in fields:
                if field.hi == bit_hi and field.lo == bit_lo:
                    field.value = application_field_value
                    field.tag = SUPPORTED_TAGS.ROUTING.name
                    field.name = APPLICATION_DIVIDER_FIELD_NAME
                    application_field = field

        return application_field, fields

    @staticmethod
    def _adjust_fixed_mask_fields_for_application_field(
            original_mask, bit_hi, bit_values):
        """
        Takes the old mask and the application field specs and makes a set
        of new fields to compensate for the placement of the application field
        :param original_mask: the old mask used by the fields
        :param bit_hi: the point where the application space starts
        :param bit_values: the value being used by fixed masks for the
        application field
        :return: the adjusted fields
        """
        if bit_values == 0:
            bit_values = 1
        value = bit_values << bit_hi
        # invert the mask
        inverted_value = ~value
        # make new mask from inverted and original mask
        new_mask = original_mask & inverted_value
        # convert new mask into fields
        fields = field_utilities.convert_mask_into_fields(new_mask)
        # readjust the fields to link to the original mask (needed for mapping
        # later on)
        for field in fields:
            field.value = original_mask
        return fields

    def _extract_keys_and_masks_from_bit_field(
            self, partition, bit_field_space, n_keys_map, seen_mask_instances):
        """
        takes the bit field space and a partition and locates the keys and masks
        for that partition given all its constraints
        :param partition: the partition to extract keys and masks for
        :param bit_field_space: the bit field space
        :param n_keys_map: the edge to n_keys map
        :param seen_mask_instances: a count of how many fixed mask instances
        have been seen, so that it can increment the routing part of the
        fixed mask fields.
        :return: the routing keys and masks for the partition and the number
        of seen fixed masks instances
        """
        routing_keys_and_masks = list()
        application_keys_and_masks = list()
        fixed_key_constraints = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedKeyAndMaskConstraint)
        fixed_mask_constraints = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedMaskConstraint)
        fixed_field_constraints = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFixedFieldConstraint)
        flexi_field_constraints = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorFlexiFieldConstraint)
        continuous_constraints = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorContiguousRangeContraint)

        if len(fixed_key_constraints) > 0:
            fixed_keys_fields = \
                self._field_mapper[fixed_key_constraints[0].keys_and_masks[0]]

            # tracker for iterator fields
            range_based_fixed_key_fields = list()

            # add the app field (must exist in this situation)
            inputs = dict()
            inputs[APPLICATION_DIVIDER_FIELD_NAME] = \
                self._fixed_key_application_field_value

            # handle the inputs for static parts of the mask
            for fixed_key_field in fixed_keys_fields:
                app_field_space = bit_field_space(**inputs)
                tag = list(app_field_space.get_tags(
                    str(fixed_key_field.name)))[0]
                if tag == SUPPORTED_TAGS.ROUTING.name:
                    inputs[str(fixed_key_field.name)] = fixed_key_field.value
                elif tag == SUPPORTED_TAGS.APPLICATION.name:
                    range_based_fixed_key_fields.append(fixed_key_field)
                else:
                    raise exceptions.PacmanConfigurationException(
                        "Don't know this tag field, sorry")

            if len(range_based_fixed_key_fields) > 1:
                raise exceptions.PacmanConfigurationException(
                    "Im not designed to work with multiple ranged based "
                    "fields for a fixed key. please fix and try again")

            # get n keys from n_keys_map for the range based mask part
            n_keys = n_keys_map.n_keys_for_partition(partition)

            # generate keys
            for key_index in range(0, n_keys):
                inputs[str(range_based_fixed_key_fields[0].name)] = key_index
                # routing keys and masks
                routing_key = bit_field_space(**inputs).get_value(
                    tag=SUPPORTED_TAGS.ROUTING.name)
                routing_mask = bit_field_space(**inputs).get_mask(
                    tag=SUPPORTED_TAGS.ROUTING.name)
                routing_keys_and_masks.append(BaseKeyAndMask(routing_key,
                                                             routing_mask))

                # application keys and masks
                application_key = bit_field_space(**inputs).get_value(
                    tag=SUPPORTED_TAGS.APPLICATION.name)
                application_mask = bit_field_space(**inputs).get_mask(
                    tag=SUPPORTED_TAGS.APPLICATION.name)
                application_keys_and_masks.append(BaseKeyAndMask(
                    application_key, application_mask))
        elif len(fixed_mask_constraints) > 0:
            # get constraint and its fields
            fixed_mask_constraint_mask = fixed_mask_constraints[0].mask
            fixed_mask_fields = self._field_mapper[fixed_mask_constraint_mask]

            # tracker for iterator fields
            range_based_fixed_mask_fields = list()

            # add the app field (must exist in this situation)
            inputs = dict()
            inputs [APPLICATION_DIVIDER_FIELD_NAME] = \
                self._fixed_mask_application_field_value

            # handle the inputs for static parts of the mask
            for fixed_mask_field in fixed_mask_fields:
                app_field_space = bit_field_space(**inputs)
                tag = list(app_field_space.get_tags(str(fixed_mask_field)))[0]
                if tag == SUPPORTED_TAGS.ROUTING.name:
                    inputs[str(fixed_mask_field)] = seen_mask_instances
                elif tag == SUPPORTED_TAGS.APPLICATION.name:
                    range_based_fixed_mask_fields.append(fixed_mask_field)
                else:
                    raise exceptions.PacmanConfigurationException(
                        "I don't recognise this tag. sorry")

            if len(range_based_fixed_mask_fields) > 1:
                raise exceptions.PacmanConfigurationException(
                    "Im not designed to work with multiple ranged based "
                    "fields for a fixed mask. please fix and try again")

            # get n keys from n_keys_map for the range based mask part
            n_keys = n_keys_map.n_keys_for_partition(partition)

            # generate keys
            for key_index in range(0, n_keys):
                inputs[str(range_based_fixed_mask_fields[0])] = key_index
                # routing keys and masks
                routing_key = bit_field_space(**inputs).get_value(
                    tag=SUPPORTED_TAGS.ROUTING.name)
                routing_mask = bit_field_space(**inputs).get_mask(
                    tag=SUPPORTED_TAGS.ROUTING.name)
                routing_keys_and_masks.append(BaseKeyAndMask(routing_key,
                                                             routing_mask))

                # application keys and masks
                application_key = bit_field_space(**inputs).get_value(
                    tag=SUPPORTED_TAGS.APPLICATION.name)
                application_mask = bit_field_space(**inputs).get_mask(
                    tag=SUPPORTED_TAGS.APPLICATION.name)
                application_keys_and_masks.append(BaseKeyAndMask(
                    application_key, application_mask))

            # update the seen mask instances so the next one gets a new key
            seen_mask_instances += 1

        elif len(fixed_field_constraints) > 0:
            # TODO need to fill this out
            raise exceptions.PacmanConfigurationException(
                "I have not filled this bit out yet. sorry")
        elif len(flexi_field_constraints) > 0:
            inputs = dict()

            # if there's a application field, add the value
            if len(self._flexi_field_application_field_values) != 0:
                inputs[APPLICATION_DIVIDER_FIELD_NAME] = \
                    self._flexi_field_application_field_values[
                        flexi_field_constraints[0].fields[0].name]

            # collect flexi fields by group
            range_based_fixed_mask_fields = list()
            for field in flexi_field_constraints[0].fields:
                if field.value is not None:
                    inputs[field.name] = field.value
                else:
                    range_based_fixed_mask_fields.append(field)

            # if the set contains a range_based flexi field do search
            if len(range_based_fixed_mask_fields) != 0:
                routing_keys_and_masks, application_keys_and_masks = \
                    self._handle_set_of_flexi_range_fields(
                        range_based_fixed_mask_fields, bit_field_space,
                        routing_keys_and_masks, application_keys_and_masks,
                        inputs, 0)

            else:  # no range, just grab the key and value
                key = bit_field_space(**inputs).get_value()
                mask = bit_field_space(**inputs).get_mask()
                routing_keys_and_masks.append(BaseKeyAndMask(key, mask))

        # if there's a continuous constraint check, check the keys for
        # continuity
        if len(continuous_constraints) != 0:
            are_continuous = self._check_keys_are_continuous(
                application_keys_and_masks)
            if not are_continuous:
                raise exceptions.PacmanConfigurationException(
                    "These keys returned from the bitfield are"
                    "not continuous. Therefore cannot be used")

            # if continuous, we only need the first key, so drop the rest
            routing_keys_and_masks = routing_keys_and_masks[0:1]

        # return keys and masks
        return routing_keys_and_masks, seen_mask_instances

    @staticmethod
    def _check_keys_are_continuous(keys_and_masks):
        """
        searches though the keys and masks and checks if they are all continuous

        :param keys_and_masks: the keys to check if they are continuous
        :return: true if they are continuous, false otherwise
        """
        last_key = None
        for keys_and_mask in keys_and_masks:
            if last_key is None:
                last_key = keys_and_mask.key
            else:
                if last_key + 1 != keys_and_mask.key:
                    return False
                last_key = keys_and_mask.key
        return True

    def _handle_set_of_flexi_range_fields(
            self, range_based_flexi_fields, bit_field_space,
            routing_keys_and_masks, application_keys_and_masks, inputs,
            position):
        """
        takes a set of flexi fields which are range based and deduces the
        routing keys and masks for the set
        :param range_based_flexi_fields: the set of range based flexi fields
        :param bit_field_space: the bit field space
        :param routing_keys_and_masks: set of routing keys and masks built from
        previous iterations
        :param application_keys_and_masks: the application keys and masks from
        previous iterations
        :param inputs: parameters used by the bit field to get keys
        :param position: the position within the set (used for exit condition)
        :return: routing keys and application keys for the flexi field set
        """

        for value in range(0,
                           range_based_flexi_fields[position].instance_n_keys):
            inputs[range_based_flexi_fields[position].name] = value
            if position < len(range_based_flexi_fields):
                # routing keys and masks
                routing_key = bit_field_space(**inputs).get_value(
                    tag=SUPPORTED_TAGS.ROUTING.name)
                routing_mask = bit_field_space(**inputs).get_mask(
                    tag=SUPPORTED_TAGS.ROUTING.name)
                routing_keys_and_masks.append(BaseKeyAndMask(routing_key,
                                                             routing_mask))

                # application keys and masks
                application_key = bit_field_space(**inputs).get_value(
                    tag=SUPPORTED_TAGS.APPLICATION.name)
                application_mask = bit_field_space(**inputs).get_mask(
                    tag=SUPPORTED_TAGS.APPLICATION.name)
                application_keys_and_masks.append(BaseKeyAndMask(
                    application_key, application_mask))
            else:

                # not at the end, keep iterating but add the results from
                # the iterations before going back upwards
                position += 1
                other_routing_keys_and_masks, \
                    other_application_keys_and_masks = \
                    self._handle_set_of_flexi_range_fields(
                        range_based_flexi_fields, bit_field_space,
                        routing_keys_and_masks, application_keys_and_masks,
                        inputs, position)

                # add keys before going upwards
                routing_keys_and_masks.extend(other_routing_keys_and_masks)
                application_keys_and_masks.extend(
                    other_application_keys_and_masks)

        # exit this iteration
        return routing_keys_and_masks, application_keys_and_masks

    def _create_application_space_in_the_bit_field_space(
            self, bit_field_space, fields, field_positions):
        """
        takes the fields seen and adjusted for bitfield and the bitfield
        object and builds the fields for being assigned to kys and masks
        :param bit_field_space: th bit field space
        :param fields: the fields which have been adjusted accordingly to
        work in the bit field scope
        :param field_positions: The positions of all fields seen
        :return:
        """
        # locate the application field if it exists
        application_field, application_field_spare_values = \
            self._locate_application_field(fields)

        # create the application based field if its not none
        if application_field is not None:
            length = (application_field.hi - application_field.lo) + 1

            # add field to positions
            field_positions.add((application_field.hi, application_field.lo))

            # add field to bit field
            bit_field_space.add_field(
                application_field.name, length, application_field.lo,
                tags=SUPPORTED_TAGS.ROUTING.name)

        # iterate though the fields, adding fields to the system
        for field in fields:
            # handle fixed mask fields
            if field == field_utilities.TYPES_OF_FIELDS.FIXED_MASK.name:
                fixed_fields = \
                    fields[field_utilities.TYPES_OF_FIELDS.FIXED_MASK.name]
                for fixed_field_key in fixed_fields:

                    # create the top level bt field space for this set
                    fixed_field_list = fixed_fields[fixed_field_key]
                    fixed_field_application_field_value = \
                        self._locate_field_value_by_name(
                            fixed_field_list, APPLICATION_DIVIDER_FIELD_NAME)
                    internal_field_space = self._create_internal_field_space(
                        bit_field_space, fixed_field_application_field_value,
                        application_field)

                    # iterate though rest of the fields adding them to the
                    #  lower position field space
                    for fixed_field in fixed_field_list:
                        if fixed_field.name != APPLICATION_DIVIDER_FIELD_NAME:
                            length = (fixed_field.hi - fixed_field.lo) + 1

                            # add to field positions
                            field_positions.add((fixed_field.hi,
                                                 fixed_field.lo))

                            # add to bit field
                            internal_field_space.add_field(
                                "{}".format(fixed_field.name), length,
                                fixed_field.lo, fixed_field.tag)
                            if fixed_field.value not in self._field_mapper:
                                self._field_mapper[fixed_field.value] = list()
                            self._field_mapper[fixed_field.value].append(
                                fixed_field.name)
                        else:
                            self._fixed_mask_application_field_value = \
                                fixed_field.value

            # handle fixed field
            elif field == field_utilities.TYPES_OF_FIELDS.FIXED_FIELD.name:
                # TODO need to check this bit out
                raise exceptions.PacmanConfigurationException(
                    "I have not completed this bit. sorry")

            # handle fixed key fields
            elif field == field_utilities.TYPES_OF_FIELDS.FIXED_KEY.name:
                fixed_keys = \
                    fields[field_utilities.TYPES_OF_FIELDS.FIXED_KEY.name]

                # handle application field
                first_fields = fixed_keys[0][1]
                application_field_value = self._locate_field_value_by_name(
                    first_fields, APPLICATION_DIVIDER_FIELD_NAME)
                internal_bit_map_space = self._create_internal_field_space(
                    bit_field_space, application_field_value, application_field)

                # record the fixed key application field value for future use
                self._fixed_key_application_field_value = \
                    application_field_value

                # handel the rest of the fields
                for (key_and_mask, fixed_key_fields) in fixed_keys:
                    for fixed_key_field in fixed_key_fields:
                        if (fixed_key_field.name !=
                                APPLICATION_DIVIDER_FIELD_NAME):
                            length = (fixed_key_field.hi -
                                      fixed_key_field.lo) + 1

                            # add field to field positions
                            field_positions.add((fixed_key_field.ki,
                                                 fixed_key_field.lo))

                            # add field to bit field space
                            internal_bit_map_space.add_field(
                                str(fixed_key_field.name), length,
                                fixed_key_field.lo, fixed_key_field.tag)

                            if key_and_mask not in self._field_mapper:
                                self._field_mapper[key_and_mask] = list()

                            # add field for the field mapper
                            self._field_mapper[key_and_mask].append(
                                fixed_key_field)
                            # set the value for the field
                            inputs = dict()

                            # deduce the value for the key for this field
                            value = self._deduce_key_value_for_field(
                                key_and_mask.key, fixed_key_field)
                            fixed_key_field.value = value
                            inputs[str(fixed_key_field.name)] = value

                            # update value in bit field space
                            internal_bit_map_space(**inputs)

            else:  # handle flexi field stuff
                if application_field is not None:

                    # create a new bit field where everything is linked off a
                    # sub internal app field
                    internal_value = application_field_spare_values[0]
                    application_field_spare_values.remove(internal_value)
                    internal_bit_field_space = \
                        self._create_internal_field_space(
                            bit_field_space, internal_value, application_field)

                    self._flexi_field_application_field_values[field] = \
                        internal_value

                    # handle the flexi fields
                    self._create_flexi_field_space_in_the_bit_field_space(
                        internal_bit_field_space, field, fields)
                else:
                    self._create_flexi_field_space_in_the_bit_field_space(
                        bit_field_space, field, fields)

    def _locate_application_field(self, fields):
        """
        searches through the fields looking for the application field, and
        when its found, deduces whats left for space space for other fields
        :param fields: the set of field types and the fields
        :return: the application field and the spare values of the field
        """
        application_field = None
        application_field_spare_values = None
        # search for the field with the correct tag
        for field in fields:
            # if a fixed mask field, locate correct application field and value
            if field == field_utilities.TYPES_OF_FIELDS.FIXED_MASK.name:
                fixed_fields = \
                    fields[field_utilities.TYPES_OF_FIELDS.FIXED_MASK.name]
                for fixed_field_key in fixed_fields:
                    fixed_field_list = fixed_fields[fixed_field_key]
                    for fixed_field in fixed_field_list:
                        # if the field is the correct field, mark and deduce
                        # usable values
                        if fixed_field.name == APPLICATION_DIVIDER_FIELD_NAME:
                            if application_field is None:
                                application_field = fixed_field
                                application_field_spare_values = \
                                    self._deduce_application_field_space(
                                        application_field)
                            else:
                                application_field_spare_values.remove(
                                    fixed_field.value)
            elif field == field_utilities.TYPES_OF_FIELDS.FIXED_KEY.name:
                fixed_keys_fields = \
                    fields[field_utilities.TYPES_OF_FIELDS.FIXED_KEY.name]
                for (_, fixed_key_fields) in fixed_keys_fields:
                    for fixed_key_field in fixed_key_fields:
                        if (fixed_key_field.name ==
                                APPLICATION_DIVIDER_FIELD_NAME):
                            if application_field is None:
                                application_field = fixed_key_field
                                application_field_spare_values = \
                                    self._deduce_application_field_space(
                                        application_field)
                            else:
                                application_field_spare_values.remove(
                                    fixed_key_field.value)
            elif field == field_utilities.TYPES_OF_FIELDS.FIXED_FIELD.name:
                # TODO NEED TO COMPLETE THIS BIT
                raise exceptions.PacmanConfigurationException(
                    "Sorry, Ive not filled this bit in yet")
        return application_field, application_field_spare_values

    def _create_flexi_field_space_in_the_bit_field_space(
            self, bit_field_space, field, fields):
        """
        creates the fields in the bit field space for the flexi fields
        :param bit_field_space: the bit field space
        :param field: the field that needs placing into the bitfield space
        :param fields: ???????
        :return: None
        """
        # field must be a flexi field, work accordingly
        example_entry = self._check_entries_are_tag_consistent(fields, field)
        if example_entry.tag is None:
            bit_field_space.add_field(field)
        else:
            bit_field_space.add_field(field, tags=example_entry.tag)

        for field_instance in fields[field]:
            # only carry on if there's more to create
            if len(fields[field][field_instance]) > 0:

                # create next level
                internal_bit_field = self._create_internal_field_space(
                    bit_field_space, field_instance.value, field_instance)

                # deal with next level hierarchy
                for nested_field in fields[field][field_instance]:
                    self._create_flexi_field_space_in_the_bit_field_space(
                        internal_bit_field, nested_field,
                        fields[field][field_instance])

            # bottom level
            if field_instance.instance_n_keys is not None:
                for value in range(0, field_instance.instance_n_keys):
                    self._create_internal_field_space(
                        bit_field_space, value, field_instance)

    def _determine_groups(self, subgraph, graph_mapper, partitionable_graph,
                          n_keys_map, progress_bar):
        """

        :param subgraph:
        :param graph_mapper:
        :param partitionable_graph:
        :param n_keys_map:
        :return:
        """

        routing_info_allocator_utilities.check_types_of_edge_constraint(
            subgraph)

        for partition in subgraph.partitions:
            fixed_key_constraints = \
                utility_calls.locate_constraints_of_type(
                    partition.constraints,
                    KeyAllocatorFixedKeyAndMaskConstraint)
            fixed_mask_constraints = \
                utility_calls.locate_constraints_of_type(
                    partition.constraints,
                    KeyAllocatorFixedMaskConstraint)
            fixed_field_constraints = \
                utility_calls.locate_constraints_of_type(
                    partition.constraints,
                    KeyAllocatorFixedFieldConstraint)

            if (len(fixed_key_constraints) == 0
                    and len(fixed_mask_constraints) == 0
                    and len(fixed_field_constraints) == 0):
                self.add_field_constraints(
                    partition, graph_mapper, partitionable_graph, n_keys_map)
            progress_bar.update()

    @staticmethod
    def _determine_fixed_mask_application_field_value(mask, bit_hi, bit_lo):
        """
        determines the value of the application field for a given mask
        :param mask: the mask to deduce the value for
        :param bit_hi: the bit high index for where the application field
        finishes
        :param bit_lo: the bit lo index for where the application field starts
        :return: the value for the application for this mask
        """
        bit_value = mask >> int(bit_lo)
        mask = int(math.pow((bit_hi - bit_lo), 2))
        bit_value &= mask
        return bit_value

    @staticmethod
    def _generate_bits_that_satisfy_constraints(
            fixed_mask_fields, required_bits):
        """
        generator for getting valid bits from the first fixed mask
        :param fixed_mask_fields: the fields from this fixed mask
        :param required_bits: the number of bits required to match the types
        :type required_bits: int
        :return: the hi and lo bit index for where the region can exist,
         as well as the original mask this generator is working on.
        """
        routing_fields = list()

        # locate fields valid for generating collections
        field = None
        for field in fixed_mask_fields:
            if field.tag == SUPPORTED_TAGS.ROUTING.name:
                routing_fields.append(field)

        # sort fields based on hi
        routing_fields.sort(key=lambda rout_field: rout_field.hi)

        # locate next set of bits to yield to higher function
        for routing_field in routing_fields:
            if routing_field.hi - routing_field.lo >= required_bits:
                current_hi = routing_field.hi
                while (current_hi - required_bits) > routing_field.lo:
                    yield (current_hi, current_hi - required_bits, field.value)
                    current_hi -= 1

    @staticmethod
    def _deduce_key_value_for_field(key, fixed_key_field):
        """

        :param key:
        :param fixed_key_field:
        :return:
        """
        new_key = key >> fixed_key_field.lo
        mask = int(math.pow(2, ((fixed_key_field.hi -
                                 fixed_key_field.lo) + 1))) - 1
        new_key &= mask
        return new_key

    @staticmethod
    def _deduce_application_field_space(application_field):
        """
        given a application field, deduces the spare spaces available to it
        :param application_field: the application field in question
        :return: the spare values
        """

        # get length of field
        length = (application_field.hi - application_field.lo) + 1
        application_field_spare_values = list()

        # build available values
        for value in range(0, ((2 ^ length) -1)):
            application_field_spare_values.append(value)

        # remove the one this application field is built from
        application_field_spare_values.remove(application_field.value)
        return application_field_spare_values

    @staticmethod
    def _check_entries_are_tag_consistent(fields, field):
        """
        checks that the tags of the fields are consistent with each other
        :param fields: the set of fields which could have tags
        :param field: field its comparing against
        :return: the first field
        """
        first = None
        for field_instance in fields[field]:
            if first is None:
                first = field_instance
            elif field_instance.tag != first.tag:
                raise exceptions.PacmanConfigurationException(
                    "Two fields with the same id, but with different tags. "
                    "This is deemed an error and therefore please fix before"
                    "trying again. thanks you")
        return first

    @staticmethod
    def add_field_constraints(
            partition, graph_mapper, partitionable_graph, n_keys_map):
        """
        searches though the subgraph adding field constraints for the key
         allocator
        :param partition:
        :param graph_mapper:
        :param partitionable_graph:
        :param n_keys_map:
        :return:
        """

        fields = list()

        verts = list(partitionable_graph.vertices)
        subvert = partition.edges[0].pre_subvertex
        vertex = graph_mapper.get_vertex_from_subvertex(subvert)
        subverts = list(graph_mapper.get_subvertices_from_vertex(vertex))

        # pop based flexi field
        fields.append(FlexiField(
            flexi_field_name="Population", value=verts.index(vertex),
            tag=SUPPORTED_TAGS.ROUTING.name, nested_level=0))

        # sub pop flexi field
        fields.append(FlexiField(
            flexi_field_name="SubPopulation{}".format(verts.index(vertex)),
            tag=SUPPORTED_TAGS.ROUTING.name, value=subverts.index(subvert),
            nested_level=1))

        fields.append(FlexiField(
            flexi_field_name="POP({}:{})Keys"
            .format(verts.index(vertex), subverts.index(subvert)),
            tag=SUPPORTED_TAGS.APPLICATION.name,
            instance_n_keys=n_keys_map.n_keys_for_partition(partition),
            nested_level=2))

        # add constraint to the subedge
        partition.add_constraint(KeyAllocatorFlexiFieldConstraint(fields))

    @staticmethod
    def _create_internal_field_space(higher_space, field_value, field):
        """

        :param higher_space:
        :param field_value:
        :param field:
        :return:
        """
        inputs = dict()
        inputs[field.name] = field_value
        return higher_space(**inputs)

    @staticmethod
    def _locate_field_value_by_name(field_list, field_name):
        """

        :param field_list:
        :param field_name:
        :return:
        """
        for field in field_list:
            if field.name == field_name:
                return field.value
        return None
