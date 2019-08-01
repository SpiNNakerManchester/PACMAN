# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from pacman.model.graphs.application import ApplicationEdge, ApplicationGraph
from uinit_test_objects import SimpleTestVertex


class TestApplicationGraphModel(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def test_create_new_empty_graph(self):
        ApplicationGraph("foo")

    def test_create_new_graph(self):
        vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2", 256)
        vert3 = SimpleTestVertex(3, "New AbstractConstrainedVertex 3", 256)
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

        assert edge1 not in graph.get_edges_ending_at_vertex(vert1)
        assert edge2 not in graph.get_edges_starting_at_vertex(vert1)
        assert edge3 not in graph.get_edges_ending_at_vertex(vert1)


if __name__ == '__main__':
    unittest.main()
