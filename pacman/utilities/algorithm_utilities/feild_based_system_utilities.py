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
from pacman import exceptions
# the different tyes of field that this system supports
from pacman.utilities import utility_calls
from pacman.utilities.utility_objs.field import Field
from pacman.utilities.utility_objs.flexi_field import SUPPORTED_TAGS

from enum import Enum

TYPES_OF_FIELDS = Enum(
    value="TYPES_OF_FIELDS",
    names=[("FIXED_MASK", 0),
           ("FIXED_KEY", 1),
           ("FIXED_FIELD", 2)])

NUM_BITS_IN_ROUTING = 31
ROUTING_MASK_BIT = 1
START_OF_ROUTING_KEY_POSITION = 0


def deduce_types(subgraph):
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
                    handle_flexi_field(constraint, seen_fields, known_fields)
                if isinstance(constraint,
                              KeyAllocatorFixedKeyAndMaskConstraint):
                    if TYPES_OF_FIELDS.FIXED_KEY.name not in seen_fields:
                        seen_fields[TYPES_OF_FIELDS.FIXED_KEY.name] = list()
                    for key_mask in constraint.keys_and_masks:
                        seen_fields[TYPES_OF_FIELDS.FIXED_KEY.name].\
                            append(key_mask)
                if isinstance(constraint, KeyAllocatorFixedMaskConstraint):
                    fields = convert_mask_into_fields(constraint.mask)
                    if TYPES_OF_FIELDS.FIXED_MASK.name not in seen_fields:
                        seen_fields[TYPES_OF_FIELDS.FIXED_MASK.name] = dict()
                    for field in fields:
                        if field.value not in seen_fields[
                                TYPES_OF_FIELDS.FIXED_MASK.name]:
                            # add a new list for this mask type
                            seen_fields[TYPES_OF_FIELDS.FIXED_MASK.name][
                                field.value] = list()
                        if field not in seen_fields[
                                TYPES_OF_FIELDS.FIXED_MASK.name][field.value]:
                            seen_fields[
                                TYPES_OF_FIELDS.FIXED_MASK.name][
                                field.value].append(field)

                if isinstance(constraint, KeyAllocatorFixedFieldConstraint):
                    if TYPES_OF_FIELDS.FIXED_FIELD not in seen_fields:
                        seen_fields[TYPES_OF_FIELDS.FIXED_FIELD.name] = list()
                    seen_fields[TYPES_OF_FIELDS.FIXED_FIELD.name].append(
                        constraint.fields)
    return seen_fields


def handle_flexi_field(constraint, seen_fields, known_fields):
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


def convert_mask_into_fields(entity):
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
