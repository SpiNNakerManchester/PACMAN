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
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask

from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities import \
    routing_info_allocator_utilities
from pacman import exceptions
from pacman.utilities.utility_objs.field import Field
from pacman.utilities.utility_objs.flexi_field \
    import FlexiField, SUPPORTED_TAGS
# swiped from rig currently.
from pacman.operations.routing_info_allocator_algorithms.\
    field_based_routing_allocator.rigs_bitfield import \
    RigsBitField

# general imports
from enum import Enum
import uuid
import math

# hard coded values
NUM_BITS_IN_ROUTING = 31
ROUTING_MASK_BIT = 1
APPLICATION_MASK_BIT = 0
START_OF_ROUTING_KEY_POSITION = 0

TYPES_OF_FIELDS = Enum(
    value="TYPES_OF_FIELDS",
    names=[("FIXED_MASK", 0),
           ("FIXED_KEY", 1),
           ("FIXED_FIELD", 2)])

APPLICATION_DIVIDER_FIELD_NAME = "APPLICATION_DIVIDER"
FLEXI_APP_FLAG = "FLEXI_APP_FIELD_VALUE"
FIXED_MASK_APP_FLAG = "FIXED_MASK_APP_FIELD_VALUE"
FIXED_KEY_APP_FLAG = ""
FIXED_MASK_FLAG = "FIXED_MASK"


