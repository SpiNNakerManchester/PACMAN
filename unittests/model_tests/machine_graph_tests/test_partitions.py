# Copyright (c) 2017-2022 The University of Manchester
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
from spinn_utilities.overrides import overrides
from pacman.config_setup import unittest_setup
from pacman.exceptions import (
    PacmanConfigurationException, PartitionMissingEdgesException,
    PacmanValueError, SDRAMEdgeSizeException)
from pacman.model.graphs import (
    AbstractMultiplePartition, AbstractSupportsSDRAMEdges)
from pacman.model.graphs.machine import (
     ConstantSDRAMMachinePartition,
     DestinationSegmentedSDRAMMachinePartition,
     SDRAMMachineEdge, SimpleMachineVertex,
     SourceSegmentedSDRAMMachinePartition)
from pacman.model.resources import ConstantSDRAM


class MockSupportsSDRAMEdges(SimpleMachineVertex, AbstractSupportsSDRAMEdges):

    @overrides(AbstractSupportsSDRAMEdges.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge):
        # A mock so that the size can be different depending on prevertex
        return 16 + self.sdram_required.fixed


class TestPartition(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def setUp(self):
        unittest_setup()

    def test_constant(self):
        """
        test ConstantSDRAMMachinePartition
        """
        v1 = MockSupportsSDRAMEdges(ConstantSDRAM(24))
        part = ConstantSDRAMMachinePartition("foo", v1)
        with self.assertRaises(PartitionMissingEdgesException):
            part.total_sdram_requirements()
        with self.assertRaises(PartitionMissingEdgesException):
            part.sdram_base_address = 100
        with self.assertRaises(PartitionMissingEdgesException):
            part.get_sdram_size_of_region_for(v1)
        v2 = MockSupportsSDRAMEdges(ConstantSDRAM(12))
        e1 = SDRAMMachineEdge(v1, v2, "foo")
        part.add_edge(e1)
        self.assertEqual(16 + 24, part.total_sdram_requirements())
        self.assertEqual(16 + 24, part.get_sdram_size_of_region_for(v1))
        v3 = MockSupportsSDRAMEdges(ConstantSDRAM(34))
        e2 = SDRAMMachineEdge(v1, v3, "foo")
        part.add_edge(e2)
        v4 = MockSupportsSDRAMEdges(ConstantSDRAM(100))
        e3 = SDRAMMachineEdge(v4, v1, "foo")
        self.assertEqual(2, len(part.edges))
        with self.assertRaises(SDRAMEdgeSizeException):
            part.add_edge(e3)
        self.assertEqual(2, len(part.edges))
        part.sdram_base_address = 200
        self.assertEqual(200, part.sdram_base_address)
        self.assertEqual(200, e1.sdram_base_address)
        self.assertEqual(200, e2.sdram_base_address)
        e4 = SDRAMMachineEdge(v1, v3, "foo")
        with self.assertRaises(PacmanConfigurationException):
            part.add_edge(e4)
        self.assertEqual(2, len(part.edges))

    def test_destination(self):
        """
        test DestinationSegmentedSDRAMMachinePartition
        """
        v1 = MockSupportsSDRAMEdges(ConstantSDRAM(24))
        part = DestinationSegmentedSDRAMMachinePartition("foo", v1)
        self.assertEqual(0, part.total_sdram_requirements())
        with self.assertRaises(PartitionMissingEdgesException):
            part.sdram_base_address = 100
        self.assertEqual(0, part.get_sdram_size_of_region_for(v1))
        v2 = MockSupportsSDRAMEdges(ConstantSDRAM(12))
        e1 = SDRAMMachineEdge(v1, v2, "foo")
        part.add_edge(e1)
        self.assertEqual(16 + 24, part.total_sdram_requirements())
        self.assertEqual(16 + 24, part.get_sdram_size_of_region_for(v1))
        v3 = MockSupportsSDRAMEdges(ConstantSDRAM(34))
        e2 = SDRAMMachineEdge(v1, v3, "foo")
        part.add_edge(e2)
        v4 = MockSupportsSDRAMEdges(ConstantSDRAM(100))
        e3 = SDRAMMachineEdge(v4, v1, "foo")
        self.assertEqual(2, len(part.edges))
        with self.assertRaises(PacmanConfigurationException):
            part.add_edge(e3)
        self.assertEqual(2, len(part.edges))
        part.sdram_base_address = 200
        self.assertEqual(200, part.sdram_base_address)
        self.assertEqual(200, e1.sdram_base_address)
        self.assertEqual(40, e1.sdram_size)
        self.assertEqual(200 + 40, e2.sdram_base_address)
        self.assertEqual(40, e2.sdram_size)
        self.assertEqual(40, part.get_sdram_size_of_region_for(v3))
        e4 = SDRAMMachineEdge(v1, v3, "foo")
        self.assertEqual(2, len(part.edges))
        with self.assertRaises(PacmanConfigurationException):
            part.add_edge(e4)
        self.assertEqual(2, len(part.edges))
        with self.assertRaises(PacmanValueError):
            part.get_sdram_size_of_region_for(v4)
        with self.assertRaises(PacmanValueError):
            part.get_sdram_base_address_for(v4)

    def test_sdram_machine_edge(self):
        """
        test SDRAMMachineEdge
        """
        v1 = MockSupportsSDRAMEdges(ConstantSDRAM(24))
        v2 = SimpleMachineVertex(ConstantSDRAM(12))
        e1 = SDRAMMachineEdge(v1, v2, "foo")
        self.assertIsNotNone(str(e1))
        self.assertIsNotNone(repr(e1))
        with self.assertRaises(PacmanConfigurationException):
            SDRAMMachineEdge(v2, v1, "bar")

    def test_source(self):
        """
        test DestinationSegmentedSDRAMMachinePartition
        """
        v1 = MockSupportsSDRAMEdges(ConstantSDRAM(24))
        v2 = MockSupportsSDRAMEdges(ConstantSDRAM(12))
        part = SourceSegmentedSDRAMMachinePartition("foo", [v1, v2])
        self.assertEqual(0, part.total_sdram_requirements())
        with self.assertRaises(PartitionMissingEdgesException):
            part.sdram_base_address = 10
        with self.assertRaises(Exception):
            part.get_sdram_size_of_region_for(v1)
        self.assertIsNone(part.get_sdram_base_address_for(v1))
        v3 = MockSupportsSDRAMEdges(ConstantSDRAM(12))
        v4 = MockSupportsSDRAMEdges(ConstantSDRAM(12))
        with self.assertRaises(PacmanConfigurationException):
            part.add_edge(SDRAMMachineEdge(v4, v1, "foo"))
        self.assertEqual(0, len(part.edges))
        e1 = SDRAMMachineEdge(v1, v3, "foo")
        part.add_edge(e1)
        with self.assertRaises(PacmanConfigurationException):
            part.add_edge(SDRAMMachineEdge(v1, v3, "foo"))
        self.assertEqual(1, len(part.edges))
        with self.assertRaises(PartitionMissingEdgesException):
            part.sdram_base_address = 100
        e2 = SDRAMMachineEdge(v2, v3, "foo")
        part.add_edge(e2)
        self.assertEqual(2, len(part.edges))
        self.assertIsNone(part.sdram_base_address)
        self.assertIsNone(part.get_sdram_base_address_for(v1))
        part.sdram_base_address = 100
        self.assertEqual(100, part.sdram_base_address)
        self.assertEqual(100, e1.sdram_base_address)
        self.assertEqual(100, part.get_sdram_base_address_for(v1))
        self.assertEqual(16 + 24, e1.sdram_size)
        self.assertEqual(40, part.get_sdram_size_of_region_for(v1))
        self.assertEqual(100 + 40, e2.sdram_base_address)
        self.assertEqual(100 + 40, part.get_sdram_base_address_for(v2))
        self.assertEqual(16 + 12, part.get_sdram_size_of_region_for(v2))
        self.assertEqual(100, part.get_sdram_base_address_for(v3))
        self.assertEqual(40 + 28, part.get_sdram_size_of_region_for(v3))

    def test_abstract_multiple_partition(self):
        v1 = MockSupportsSDRAMEdges(ConstantSDRAM(12))
        v2 = MockSupportsSDRAMEdges(ConstantSDRAM(12))
        v3 = MockSupportsSDRAMEdges(ConstantSDRAM(12))
        with self.assertRaises(PacmanConfigurationException):
            AbstractMultiplePartition([v1, v1], "foo", None)
        part = AbstractMultiplePartition([v1, v2], "foo", None)
        with self.assertRaises(Exception):
            part.add_edge(SDRAMMachineEdge(v3, v1, "foo"))
