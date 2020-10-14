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
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import MachineEdge, SimpleMachineVertex
from uinit_test_objects import SimpleTestEdge, SimpleTestVertex


class TestGraphMapping(unittest.TestCase):
    """
    graph mapper tests
    """

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
