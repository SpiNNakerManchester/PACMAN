import unittest
from pacman.model.graph_mapper.graph_mapper \
    import GraphMapper
from pacman.model.partitionable_graph.abstract_constrained_vertex import AbstractConstrainedVertex
from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.partitioned_graph.partitioned_edge import PartitionedEdge


class MyVertex(AbstractConstrainedVertex):
    def get_resources_used_by_atoms(self, lo_atom, hi_atom):
        pass


class TestGraphSubgraphMapper(unittest.TestCase):
    def test_create_new_mapper(self):
        GraphMapper()

    def test_get_subedges_from_edge(self):
        subvertices = list()
        subedges = list()
        subvertices.append(PartitionedVertex(0, 4, None))
        subvertices.append(PartitionedVertex(5, 9, None))
        subedges.append(PartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(PartitionedEdge(subvertices[1], subvertices[1]))
        sube = PartitionedEdge(subvertices[1], subvertices[0])
        subedges.append(sube)
        graph = GraphMapper()
        edge = PartitionableEdge(MyVertex(10, "pre"), MyVertex(5, "post"))
        graph.add_subedge(sube, edge)
        graph.add_subedge(subedges[0], edge)
        subedges_from_edge = graph.get_subedges_from_edge(edge)
        self.assertIn(sube, subedges_from_edge)
        self.assertIn(subedges[0], subedges_from_edge)
        self.assertNotIn(subedges[1], subedges_from_edge)

    def test_get_subvertices_from_vertex(self):
        subvertices = list()
        subedges = list()
        subvertices.append(PartitionedVertex(0, 4, None))
        subvertices.append(PartitionedVertex(5, 9, None))
        subedges.append(PartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(PartitionedEdge(subvertices[1], subvertices[1]))
        subvert1 = PartitionedVertex(1, 2, None)
        subvert2 = PartitionedVertex(3, 4, None)
        graph = GraphMapper()
        vert = MyVertex(4, "Some testing vertex")
        graph.add_subvertices([subvert1, subvert2], vert)
        returned_subverts = graph.get_subvertices_from_vertex(vert)
        self.assertIn(subvert1, returned_subverts)
        self.assertIn(subvert2, returned_subverts)
        for sub in subvertices:
            self.assertNotIn(sub, returned_subverts)

    def test_get_vertex_from_subvertex(self):
        subvertices = list()
        subedges = list()
        subvertices.append(PartitionedVertex(0, 4, None))
        subvertices.append(PartitionedVertex(5, 9, None))
        subedges.append(PartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(PartitionedEdge(subvertices[1], subvertices[1]))
        subvert1 = PartitionedVertex(1, 2, None)
        subvert2 = PartitionedVertex(3, 4, None)
        graph = GraphMapper()
        vert = MyVertex(4, "Some testing vertex")
        graph.add_subvertices([subvert1, subvert2], vert)
        self.assertEqual(vert, graph.get_vertex_from_subvertex(subvert1))
        self.assertEqual(vert, graph.get_vertex_from_subvertex(subvert2))
        self.assertEqual(None, graph.get_vertex_from_subvertex(subvertices[0]))
        self.assertEqual(None, graph.get_vertex_from_subvertex(subvertices[1]))

    def test_get_edge_from_subedge(self):
        subvertices = list()
        subedges = list()
        subvertices.append(PartitionedVertex(0, 4, None))
        subvertices.append(PartitionedVertex(5, 9, None))
        subedges.append(PartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(PartitionedEdge(subvertices[1], subvertices[1]))
        sube = PartitionedEdge(subvertices[1], subvertices[0])
        subedges.append(sube)
        graph = GraphMapper()
        edge = PartitionableEdge(MyVertex(10, "pre"), MyVertex(5, "post"))
        graph.add_subedge(sube, edge)
        graph.add_subedge(subedges[0], edge)
        edge_from_subedge = graph.get_edge_from_subedge(sube)
        self.assertEqual(edge_from_subedge, edge)
        self.assertEqual(graph.get_edge_from_subedge(subedges[0]), edge)
        self.assertEqual(graph.get_edge_from_subedge(subedges[1]), None)


if __name__ == '__main__':
    unittest.main()
