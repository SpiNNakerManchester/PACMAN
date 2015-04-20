"""
test that tests the partitionable edge generation
"""

# pacman imports
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_contiguous_range_constraint import \
    KeyAllocatorContiguousRangeContraint
from pacman.model.graph_mapper.slice import Slice

# unit tests imports
from uinit_test_objects.test_edge import TestPartitionableEdge
from uinit_test_objects.test_vertex import TestVertex


# general imports
import unittest
from pacman.model.abstract_classes.abstract_partitioned_edge import \
    AbstractPartitionedEdge


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
        edge1 = TestPartitionableEdge(vert1, vert2, "First edge")
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)

    def test_create_new_edge_without_label(self):
        """
        test initisation of a edge without a label
        :return:
        """
        vert1 = TestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = TestVertex(5, "New AbstractConstrainedVertex 2", 256)
        edge1 = TestPartitionableEdge(vert1, vert2)
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)
        self.assertEqual(edge1.label, None)

    def test_create_new_edge_with_constraint_list(self):
        """
        test initisation of a edge with a constraint
        :return:
        """
        constraints = list()
        constraints.append(KeyAllocatorContiguousRangeContraint())
        vert1 = TestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = TestVertex(5, "New AbstractConstrainedVertex 2", 256)
        edge1 = TestPartitionableEdge(vert1, vert2, "edge 1", constraints)
        self.assertEqual(edge1.constraints[0], constraints[0])

    def test_create_new_edge_add_constraint(self):
        """
        test creating a edge and then adding constraints in a list
        :return:
        """
        constraint1 = KeyAllocatorContiguousRangeContraint()
        constraint2 = KeyAllocatorContiguousRangeContraint()
        constr = list()
        constr.append(constraint1)
        constr.append(constraint2)
        vert1 = TestVertex(10, "New AbstractConstrainedVertex", 256)
        vert2 = TestVertex(10, "New AbstractConstrainedVertex", 256)
        edge1 = TestPartitionableEdge(vert1, vert2, "edge 1")
        edge1.add_constraints(constr)
        for constraint in constr:
            self.assertIn(constraint, edge1.constraints)

    def test_create_new_vertex_add_constraints(self):
        """
        test that  creating a edge and then adding constraints indivusally
        :return:
        """
        constraint1 = KeyAllocatorContiguousRangeContraint()
        constraint2 = KeyAllocatorContiguousRangeContraint()
        constr = list()
        constr.append(constraint1)
        constr.append(constraint2)
        vert1 = TestVertex(10, "New AbstractConstrainedVertex", 256)
        vert2 = TestVertex(10, "New AbstractConstrainedVertex", 256)
        edge1 = TestPartitionableEdge(vert1, vert2, "edge 1")
        edge1.add_constraint(constraint1)
        edge1.add_constraint(constraint2)

        for constraint in constr:
            self.assertIn(constraint, edge1.constraints)

    def test_create_subvertex_from_vertex_with_previous_constraints(self):
        """
        test the create subedge command given by the
        TestPartitionableEdge actually works and generates a subedge
        with the same constraints mapped over
        :return:
        """
        constraint1 = KeyAllocatorContiguousRangeContraint()
        vert1 = TestVertex(10, "New AbstractConstrainedVertex", 256)
        subv_from_vert1 = vert1.create_subvertex(
            Slice(0, 9),
            vert1.get_resources_used_by_atoms(Slice(0, 9), None))
        vert2 = TestVertex(10, "New AbstractConstrainedVertex", 256)
        subv_from_vert2 = vert2.create_subvertex(
            Slice(0, 9),
            vert2.get_resources_used_by_atoms(Slice(0, 9), None))
        edge1 = TestPartitionableEdge(vert1, vert2, "edge 1")
        edge1.add_constraint(constraint1)

        subedge = edge1.create_subedge(subv_from_vert1, subv_from_vert2)
        self.assertIn(constraint1, subedge.constraints)

    def test_new_create_subvertex_from_vertex_no_constraints(self):
        """
        test the creating of a subedge by the AbstractPartitionableEdge
        create subedge method will actually create a subedge of the
        partitioned edge type.
        :return:
        """
        vert1 = TestVertex(10, "New AbstractConstrainedVertex", 256)
        subv_from_vert1 = vert1.create_subvertex(
            Slice(0, 9),
            vert1.get_resources_used_by_atoms(Slice(0, 9), None))
        vert2 = TestVertex(10, "New AbstractConstrainedVertex", 256)
        subv_from_vert2 = vert2.create_subvertex(
            Slice(0, 9),
            vert2.get_resources_used_by_atoms(Slice(0, 9), None))
        edge1 = TestPartitionableEdge(vert1, vert2, "edge 1")

        subedge = edge1.create_subedge(subv_from_vert1, subv_from_vert2)
        self.assertIsInstance(subedge, AbstractPartitionedEdge)

    def test_create_new_subedge_from_edge(self):
        """
        test that you can use the TestPartitionableEdge.create-subedge
        method and not cause errors
        :return:
        """
        vert1 = TestVertex(10, "New AbstractConstrainedVertex 1", 256)
        subv_from_vert1 = vert1.create_subvertex(
            Slice(0, 9), vert1.get_resources_used_by_atoms(Slice(0, 9), None))
        vert2 = TestVertex(5, "New AbstractConstrainedVertex 2", 256)
        subv_from_vert2 = vert2.create_subvertex(
            Slice(0, 4), vert2.get_resources_used_by_atoms(Slice(0, 4), None))
        edge1 = TestPartitionableEdge(vert1, vert2, "First edge")
        subedge1 = edge1.create_subedge(subv_from_vert1, subv_from_vert2,
                                        None, "First sub edge")
        self.assertEqual(subedge1.label, "First sub edge")