# Copyright (c) 2014-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
        self.assertEqual("First edge", edge1.label)
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_edge(edge1, "spikes")
        graph.add_vertex(vert1)
        with self.assertRaises(PacmanInvalidParameterException):
            graph.add_edge(edge1, "spikes")
        graph.add_vertex(vert2)
        graph.add_edge(edge1, "spikes")


if __name__ == '__main__':
    unittest.main()
