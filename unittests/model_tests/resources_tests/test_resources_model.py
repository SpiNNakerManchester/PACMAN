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
from enum import Enum
import tempfile
import unittest
from pacman.config_setup import unittest_setup
from pacman.exceptions import PacmanConfigurationException
from pacman.model.resources import (
    ConstantSDRAM, IPtagResource, MultiRegionSDRAM, ReverseIPtagResource,
    VariableSDRAM)


class MockEnum(Enum):
    ZERO = 0
    ONE = 1


class TestResourceModels(unittest.TestCase):
    """
    unit tests on the resources object
    """

    def setUp(self):
        unittest_setup()

    def test_sdram(self):
        """
        test that adding a SDRAM resource to a resource container works
        correctly
        """
        const1 = ConstantSDRAM(128)
        self.assertEqual(const1.get_total_sdram(None), 128)
        const2 = ConstantSDRAM(256)
        combo = const1 + const2
        self.assertEqual(combo.get_total_sdram(None), 128+256)
        combo = const1 - const2
        self.assertEqual(combo.get_total_sdram(None), 128-256)
        combo = const2 + const1
        self.assertEqual(combo.get_total_sdram(None), 256+128)
        combo = const2 - const1
        self.assertEqual(combo.get_total_sdram(None), 256-128)

        var1 = VariableSDRAM(124, 8)
        self.assertEqual(var1.get_total_sdram(100), 124 + 8 * 100)
        combo = var1 + const1
        self.assertEqual(combo.get_total_sdram(100), 124 + 8 * 100 + 128)
        combo = var1 - const1
        self.assertEqual(combo.get_total_sdram(100), 124 + 8 * 100 - 128)
        combo = const1 + var1
        self.assertEqual(combo.get_total_sdram(100), 128 + 124 + 8 * 100)
        combo = const1 - var1
        self.assertEqual(combo.get_total_sdram(100), 128 - (124 + 8 * 100))
        var2 = VariableSDRAM(234, 6)
        combo = var2 + var1
        self.assertEqual(combo.get_total_sdram(150), 234 + 124 + (6 + 8) * 150)
        combo = var2 - var1
        self.assertEqual(combo.get_total_sdram(150), 234 - 124 + (6 - 8) * 150)

        multi1 = MultiRegionSDRAM()
        multi1.add_cost(1, 100, 4)
        multi1.add_cost(2, 50, 3)
        multi1.add_cost("overheads", 20)
        multi2 = MultiRegionSDRAM()
        multi2.add_cost(MockEnum.ZERO, 88)
        multi2.add_cost(MockEnum.ONE, 72)
        multi2.add_cost("overheads", 22)
        self.assertEqual(multi1, VariableSDRAM(100 + 50 + 20, 4 + 3))
        self.assertNotEqual(multi1, VariableSDRAM(100 + 50 + 20, 12))
        self.assertNotEqual(multi1, VariableSDRAM(45, 4 + 3))
        self.assertNotEqual(multi1, "multi1")

        combo = multi1 + multi2
        self.assertEqual(combo.get_total_sdram(150),
                         100 + 50 + 20 + 88 + 72 + 22 + (4 + 3) * 150)

        multi3 = MultiRegionSDRAM()
        multi3.nest("foo", multi1)
        multi3.nest("bar", multi2)

        multi1.merge(multi2)
        self.assertEqual(len(multi1.regions), 5)
        self.assertEqual(multi1.regions["overheads"], ConstantSDRAM(20 + 22))
        self.assertEqual(multi1.get_total_sdram(150),
                         100 + 50 + 20 + 88 + 72 + 22 + (4 + 3) * 150)
        self.assertEqual(multi1, combo)
        self.assertEqual(multi1, multi3)
        with tempfile.TemporaryFile(mode="w") as target:
            multi3.report(1000, target=target)
        multi3.report(1000, preamble="core (0,0,1):")

    def test_add(self):
        multi1 = MultiRegionSDRAM()
        multi1.add_cost(1, 100, 4)
        multi1.add_cost(1, 50)
        self.assertEqual(multi1.regions[1], VariableSDRAM(150, 4))

    def test_nest(self):
        multi1 = MultiRegionSDRAM()
        multi1.add_cost(1, 100, 4)
        multi2 = MultiRegionSDRAM()
        multi2.add_cost(2, 50)
        multi1.nest(1, multi2)
        self.assertEqual(multi1.regions[1], VariableSDRAM(150, 4))

    def test_nest2(self):
        multi1 = MultiRegionSDRAM()
        multi1.add_cost(1, 100, 4)
        multi2 = MultiRegionSDRAM()
        multi2.add_cost(2, 50)
        multi3 = MultiRegionSDRAM()
        multi3.nest(12, multi1)
        multi3.nest(12, multi2)
        self.assertEqual(multi3.regions[12], VariableSDRAM(150, 4))
        multi3.report(1000)

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
        riptr2 = ReverseIPtagResource(1, 2, 3)
        self.assertNotEqual(riptr, str(riptr))
        self.assertEqual(riptr, riptr2)
        self.assertEqual(hash(riptr), hash(riptr2))

    def test_sub(self):
        const1 = ConstantSDRAM(128)
        const2 = ConstantSDRAM(28)
        self.assertEqual(ConstantSDRAM(100), const1 - const2)
        self.assertEqual(ConstantSDRAM(100), const2.sub_from(const1))
        var1 = VariableSDRAM(100, 5)
        self.assertEqual(VariableSDRAM(28, -5), const1 - var1)
        self.assertEqual(VariableSDRAM(-28, 5), var1 - const1)
        self.assertEqual(VariableSDRAM(-28, 5), const1.sub_from(var1))

    def test_total(self):
        var0 = VariableSDRAM(28, 0)
        self.assertEqual(28, var0.get_total_sdram(None))
        var4 = VariableSDRAM(28, 4)
        with self.assertRaises(PacmanConfigurationException):
            var4.get_total_sdram(None)


if __name__ == '__main__':
    unittest.main()
