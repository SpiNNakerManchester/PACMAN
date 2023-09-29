# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from pacman.config_setup import unittest_setup
from pacman.exceptions import PacmanConfigurationException
from pacman.model.partitioner_splitters import SplitterOneToOneLegacy
from pacman_test_objects import (
    NonLegacyApplicationVertex, SimpleTestVertex)
from pacman.utilities.utility_objs.chip_counter import ChipCounter


class TestSplitterFixedLegacy(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_api(self):
        splitter = SplitterOneToOneLegacy()
        self.assertIsNotNone(str(splitter))
        self.assertIsNotNone(repr(splitter))
        v1 = SimpleTestVertex(1, "v1")
        v1.splitter = splitter
        v2 = SimpleTestVertex(1, "v2")
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_governed_app_vertex(v2)
        chip_counter = ChipCounter()
        splitter.create_machine_vertices(chip_counter)
        mvs = list(v1.machine_vertices)
        self.assertEqual(1, len(mvs))
        slices = [mvs[0].vertex_slice]
        self.assertEqual(splitter.get_out_going_slices(), slices)
        self.assertEqual(splitter.get_in_coming_slices(), slices)
        self.assertEqual(splitter.get_in_coming_vertices("foo"), mvs)
        self.assertEqual(splitter.get_out_going_vertices("foo"), mvs)
        self.assertEqual(splitter.machine_vertices_for_recording("foo"), mvs)
        splitter.reset_called()

    def test_not_api(self):
        splitter = SplitterOneToOneLegacy()
        v1 = NonLegacyApplicationVertex("v1")
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_governed_app_vertex(v1)
