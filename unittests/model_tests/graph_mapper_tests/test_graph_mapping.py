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

"""
tests for graph mapping
"""
import unittest

from pacman.config_setup import unittest_setup
from pacman.model.graphs.application import ApplicationGraph
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman_test_objects import SimpleTestVertex


class TestGraphMapping(unittest.TestCase):
    """
    graph mapper tests
    """

    def setUp(self):
        unittest_setup()

    def test_get_vertices_from_vertex(self):
        """
        test getting the vertex from a graph mapper via the vertex
        """
        vertices = list()
        app_graph = ApplicationGraph("bacon")
        vert = SimpleTestVertex(10, "Some testing vertex")
        app_graph.add_vertex(vert)
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))
        vertex1 = SimpleMachineVertex(
            None, "", vertex_slice=Slice(0, 1), app_vertex=vert)
        vertex2 = SimpleMachineVertex(
            None, "", vertex_slice=Slice(2, 3), app_vertex=vert)
        vert.remember_machine_vertex(vertex1)
        vert.remember_machine_vertex(vertex2)

        returned_vertices = vert.machine_vertices

        self.assertIn(vertex1, returned_vertices)
        self.assertIn(vertex2, returned_vertices)
        for v in vertices:
            self.assertNotIn(v, returned_vertices)

    def test_get_vertex_from_vertex(self):
        """
        test that the graph mapper can retrieve a vertex from a given vertex
        """
        app_graph = ApplicationGraph("bacon")
        vert = SimpleTestVertex(10, "Some testing vertex")
        app_graph.add_vertex(vert)
        vertex1 = SimpleMachineVertex(None, "", app_vertex=vert,
                                      vertex_slice=Slice(0, 1))
        vertex2 = SimpleMachineVertex(None, "", app_vertex=vert,
                                      vertex_slice=Slice(2, 3))
        vert.remember_machine_vertex(vertex1)
        vert.remember_machine_vertex(vertex2)

        self.assertEqual(vert, vertex1.app_vertex)
        self.assertEqual(vert, vertex2.app_vertex)
        self.assertEqual([vertex1, vertex2], list(vert.machine_vertices))


if __name__ == '__main__':
    unittest.main()
