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
        graph.add_partitioned_edge(sube, edge)
        graph.add_partitioned_edge(subedges[0], edge)
        subedges_from_edge = graph.get_partitioned_edges_from_partitionable_edge(edge)
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
        graph_mapper = GraphMapper()
        vert = MyVertex(4, "Some testing vertex")
        graph_mapper.add_subvertex(subvert1, 1, 2, vert)
        graph_mapper.add_subvertex(subvert2, 3, 4, vert)
        returned_subverts = graph_mapper.get_subvertices_from_vertex(vert)
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
        graph_mapper = GraphMapper()
        vert = MyVertex(4, "Some testing vertex")
        graph_mapper.add_subvertex(subvert1, 1, 2, vert)
        graph_mapper.add_subvertex(subvert2, 3, 4, vert)
        self.assertEqual(vert, graph_mapper.get_vertex_from_subvertex(subvert1))
        self.assertEqual(vert, graph_mapper.get_vertex_from_subvertex(subvert2))
        self.assertEqual(None, graph_mapper.get_vertex_from_subvertex(subvertices[0]))
        self.assertEqual(None, graph_mapper.get_vertex_from_subvertex(subvertices[1]))

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
        graph.add_partitioned_edge(sube, edge)
        graph.add_partitioned_edge(subedges[0], edge)
        edge_from_subedge = graph.get_partitionable_edge_from_partitioned_edge(sube)
        self.assertEqual(edge_from_subedge, edge)
        self.assertEqual(graph.get_partitionable_edge_from_partitioned_edge(subedges[0]), edge)
        self.assertEqual(graph.get_partitionable_edge_from_partitioned_edge(subedges[1]), None)

    def test_get_subedges_from_pre_subvertex(self):
        """Tests that subedges may be queried from the subgraph mapper based on
        pre-subvertex.
        """
        # Create subvertices and subedges
        vertices = [MyVertex(l) for l in ['A', 'B']]
        subvertices = [PartitionedVertex(None, 'A'), PartitionedVertex(None, 'B')]
        subedges = [PartitionedEdge(subvertices[0], subvertices[1]),
                    PartitionedEdge(subvertices[1], subvertices[0])]
        edges = [PartitionableEdge(vertices[0], vertices[1]),
                 PartitionableEdge(vertices[1], vertices[0])]


        # Construct the graph mapping
        gm = GraphMapper()
        for sv in subvertices:
            gm.add_subvertex(sv, 0, 1)

        for se, e in zip(subedges, edges):
            gm.add_partitioned_edge(se, e)

        # Get subedges from pre-subvertex
        subedges0 = gm.get_partitioned_edges_from_pre_partitioned_vertex(
            subvertices[0]
        )
        subedges1 = gm.get_partitioned_edges_from_pre_partitioned_vertex(
            subvertices[1]
        )

        # Assert these were returned correctly
        self.assertIn(subedges[0], subedges0)
        self.assertNotIn(subedges[1], subedges0)
        self.assertIn(subedges[1], subedges1)
        self.assertNotIn(subedges[0], subedges1)

if __name__ == '__main__':
    unittest.main()
