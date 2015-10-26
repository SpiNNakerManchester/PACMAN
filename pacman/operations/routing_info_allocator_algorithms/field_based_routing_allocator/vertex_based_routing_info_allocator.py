"""

"""
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_key_and_mask_constraint import \
    KeyAllocatorFixedKeyAndMaskConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_mask_constraint import \
    KeyAllocatorFixedMaskConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_flexi_field_constraint import \
    KeyAllocatorFlexiFieldConstraint
from pacman.operations.routing_info_allocator_algorithms import \
    MallocBasedRoutingInfoAllocator
from pacman.utilities import utility_calls

import math
from pacman.utilities.utility_objs.flexi_field import FlexiField


class VertexBasedRoutingInfoAllocator(object):
    """
    VertexBasedRoutingInfoAllocator
    """

    def __call__(self, partitionable_graph, graph_mapper, subgraph, n_keys_map,
                 routing_paths):

        self._determine_groups(
            subgraph, partitionable_graph, graph_mapper)

        allocator = MallocBasedRoutingInfoAllocator()
        return allocator(subgraph, n_keys_map, routing_paths)

    def _determine_groups(self, subgraph, partitionable_graph, graph_mapper):
        vertices = list(partitionable_graph.vertices)

        for partition in subgraph.partitions:
            fixed_key_constraints = \
                utility_calls.locate_constraints_of_type(
                    partition.constraints,
                    KeyAllocatorFixedKeyAndMaskConstraint)
            fixed_mask_constraints = \
                utility_calls.locate_constraints_of_type(
                    partition.constraints,
                    KeyAllocatorFixedMaskConstraint)
            if (len(fixed_key_constraints) == 0
                    and len(fixed_mask_constraints) == 0):
                self._add_field_constraints(partition, vertices, graph_mapper)

    @staticmethod
    def _add_field_constraints(partition, vertices, graph_mapper):
        """
        searches though the subgraph adding field constraints for the key
         allocator
        :param partition:
        :return:
        """

        fields = list()
        # pop based flexi field
        vertex = graph_mapper.get_vertex_from_subvertex(
            partition.edges[0].pre_subvertex)
        fields.append(FlexiField(flexi_field_id="Population",
                                 instance_id=vertices.index(vertex)))
        # subpop flexi field
        subverts = list(graph_mapper.get_subvertices_from_vertex(vertex))
        fields.append(FlexiField(
            flexi_field_id="SubPopulation",
            instance_id=subverts.index(partition.edges[0].pre_subvertex)))

        # add constraint to the subedge
        partition.add_constraint(KeyAllocatorFlexiFieldConstraint(fields))