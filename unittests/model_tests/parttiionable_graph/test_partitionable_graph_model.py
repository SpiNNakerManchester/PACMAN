"""
test that tests the partitionable graph
"""

# pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex   
from pacman.model.partitionable_graph.abstract_partitionable_edge \
    import AbstractPartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph \
    import PartitionableGraph
from pacman.model.constraints.partitioner_constraints\
    .partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint
from pacman.model.graph_mapper.slice import Slice
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.resources.resource_container import ResourceContainer

# general imports
import unittest


class MyVertex(AbstractPartitionableVertex):
    """
    test vertex
    """

    def get_resources_used_by_atoms(self, vertex_slice, vertex_in_edges):
        """
        standard method call to get the sdram, cpu and dtcm usage of a
        collection of atoms
        :param vertex_slice: the collection of atoms
        :param vertex_in_edges: the edges coming into this partitionable vertex
        :return:
        """
        return ResourceContainer(None, None, None)

    def model_name(self):
        """
        the model name of this test vertex
        :return:
        """
        return "test model"

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice: the atoms being considered
        :param graph: the partitionable graph
        :return: the amount of cpu (in cycles this model will use)
        """
        return 1 * vertex_slice.n_atoms

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice: the atoms being considered
        :param graph: the partitionable graph
        :return: the amount of dtcm (in bytes this model will use)
        """
        return 1 * vertex_slice.n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        :param vertex_slice: the atoms being considered
        :param graph: the partitionable graph
        :return: the amount of sdram (in bytes this model will use)
        """
        return 1 * vertex_slice.n_atoms


class TestPartitionableGraphModel(unittest.TestCase):
    """
    tests which test the partitionable graph object
    """
    def test_create_new_vertex(self):
        """
        test initisation of a vertex
        :return:
        """
        vert = MyVertex(10, "New AbstractConstrainedVertex", 256)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")

    def test_create_new_vertex_without_label(self):
        """
        test initisation of a vertex without a label
        :return:
        """
        vert = MyVertex(10, "Population", 256)
        self.assertEqual(vert.n_atoms, 10)
        pieces = vert.label.split(" ")
        self.assertIn(pieces[0], "Population n")

    def test_create_new_vertex_with_constraint_list(self):
        """
        test initisation of a vertex with a max size constraint
        :return:
        """
        constraint = PartitionerMaximumSizeConstraint(2)
        vert = MyVertex(10, "New AbstractConstrainedVertex", 256, [constraint])
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")
        self.assertEqual(vert.constraints[0], constraint)

    def test_create_new_vertex_add_constraint(self):
        """
        test creating a vertex and then adding constraints indivusally
        :return:
        """
        constraint1 = PartitionerMaximumSizeConstraint(2)
        constraint2 = PartitionerMaximumSizeConstraint(3)
        constr = list()
        constr.append(constraint1)
        constr.append(constraint2)
        vert = MyVertex(10, "New AbstractConstrainedVertex", 256,
                        [constraint1])
        vert.add_constraint(constraint2)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(len(vert.constraints), 2 + 1)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")
        for constraint in constr:
            self.assertIn(constraint, vert.constraints)

    def test_create_new_vertex_add_constraints(self):
        """
        test that  creating a vertex and then adding constraints in a list
        :return:
        """
        constraint1 = PartitionerMaximumSizeConstraint(2)
        constraint2 = PartitionerMaximumSizeConstraint(3)
        constr = list()
        constr.append(constraint1)
        constr.append(constraint2)
        vert = MyVertex(10, "New AbstractConstrainedVertex", 256,
                        [constraint1])
        vert.add_constraints(constr)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")
        self.assertEqual(len(vert.constraints), 3 + 1)
        for constraint in constr:
            self.assertIn(constraint, vert.constraints)

    def test_create_subvertex_from_vertex_with_previous_constraints(self):
        """
        test the create subvertex command given by the
        AbstractPartitionableVertex actually works and generates a subvertex
        with the same constraints mapped over
        :return:
        """
        constraint1 = PartitionerMaximumSizeConstraint(2)
        vert = MyVertex(10, "New AbstractConstrainedVertex", 256,
                        [constraint1])
        subv_from_vert = vert.create_subvertex(
            Slice(0, 9),
            vert.get_resources_used_by_atoms(Slice(0, 9), None))
        self.assertIn(constraint1, subv_from_vert.constraints)

    def test_new_create_subvertex_from_vertex_no_constraints(self):
        """
        test the creating of a subvertex by the AbstractPartitionableVertex
        create subvertex method will actually create a subvertex of the
        partitioned vertex type.
        :return:
        """
        vert = MyVertex(10, "New AbstractConstrainedVertex", 256)
        subvertex = vert.create_subvertex(
            Slice(0, 9),
            vert.get_resources_used_by_atoms(Slice(0, 9), None))
        self.assertIsInstance(subvertex, PartitionedVertex)

    def test_new_create_subvertex_from_vertex_check_resources(self):
        """ check that the creation of a subvertex means that the reosurces
        calcualted by the partitionable vertex is the same as what the
        parttiioned vertex says (given same sizes)

        :return:
        """
        vert = MyVertex(10, "New AbstractConstrainedVertex", 256)
        resources = vert.get_resources_used_by_atoms(0, 9, None)
        subv_from_vert = vert.create_subvertex(Slice(0, 9), resources, "")
        self.assertEqual(subv_from_vert.resources_required, resources)

    def test_create_new_subvertex_from_vertex_with_additional_constraints(
            self):
        """
        test that a subvertex created from a parti9onable vertex with
        constraints can have more constraints added to it.
        :return:
        """
        constraint1 = PartitionerMaximumSizeConstraint(2)
        constraint2 = PartitionerMaximumSizeConstraint(3)
        vert = MyVertex(10, "New AbstractConstrainedVertex", 256,
                        [constraint1])
        subv_from_vert = vert.create_subvertex(
            Slice(0, 9),
            vert.get_resources_used_by_atoms(Slice(0, 9), None), "",
            [constraint2])
        self.assertEqual(len(subv_from_vert.constraints), 2 + 1)
        self.assertEqual(subv_from_vert.constraints[1], constraint1)
        self.assertEqual(subv_from_vert.constraints[0], constraint2)

    def test_create_new_edge(self):
        """
        test that you can create a edge between two vertices
        :return:
        """
        vert1 = MyVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = MyVertex(5, "New AbstractConstrainedVertex 2", 256)
        edge1 = AbstractPartitionableEdge(vert1, vert2, "First edge")
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)

    def test_create_new_subedge_from_edge(self):
        """
        test that you can use the AbstractPartitionableEdge.create-subedge
        method and not cause errors
        :return:
        """
        vert1 = MyVertex(10, "New AbstractConstrainedVertex 1", 256)
        subv_from_vert1 = vert1.create_subvertex(
            Slice(0, 9), vert1.get_resources_used_by_atoms(Slice(0, 9), None))
        vert2 = MyVertex(5, "New AbstractConstrainedVertex 2", 256)
        subv_from_vert2 = vert2.create_subvertex(
            Slice(0, 4), vert2.get_resources_used_by_atoms(Slice(0, 4), None))
        edge1 = AbstractPartitionableEdge(vert1, vert2, "First edge")
        subedge1 = edge1.create_subedge(subv_from_vert1, subv_from_vert2)
        self.assertEqual(subedge1.label, "First edge")

    def test_create_new_empty_graph(self):
        """

        :return:
        """
        PartitionableGraph()

    def test_create_new_graph(self):
        vert1 = MyVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = MyVertex(5, "New AbstractConstrainedVertex 2", 256)
        vert3 = MyVertex(3, "New AbstractConstrainedVertex 3", 256)
        edge1 = AbstractPartitionableEdge(vert1, vert2, "First edge")
        edge2 = AbstractPartitionableEdge(vert2, vert1, "First edge")
        edge3 = AbstractPartitionableEdge(vert1, vert3, "First edge")
        verts = [vert1, vert2, vert3]
        edges = [edge1, edge2, edge3]
        graph = PartitionableGraph("Graph", verts, edges)
        for i in range(3):
            self.assertEqual(graph.vertices[i], verts[i])
            self.assertEqual(graph.edges[i], edges[i])

        oev = graph.outgoing_edges_from_vertex(vert1)
        if edge2 in oev:
            raise AssertionError("edge2 is in outgoing_edges_from vert1")
        iev = graph.incoming_edges_to_vertex(vert1)
        if edge1 in iev or edge3 in iev:
            raise AssertionError(
                "edge1 or edge3 is in incoming_edges_to vert1")


if __name__ == '__main__':
    unittest.main()
