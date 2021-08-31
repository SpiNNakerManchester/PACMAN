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

"""
test for SplitterPartitioner functions
"""

import unittest
from pacman.config_setup import unittest_setup
from pacman.model.partitioner_splitters import SplitterSliceLegacy
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractDependentSplitter)
from pacman.operations.partition_algorithms import SplitterPartitioner
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanPartitionException)
from pacman_test_objects import SimpleTestVertex


class MockDependant(AbstractDependentSplitter):

    def create_machine_vertices(self, resource_tracker, machine_graph):
        raise NotImplementedError()

    def get_out_going_slices(self):
        raise NotImplementedError()

    def get_in_coming_slices(self):
        raise NotImplementedError()

    def get_out_going_vertices(self, outgoing_edge_partition):
        raise NotImplementedError()

    def get_in_coming_vertices(self, outgoing_edge_partition):
        raise NotImplementedError()

    def machine_vertices_for_recording(self, variable_to_record):
        raise NotImplementedError()

    def reset_called(self):
        raise NotImplementedError()


class TestSplitterPartitioner(unittest.TestCase):
    """
    test for SplitterPartitioner functions
    """
    # pylint: disable=attribute-defined-outside-init

    def setUp(self):
        unittest_setup()

    def test_order_vertices_for_dependent_splitters(self):
        vertices = list()
        v1 = SimpleTestVertex(1, splitter=SplitterSliceLegacy(), label="v1")
        vertices.append(v1)
        s2 = SplitterSliceLegacy()
        v2 = SimpleTestVertex(1, splitter=s2, label="v2")
        s3 = SplitterSliceLegacy()
        s2a = MockDependant(s2, "depends on v2")
        v2a = SimpleTestVertex(1, splitter=s2a, label="A depends on v2")
        s2a.set_governed_app_vertex(v2a)
        v2aa = SimpleTestVertex(
            1, splitter=MockDependant(s2a, "depends on v2a"),
            label="A depends on v2a")
        vertices.append(v2aa)
        v3a = SimpleTestVertex(1, splitter=MockDependant(s3, "depends on v3"),
                               label="A depends on v3")
        vertices.append(v3a)
        vertices.append(v2a)
        v2b = SimpleTestVertex(1, splitter=MockDependant(s2, "depends on v2"),
                               label="B depends on v2")
        vertices.append(v2b)
        vertices.append(v2)
        v3 = SimpleTestVertex(1, splitter=s3, label="v3")
        vertices.append(v3)
        v4 = SimpleTestVertex(1, splitter=SplitterSliceLegacy(), label="v4")
        vertices.append(v4)
        sp = SplitterPartitioner()
        sp.order_vertices_for_dependent_splitters(vertices)
        self.assertLess(vertices.index(v1), vertices.index(v2))
        self.assertLess(vertices.index(v2), vertices.index(v3))
        self.assertLess(vertices.index(v3), vertices.index(v4))
        self.assertLess(vertices.index(v2), vertices.index(v2a))
        self.assertLess(vertices.index(v2a), vertices.index(v2aa))
        self.assertLess(vertices.index(v2), vertices.index(v2b))
        self.assertLess(vertices.index(v3), vertices.index(v3a))

    def test_detect_circular(self):
        s1 = MockDependant(None, "depends on s3")
        SimpleTestVertex(1, splitter=s1, label="v1")
        s2 = MockDependant(s1, "depends on s1")
        SimpleTestVertex(1, splitter=s2, label="v2")
        s3 = MockDependant(s2, "depends on s2")
        SimpleTestVertex(1, splitter=s3, label="v3")
        with self.assertRaises(PacmanAlreadyExistsException):
            s3.other_splitter = s1
        with self.assertRaises(PacmanPartitionException):
            s1.other_splitter = s3
        with self.assertRaises(PacmanPartitionException):
            s1.other_splitter = s1


if __name__ == '__main__':
    unittest.main()
