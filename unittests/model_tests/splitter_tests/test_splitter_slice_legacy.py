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
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from pacman.model.partitioner_splitters import SplitterSliceLegacy


class MockLegacyApi(ApplicationVertex, LegacyPartitionerAPI):
    def __init__(self, label):
        super(MockLegacyApi, self).__init__(
            label=label, constraints=None,  max_atoms_per_core=None)

    def get_resources_used_by_atoms(self, vertex_slice):
        pass

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        pass

    def n_atoms(self):
        pass


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


class MockNotLegacy(ApplicationVertex):
    def __init__(self, label):
        super(MockNotLegacy, self).__init__(
            label=label, constraints=None,  max_atoms_per_core=None)

    def n_atoms(self):
        pass


class TestSplitterSliceLegacy(unittest.TestCase):
    def test_api(self):
        splitter = SplitterSliceLegacy("foo")
        a = str(splitter)
        self.assertIsNotNone(a)
        v1 = MockLegacyApi("v1")
        splitter.set_governed_app_vertex(v1)
        a = str(splitter)
        self.assertIsNotNone(a)
        splitter.set_governed_app_vertex(v1)
        v2 = MockLegacyApi("v1")
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_governed_app_vertex(v2)

    def test_not_api(self):
        splitter = SplitterSliceLegacy("foo")
        v1 = MockNotLegacy("v1")
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_governed_app_vertex(v1)

    def test_legacy(self):
        splitter = SplitterSliceLegacy("foo")
        v1 = MockLegacy("v1")
        splitter.set_governed_app_vertex(v1)

    def test_max_atoms_start_variable(self):
        # set same variable
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, False)
        splitter.set_max_atoms_per_core(100, False)
        self.assertEqual(splitter._max_atoms_per_core, 100)
        self.assertFalse(splitter._is_fixed_atoms_per_core)

        # set more variable
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, False)
        splitter.set_max_atoms_per_core(200, False)
        self.assertEqual(splitter._max_atoms_per_core, 100)
        self.assertFalse(splitter._is_fixed_atoms_per_core, 100)

        # set less variable
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, False)
        splitter.set_max_atoms_per_core(50, False)
        self.assertEqual(splitter._max_atoms_per_core, 50)
        self.assertFalse(splitter._is_fixed_atoms_per_core)

        # set same Fixed
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, False)
        splitter.set_max_atoms_per_core(100, True)
        self.assertEqual(splitter._max_atoms_per_core, 100)
        self.assertTrue(splitter._is_fixed_atoms_per_core)

        # set more Fixed
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, False)
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_max_atoms_per_core(200, True)

        # set less fixed
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, False)
        splitter.set_max_atoms_per_core(50, True)
        self.assertEqual(splitter._max_atoms_per_core, 50)
        self.assertTrue(splitter._is_fixed_atoms_per_core)

    def test_max_atoms_start_fixed(self):
        # set same variable
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, True)
        splitter.set_max_atoms_per_core(100, False)
        self.assertEqual(splitter._max_atoms_per_core, 100)
        self.assertTrue(splitter._is_fixed_atoms_per_core)

        # set more variable
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, True)
        splitter.set_max_atoms_per_core(200, False)
        self.assertEqual(splitter._max_atoms_per_core, 100)
        self.assertTrue(splitter._is_fixed_atoms_per_core)

        # set less variable
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, True)
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_max_atoms_per_core(50, False)

        # set same Fixed
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, True)
        splitter.set_max_atoms_per_core(100, True)
        self.assertEqual(splitter._max_atoms_per_core, 100)
        self.assertTrue(splitter._is_fixed_atoms_per_core)

        # set more Fixed
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, True)
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_max_atoms_per_core(200, True)

        # set less Fixed
        splitter = SplitterSliceLegacy("foo")
        splitter.set_max_atoms_per_core(100, True)
        with self.assertRaises(PacmanConfigurationException):
            splitter.set_max_atoms_per_core(50, True)
