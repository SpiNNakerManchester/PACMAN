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
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from pacman.model.partitioner_splitters import SplitterOneAppOneMachine


class MockLegacy(ApplicationVertex):
    def __init__(self, label):
        super(MockLegacy, self).__init__(
            label=label, constraints=None,  max_atoms_per_core=None)

    def get_resources_used_by_atoms(self, vertex_slice):
        pass

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        pass

    def n_atoms(self):
        pass


class MockNot(ApplicationVertex):
    def __init__(self, label):
        super(MockNot, self).__init__(
            label=label, constraints=None,  max_atoms_per_core=None)

    def n_atoms(self):
        pass


class MockApi(AbstractOneAppOneMachineVertex):
    def __init__(self, label):
        super(MockApi, self).__init__(
            machine_vertex=None, label=label, constraints=None)


class TestSplitterOneAppOneMachine(unittest.TestCase):
    def test_legacy(self):
        splitter = SplitterOneAppOneMachine("foo")
        v1 = MockNot("v1")
        a = str(splitter)
        self.assertIsNotNone(a)
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_governed_app_vertex(v1)
        v2 = MockApi("v1")
        splitter.set_governed_app_vertex(v2)
        a = str(splitter)
        self.assertIsNotNone(a)
