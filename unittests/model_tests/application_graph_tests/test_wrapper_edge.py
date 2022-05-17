# Copyright (c) 2022 The University of Manchester
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

from pacman.model.graphs.wrapper.wrapper_application_edge import (
    WrapperApplicationEdge)
from pacman.model.graphs.machine import MachineEdge, SimpleMachineVertex
from pacman_test_objects import SimpleTestVertex


class ExtraEdge(MachineEdge):
    pass


class TestApplicationEdgeModel(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def setUp(self):
        unittest_setup()

    def test_wrap_normal(self):
        """
        test that you can wrap a normal MachineEdge
        """
        vert1 = SimpleMachineVertex(None)
        vert2 = SimpleMachineVertex(None)
        edge1 = MachineEdge(vert1, vert2, "First edge")
        wrapper = WrapperApplicationEdge(edge1)
        self.assertEqual(vert1.app_vertex, wrapper.pre_vertex)
        self.assertEqual(vert2.app_vertex, wrapper.post_vertex)

    def test_no_wrap_extra(self):
        """
        test that you can not wrap an subclass of MachineVertex
        """
        vert1 = SimpleMachineVertex(None)
        vert2 = SimpleMachineVertex(None)
        edge1 = ExtraEdge(vert1, vert2, "First edge")
        with self.assertRaises(NotImplementedError):
            WrapperApplicationEdge(edge1)

    def test_wrap_mixed(self):
        """
        test that you could wrap an Edge between an ApplicationVertex
        and a MachineVertex.

        While mixing Application and Machine level is supported here
        it may not be supported elsewhere.
        """
        vert1 = SimpleMachineVertex(None)
        vert1._app_vertex = "MOCK"
        vert2 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1", 256)
        edge1 = MachineEdge(vert1, vert2, "First edge")
        wrapper1 = WrapperApplicationEdge(edge1)
        self.assertEqual(vert1.app_vertex, wrapper1.pre_vertex)
        self.assertEqual(vert2, wrapper1.post_vertex)
        edge2 = MachineEdge(vert2, vert1, "First edge")
        wrapper2 = WrapperApplicationEdge(edge2)
        self.assertEqual(vert2, wrapper2.pre_vertex)
        self.assertEqual(vert1.app_vertex, wrapper2.post_vertex)
