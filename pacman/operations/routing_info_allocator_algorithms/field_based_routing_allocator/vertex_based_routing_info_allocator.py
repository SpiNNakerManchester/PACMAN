"""

"""
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
# swiped from rig currently.
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.operations.routing_info_allocator_algorithms.\
    field_based_routing_allocator.rigs_bitfield import \
    RigsBitField
from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities import \
    routing_info_allocator_utilities
from pacman import exceptions

import uuid

from pacman.utilities.utility_objs.flexi_field import FlexiField, SUPPORTED_TAGS


class VertexBasedRoutingInfoAllocator(object):
    """
    VertexBasedRoutingInfoAllocator
    """

    def __call__(self, partitionable_graph, graph_mapper, subgraph, n_keys_map,
                 routing_paths):

        # ensure groups are stable and correct
        self._determine_groups(subgraph, graph_mapper, partitionable_graph,
                               n_keys_map)

        # define the key space
        bit_field_space = RigsBitField(32)

        # locate however many types of constrants there are
        seen_fields = self._deduce_types(subgraph)

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

        # extract keys and masks for each edge from the bitfield
        for partition in subgraph.partitions:
            # get keys and masks
            keys_and_masks = self._discover_keys_and_masks(
                partition, bit_field_space, n_keys_map)

            # update routing info for each edge in the partition
            for edge in partition.edges:
                sub_edge_info = SubedgeRoutingInfo(keys_and_masks, edge)
                routing_info.add_subedge_info(sub_edge_info)

                # update routing tables with entries
                routing_info_allocator_utilities.add_routing_key_entries(
                    routing_paths, sub_edge_info, edge, routing_tables)

        return {'routing_infos': routing_info,
                'routing_tables': routing_tables}

    def _discover_keys_and_masks(self, partition, bit_field_space, n_keys_map):
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
            print "ah2"
        elif len(fixed_field_constraints) > 0:
            print "ah3"
        elif len(flexi_field_constraints) > 0:
            inputs = dict()
            range_based_flexi_fields = list()
            for field in flexi_field_constraints[0].fields:
                if field.instance_value is not None:
                    inputs[field.id] = field.instance_value
                else:
                    range_based_flexi_fields.append(field)
            if len(range_based_flexi_fields) != 0:
                routing_keys_and_masks, application_keys_and_masks = \
                    self._handle_recursive_range_fields(
                        range_based_flexi_fields, bit_field_space,
                        routing_keys_and_masks, application_keys_and_masks,
                        inputs, 0)
                if len(continious_constraints) != 0:
                    are_continious = self._check_keys_are_continious(
                        application_keys_and_masks)
                    if not are_continious:
                        raise exceptions.PacmanConfigurationException(
                            "These keys returned from the bitfield are"
                            "not continous. Therefore cannot be used")
                    result = list()
                    result.append(routing_keys_and_masks[0])
                return result
            else:
                key = bit_field_space(**inputs).get_value()
                mask = bit_field_space(**inputs).get_mask()
                routing_keys_and_masks.append(BaseKeyAndMask(key, mask))
                return routing_keys_and_masks

        else:
            raise exceptions.PacmanConfigurationException(
                "Cant figure out what to do with a partition with no "
                "constraints. exploded.")

        return routing_keys_and_masks

    @staticmethod
    def _check_keys_are_continious(keys_and_masks):
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

        for value in range(0,
                           range_based_flexi_fields[position].instance_n_keys):
            inputs[range_based_flexi_fields[position].id] = value
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

        for field in fields:
            if field == "FIXED_MASK":
                for (position, length) in fields['FIXED_MASK']:
                    random_identifer = uuid.uuid4()
                    field_mapper[
                        "FIXED_MASK:{}:{}".format(position, length)] = \
                        random_identifer
                    bit_field_space.add_field(random_identifer, length,
                                              position)
            elif field == "FIXED_FIELDS":
                for fixed_field in fields['FIXED_FIELDS']:
                    fields_data = self._convert_into_fields(fixed_field.mask)
                    for (position, length) in fields_data:
                        random_identifer = uuid.uuid4()
                        field_mapper[fixed_field] = random_identifer
                        bit_field_space.add_field(
                            random_identifer, length, position)
            elif field == "FIXED_KEYS":
                for key_and_mask in fields["FIXED_KEYS"]:
                    random_identifer = uuid.uuid4()
                    top_level_bit_field.add_field(random_identifer, 31, 0)
                    field_mapper[key_and_mask] = random_identifer
                    # set the value for the field
                    inputs = dict()
                    inputs[random_identifer] = key_and_mask.key
                    top_level_bit_field(**inputs)
            else:
                self._handle_flexi_field_allocation(bit_field_space, field,
                                                    fields)

    def _handle_flexi_field_allocation(self, bit_field_space, field, fields):
        # field must be a flexi field, work accordingly
        example_entry = self._check_entries_are_tag_consistent(fields, field)
        if example_entry.tag is None:
            bit_field_space.add_field(field)
        else:
            bit_field_space.add_field(field, tags=example_entry.tag)

        for field_instance in fields[field]:
            # only carry on if theres more to create
            if len(fields[field][field_instance]) > 0:
                inputs = dict()
                inputs[field] = field_instance.instance_value
                internal_bit_field = bit_field_space(**inputs)
                for nested_field in fields[field][field_instance]:
                    self._handle_flexi_field_allocation(
                        internal_bit_field, nested_field,
                        fields[field][field_instance])
            if field_instance.instance_n_keys is not None:
                for value in range(0, field_instance.instance_n_keys):
                    inputs = dict()
                    inputs[field] = value
                    bit_field_space(**inputs)

    @staticmethod
    def _check_entries_are_tag_consistent(fields, field):
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
        results = list()
        expanded_mask = utility_calls.expand_to_bit_array(entity)
        # set up for first location
        detected_change = True
        detected_change_position = 31
        detected_last_state = expanded_mask[31]
        # iterate up the key looking for fields
        for position in range(30, 0, -1):
            if (expanded_mask[position] != detected_last_state
                    and detected_change):
                detected_change = False
                detected_last_state = expanded_mask[position]
                results.append((31 - detected_change_position,
                                (detected_change_position - position)))
                detected_change_position = position - 1
            if (expanded_mask[position] != detected_last_state
                    and not detected_change):
                detected_change = True
                detected_last_state = expanded_mask[position]
                detected_change_position = position
        if detected_change_position != 0:
            results.append((31 - detected_change_position,
                            detected_change_position))
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
                        self._handle_felxi_field(
                            constraint, seen_fields, known_fields)
                    if isinstance(constraint,
                                  KeyAllocatorFixedKeyAndMaskConstraint):
                        if "FIXED_KEYS" not in seen_fields:
                            seen_fields["FIXED_KEYS"] = list()
                        for key_mask in constraint.keys_and_masks:
                            seen_fields["FIXED_KEYS"].append(key_mask)
                    if isinstance(constraint, KeyAllocatorFixedMaskConstraint):
                        fields = self._convert_into_fields(constraint.mask)
                        if "FIXED_MASK" not in seen_fields:
                            seen_fields["FIXED_MASK"] = list()
                            for field in fields:
                                if field not in seen_fields["FIXED_MASK"]:
                                    seen_fields["FIXED_MASK"].append(field)
                    if isinstance(constraint, KeyAllocatorFixedFieldConstraint):
                        if "FIXED_FIELDS" not in seen_fields:
                            seen_fields["FIXED_FIELDS"] = list()
                        seen_fields["FIXED_FIELDS"].append(constraint.fields)
        return seen_fields

    @staticmethod
    def _handle_felxi_field(constraint, seen_fields, known_fields):
        # set the level of search
        current_level = seen_fields
        for constraint_field in constraint.fields:
            found_field = None

            # try to locate field in level
            for seen_field in current_level:
                if constraint_field.id == seen_field:
                    found_field = seen_field

            # seen the field before but not at this level. error
            if found_field is None and constraint_field in known_fields:
                raise exceptions.PacmanConfigurationException(
                    "Cant find the field {} in the expected position"
                        .format(constraint_field))

            # if not seen the field before
            if found_field is None and constraint_field.id not in known_fields:
                next_level = dict()
                instance_level = dict()
                current_level[constraint_field.id] = instance_level
                instance_level[constraint_field] = next_level
                known_fields.append(constraint_field.id)
                current_level = next_level

            # if found a field, check if its instance has indeed been put in
            # before
            if found_field is not None:
                instances = current_level[constraint_field.id]
                if constraint_field in instances:
                    current_level = instances[constraint_field]
                elif constraint_field.instance_value not in instances:
                    next_level = dict()
                    instance_level = dict()
                    instances[constraint_field] = instance_level
                    instances[constraint_field] = next_level
                    current_level = next_level

    def _determine_groups(self, subgraph, graph_mapper, partitionable_graph,
                          n_keys_map):

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
        fields.append(FlexiField(flexi_field_id="Population",
                                 instance_value=verts.index(vertex),
                                 tag=SUPPORTED_TAGS.ROUTING.name))

        # subpop flexi field
        fields.append(FlexiField(
            flexi_field_id="SubPopulation{}".format(verts.index(vertex)),
            tag=SUPPORTED_TAGS.ROUTING.name,
            instance_value=subverts.index(subvert)))

        fields.append(FlexiField(
            flexi_field_id="POP({}:{})Keys"
            .format(verts.index(vertex), subverts.index(subvert)),
            tag=SUPPORTED_TAGS.APPLICATION.name,
            instance_n_keys=n_keys_map.n_keys_for_partitioned_edge(
                partition.edges[0])))

        # add constraint to the subedge
        partition.add_constraint(KeyAllocatorFlexiFieldConstraint(fields))
