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
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from pacman.model.graphs.common import Slice
from pacman.model.partitioner_splitters import SplitterOneAppOneMachine
from pacman.model.resources import ConstantSDRAM
from pacman_test_objects import NonLegacyApplicationVertex
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.utilities.utility_objs.chip_counter import ChipCounter


class TestSplitterOneAppOneMachine(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_legacy(self):
        splitter = SplitterOneAppOneMachine("foo")
        v1 = NonLegacyApplicationVertex("v1")
        a = str(splitter)
        self.assertIsNotNone(a)
        self.assertIsNotNone(repr(splitter))
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_governed_app_vertex(v1)
        mv = SimpleMachineVertex(ConstantSDRAM(10), vertex_slice=Slice(0, 5))
        v2 = AbstractOneAppOneMachineVertex(
            machine_vertex=mv, label="v1", constraints=None)
        splitter.set_governed_app_vertex(v2)
        a = str(splitter)
        self.assertIsNotNone(a)
        chip_counter = ChipCounter()
        splitter.create_machine_vertices(chip_counter)
        self.assertEqual(splitter.get_out_going_slices(), [mv.vertex_slice])
        self.assertEqual(splitter.get_in_coming_slices(), [mv.vertex_slice])
        self.assertEqual(splitter.get_in_coming_vertices("foo"), [mv])
        self.assertEqual(splitter.get_out_going_vertices("foo"), [mv])
        self.assertEqual(splitter.machine_vertices_for_recording("foo"), [mv])
        splitter.reset_called()
        v2.remember_machine_vertex(mv)
        self.assertEqual(6, v2.n_atoms)
        v2.reset()

    def test_default_name(self):
        splitter = SplitterOneAppOneMachine()
        self.assertIn("SplitterOneAppOneMachine", str(splitter))
