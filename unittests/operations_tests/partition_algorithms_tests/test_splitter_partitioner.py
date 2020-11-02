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
from pacman.model.partitioner_splitters import SplitterSliceLegacy
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractDependentSplitter)
from pacman.operations.partition_algorithms import SplitterPartitioner
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanPartitionException)


class MockVertex(LegacyPartitionerAPI):
    def __init__(self, splitter, label):
        self.splitter = splitter
        self.splitter.set_governed_app_vertex(self)
        self.label = label

    @property
    def constraints(self):
        return []

    def __str__(self):
        return self.label

    def get_resources_used_by_atoms(self, vertex_slice):
        raise NotImplementedError()

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        raise NotImplementedError()

    def n_atoms(self):
        raise NotImplementedError()


class MockDependant(AbstractDependentSplitter):

    def create_machine_vertices(self, resource_tracker, machine_graph):
        raise NotImplementedError()

    def get_out_going_slices(self):
        raise NotImplementedError()

    def get_in_coming_slices(self):
        raise NotImplementedError()

    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        raise NotImplementedError()

    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
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

    def test_order_vertices_for_dependent_splitters(self):
        vertices = list()
        v1 = MockVertex(SplitterSliceLegacy(), "v1")
        vertices.append(v1)
        s2 = SplitterSliceLegacy()
        v2 = MockVertex(s2, "v2")
        s3 = SplitterSliceLegacy()
        s2a = MockDependant(s2, "depends on v2")
        v2a = MockVertex(MockDependant(s2, "depends on v2"), "A depends on v2")
        s2a.set_governed_app_vertex(v2a)
        v2aa = MockVertex(
            MockDependant(s2a, "depends on v2a"), "A depends on v2a")
        vertices.append(v2aa)
        v3a = MockVertex(MockDependant(s3, "depends on v3"), "A depends on v3")
        vertices.append(v3a)
        vertices.append(v2a)
        v2b = MockVertex(MockDependant(s2, "depends on v2"), "B depends on v2")
        vertices.append(v2b)
        vertices.append(v2)
        v3 = MockVertex(s3, "v3")
        vertices.append(v3)
        v4 = MockVertex(SplitterSliceLegacy(), "v4")
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
        MockVertex(s1, "v1")
        s2 = MockDependant(s1, "depends on s1")
        MockVertex(s2, "v1")
        s3 = MockDependant(s2, "depends on s2")
        MockVertex(s3, "v1")
        with self.assertRaises(PacmanAlreadyExistsException):
            s3.other_splitter = s1
        with self.assertRaises(PacmanPartitionException):
            s1.other_splitter = s3
        with self.assertRaises(PacmanPartitionException):
            s1.other_splitter = s1


if __name__ == '__main__':
    unittest.main()
