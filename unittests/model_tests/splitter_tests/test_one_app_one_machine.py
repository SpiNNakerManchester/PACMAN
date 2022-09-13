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
from pacman.model.partitioner_splitters import SplitterOneAppOneMachine
from pacman_test_objects import NonLegacyApplicationVertex
from pacman.model.graphs.machine import SimpleMachineVertex


class TestSplitterOneAppOneMachine(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_legacy(self):
        splitter = SplitterOneAppOneMachine("foo")
        v1 = NonLegacyApplicationVertex("v1")
        a = str(splitter)
        self.assertIsNotNone(a)
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_governed_app_vertex(v1)
        v2 = AbstractOneAppOneMachineVertex(
            machine_vertex=SimpleMachineVertex(None), label="v1")
        splitter.set_governed_app_vertex(v2)
        a = str(splitter)
        self.assertIsNotNone(a)
