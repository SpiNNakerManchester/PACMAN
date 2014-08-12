import unittest
from pacman.model.partitionable_graph.vertex import Vertex
from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph import PartitionableGraph
from pacman.model.constraints.partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint


class MyVertex(Vertex):
    def get_resources_used_by_atoms(self, lo_atom, hi_atom):
        pass


class TestGraphModel(unittest.TestCase):
    def test_create_new_vertex(self):
        vert = MyVertex(10, "New Vertex")
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New Vertex")

    def test_create_new_vertex_without_label(self):
        vert = MyVertex(10, None)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "Population 0")

    def test_create_new_vertex_with_constraint_list(self):
        constraint = PartitionerMaximumSizeConstraint(2)
        vert = MyVertex(10, "New Vertex", [constraint])
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New Vertex")
        self.assertEqual(vert.constraints[0], constraint)

    def test_create_new_vertex_add_constraint(self):
        constraint1 = PartitionerMaximumSizeConstraint(2)
        constraint2 = PartitionerMaximumSizeConstraint(3)
        vert = MyVertex(10, "New Vertex", [constraint1])
        vert.add_constraint(constraint2)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New Vertex")
        self.assertEqual(vert.constraints[0], constraint1)
        self.assertEqual(vert.constraints[1], constraint2)

    def test_create_new_vertex_add_constraints(self):
        constraint1 = PartitionerMaximumSizeConstraint(2)
        constraint2 = PartitionerMaximumSizeConstraint(3)
        constr = list()
        constr.append(constraint1)
        constr.append(constraint2)
        vert = MyVertex(10, "New Vertex", [constraint1])
        vert.add_constraints(constr)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New Vertex")
        self.assertEqual(vert.constraints[0], constraint1)
        self.assertEqual(vert.constraints[1], constraint1)
        self.assertEqual(vert.constraints[2], constraint2)

    def test_create_subvertex_from_vertex_with_previous_constraints(self):
        constraint1 = PartitionerMaximumSizeConstraint(2)
        vert = MyVertex(10, "New Vertex", [constraint1])
        subv_from_vert = vert.create_subvertex(0, 9)
        self.assertEqual(subv_from_vert.constraints[0], constraint1)
        self.assertEqual(subv_from_vert.lo_atom, 0)
        self.assertEqual(subv_from_vert.hi_atom, 9)

    def test_new_create_subvertex_from_vertex_no_constraints(self):
        vert = MyVertex(10, "New Vertex")
        subv_from_vert = vert.create_subvertex(0, 9)
        self.assertEqual(subv_from_vert.lo_atom, 0)
        self.assertEqual(subv_from_vert.hi_atom, 9)


    def test_create_new_subvertex_from_vertex_with_additional_constraints(self):
        constraint1 = PartitionerMaximumSizeConstraint(2)
        constraint2 = PartitionerMaximumSizeConstraint(3)
        vert = MyVertex(10, "New Vertex", [constraint1])
        subv_from_vert = vert.create_subvertex(0, 9, None, [constraint2])
        self.assertEqual(len(subv_from_vert.constraints), 2)
        self.assertEqual(subv_from_vert.constraints[1], constraint1)
        self.assertEqual(subv_from_vert.constraints[0], constraint2)
        self.assertEqual(subv_from_vert.lo_atom, 0)
        self.assertEqual(subv_from_vert.hi_atom, 9)

    def test_create_new_edge(self):
        vert1 = MyVertex(10, "New Vertex 1")
        vert2 = MyVertex(5, "New Vertex 2")
        edge1 = PartitionableEdge(vert1, vert2, "First edge")
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)

    def test_create_new_subedge_from_edge(self):
        vert1 = MyVertex(10, "New Vertex 1")
        subv_from_vert1 = vert1.create_subvertex(0, 9)
        vert2 = MyVertex(5, "New Vertex 2")
        subv_from_vert2 = vert2.create_subvertex(0, 4)
        edge1 = PartitionableEdge(vert1, vert2, "First edge")
        subedge1 = edge1.create_subedge(subv_from_vert1, subv_from_vert2)
        self.assertEqual(subedge1.label, "First edge")

    def test_create_new_empty_graph(self):
        PartitionableGraph()

    def test_create_new_graph(self):
        vert1 = MyVertex(10, "New Vertex 1")
        vert2 = MyVertex(5, "New Vertex 2")
        vert3 = MyVertex(3, "New Vertex 3")
        edge1 = PartitionableEdge(vert1, vert2, "First edge")
        edge2 = PartitionableEdge(vert2, vert1, "First edge")
        edge3 = PartitionableEdge(vert1, vert3, "First edge")
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
            raise AssertionError("edge1 or edge3 is in incoming_edges_to vert1")


if __name__ == '__main__':
    unittest.main()
