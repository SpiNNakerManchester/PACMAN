"""
tests for graph mapper
"""

# unit test objects
from uinit_test_objects.test_edge import TestPartitionableEdge
from uinit_test_objects.test_vertex import TestVertex

# pacman imports
from pacman.model.graph_mapper.slice import Slice
from pacman.model.graph_mapper.graph_mapper \
    import GraphMapper
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.exceptions import (PacmanNotFoundError)

# general imports
import unittest


class TestGraphSubgraphMapper(unittest.TestCase):
    """
    graph mapper tests
    """

    def test_create_new_mapper(self):
        """
        test creating a empty graph mapper
        :return:
        """
        GraphMapper()

    def test_get_subedges_from_edge(self):
        """
        test getting the subedges from a graph mapper from a edge
        :return:
        """
        subvertices = list()
        subedges = list()
        subvertices.append(PartitionedVertex(None, ""))
        subvertices.append(PartitionedVertex(None, ""))
        subedges.append(MultiCastPartitionedEdge(subvertices[0],
                                                 subvertices[1]))
        subedges.append(MultiCastPartitionedEdge(subvertices[1],
                                                 subvertices[1]))
        sube = MultiCastPartitionedEdge(subvertices[1], subvertices[0])
        subedges.append(sube)
        graph = GraphMapper()
        edge = TestPartitionableEdge(TestVertex(10, "pre"),
                                     TestVertex(5, "post"))
        graph.add_partitioned_edge(sube, edge)
        graph.add_partitioned_edge(subedges[0], edge)
        subedges_from_edge = \
            graph.get_partitioned_edges_from_partitionable_edge(edge)
        self.assertIn(sube, subedges_from_edge)
        self.assertIn(subedges[0], subedges_from_edge)
        self.assertNotIn(subedges[1], subedges_from_edge)

    def test_get_subvertices_from_vertex(self):
        """
        test getting the subvertex from a graph mappert via the vertex
        :return:
        """
        subvertices = list()
        subvertices.append(PartitionedVertex(None, ""))
        subvertices.append(PartitionedVertex(None, ""))
        subvert1 = PartitionedVertex(None, "")
        subvert2 = PartitionedVertex(None, "")

        subedges = list()
        subedges.append(MultiCastPartitionedEdge(subvertices[0],
                                                 subvertices[1]))
        subedges.append(MultiCastPartitionedEdge(subvertices[1],
                                                 subvertices[1]))

        graph_mapper = GraphMapper()
        vert = TestVertex(4, "Some testing vertex")

        vertex_slice = Slice(0, 1)
        graph_mapper.add_subvertex(subvert1, vertex_slice, vert)
        vertex_slice = Slice(2, 3)
        graph_mapper.add_subvertex(subvert2, vertex_slice, vert)

        returned_subverts = graph_mapper.get_subvertices_from_vertex(vert)

        self.assertIn(subvert1, returned_subverts)
        self.assertIn(subvert2, returned_subverts)
        for sub in subvertices:
            self.assertNotIn(sub, returned_subverts)

    def test_get_vertex_from_subvertex(self):
        subvertices = list()
        subvertices.append(PartitionedVertex(None, ""))
        subvertices.append(PartitionedVertex(None, ""))

        subvert1 = PartitionedVertex(None, "")
        subvert2 = PartitionedVertex(None, "")

        graph_mapper = GraphMapper()
        vert = TestVertex(10, "Some testing vertex")

        vertex_slice = Slice(0, 1)
        graph_mapper.add_subvertex(subvert1, vertex_slice, vert)
        vertex_slice = Slice(2, 3)
        graph_mapper.add_subvertex(subvert2, vertex_slice, vert)

        self.assertEqual(
            vert, graph_mapper.get_vertex_from_subvertex(subvert1))
        self.assertEqual(
            vert, graph_mapper.get_vertex_from_subvertex(subvert2))
        self.assertEqual(
            None, graph_mapper.get_vertex_from_subvertex(subvertices[0]))
        self.assertEqual(
            None, graph_mapper.get_vertex_from_subvertex(subvertices[1]))

    def test_get_edge_from_subedge(self):
        """
        test that tests getting a edge from a graph mapper based off its subedge
        :return:
        """
        subvertices = list()
        subvertices.append(PartitionedVertex(None, ""))
        subvertices.append(PartitionedVertex(None, ""))

        subedges = list()
        subedges.append(MultiCastPartitionedEdge(subvertices[0],
                                                 subvertices[1]))
        subedges.append(MultiCastPartitionedEdge(subvertices[1],
                                                 subvertices[1]))

        sube = MultiCastPartitionedEdge(subvertices[1], subvertices[0])
        subedges.append(sube)

        # Create the graph mapper
        graph = GraphMapper()

        edge = TestPartitionableEdge(TestVertex(10, "pre"),
                                     TestVertex(5, "post"))
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
