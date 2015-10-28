"""

"""
from pacman.model.constraints.key_allocator_constraints.key_allocator_contiguous_range_constraint import \
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
from pacman.operations.routing_info_allocator_algorithms.\
    field_based_routing_allocator.rigs_bitfield import \
    RigsBitField
from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities import \
    routing_info_allocator_utilities
from pacman import exceptions

import uuid

from pacman.utilities.utility_objs.flexi_field import FlexiField


class VertexBasedRoutingInfoAllocator(object):
    """
    VertexBasedRoutingInfoAllocator
    """

    def __call__(self, partitionable_graph, graph_mapper, subgraph, n_keys_map,
                 routing_paths):

        # ensure groups are stable and correct
        self._determine_groups(subgraph, graph_mapper, partitionable_graph)

        # define the key space
        bit_field_space = RigsBitField(32)

        # locate however many types of constrants there are
        seen_fields = self._deduce_types(subgraph)

        field_mapper = dict()
        # handle the application space
        self._handle_application_space(
            bit_field_space, seen_fields, field_mapper, bit_field_space)

        # set up values
        for partition in subgraph.partitions:
            for constraint in partition.constraints:
                if isinstance(constraint, KeyAllocatorFixedFieldConstraint):
                    pass
                if isinstance(constraint, KeyAllocatorFlexiFieldConstraint):
                    inputs = dict()
                    for field in constraint.fields:
                        if field.instance_value is not None:
                            inputs[field.id] = field.instance_value
                    bit_field_space(**inputs)

                if isinstance(constraint, KeyAllocatorFixedMaskConstraint):
                    pass
                if isinstance(constraint,
                              KeyAllocatorFixedKeyAndMaskConstraint):
                    for key_and_mask in constraint.keys_and_masks:
                        random_identifer = field_mapper[key_and_mask]
                        # set the value for the field
                        bit_field_space(random_identifer=key_and_mask.key)

        # extract keys for each partition
        bit_field_space.assign_fields()

        # create routing_info_allocator
        routing_info = RoutingInfo()
        routing_tables = MulticastRoutingTables()

        for partition in subgraph.partitions:
            for edge in partition.edges:
                sub_edge_info = SubedgeRoutingInfo("", edge)
                routing_info.add_subedge_info(sub_edge_info)

                # update routing tables with entries
                routing_info_allocator_utilities.add_routing_key_entries(
                    routing_paths, sub_edge_info, edge, routing_tables)

        return {'routing_infos': routing_info,
                'routing_tables': routing_tables}

    def _handle_application_space(
            self, bit_field_space, fields, field_mapper,
            top_level_bit_field):

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
                    top_level_bit_field(random_identifer=key_and_mask.key)
            else:
                self._handle_flexi_field_allocation(bit_field_space, field,
                                                    fields)

    def _handle_flexi_field_allocation(self, bit_field_space, field, fields):
        # field must be a flexi field, work accordingly
        bit_field_space.add_field(field)
        for nested_fields in fields[field]:
            self._handle_flexi_field_allocation(bit_field_space, nested_fields,
                                                fields[field])

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

            # check for state
            if found_field is None and constraint_field in known_fields:
                raise exceptions.PacmanConfigurationException(
                    "Cant find the field {} in the expected position"
                        .format(constraint_field))
            if found_field is None and constraint_field.id not in known_fields:
                current_level[constraint_field.id] = dict()
                known_fields.append(constraint_field.id)
                current_level = current_level[constraint_field.id]
            if found_field is not None:
                current_level = current_level[constraint_field.id]

    def _determine_groups(self, subgraph, graph_mapper, partitionable_graph):

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
                    partition, graph_mapper, partitionable_graph)

    @staticmethod
    def _add_field_constraints(partition, graph_mapper, partitionable_graph):
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
                                 instance_value=verts.index(vertex)))

        # subpop flexi field
        fields.append(FlexiField(flexi_field_id="SubPopulation",
                                 instance_value=subverts.index(subvert)))

        fields.append(FlexiField(
            flexi_field_id="POP({}:{})Neurons"
            .format(verts.index(vertex), subverts.index(subvert)),
            instance_range=graph_mapper.get_subvertex_slice(subvert)))

        # add constraint to the subedge
        partition.add_constraint(KeyAllocatorFlexiFieldConstraint(fields))
