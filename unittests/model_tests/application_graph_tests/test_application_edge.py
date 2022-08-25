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
    PartitionMissingEdgesException, SDRAMEdgeSizeException)
from pacman.model.graphs import AbstractSupportsSDRAMEdges
from pacman.model.graphs.machine import (
    ConstantSDRAMMachinePartition, SDRAMMachineEdge, SimpleMachineVertex)
from pacman.model.resources import ConstantSDRAM


class MockSupportsSDRAMEdges(SimpleMachineVertex, AbstractSupportsSDRAMEdges):

    @overrides(AbstractSupportsSDRAMEdges.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge):
        # A mock so that the size can be different depending on prevertex
        return ConstantSDRAM(16) + self.sdram_required


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
        self.assertEqual(ConstantSDRAM(16+24), part.total_sdram_requirements())
        self.assertEqual(ConstantSDRAM(16+24),
                         part.get_sdram_size_of_region_for(v1))
        v3 = MockSupportsSDRAMEdges(ConstantSDRAM(34))
        e2 = SDRAMMachineEdge(v1, v3, "foo")
        part.add_edge(e2)
        v4 = MockSupportsSDRAMEdges(ConstantSDRAM(100))
        e3 = SDRAMMachineEdge(v4, v1, "foo")
        with self.assertRaises(SDRAMEdgeSizeException):
            part.add_edge(e3)
        part.sdram_base_address = 200
        self.assertEqual(200, part.sdram_base_address)
        self.assertEqual(200, e1.sdram_base_address)
        self.assertEqual(200, e2.sdram_base_address)
