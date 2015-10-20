"""

"""
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_mask_constraint import \
    KeyAllocatorFixedMaskConstraint
from pacman.operations.routing_info_allocator_algorithms import \
    MallocBasedRoutingInfoAllocator
from pacman.utilities.utility_objs.field import Field

import math


class PopulationbasedRoutingInfoAllocator(object):
    """
    PopulationbasedRoutingInfoAllocator
    """

    def __call__(self, partitionable_graph, graph_mapper, subgraph, n_keys_map,
                 routing_paths):

        self._add_field_constraints(subgraph, partitionable_graph, graph_mapper)
        allocator = MallocBasedRoutingInfoAllocator()
        return allocator(subgraph, n_keys_map, routing_paths)

    def _add_field_constraints(self, subgraph, partitionable_graph,
                               graph_mapper):
        """
        searches though the subgraph adding field constraints for the key allocator
        :param subgraph:
        :param partitionable_graph:
        :param graph_mapper:
        :return:
        """
        total_vertices = len(partitionable_graph.vertices)

        max_atoms = 0
        max_subvertices = 0

        for subvert in subgraph.subvertices:
            if graph_mapper.get_subvertex_slice(subvert).n_atoms > max_atoms:
                max_atoms = graph_mapper.get_subvertex_slice(subvert).n_atoms
        for vertex in partitionable_graph.vertices:
            n_subverts = len(graph_mapper.get_subvertices_from_vertex(vertex))
            if n_subverts > max_subvertices:
                max_subvertices = n_subverts

        for subvertex in subgraph.subvertices:
            vertex = graph_mapper.get_vertex_from_subvertex(subvertex)
            total_subvertices = \
                len(graph_mapper.get_subvertices_from_vertex(vertex))
            total_atoms = vertex.n_atoms

            bits_for_atoms = int(self._deduce_bits_to_cover_field(total_atoms))
            mask_for_atoms = (2**bits_for_atoms) - 1

            bits_for_vertices = \
                int(self._deduce_bits_to_cover_field(total_vertices))
            mask_for_vertices = (2**bits_for_vertices) - 1

            bits_for_sub_vertices = \
                int(self._deduce_bits_to_cover_field(total_subvertices))
            mask_for_sub_vertices = (2**bits_for_sub_vertices) - 1

            fields = self._create_fields(
                mask_for_atoms, mask_for_sub_vertices, mask_for_vertices,
                bits_for_atoms, bits_for_sub_vertices, bits_for_vertices,
                total_vertices, max_subvertices, max_atoms, total_atoms,
                total_subvertices)

            edge_mask = 0
            for field in fields:
                edge_mask |= field.mask

            subvertex.add_constraint(KeyAllocatorFixedMaskConstraint(
                mask=edge_mask, fields=fields))

    @staticmethod
    def _create_fields(mask_for_n, mask_for_sp, mask_for_p, bits_for_n,
                       bits_for_sp, bits_for_p, total_vertices,
                       max_no_subverts, max_no_atoms, no_n, no_sp):
        """

        :param mask_for_n:
        :param mask_for_sp:
        :param mask_for_p:
        :param bits_for_n:
        :param bits_for_sp:
        :param bits_for_p:
        :param total_vertices:
        :param max_no_subverts:
        :param max_no_atoms:
        :param no_n:
        :param no_sp:
        :return:
        """

        fields = list()

        # adjust masks for field sizes
        mask_for_p <<= 32 - bits_for_p
        mask_for_sp <<= 32 - (bits_for_p + bits_for_sp)

        # add fields
        fields.append(Field(0, total_vertices, mask=mask_for_p))
        fields.append(Field(0, no_sp, mask=mask_for_sp))

        # calculate left over field
        total_bits = 32
        total_bits = total_bits - (bits_for_n + bits_for_sp + bits_for_p)
        mask_for_left_over = (2**total_bits) - 1
        mask_for_left_over <<= bits_for_n
        fields.append(Field(0, total_bits, mask=mask_for_left_over))

        # return fields
        return fields

    @staticmethod
    def _deduce_bits_to_cover_field(value):
        # equation to deduce next power of 2
        # (http://stackoverflow.com/questions/14267555/how-can-i-find-the-smallest-power-of-2-greater-than-n-in-python)
        return math.ceil(math.log(float(value), float(2)))