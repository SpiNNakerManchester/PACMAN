# pacman imports
from pacman.model.graphs.application.simple_application_edge \
    import SimpleApplicationEdge
from pacman.model.graphs.application.application_graph \
    import ApplicationGraph

# uinit test object imports
from uinit_test_objects.test_vertex import TestVertex

# general imports
import unittest


class TestApplicationGraphModel(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def test_create_new_empty_graph(self):
        """

        :return:
        """
        ApplicationGraph()

    def test_create_new_graph(self):
        vert1 = TestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = TestVertex(5, "New AbstractConstrainedVertex 2", 256)
        vert3 = TestVertex(3, "New AbstractConstrainedVertex 3", 256)
        edge1 = SimpleApplicationEdge(vert1, vert2, None, "First edge")
        edge2 = SimpleApplicationEdge(vert2, vert1, None, "First edge")
        edge3 = SimpleApplicationEdge(vert1, vert3, None, "First edge")
        verts = [vert1, vert2, vert3]
        edges = [edge1, edge2, edge3]
        graph = ApplicationGraph("Graph", verts, edges)
        for i in range(3):
            self.assertEqual(graph.vertices[i], verts[i])
            self.assertEqual(graph.edges[i], edges[i])

        oev = graph.get_edges_starting_at_vertex(vert1)
        if edge2 in oev:
            raise AssertionError("edge2 is in outgoing_edges_from vert1")
        iev = graph.get_edges_ending_at_vertex(vert1)
        if edge1 in iev or edge3 in iev:
            raise AssertionError(
                "edge1 or edge3 is in incoming_edges_to vert1")


if __name__ == '__main__':
    unittest.main()
