# Copyright (c) 2015 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    SharedSDRAM, VariableSDRAM)


class MockEnum(Enum):
    ZERO = 0
    ONE = 1


class TestResourceModels(unittest.TestCase):
    """
    unit tests on the resources object
    """

    def setUp(self) -> None:
        unittest_setup()

    def test_sdram(self) -> None:
        """
        test that adding a SDRAM resource to a resource container works
        correctly
        """
        const1 = ConstantSDRAM(128)
        self.assertEqual(const1.get_total_sdram(None), 128)
        const2 = ConstantSDRAM(256)
        combo = const1 + const2
        self.assertEqual(combo.get_total_sdram(None), 128+256)
        combo = const2 + const1
        self.assertEqual(combo.get_total_sdram(None), 256+128)

        var1 = VariableSDRAM(124, 8)
        self.assertEqual(var1.get_total_sdram(100), 124 + 8 * 100)
        combo = var1 + const1
        self.assertEqual(combo.get_total_sdram(100), 124 + 8 * 100 + 128)
        combo = const1 + var1
        self.assertEqual(combo.get_total_sdram(100), 128 + 124 + 8 * 100)
        var2 = VariableSDRAM(234, 6)
        combo = var2 + var1
        self.assertEqual(combo.get_total_sdram(150), 234 + 124 + (6 + 8) * 150)

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

    def test_add(self) -> None:
        multi1 = MultiRegionSDRAM()
        multi1.add_cost(1, 100, 4)
        multi1.add_cost(1, 50)
        self.assertEqual(multi1.regions[1], VariableSDRAM(150, 4))

    def test_nest(self) -> None:
        multi1 = MultiRegionSDRAM()
        multi1.add_cost(1, 100, 4)
        multi2 = MultiRegionSDRAM()
        multi2.add_cost(2, 50)
        multi1.nest(1, multi2)
        self.assertEqual(multi1.regions[1], VariableSDRAM(150, 4))

    def test_nest2(self) -> None:
        multi1 = MultiRegionSDRAM()
        multi1.add_cost(1, 100, 4)
        multi2 = MultiRegionSDRAM()
        multi2.add_cost(2, 50)
        multi3 = MultiRegionSDRAM()
        multi3.nest(12, multi1)
        multi3.nest(12, multi2)
        self.assertEqual(multi3.regions[12], VariableSDRAM(150, 4))
        multi3.report(1000)

    def test_tags_resources(self) -> None:
        IPtagResource("1", 2, True)  # Minimal args
        iptr = IPtagResource("1.2.3.4", 2, False, 4, "bacon")
        self.assertEqual(iptr.ip_address, "1.2.3.4")
        self.assertEqual(iptr.port, 2)
        self.assertEqual(iptr.strip_sdp, False)
        self.assertEqual(iptr.tag, 4)
        self.assertEqual(iptr.traffic_identifier, "bacon")
        self.assertEqual(str(iptr),
                         "IPTagResource(ip_address=1.2.3.4, port=2, "
                         "strip_sdp=False, tag=4, traffic_identifier=bacon)")

        ReverseIPtagResource()  # Minimal args
        riptr = ReverseIPtagResource(1, 2, 3)
        self.assertEqual(riptr.port, 1)
        self.assertEqual(riptr.sdp_port, 2)
        self.assertEqual(riptr.tag, 3)
        self.assertEqual(str(riptr),
                         "ReverseIPTagResource(port=1, sdp_port=2, tag=3)")
        riptr2 = ReverseIPtagResource(1, 2, 3)
        self.assertNotEqual(riptr, str(riptr))
        self.assertEqual(riptr, riptr2)
        self.assertEqual(hash(riptr), hash(riptr2))

    def test_total(self) -> None:
        var0 = VariableSDRAM(28, 0)
        self.assertEqual(28, var0.get_total_sdram(None))
        var4 = VariableSDRAM(28, 4)
        with self.assertRaises(PacmanConfigurationException):
            var4.get_total_sdram(None)

    def test_shared(self) -> None:
        var1 = VariableSDRAM(20, 1)
        sh1 = SharedSDRAM({"foo": var1})
        sh1.report(10)
        str(sh1)
        self.assertEqual(sh1.get_total_sdram(5), 25)
        combo1 = sh1 + sh1
        self.assertEqual(combo1.get_total_sdram(5), 25)
        self.assertEqual(combo1, sh1)
        combo2 = var1 + var1
        self.assertEqual(combo2.get_total_sdram(5), 50)
        con1 = ConstantSDRAM(12)
        combo3 = sh1 + con1
        self.assertEqual(combo3.get_total_sdram(5), 37)
        combo4 = con1 + sh1
        self.assertEqual(combo4.get_total_sdram(5), 37)
        self.assertEqual(combo3, combo4)

    def test_sdram_multi(self) -> None:
        multi1 = MultiRegionSDRAM()
        multi1.add_cost(1, 100, 4)
        sh1 = SharedSDRAM({"foo": multi1})
        self.assertEqual(sh1.get_total_sdram(10), 100 + 4 * 10)

        multi2 = MultiRegionSDRAM()
        var2 = VariableSDRAM(20, 1)
        sh2 = SharedSDRAM({"bar": var2})
        multi2.nest(2, sh2)
        self.assertEqual(multi2.get_total_sdram(10), 20 + 10)

        combo = sh1 + sh2
        self.assertEqual(combo.get_total_sdram(10), 100 + 4 * 10 + 20 + 10)

    def test_nested_shared(self) -> None:
        # nested sdram do not make sense but do work
        # all but the outer sdram acts like a non shared sdram
        c1 = ConstantSDRAM(45)
        sh1 = SharedSDRAM({"foo": c1})
        sh2 = SharedSDRAM({"bar": sh1})
        self.assertEqual(sh2.get_total_sdram(None), 45)

    def test_reused_key(self) -> None:
        var1 = VariableSDRAM(20, 1)
        sh1 = SharedSDRAM({"foo": var1})
        var2 = VariableSDRAM(20, 1)
        sh2 = SharedSDRAM({"foo": var2})

        v_sum = var1 + var2
        self.assertEqual(v_sum.get_total_sdram(10), 2 * (20 + 10))

        # same shared entered more than once is the same as entered once
        combo = sh1 + sh2
        self.assertEqual(combo.get_total_sdram(10), 20 + 10)

        # Same share inside a multiple is NOT summed!
        multi = MultiRegionSDRAM()
        multi.nest(1, sh1)
        multi.nest(2, sh1)
        self.assertEqual(combo.get_total_sdram(10), 20 + 10)

        var3 = VariableSDRAM(30, 2)
        # reusing key with different values is HIGHLy discouraged
        sh3 = SharedSDRAM({"foo": var3})

        # But will go boom it the shared are combined.
        # Remember this will happen is placed on same Chip
        with self.assertRaises(PacmanConfigurationException):
            sh1 + sh3

        sh4 = SharedSDRAM({"bar": var3})
        multi4 = MultiRegionSDRAM()
        multi4.nest(1, sh1)
        multi4.nest(2, sh4)
        self.assertEqual(multi4.get_total_sdram(10), 20 + 10 + 30 + 2 * 10)


if __name__ == '__main__':
    unittest.main()
