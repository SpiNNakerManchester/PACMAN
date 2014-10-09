import unittest
from pacman.model.graph_mapper.graph_mapper \
    import GraphMapper
from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from pacman.model.partitionable_graph.partitionable_edge import \
    PartitionableEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.partitioned_graph.partitioned_edge import PartitionedEdge

from pacman.exceptions import (PacmanValueError, PacmanNotFoundError)


class MyVertex(AbstractPartitionableVertex):
    def __init__(self, n_atoms, label):
        super(MyVertex, self).__init__(n_atoms, label, 100)

    def get_resources_used_by_atoms(self, lo_atom, hi_atom):
        pass

    def get_cpu_usage_for_atoms(*args):
        pass

    def get_dtcm_usage_for_atoms(*args):
        pass

    def get_sdram_usage_for_atoms(*args):
        pass

    def model_name(*args):
        pass


class TestGraphSubgraphMapper(unittest.TestCase):
    def test_create_new_mapper(self):
        GraphMapper()

    def test_get_subedges_from_edge(self):
        subvertices = list()
        subedges = list()
        subvertices.append(PartitionedVertex(None, None))
        subvertices.append(PartitionedVertex(None, None))
        subedges.append(PartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(PartitionedEdge(subvertices[1], subvertices[1]))
        sube = PartitionedEdge(subvertices[1], subvertices[0])
        subedges.append(sube)
        graph = GraphMapper()
        edge = PartitionableEdge(MyVertex(10, "pre"), MyVertex(5, "post"))
        graph.add_partitioned_edge(sube, edge)
        graph.add_partitioned_edge(subedges[0], edge)
        subedges_from_edge = \
            graph.get_partitioned_edges_from_partitionable_edge(edge)
        self.assertIn(sube, subedges_from_edge)
        self.assertIn(subedges[0], subedges_from_edge)
        self.assertNotIn(subedges[1], subedges_from_edge)

    def test_get_subvertices_from_vertex(self):
        subvertices = list()
        subvertices.append(PartitionedVertex(0, 4, None))
        subvertices.append(PartitionedVertex(5, 9, None))
        subvert1 = PartitionedVertex(1, 2, None)
        subvert2 = PartitionedVertex(3, 4, None)

        subedges = list()
        subedges.append(PartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(PartitionedEdge(subvertices[1], subvertices[1]))

        graph_mapper = GraphMapper()
        vert = MyVertex(4, "Some testing vertex")

        graph_mapper.add_subvertex(subvert1, 0, 1, vert)
        graph_mapper.add_subvertex(subvert2, 2, 3, vert)

        returned_subverts = graph_mapper.get_subvertices_from_vertex(vert)

        self.assertIn(subvert1, returned_subverts)
        self.assertIn(subvert2, returned_subverts)
        for sub in subvertices:
            self.assertNotIn(sub, returned_subverts)

    def test_get_vertex_from_subvertex(self):
        subvertices = list()
        subvertices.append(PartitionedVertex(0, 4, None))
        subvertices.append(PartitionedVertex(5, 9, None))

        subvert1 = PartitionedVertex(1, 2, None)
        subvert2 = PartitionedVertex(3, 4, None)

        graph_mapper = GraphMapper()
        vert = MyVertex(10, "Some testing vertex")

        graph_mapper.add_subvertex(subvert1, 1, 2, vert)
        graph_mapper.add_subvertex(subvert2, 3, 4, vert)

        self.assertEqual(
            vert, graph_mapper.get_vertex_from_subvertex(subvert1))
        self.assertEqual(
            vert, graph_mapper.get_vertex_from_subvertex(subvert2))
        self.assertRaises(
            PacmanNotFoundError, graph_mapper.get_vertex_from_subvertex,
            subvertices[0])
        self.assertRaises(
            PacmanNotFoundError, graph_mapper.get_vertex_from_subvertex,
            subvertices[1])

    def test_get_edge_from_subedge(self):
        subvertices = list()
        subvertices.append(PartitionedVertex(0, 4, None))
        subvertices.append(PartitionedVertex(5, 9, None))

        subedges = list()
        subedges.append(PartitionedEdge(subvertices[0], subvertices[1]))
        subedges.append(PartitionedEdge(subvertices[1], subvertices[1]))

        sube = PartitionedEdge(subvertices[1], subvertices[0])
        subedges.append(sube)

        # Create the graph mapper
        graph = GraphMapper()

        edge = PartitionableEdge(MyVertex(10, "pre"), MyVertex(5, "post"))
        graph.add_partitioned_edge(sube, edge)
        graph.add_partitioned_edge(subedges[0], edge)

        edge_from_subedge = \
            graph.get_partitionable_edge_from_partitioned_edge(sube)

        self.assertEqual(edge_from_subedge, edge)
        self.assertEqual(
            graph.get_partitionable_edge_from_partitioned_edge(subedges[0]),
            edge
        )
        self.assertRaises(
            PacmanNotFoundError,
            graph.get_partitionable_edge_from_partitioned_edge,
            subedges[1]
        )


if __name__ == '__main__':
    unittest.main()
