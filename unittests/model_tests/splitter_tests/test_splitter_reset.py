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
from pacman.data import PacmanDataView
from pacman.model.partitioner_splitters import (
    SplitterFixedLegacy, splitter_reset)
from pacman_test_objects import SimpleTestVertex


class TestSplitterReset(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_reset(self):
        # With slitter
        v1 = SimpleTestVertex(1, "v1")
        PacmanDataView.add_vertex(v1)
        splitter = SplitterFixedLegacy()
        v1.splitter = splitter
        # no splitter
        v2 = SimpleTestVertex(1, "v2")
        PacmanDataView.add_vertex(v2)
        splitter_reset.splitter_reset()
