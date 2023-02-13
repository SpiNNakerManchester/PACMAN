# Copyright (c) 2017-2023 The University of Manchester
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

"""
tests for graph mapping
"""
import unittest

from pacman.config_setup import unittest_setup
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
        vert = SimpleTestVertex(10, "Some testing vertex")
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
        vert = SimpleTestVertex(10, "Some testing vertex")
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
