"""
tests for graph mapper
"""
import unittest
from pacman.model.graphs.common import Slice, GraphMapper
from pacman.model.graphs.machine import MachineEdge, SimpleMachineVertex
from uinit_test_objects import SimpleTestEdge, SimpleTestVertex


class TestGraphMapper(unittest.TestCase):
    """
    graph mapper tests
    """

    def test_create_new_mapper(self):
        """
        test creating a empty graph mapper
        """
        GraphMapper()

    def test_get_edges_from_edge(self):
        """
        test getting the edges from a graph mapper from a edge
        """
        vertices = list()
        edges = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))
        edges.append(MachineEdge(vertices[0], vertices[1]))
        edges.append(MachineEdge(vertices[1], vertices[1]))
        sube = MachineEdge(vertices[1], vertices[0])
        edges.append(sube)
        graph = GraphMapper()
        edge = SimpleTestEdge(SimpleTestVertex(10, "pre"),
                              SimpleTestVertex(5, "post"))
        graph.add_edge_mapping(sube, edge)
        graph.add_edge_mapping(edges[0], edge)
        edges_from_edge = graph.get_machine_edges(edge)
        self.assertIn(sube, edges_from_edge)
        self.assertIn(edges[0], edges_from_edge)
        self.assertNotIn(edges[1], edges_from_edge)

    def test_get_vertices_from_vertex(self):
        """
        test getting the vertex from a graph mapper via the vertex
        """
        vertices = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))
        vertex1 = SimpleMachineVertex(None, "")
        vertex2 = SimpleMachineVertex(None, "")

        edges = list()
        edges.append(MachineEdge(vertices[0], vertices[1]))
        edges.append(MachineEdge(vertices[1], vertices[1]))

        graph_mapper = GraphMapper()
        vert = SimpleTestVertex(4, "Some testing vertex")

        vertex_slice = Slice(0, 1)
        graph_mapper.add_vertex_mapping(vertex1, vertex_slice, vert)
        vertex_slice = Slice(2, 3)
        graph_mapper.add_vertex_mapping(vertex2, vertex_slice, vert)

        returned_vertices = graph_mapper.get_machine_vertices(vert)

        self.assertIn(vertex1, returned_vertices)
        self.assertIn(vertex2, returned_vertices)
        for v in vertices:
            self.assertNotIn(v, returned_vertices)

    def test_get_vertex_from_vertex(self):
        """
        test that the graph mapper can retrieve a vertex from a given vertex
        """
        vertices = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))

        vertex1 = SimpleMachineVertex(None, "")
        vertex2 = SimpleMachineVertex(None, "")

        graph_mapper = GraphMapper()
        vert = SimpleTestVertex(10, "Some testing vertex")

        vertex_slice = Slice(0, 1)
        graph_mapper.add_vertex_mapping(vertex1, vertex_slice, vert)
        vertex_slice = Slice(2, 3)
        graph_mapper.add_vertex_mapping(vertex2, vertex_slice, vert)

        self.assertEquals(
            vert, graph_mapper.get_application_vertex(vertex1))
        self.assertEquals(
            vert, graph_mapper.get_application_vertex(vertex2))
        self.assertEquals(
            None, graph_mapper.get_application_vertex(vertices[0]))
        self.assertEquals(
            None, graph_mapper.get_application_vertex(vertices[1]))

    def test_get_edge_from_machine_edge(self):
        """
        test that tests getting a edge from a graph mapper
        """
        vertices = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))

        edges = list()
        edges.append(MachineEdge(vertices[0], vertices[1]))
        edges.append(MachineEdge(vertices[1], vertices[1]))

        sube = MachineEdge(vertices[1], vertices[0])
        edges.append(sube)

        # Create the graph mapper
        graph = GraphMapper()

        edge = SimpleTestEdge(SimpleTestVertex(10, "pre"),
                              SimpleTestVertex(5, "post"))
        graph.add_edge_mapping(sube, edge)
        graph.add_edge_mapping(edges[0], edge)

        edge_from_machine_edge = graph.get_application_edge(sube)

        self.assertEquals(edge_from_machine_edge, edge)
        self.assertEquals(
            graph.get_application_edge(edges[0]),
            edge)
        self.assertIsNone(graph.get_application_edge(edges[1]))


if __name__ == '__main__':
    unittest.main()
