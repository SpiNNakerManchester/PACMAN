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
from pacman.config_setup import unittest_setup
from pacman.model.graphs.application import ApplicationEdge, ApplicationGraph
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)
from pacman_test_objects import SimpleTestVertex


class TestApplicationGraphModel(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def setUp(self):
        unittest_setup()

    def test_create_new_empty_graph(self):
        ApplicationGraph()

    def test_create_new_graph(self):
        vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2", 256)
        vert3 = SimpleTestVertex(3, "New AbstractConstrainedVertex 3", 256)
        edge1 = ApplicationEdge(vert1, vert2, label="First edge")
        edge2 = ApplicationEdge(vert2, vert1, label="First edge")
        edge3 = ApplicationEdge(vert1, vert3, label="First edge")
        verts = [vert1, vert2, vert3]
        edges = [edge1, edge2, edge3]
        graph = ApplicationGraph()
        for vertex in verts:
            graph.add_vertex(vertex)
        for edge in edges:
            graph.add_edge(edge, "foo")  # Any old partition label
        assert frozenset(verts) == frozenset(graph.vertices)
        assert frozenset(edges) == frozenset(graph.edges)
        graph.reset()

    def test_add_vertex(self):
        graph = ApplicationGraph()
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_vertex("vertex")
        vert1 = SimpleTestVertex(10, "Test", 256)
        graph.add_vertex(vert1)
        with self.assertRaises(PacmanAlreadyExistsException):
            graph.add_vertex(vert1)
        vert2 = SimpleTestVertex(10, "Test", 256)
        self.assertNotEqual(vert1, vert2)
        self.assertEqual(vert1.label, vert2.label)
        graph.add_vertex(vert2)
        self.assertNotEqual(vert1.label, vert2.label)
        self.assertEqual(vert1, graph.vertex_by_label("Test"))

    def test_add_edge(self):
        graph = ApplicationGraph()
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_edge("edge", "spikes")
        vert1 = SimpleTestVertex(10, "Vertex 1", 256)
        vert2 = SimpleTestVertex(5, "Vertex 2", 256)
        edge1 = ApplicationEdge(vert1, vert2, label="First edge")
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_edge(edge1, "spikes")
        graph.add_vertex(vert1)
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_edge(edge1, "spikes")
        graph.add_vertex(vert2)
        graph.add_edge(edge1, "spikes")


if __name__ == '__main__':
    unittest.main()
