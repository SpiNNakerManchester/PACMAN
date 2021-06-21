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
from pacman.model.graphs.machine import MachineEdge, SimpleMachineVertex, \
    MachineGraph
from pacman_test_objects import SimpleTestEdge, SimpleTestVertex


class TestGraphMapping(unittest.TestCase):
    """
    graph mapper tests
    """

    def setUp(self):
        unittest_setup()

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
        edge = SimpleTestEdge(SimpleTestVertex(10, "pre"),
                              SimpleTestVertex(5, "post"))
        edge.remember_associated_machine_edge(sube)
        edge.remember_associated_machine_edge(edges[0])
        edges_from_edge = edge.machine_edges
        self.assertIn(sube, edges_from_edge)
        self.assertIn(edges[0], edges_from_edge)
        self.assertNotIn(edges[1], edges_from_edge)

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
        mac_graph = MachineGraph("cooked bacon", application_graph=app_graph)
        vertex1 = SimpleMachineVertex(
            None, "", vertex_slice=Slice(0, 1), app_vertex=vert)
        vertex2 = SimpleMachineVertex(
            None, "", vertex_slice=Slice(2, 3), app_vertex=vert)
        mac_graph.add_vertex(vertex1)
        mac_graph.add_vertex(vertex2)

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
        machine_graph = MachineGraph(
            application_graph=app_graph, label="cooked_bacon")
        machine_graph.add_vertex(vertex1)
        machine_graph.add_vertex(vertex2)

        self.assertEqual(vert, vertex1.app_vertex)
        self.assertEqual(vert, vertex2.app_vertex)
        self.assertEqual([vertex1, vertex2], list(vert.machine_vertices))

    def test_get_edge_from_machine_edge(self):
        """
        test that tests getting a edge from a graph mapper
        """
        vertices = list()
        vertices.append(SimpleMachineVertex(None, ""))
        vertices.append(SimpleMachineVertex(None, ""))

        edge = SimpleTestEdge(SimpleTestVertex(10, "pre"),
                              SimpleTestVertex(5, "post"))

        edges = list()
        edges.append(MachineEdge(vertices[0], vertices[1], app_edge=edge))
        edges.append(MachineEdge(vertices[1], vertices[1]))

        sube = MachineEdge(vertices[1], vertices[0], app_edge=edge)
        edges.append(sube)

        edge.remember_associated_machine_edge(sube)
        edge.remember_associated_machine_edge(edges[0])

        self.assertEqual(sube.app_edge, edge)
        self.assertEqual(edges[0].app_edge, edge)
        self.assertIsNone(edges[1].app_edge)


if __name__ == '__main__':
    unittest.main()