class VertexBasedRoutingInfoAllocator(object):
    """
    VertexBasedRoutingInfoAllocator
    """


    def __call__(self, partitionable_graph, graph_mapper, subgraph, n_keys_map,
                 routing_paths):
        """

        :param partitionable_graph:
        :param graph_mapper:
        :param subgraph:
        :param n_keys_map:
        :param routing_paths:
        :return:
        """

        # ensure groups are stable and correct
        self._determine_groups(subgraph, graph_mapper, partitionable_graph,
                               n_keys_map)

        # define the key space
        bit_field_space = RigsBitField(32)

        # locate however many types of constrants there are
        seen_fields = self._deduce_types(subgraph)

        uses_application_field = False
        if len(seen_fields) > 1:
            self._locate_application_field_space(seen_fields)
            uses_application_field = True

        field_mapper = dict()
        # handle the application space
        self._handle_application_space(
            bit_field_space, seen_fields, field_mapper, bit_field_space)

        # assgin fields to positions in the space. if shits going to hit the
        # fan, its here
        bit_field_space.assign_fields()

        # create routing_info_allocator
        routing_info = RoutingInfo()
        routing_tables = MulticastRoutingTables()

        seen_mask_instances = 0

        # extract keys and masks for each edge from the bitfield
        for partition in subgraph.partitions:
            # get keys and masks
            keys_and_masks, seen_mask_instances = self._discover_keys_and_masks(
                partition, bit_field_space, n_keys_map, uses_application_field,
                field_mapper, seen_mask_instances)

            # update routing info for each edge in the partition
            for edge in partition.edges:
                sub_edge_info = SubedgeRoutingInfo(keys_and_masks, edge)
                routing_info.add_subedge_info(sub_edge_info)

                # update routing tables with entries
                routing_info_allocator_utilities.add_routing_key_entries(
                    routing_paths, sub_edge_info, edge, routing_tables)

        return {'routing_infos': routing_info,
                'routing_tables': routing_tables}

    def _locate_application_field_space(self, seen_fields):
        required_bits = int(math.ceil(math.log(len(seen_fields), 2)))
        if TYPES_OF_FIELDS.FIXED_KEY.name in seen_fields:
            fixed_keys = seen_fields[TYPES_OF_FIELDS.FIXED_KEY.name]
            # use yield and genrator here

        else:
            if TYPES_OF_FIELDS.FIXED_MASK.name in seen_fields:
                fixed_mask_masks = seen_fields[TYPES_OF_FIELDS.FIXED_MASK.name]
                if len(fixed_mask_masks) > 1:
                    keys = list(fixed_mask_masks.keys)
                    fields = fixed_mask_masks[keys[0]]
                    searching = True
                    bit_generator = \
                        self._generate_bits_that_satisfy_contraints(
                            fields, required_bits)
                    while not searching:
                        searching = True
                    print "AHHH"

                else:
                    keys = list(fixed_mask_masks.keys())
                    fields = fixed_mask_masks[keys[0]]
                    bit_generator = \
                        self._generate_bits_that_satisfy_contraints(
                            fields, required_bits)
                    self._deal_with_first_fixed_mask_fields(
                        fixed_mask_masks, bit_generator)

    def _deal_with_first_fixed_mask_fields(
            self, fixed_mask_masks, bit_generator):
        keys = list(fixed_mask_masks.keys())
        (bit_hi, bit_lo, original_mask) = bit_generator.next()
        bit_values = self._deduce_bit_value(original_mask, bit_hi, bit_lo)
        fields = \
            self._reduce_fixed_field_scope(original_mask, bit_hi, bit_values)
        distance_in_bits = bit_hi - bit_lo
        if distance_in_bits == 1:
            for field in fields:
                if field.hi == bit_hi and field.lo == bit_hi:
                    field.value = bit_values
                    field.tag = SUPPORTED_TAGS.ROUTING.name
                    field.name = APPLICATION_DIVIDER_FIELD_NAME
        else:
            for field in fields:
                if field.hi == bit_hi and field.lo == bit_lo:
                    field.value = bit_values
                    field.tag = SUPPORTED_TAGS.ROUTING.name
                    field.name = APPLICATION_DIVIDER_FIELD_NAME
        fixed_mask_masks[keys[0]] = fields

    def _reduce_fixed_field_scope(self, fields_mask, bit_hi, bit_values):
        """

        :param fields_mask:
        :param bits:
        :param bit_values:
        :return:
        """
        value = bit_values << bit_hi
        inverted_value = ~value
        new_mask = fields_mask & inverted_value
        fields = self._convert_into_fields(new_mask)
        for field in fields:
            field.value = fields_mask
        return fields

    @staticmethod
    def _deduce_bit_value(mask, bit_hi, bit_lo):
        """

        :param mask:
        :param bits:
        :return:
        """
        bit_value = mask >> int(bit_lo)
        mask = int(math.pow((bit_hi - bit_lo), 2))
        bit_value &= mask
        return bit_value

    @staticmethod
    def _generate_bits_that_satisfy_contraints(
            fixed_mask_fields, required_bits):
        """
        generator for getting valid bits from the first fixed mask
        :param fixed_mask_fields: the fields from this fixed mask
        :param required_bits: the number of bits required to match the types
        :type required_bits: int
        :return:
        """
        routing_fields = list()

        # locate fields valid for generating collections
        for field in fixed_mask_fields:
            if field.tag == SUPPORTED_TAGS.ROUTING.name:
                routing_fields.append(field)

        # sort fields based on hi
        routing_fields.sort(key=lambda field: field.hi)

        # locate next set of bits to yield to higher function
        for routing_field in routing_fields:
            if routing_field.hi - routing_field.lo >= required_bits:
                current_hi = routing_field.hi
                while (current_hi - required_bits) > routing_field.lo:
                    yield (current_hi, current_hi - required_bits, field.value)
                    current_hi -= 1

    def _discover_keys_and_masks(
            self, partition, bit_field_space, n_keys_map,
            uses_application_space, field_mapper, seen_mask_instances):
        """

        :param partition:
        :param bit_field_space:
        :param n_keys_map:
        :param uses_application_space:
        :param seen_mask_instances:
        :return:
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
        continious_constraints = utility_calls.locate_constraints_of_type(
            partition.constraints, KeyAllocatorContiguousRangeContraint)

        if len(fixed_key_constraints) > 0:
            print "ah"
        elif len(fixed_mask_constraints) > 0:
            # get constraint and its fields
            fixed_mask_constraint_mask = fixed_mask_constraints[0].mask
            fixed_mask_fields = field_mapper[
                "{}:{}".format(FIXED_MASK_FLAG, fixed_mask_constraint_mask)]
            fixed_mask_app_field_value = \
                field_mapper["{}".format(FIXED_MASK_APP_FLAG)]
            # trakcer for iterator fields
            range_based_fixed_mask_fields = list()

            # add the app field (must exist in this situation)
            inputs = dict()
            inputs [APPLICATION_DIVIDER_FIELD_NAME] = fixed_mask_app_field_value

            # handle the inotus for static parts of the mask
            for fixed_mask_field in fixed_mask_fields:
                app_field_space = bit_field_space(**inputs)
                tag = list(app_field_space.get_tags(
                    "{}".format(fixed_mask_field)))[0]
                if tag == SUPPORTED_TAGS.ROUTING.name:
                    inputs["{}".format(fixed_mask_field)] = seen_mask_instances
                else:
                    range_based_fixed_mask_fields.append(fixed_mask_field)

            if len(range_based_fixed_mask_fields) > 1:
                raise exceptions.PacmanConfigurationException(
                    "Im not designed to work with multiple ranged based "
                    "fields for a fixed mask. please fix and try again")

            # get n keys from n_keys_map for the range based mask part
            n_keys = n_keys_map.n_keys_for_partitioned_edge(partition.edges[0])

            # generate keys
            for key_index in range(0, n_keys):
                inputs["{}".format(range_based_fixed_mask_fields[0])] = \
                    key_index
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
            seen_mask_instances += 1

        elif len(fixed_field_constraints) > 0:
            print "ah3"
        elif len(flexi_field_constraints) > 0:
            inputs = dict()

            # if theres a application field, add the value
            if uses_application_space:
                inputs[APPLICATION_DIVIDER_FIELD_NAME] = \
                    field_mapper["{}:{}".format(
                        FLEXI_APP_FLAG,
                        flexi_field_constraints[0].fields[0].name)]

            # collect flexi fields by group
            range_based_fixed_mask_fields = list()
            for field in flexi_field_constraints[0].fields:
                if field.value is not None:
                    inputs[field.name] = field.value
                else:
                    range_based_fixed_mask_fields.append(field)

            # if the set contains a ranfe_based felxi field do search
            if len(range_based_fixed_mask_fields) != 0:
                routing_keys_and_masks, application_keys_and_masks = \
                    self._handle_recursive_range_fields(
                        range_based_fixed_mask_fields, bit_field_space,
                        routing_keys_and_masks, application_keys_and_masks,
                        inputs, 0)

            else:  # no range, just grab the key and value
                key = bit_field_space(**inputs).get_value()
                mask = bit_field_space(**inputs).get_mask()
                routing_keys_and_masks.append(BaseKeyAndMask(key, mask))

        # if theres a continious constraint check, check the keys for
        # continiouity
        if len(continious_constraints) != 0:
            are_continious = self._check_keys_are_continious(
                application_keys_and_masks)
            if not are_continious:
                raise exceptions.PacmanConfigurationException(
                    "These keys returned from the bitfield are"
                    "not continous. Therefore cannot be used")
            result = list()
            result.append(routing_keys_and_masks[0])

            # return keys and masks
            return result, seen_mask_instances

        # return keys and masks
        return routing_keys_and_masks, seen_mask_instances

    @staticmethod
    def _check_keys_are_continious(keys_and_masks):
        """

        :param keys_and_masks:
        :return:
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

    def _handle_recursive_range_fields(
            self, range_based_flexi_fields, bit_field_space,
            routing_keys_and_masks, application_keys_and_masks, inputs,
            position):
        """

        :param range_based_flexi_fields:
        :param bit_field_space:
        :param routing_keys_and_masks:
        :param application_keys_and_masks:
        :param inputs:
        :param position:
        :return:
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
                position += 1
                other_routing_keys_and_masks, \
                    other_application_keys_and_masks = \
                    self._handle_recursive_range_fields(
                        range_based_flexi_fields, bit_field_space,
                        routing_keys_and_masks, application_keys_and_masks,
                        inputs, position)

                routing_keys_and_masks.extend(other_routing_keys_and_masks)
                application_keys_and_masks.extend(
                    other_application_keys_and_masks)
        return routing_keys_and_masks, application_keys_and_masks

    def _handle_application_space(
            self, bit_field_space, fields, field_mapper, top_level_bit_field):
        """

        :param bit_field_space:
        :param fields:
        :param field_mapper:
        :param top_level_bit_field:
        :return:
        """
        # locate the application field if it exists
        application_field, application_field_spare_values = \
            self._locate_application_field(fields)

        if application_field is not None:
            # create the application basd field if its not none
            length = application_field.hi - application_field.lo
            if length == 0:
                length = 1
            bit_field_space.add_field(
                application_field.name, length, application_field.lo,
                tags=SUPPORTED_TAGS.ROUTING.name)

        # iterate though the fields, adding fields to the system
        for field in fields:
            # handle fixed mask fields
            if field == TYPES_OF_FIELDS.FIXED_MASK.name:
                fixed_fields = fields[TYPES_OF_FIELDS.FIXED_MASK.name]
                for fixed_field_key in fixed_fields:

                    # create the top level bt field space for this set
                    fixed_feild_list = fixed_fields[fixed_field_key]
                    fixed_field_application_field = self._locate_field_by_name(
                        fixed_feild_list, APPLICATION_DIVIDER_FIELD_NAME)
                    internal_field_space = self._create_internal_field_space(
                        bit_field_space, fixed_field_application_field.value,
                        fixed_field_application_field)

                    # iterate though rest of the fields adding them to the
                    #  lower position field space
                    for fixed_field in fixed_feild_list:
                        if fixed_field.name != APPLICATION_DIVIDER_FIELD_NAME:
                            length = fixed_field.hi - fixed_field.lo
                            if length == 0:
                                length = 1
                            internal_field_space.add_field(
                                "{}".format(fixed_field.name), length,
                                fixed_field.lo, fixed_field.tag)
                            key = "{}:{}".format(
                                FIXED_MASK_FLAG, fixed_field.value)
                            if key not in field_mapper:
                                field_mapper[key] = list()
                            field_mapper[key].append(fixed_field.name)
                        else:
                            field_mapper[FIXED_MASK_APP_FLAG] = \
                                fixed_field.value

            # hnadle fixed field
            elif field == TYPES_OF_FIELDS.FIXED_FIELD.name:
                for fixed_field in fields[TYPES_OF_FIELDS.FIXED_FIELD.name]:
                    fields_data = self._convert_into_fields(fixed_field.mask)
                    for (position, length) in fields_data:
                        random_identifer = uuid.uuid4()
                        field_mapper[fixed_field] = random_identifer
                        bit_field_space.add_field(
                            random_identifer, length, position)

            # handle fixed key fields
            elif field == TYPES_OF_FIELDS.FIXED_KEY.name:
                for key_and_mask in fields[TYPES_OF_FIELDS.FIXED_KEY.name]:
                    random_identifer = uuid.uuid4()
                    top_level_bit_field.add_field(
                        random_identifer, NUM_BITS_IN_ROUTING, 0)
                    field_mapper[key_and_mask] = random_identifer
                    # set the value for the field
                    inputs = dict()
                    inputs[random_identifer] = key_and_mask.key
                    top_level_bit_field(**inputs)

            else:  # handle flexi field stuff
                if application_field is not None:

                    # create a new bit field where everyhting is linked off a
                    # sub internal app field
                    internal_value = application_field_spare_values[0]
                    application_field_spare_values.remove(internal_value)
                    internal_bit_field_space = \
                        self._create_internal_field_space(
                            bit_field_space, internal_value, application_field)
                    field_mapper["{}:{}".format(FLEXI_APP_FLAG, field)] = \
                        internal_value

                    # handle the flexi fields
                    self._handle_flexi_field_allocation(
                        internal_bit_field_space, field, fields)
                else:
                    self._handle_flexi_field_allocation(
                        bit_field_space, field, fields)

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
    def _locate_field_by_name(feild_list, field_name):
        """

        :param feild_list:
        :param field_name:
        :return:
        """
        for field in feild_list:
            if field.name == field_name:
                return field
        return None

    def _locate_application_field(self, fields):
        """

        :param fields:
        :return:
        """
        application_feild = None
        application_field_spare_values = None
        # search for the field with the correct tag
        for field in fields:
            # if a fixed mask field, locate correct application field and value
            if field == TYPES_OF_FIELDS.FIXED_MASK.name:
                fixed_fields = fields[TYPES_OF_FIELDS.FIXED_MASK.name]
                for fixed_field_key in fixed_fields:
                    fixed_feild_list = fixed_fields[fixed_field_key]
                    for fixed_field in fixed_feild_list:
                        # if the field is the correct field, mark and deduce
                        # usable values
                        if fixed_field.name == APPLICATION_DIVIDER_FIELD_NAME:
                            if application_feild is None:
                                application_feild = fixed_field
                                application_field_spare_values = \
                                    self._deduce_application_field_space(
                                        application_feild)
                            else:
                                application_field_spare_values.remove(
                                    fixed_field.value)
            elif field == TYPES_OF_FIELDS.FIXED_KEY.name:
                pass
        return application_feild, application_field_spare_values

    @staticmethod
    def _deduce_application_field_space(application_feild):
        """

        :param application_feild:
        :return:
        """
        length = application_feild.hi - application_feild.lo
        application_field_spare_values = list()
        if length == 0:
            length = 1
        for value in range(0, ((2 ^ length) -1)):
            application_field_spare_values.append(value)
        application_field_spare_values.remove(application_feild.value)
        return application_field_spare_values

    def _handle_flexi_field_allocation(
            self, bit_field_space, field, fields):
        """

        :param bit_field_space:
        :param field:
        :param fields:
        :return:
        """
        # field must be a flexi field, work accordingly
        example_entry = self._check_entries_are_tag_consistent(fields, field)
        if example_entry.tag is None:
            bit_field_space.add_field(field)
        else:
            bit_field_space.add_field(field, tags=example_entry.tag)

        for field_instance in fields[field]:
            # only carry on if theres more to create
            if len(fields[field][field_instance]) > 0:

                # create next level
                internal_bit_field = self._create_internal_field_space(
                    bit_field_space, field_instance.value, field_instance)

                # deal with next level hirarckhy
                for nested_field in fields[field][field_instance]:
                    self._handle_flexi_field_allocation(
                        internal_bit_field, nested_field,
                        fields[field][field_instance])

            # bottom level
            if field_instance.instance_n_keys is not None:
                for value in range(0, field_instance.instance_n_keys):
                    self._create_internal_field_space(
                        bit_field_space, value, field_instance)

    @staticmethod
    def _check_entries_are_tag_consistent(fields, field):
        """

        :param fields:
        :param field:
        :return:
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
    def _convert_into_fields(entity):
        """

        :param entity:
        :return:
        """
        results = list()
        expanded_mask = utility_calls.expand_to_bit_array(entity)
        # set up for first location
        detected_change = True
        detected_change_position = NUM_BITS_IN_ROUTING
        detected_last_state = expanded_mask[NUM_BITS_IN_ROUTING]
        # iterate up the key looking for fields
        for position in range(NUM_BITS_IN_ROUTING - 1,
                              START_OF_ROUTING_KEY_POSITION - 2, -1):
            # check for last bit iteration
            if position == -1:
                # if last bit has changed, create new field
                if detected_change_position != position:

                    # create field with correct routing tag
                    if detected_last_state == ROUTING_MASK_BIT:
                        results.append(Field(
                            NUM_BITS_IN_ROUTING - detected_change_position,
                            NUM_BITS_IN_ROUTING, entity,
                            SUPPORTED_TAGS.ROUTING.name))
                    else:
                        results.append(Field(
                            NUM_BITS_IN_ROUTING - detected_change_position,
                            NUM_BITS_IN_ROUTING, entity,
                            SUPPORTED_TAGS.APPLICATION.name))
            else:
                # check for bit iteration
                if expanded_mask[position] != detected_last_state:
                    # if changed state, a field needs to be created. check for
                    # which type of field to support
                    if detected_last_state == ROUTING_MASK_BIT:
                        results.append(Field(
                            NUM_BITS_IN_ROUTING - detected_change_position,
                            NUM_BITS_IN_ROUTING - (position + 1),
                            entity, SUPPORTED_TAGS.ROUTING.name))
                    else:
                        results.append(Field(
                            NUM_BITS_IN_ROUTING - detected_change_position,
                            NUM_BITS_IN_ROUTING - (position + 1),
                            entity, SUPPORTED_TAGS.APPLICATION.name))
                    # update positions
                    detected_last_state = expanded_mask[position]
                    detected_change_position = position
        return results

    def _deduce_types(self, subgraph):
        """
        deducing the number of applications required for this key space
        :param subgraph:
        :return:
        """
        seen_fields = dict()
        known_fields = list()
        for partition in subgraph.partitions:
            for constraint in partition.constraints:
                if not isinstance(constraint,
                                  KeyAllocatorContiguousRangeContraint):
                    if isinstance(constraint, KeyAllocatorFlexiFieldConstraint):
                        self._handle_flexi_field(
                            constraint, seen_fields, known_fields)
                    if isinstance(constraint,
                                  KeyAllocatorFixedKeyAndMaskConstraint):
                        if TYPES_OF_FIELDS.FIXED_KEYS.name not in seen_fields:
                            seen_fields[TYPES_OF_FIELDS.FIXED_KEYS.name] = \
                                list()
                        for key_mask in constraint.keys_and_masks:
                            seen_fields[TYPES_OF_FIELDS.FIXED_KEYS.name].\
                                append(key_mask)
                    if isinstance(constraint, KeyAllocatorFixedMaskConstraint):
                        fields = self._convert_into_fields(constraint.mask)
                        if TYPES_OF_FIELDS.FIXED_MASK.name not in seen_fields:
                            seen_fields[TYPES_OF_FIELDS.FIXED_MASK.name] =\
                                dict()
                        for field in fields:
                            if field.value not in seen_fields[
                                    TYPES_OF_FIELDS.FIXED_MASK.name]:
                                # add a new list for this mask type
                                seen_fields[
                                    TYPES_OF_FIELDS.FIXED_MASK.name][
                                    field.value] = list()
                            if field not in seen_fields[
                                    TYPES_OF_FIELDS.FIXED_MASK.name][
                                    field.value]:
                                seen_fields[
                                    TYPES_OF_FIELDS.FIXED_MASK.name][
                                    field.value].append(field)

                    if isinstance(constraint, KeyAllocatorFixedFieldConstraint):
                        if TYPES_OF_FIELDS.FIXED_FIELD not in seen_fields:
                            seen_fields[TYPES_OF_FIELDS.FIXED_FIELD.name] = \
                                list()
                        seen_fields[TYPES_OF_FIELDS.FIXED_FIELD.name].\
                            append(constraint.fields)
        return seen_fields

    @staticmethod
    def _handle_flexi_field(constraint, seen_fields, known_fields):
        """

        :param constraint:
        :param seen_fields:
        :param known_fields:
        :return:
        """
        # set the level of search
        current_level = seen_fields
        for constraint_field in constraint.fields:
            found_field = None

            # try to locate field in level
            for seen_field in current_level:
                if constraint_field.name == seen_field:
                    found_field = seen_field

            # seen the field before but not at this level. error
            if found_field is None and constraint_field in known_fields:
                raise exceptions.PacmanConfigurationException(
                    "Cant find the field {} in the expected position"
                        .format(constraint_field))

            # if not seen the field before
            if found_field is None and constraint_field.name not in known_fields:
                next_level = dict()
                instance_level = dict()
                current_level[constraint_field.name] = instance_level
                instance_level[constraint_field] = next_level
                known_fields.append(constraint_field.name)
                current_level = next_level

            # if found a field, check if its instance has indeed been put in
            # before
            if found_field is not None:
                instances = current_level[constraint_field.name]
                if constraint_field in instances:
                    current_level = instances[constraint_field]
                elif constraint_field.value not in instances:
                    next_level = dict()
                    instance_level = dict()
                    instances[constraint_field] = instance_level
                    instances[constraint_field] = next_level
                    current_level = next_level

    def _determine_groups(self, subgraph, graph_mapper, partitionable_graph,
                          n_keys_map):
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
                self._add_field_constraints(
                    partition, graph_mapper, partitionable_graph, n_keys_map)

    @staticmethod
    def _add_field_constraints(partition, graph_mapper, partitionable_graph,
                               n_keys_map):
        """
        searches though the subgraph adding field constraints for the key
         allocator
        :param partition:
        :param graph_mapper:
        :param partitionable_graph:
        :return:
        """

        fields = list()

        verts = list(partitionable_graph.vertices)
        subvert = partition.edges[0].pre_subvertex
        vertex = graph_mapper.get_vertex_from_subvertex(subvert)
        subverts = list(graph_mapper.get_subvertices_from_vertex(vertex))

        # pop based flexi field
        fields.append(FlexiField(flexi_field_name="Population",
                                 value=verts.index(vertex),
                                 tag=SUPPORTED_TAGS.ROUTING.name))

        # subpop flexi field
        fields.append(FlexiField(
            flexi_field_name="SubPopulation{}".format(verts.index(vertex)),
            tag=SUPPORTED_TAGS.ROUTING.name,
            value=subverts.index(subvert)))

        fields.append(FlexiField(
            flexi_field_name="POP({}:{})Keys"
            .format(verts.index(vertex), subverts.index(subvert)),
            tag=SUPPORTED_TAGS.APPLICATION.name,
            instance_n_keys=n_keys_map.n_keys_for_partitioned_edge(
                partition.edges[0])))

        # add constraint to the subedge
        partition.add_constraint(KeyAllocatorFlexiFieldConstraint(fields))
