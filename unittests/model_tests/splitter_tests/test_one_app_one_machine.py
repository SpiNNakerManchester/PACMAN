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
        splitter = SplitterOneAppOneMachine()
        v1 = NonLegacyApplicationVertex("v1")
        a = str(splitter)
        self.assertIsNotNone(a)
        self.assertIsNotNone(repr(splitter))
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_governed_app_vertex(v1)
        mv = SimpleMachineVertex(ConstantSDRAM(10), vertex_slice=Slice(0, 5))
        v2 = AbstractOneAppOneMachineVertex(
            machine_vertex=mv, label="v1")
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
