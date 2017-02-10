# pacman imports
from pacman.model.graphs.application.impl.application_edge \
    import ApplicationEdge

from pacman.model.graphs.application.impl.application_graph \
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
        ApplicationGraph("foo")

    def test_create_new_graph(self):
        vert1 = TestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = TestVertex(5, "New AbstractConstrainedVertex 2", 256)
        vert3 = TestVertex(3, "New AbstractConstrainedVertex 3", 256)
        edge1 = ApplicationEdge(vert1, vert2, None, "First edge")
        edge2 = ApplicationEdge(vert2, vert1, None, "First edge")
        edge3 = ApplicationEdge(vert1, vert3, None, "First edge")
        verts = [vert1, vert2, vert3]
        edges = [edge1, edge2, edge3]
        graph = ApplicationGraph("Graph")
        graph.add_vertices(verts)
        graph.add_edges(edges, "foo")  # Any old partition label
        assert frozenset(verts) == frozenset(graph.vertices)
        assert frozenset(edges) == frozenset(graph.edges)

        oev = graph.get_edges_starting_at_vertex(vert1)
        if edge2 in oev:
            raise AssertionError("edge2 is in outgoing_edges_from vert1")
        iev = graph.get_edges_ending_at_vertex(vert1)
        if edge1 in iev or edge3 in iev:
            raise AssertionError(
                "edge1 or edge3 is in incoming_edges_to vert1")


if __name__ == '__main__':
    unittest.main()
