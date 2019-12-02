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
test for the resources model
"""
from __future__ import division
import unittest
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer,
    IPtagResource, ReverseIPtagResource, SpecificBoardIPtagResource,
    SpecificBoardReverseIPtagResource, TimeBasedSDRAM, VariableSDRAM)


class TestResourceModels(unittest.TestCase):
    """
    unit tests on the resources object
    """

    def test_sdram(self):
        """
        test that adding a SDRAM resource to a resource container works
        correctly
        """
        const1 = ConstantSDRAM(128)
        self.assertEqual(const1.get_sdram_for_simtime(None), 128)
        const2 = ConstantSDRAM(256)
        combo = const1 + const2
        self.assertEqual(combo.get_sdram_for_simtime(None), 128+256)
        combo = const1 - const2
        self.assertEqual(combo.get_sdram_for_simtime(None), 128-256)
        combo = const2 + const1
        self.assertEqual(combo.get_sdram_for_simtime(None), 256+128)
        combo = const2 - const1
        self.assertEqual(combo.get_sdram_for_simtime(None), 256-128)

        var1 = VariableSDRAM(124, 8, 1000)
        self.assertEqual(var1.get_sdram_for_simtime(100 * 1000),
                         124 + 8 * 100)
        combo = var1 + const1
        self.assertEqual(combo.get_sdram_for_simtime(100 * 1000),
                         124 + 8 * 100 + 128)
        combo = var1 - const1
        self.assertEqual(combo.get_sdram_for_simtime(100 * 1000),
                         124 + 8 * 100 - 128)
        combo = const1 + var1
        self.assertEqual(combo.get_sdram_for_simtime(100 * 1000),
                         128 + 124 + 8 * 100)
        combo = const1 - var1
        self.assertEqual(combo.get_sdram_for_simtime(100 * 1000),
                         128 - (124 + 8 * 100))
        var2 = VariableSDRAM(234, 6, 1000)
        combo = var2 + var1
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         234 + 124 + (6 + 8) * 150)
        combo = var2 - var1
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         234 - 124 + (6 - 8) * 150)
        tb1 = TimeBasedSDRAM(124, 8 / 1000)
        self.assertEqual(tb1.get_sdram_for_simtime(100 * 1000),
                         124 + 8 * 100)
        combo = tb1 + const1
        self.assertEqual(combo.get_sdram_for_simtime(100 * 1000),
                         124 + 8 * 100 + 128)
        combo = tb1 - const1
        self.assertEqual(combo.get_sdram_for_simtime(100 * 1000),
                         124 + 8 * 100 - 128)
        combo = const1 + tb1
        self.assertEqual(combo.get_sdram_for_simtime(100 * 1000),
                         128 + 124 + 8 * 100)
        combo = const1 - tb1
        self.assertEqual(combo.get_sdram_for_simtime(100 * 1000),
                         128 - (124 + 8 * 100))
        tb2 = TimeBasedSDRAM(234, 6 / 1000)
        combo = tb2 + var1
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         234 + 124 + (6 + 8) * 150)
        combo = tb2 - var1
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         234 - 124 + (6 - 8) * 150)

        combo = var1 - tb2
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         124 - 234 + (8 - 6) * 150)

        var3 = VariableSDRAM(145, 2, 500)
        combo = var3 + var1
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         145 + 124 + (4 + 8) * 150)
        combo = var3 - var1
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         145 - 124 + (4 - 8) * 150)
        combo = tb2 + var3
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         234 + 145 + (6 + 4) * 150)
        combo = tb2 - var3
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         234 - 145 + (6 - 4) * 150)
        combo = var3 - tb2
        self.assertEqual(combo.get_sdram_for_simtime(150 * 1000),
                         145 - 234 + (4 - 6) * 150)

    def test_VariableSdram(self):
        var1 = VariableSDRAM(124, 8, 1000)
        self.assertEqual(124 + 8 * 5, var1.get_sdram_for_simtime(5000))
        with self.assertRaises(Exception):
            var1.get_sdram_for_simtime(5001)

    def test_dtcm(self):
        """
        test that adding a DTCM resource to a resource container works
        correctly
        """
        dtcm = DTCMResource(128 * (2**20))
        self.assertEqual(dtcm.get_value(), 128 * (2**20))
        dtcm = DTCMResource(128 * (2**19))
        self.assertEqual(dtcm.get_value(), 128 * (2**19))
        dtcm = DTCMResource(128 * (2**21))
        self.assertEqual(dtcm.get_value(), 128 * (2**21))

    def test_cpu(self):
        """
        test that adding a CPU resource to a resource container works
        correctly
        """
        cpu = CPUCyclesPerTickResource(128 * (2**20))
        self.assertEqual(cpu.get_value(), 128 * (2**20))
        cpu = CPUCyclesPerTickResource(128 * (2**19))
        self.assertEqual(cpu.get_value(), 128 * (2**19))
        cpu = CPUCyclesPerTickResource(128 * (2**21))
        self.assertEqual(cpu.get_value(), 128 * (2**21))

    def test_resource_container(self):
        """
        tests that creating multiple resource containers doesn't cause issues.
        """
        sdram = ConstantSDRAM(128 * (2**20))
        dtcm = DTCMResource(128 * (2**20) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**20) + 2)

        container = ResourceContainer(dtcm, sdram, cpu)
        self.assertEqual(
            container.sdram.get_sdram_for_simtime(None), 128 * (2**20))
        self.assertEqual(container.dtcm.get_value(), 128 * (2**20) + 1)
        self.assertEqual(container.cpu_cycles.get_value(), 128 * (2**20) + 2)

        sdram = ConstantSDRAM(128 * (2**19))
        dtcm = DTCMResource(128 * (2**19) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**19) + 2)

        container = ResourceContainer(dtcm, sdram, cpu)
        self.assertEqual(
            container.sdram.get_sdram_for_simtime(None), 128 * (2**19))
        self.assertEqual(container.dtcm.get_value(), 128 * (2**19) + 1)
        self.assertEqual(container.cpu_cycles.get_value(), 128 * (2**19) + 2)

        sdram = ConstantSDRAM(128 * (2**21))
        dtcm = DTCMResource(128 * (2**21) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**21) + 2)

        container = ResourceContainer(dtcm, sdram, cpu)
        self.assertEqual(
            container.sdram.get_sdram_for_simtime(None), 128 * (2**21))
        self.assertEqual(container.dtcm.get_value(), 128 * (2**21) + 1)
        self.assertEqual(container.cpu_cycles.get_value(), 128 * (2**21) + 2)

    def test_tags_resources(self):
        IPtagResource("1", 2, 3)  # Minimal args
        iptr = IPtagResource("1.2.3.4", 2, 3, 4, 5)
        self.assertEqual(iptr.ip_address, "1.2.3.4")
        self.assertEqual(iptr.port, 2)
        self.assertEqual(iptr.strip_sdp, 3)
        self.assertEqual(iptr.tag, 4)
        self.assertEqual(iptr.traffic_identifier, 5)
        self.assertEqual(iptr.get_value(), ['1.2.3.4', 2, 3, 4, 5])
        self.assertEqual(str(iptr),
                         "IPTagResource(ip_address=1.2.3.4, port=2, "
                         "strip_sdp=3, tag=4, traffic_identifier=5)")

        ReverseIPtagResource()  # Minimal args
        riptr = ReverseIPtagResource(1, 2, 3)
        self.assertEqual(riptr.port, 1)
        self.assertEqual(riptr.sdp_port, 2)
        self.assertEqual(riptr.tag, 3)
        self.assertEqual(riptr.get_value(), [1, 2, 3])
        self.assertEqual(str(riptr),
                         "ReverseIPTagResource(port=1, sdp_port=2, tag=3)")

        b = "4.3.2.1"

        SpecificBoardIPtagResource(b, "1", 2, 3)  # Minimal args
        iptr = SpecificBoardIPtagResource(b, "1.2.3.4", 2, 3, 4, 5)
        self.assertEqual(iptr.board, b)
        self.assertEqual(iptr.ip_address, "1.2.3.4")
        self.assertEqual(iptr.port, 2)
        self.assertEqual(iptr.strip_sdp, 3)
        self.assertEqual(iptr.tag, 4)
        self.assertEqual(iptr.traffic_identifier, 5)
        self.assertEqual(iptr.get_value(), [b, '1.2.3.4', 2, 3, 4, 5])
        self.assertEqual(str(iptr),
                         "IPTagResource(board_address=" + b + ", "
                         "ip_address=1.2.3.4, port=2, strip_sdp=3, tag=4, "
                         "traffic_identifier=5)")

        SpecificBoardReverseIPtagResource(b)  # Minimal args
        riptr = SpecificBoardReverseIPtagResource(b, 1, 2, 3)
        self.assertEqual(riptr.board, b)
        self.assertEqual(riptr.port, 1)
        self.assertEqual(riptr.sdp_port, 2)
        self.assertEqual(riptr.tag, 3)
        self.assertEqual(riptr.get_value(), [b, 1, 2, 3])
        self.assertEqual(str(riptr),
                         "ReverseIPTagResource(board=" + b + ", port=1, "
                         "sdp_port=2, tag=3)")


if __name__ == '__main__':
    unittest.main()
