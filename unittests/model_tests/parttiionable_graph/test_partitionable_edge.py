"""
test that tests the partitionable edge generation
"""

# pacman imports
from pacman.model.constraints.key_allocator_constraints.key_allocator_contiguous_range_constraint import \
    KeyAllocatorContiguousRangeContraint
from pacman.model.partitionable_graph.abstract_partitionable_edge \
    import AbstractPartitionableEdge
from pacman.model.graph_mapper.slice import Slice

# general imports
import unittest
from unittests.test_vertex import TestVertex


class TestPartitionableEdgeModel(unittest.TestCase):
    """
    tests which test the partitionable graph object
    """

    def test_create_new_edge(self):
        """
        test that you can create a edge between two vertices
        :return:
        """
        vert1 = TestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = TestVertex(5, "New AbstractConstrainedVertex 2", 256)
        edge1 = AbstractPartitionableEdge(vert1, vert2, "First edge")
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)

    def test_create_new_edge_without_label(self):
        """
        test initisation of a edge without a label
        :return:
        """
        vert1 = TestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = TestVertex(5, "New AbstractConstrainedVertex 2", 256)
        edge1 = AbstractPartitionableEdge(vert1, vert2)
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)
        self.assertEqual(edge1.label, None)

    def test_create_new_edge_with_constraint_list(self):
        """
        test initisation of a vertex with a max size constraint
        :return:
        """
        constraint = KeyAllocatorContiguousRangeContraint()
        vert1 = TestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = TestVertex(5, "New AbstractConstrainedVertex 2", 256)
        edge1 = AbstractPartitionableEdge(vert1, vert2, "edge 1", constraint)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")
        self.assertEqual(vert.constraints[0], constraint)



    def test_create_new_subedge_from_edge(self):
        """
        test that you can use the AbstractPartitionableEdge.create-subedge
        method and not cause errors
        :return:
        """
        vert1 = TestVertex(10, "New AbstractConstrainedVertex 1", 256)
        subv_from_vert1 = vert1.create_subvertex(
            Slice(0, 9), vert1.get_resources_used_by_atoms(Slice(0, 9), None))
        vert2 = TestVertex(5, "New AbstractConstrainedVertex 2", 256)
        subv_from_vert2 = vert2.create_subvertex(
            Slice(0, 4), vert2.get_resources_used_by_atoms(Slice(0, 4), None))
        edge1 = AbstractPartitionableEdge(vert1, vert2, "First edge")
        subedge1 = edge1.create_subedge(subv_from_vert1, subv_from_vert2)
        self.assertEqual(subedge1.label, "First edge")