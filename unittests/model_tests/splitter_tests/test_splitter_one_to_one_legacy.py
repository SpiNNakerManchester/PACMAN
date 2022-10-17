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
