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
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import MachineEdge
from uinit_test_objects import SimpleTestEdge, SimpleTestVertex


class TestApplicationEdgeModel(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def test_create_new_edge(self):
        """
        test that you can create a edge between two vertices
        """
        vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2", 256)
        edge1 = SimpleTestEdge(vert1, vert2, "First edge")
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)

    def test_create_new_edge_without_label(self):
        """
        test initisation of a edge without a label
        """
        vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1", 256)
        vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2", 256)
        edge1 = SimpleTestEdge(vert1, vert2)
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)
        self.assertEqual(edge1.label, None)

    def test_new_create_machine_vertex_from_vertex_no_constraints(self):
        """
        test the creating of a edge by the SimpleTestEdge
        create edge method will actually create a edge of the
        edge type.
        """
        vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        v_from_vert1 = vert1.create_machine_vertex(
            Slice(0, 9),
            vert1.get_resources_used_by_atoms(Slice(0, 9)))
        vert2 = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        v_from_vert2 = vert2.create_machine_vertex(
            Slice(0, 9),
            vert2.get_resources_used_by_atoms(Slice(0, 9)))
        edge1 = SimpleTestEdge(vert1, vert2, "edge 1")

        edge = edge1.create_machine_edge(v_from_vert1, v_from_vert2, "edge")
        self.assertIsInstance(edge, MachineEdge)

    def test_create_new_machine_edge_from_edge(self):
        """
        test that you can use the SimpleTestEdge.create-edge
        method and not cause errors
        """
        vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1", 256)
        v_from_vert1 = vert1.create_machine_vertex(
            Slice(0, 9), vert1.get_resources_used_by_atoms(Slice(0, 9)))
        vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2", 256)
        v_from_vert2 = vert2.create_machine_vertex(
            Slice(0, 4), vert2.get_resources_used_by_atoms(Slice(0, 4)))
        edge1 = SimpleTestEdge(vert1, vert2, "First edge")
        edge = edge1.create_machine_edge(v_from_vert1, v_from_vert2,
                                         "First edge")
        self.assertEqual(edge.label, "First edge")
