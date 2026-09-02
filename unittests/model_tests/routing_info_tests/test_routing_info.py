# Copyright (c) 2017 The University of Manchester
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

import unittest

from pacman.config_setup import unittest_setup
from pacman.exceptions import (
    IrregularFixedMaskException,
    PacmanAlreadyExistsException,
    PacmanConfigurationException,
    PacmanValueError,
)
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import ConstantSDRAM
from pacman.model.routing_info import (
    BaseKeyAndMask,
    FixedAppVertexRoutingInfo,
    FixedMachineVertexRoutingInfo,
    GlobalAppVertexRoutingInfo,
    GlobalMachineVertexRoutingInfo,
    RoutingInfo,
    SpecificAppVertexRoutingInfo,
    SpecificMachineVertexRoutingInfo,
)
from pacman.utilities.constants import FULL_MASK

from pacman_test_objects import SimpleTestVertex


class TestRoutingInfo(unittest.TestCase):

    def setUp(self) -> None:
        unittest_setup()

    def test_routing_info(self) -> None:
        pre_vertex = SimpleMachineVertex(ConstantSDRAM(0))
        key = 12345
        bkm1 = BaseKeyAndMask(key, FULL_MASK)
        info = GlobalMachineVertexRoutingInfo(
            bkm1, "Test", pre_vertex, 0, FULL_MASK)
        routing_info = RoutingInfo()
        routing_info.add_routing_info(info)
        orphan = SimpleMachineVertex(ConstantSDRAM(0))

        with self.assertRaises(PacmanAlreadyExistsException):
            routing_info.add_routing_info(info)

        assert routing_info.get_info_from(
            pre_vertex, "Test") == info
        with self.assertRaises(KeyError):
            routing_info.get_info_from(
                None, "Test")  # type: ignore[arg-type]
        with self.assertRaises(KeyError):
            routing_info.get_info_from(
                pre_vertex, None)  # type: ignore[arg-type]

        assert routing_info.get_key_from(
            pre_vertex, "Test") == key
        with self.assertRaises(KeyError):
            routing_info.get_key_from(
                None, "Test")  # type: ignore[arg-type]
        with self.assertRaises(KeyError):
            routing_info.get_key_from(
                pre_vertex, "None")  # type: ignore[arg-type]

        assert list(routing_info.get_partitions_from(
            pre_vertex)) == ["Test"]
        assert list(routing_info.get_partitions_from(
            orphan)) == []

        # This should work as can be either partition
        routing_info.check_info_from(
            pre_vertex, {"Test", "Test2"})

        # Works because orphan has no partitions!
        routing_info.check_info_from(orphan, {"Test"})

        # This should not work
        with self.assertRaises(KeyError):
            routing_info.check_info_from(pre_vertex, {"Test2"})

        assert routing_info.has_info_from(
            pre_vertex, "Test")
        assert not routing_info.has_info_from(
            None, "Test")  # type: ignore[arg-type]
        assert not routing_info.has_info_from(
            pre_vertex, "None")

        assert next(iter(routing_info)) == info

        info2 = GlobalMachineVertexRoutingInfo(
            bkm1, "Test", pre_vertex, 0, FULL_MASK)

        with self.assertRaises(PacmanAlreadyExistsException):
            routing_info.add_routing_info(info2)
        assert info != info2

        info3 = GlobalMachineVertexRoutingInfo(
            bkm1, "Test2", pre_vertex, 0, FULL_MASK)
        routing_info.add_routing_info(info3)
        assert info != info3
        assert routing_info.get_info_from(
                pre_vertex, "Test2") !=\
            routing_info.get_info_from(
                pre_vertex, "Test")
        assert routing_info.get_info_from(
            pre_vertex, "Test2").get_keys().tolist() == [key]
        with self.assertRaises(KeyError):
            routing_info.get_single_info_from(
                pre_vertex)
        with self.assertRaises(KeyError):
            routing_info.get_single_key_from(pre_vertex)

        self.assertEqual(len(routing_info), len(list(routing_info)))

    def test_multiple(self) -> None:
        routing_info = RoutingInfo()
        vertex1 = SimpleMachineVertex(ConstantSDRAM(0))
        key = 12345
        bkm1 = BaseKeyAndMask(key, FULL_MASK)
        info = GlobalMachineVertexRoutingInfo(
            bkm1, "Test", vertex1, 0, FULL_MASK)
        routing_info.add_routing_info(info)
        key = 67890
        bkm2 = BaseKeyAndMask(key, FULL_MASK)
        info = GlobalMachineVertexRoutingInfo(
            bkm2, "Test2", vertex1, 0, FULL_MASK)
        routing_info.add_routing_info(info)
        self.assertEqual(len(routing_info), len(list(routing_info)))

    def test_base_key_and_mask(self) -> None:
        with self.assertRaises(PacmanConfigurationException):
            BaseKeyAndMask(0xF0, 0x40)
        bkm1 = BaseKeyAndMask(0x40, 0xF0)
        assert bkm1 == bkm1
        assert bkm1 != []
        assert str(bkm1) == "KeyAndMask:0x40:0xf0"
        assert bkm1.n_keys == 268435456
        bkm2 = BaseKeyAndMask(0x40000000, FULL_MASK & ~1)
        assert bkm1 != bkm2
        assert bkm2.n_keys == 2
        k, n = bkm2.get_keys()
        assert k.tolist() == [1073741824, 1073741825]
        assert n == 2

    def test_fixed_machine_vertex_routing_info(self) -> None:
        global_app = 0xff000000
        global_mac = 0xffffff00
        specific_app = 0xFFF00000
        specific_mac = 0xFFFFF000
        bka = BaseKeyAndMask(0x11000000, specific_app)
        bkm1 = BaseKeyAndMask(0x11002000, specific_mac)
        vertex1 = SimpleMachineVertex(ConstantSDRAM(0))
        info = FixedMachineVertexRoutingInfo(
            bkm1, "test", vertex1, 2, bka)

        # global masks set later so these fail until set
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.global_app_mask
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.has_global_app_masks
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.global_machine_mask
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.has_global_machine_masks
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.global_app_shift

        # Regular stiff works right away
        self.assertEqual(info.key_and_mask, bkm1)
        self.assertTrue(info.has_fixed_keys)
        self.assertEqual(info.app_mask, specific_app)
        self.assertEqual(info.machine_mask, specific_mac)
        self.assertTrue(info.is_machine_shiftable)
        self.assertEqual(info.machine_shift, 12)
        self.assertEqual(info.machine_index_mask, 0x000FF000)
        self.assertEqual(info.atom_mask, 0x00000FFF)
        self.assertEqual((8, 18), info.get_atom_bits_needed_range())

        info.set_global_masks(global_app, global_mac)
        self.assertFalse(info.has_global_app_masks)
        self.assertEqual(info.global_app_shift, 24)
        self.assertFalse(info.has_global_machine_masks)

    def test_not_shiftable(self) -> None:
        global_app = 0xff000000
        global_mac = 0xffffff00
        specific_app = 0xFFF00000
        specific_mac = 0xFFF3b000
        bkm1 = BaseKeyAndMask(0x11002000, specific_mac)
        vertex1 = SimpleMachineVertex(ConstantSDRAM(0))
        bkma = BaseKeyAndMask(0x11000000, specific_app)
        info = FixedMachineVertexRoutingInfo(
            bkm1, "test", vertex1, 2, bkma)
        info.set_global_masks(global_app, global_mac)
        self.assertEqual(info.key_and_mask, bkm1)
        self.assertFalse(info.has_global_app_masks)
        self.assertFalse(info.has_global_machine_masks)
        self.assertTrue(info.has_fixed_keys)
        self.assertEqual(info.app_mask, specific_app)
        self.assertEqual(info.global_app_shift, 24)
        self.assertEqual(info.machine_mask, specific_mac)
        self.assertFalse(info.has_global_app_masks)
        self.assertFalse(info.is_machine_shiftable)
        with self.assertRaises(PacmanValueError):
            _ = info.machine_shift
        # based on global
        self.assertEqual(info.machine_index_mask, 0x0003b000)
        self.assertEqual(hex(info.atom_mask), hex(0x000c4FfF))
        self.assertEqual((8, 18), info.get_atom_bits_needed_range())

    def test_fixed_one_to_one_routing_info(self) -> None:
        global_app = 0xff000000
        global_mac = 0xffffff00
        specific = 0xFFFFF000
        vertex1 = SimpleMachineVertex(ConstantSDRAM(0))
        bk = BaseKeyAndMask(0x11000000, specific)
        info = FixedMachineVertexRoutingInfo(
            bk, "test", vertex1, 0, bk)
        info.set_global_masks(global_app, global_mac)
        self.assertEqual(info.key_and_mask, bk)
        self.assertFalse(info.has_global_app_masks)
        self.assertFalse(info.has_global_machine_masks)
        self.assertTrue(info.has_fixed_keys)
        self.assertEqual(info.app_mask, specific)
        self.assertEqual(info.global_app_shift, 24)
        self.assertEqual(info.machine_mask, specific)
        self.assertEqual(info.machine_shift, 12)
        # uses global
        self.assertEqual(info.machine_index_mask, 0x00000000)
        self.assertEqual(info.atom_mask, 0x00000FFF)
        self.assertEqual((0, 20), info.get_atom_bits_needed_range())

    def test_weird_machine_vertex_routing_info(self) -> None:
        specific_app = 0xF000000F
        specific_mac = 0xF0F0000F
        bkm1 = BaseKeyAndMask(0x00100000, specific_mac)
        vertex1 = SimpleMachineVertex(ConstantSDRAM(0))
        bka = BaseKeyAndMask(specific_app, specific_mac)
        with self.assertRaises(IrregularFixedMaskException):
            FixedMachineVertexRoutingInfo(
                bkm1, "test", vertex1, 2, bka)

    def test_specific_machine_vertex_routing_info(self) -> None:
        global_app = 0xff000000
        global_mac = 0xffffff00
        specific_mac = 0xFFFF0000
        mac_key = 0x00110000
        bkm1 = BaseKeyAndMask(mac_key, specific_mac)
        vertex1 = SimpleMachineVertex(ConstantSDRAM(0))
        info = SpecificMachineVertexRoutingInfo(
            bkm1, "test", vertex1, 2, global_app, global_mac)
        self.assertEqual(info.key_and_mask, bkm1)
        self.assertTrue(info.has_global_app_masks)
        self.assertFalse(info.has_global_machine_masks)
        self.assertFalse(info.has_fixed_keys)
        self.assertEqual(info.app_mask, global_app)
        self.assertEqual(info.global_app_shift, 24)
        self.assertEqual(info.machine_mask, specific_mac)
        self.assertEqual(info.machine_shift, 16)
        self.assertEqual(info.machine_index_mask, 0x00FF0000)
        self.assertEqual(info.atom_mask, 0x0000FFFF)

    def test_global_machine_vertex_routing_info(self) -> None:
        global_app = 0xff000000
        global_mac = 0xffffff00
        vertex1 = SimpleMachineVertex(ConstantSDRAM(0))
        bkm1 = BaseKeyAndMask(0x00110000, global_mac)
        info = GlobalMachineVertexRoutingInfo(
            bkm1, "test", vertex1, 2, global_app)
        self.assertEqual(info.key_and_mask, bkm1)
        self.assertTrue(info.has_global_app_masks)
        self.assertTrue(info.has_global_machine_masks)
        self.assertFalse(info.has_fixed_keys)
        self.assertEqual(info.app_mask, global_app)
        self.assertEqual(info.global_app_shift, 24)
        self.assertEqual(info.machine_mask, global_mac)
        self.assertEqual(info.machine_shift, 8)
        self.assertEqual(info.machine_index_mask, 0x00FFFF00)
        self.assertEqual(info.atom_mask, 0x000000FF)

    def test_fixed_app_vertex_routing_info(self) -> None:
        unittest_setup()
        global_app = 0xff000000
        global_mac = 0xffffff00
        specific_app = 0xFFF00000
        specific_mac = 0xFFFF0000
        key = 0x11000000
        bkm = BaseKeyAndMask(key, specific_app)
        vertex1 = SimpleTestVertex(4, "fixed")
        info = FixedAppVertexRoutingInfo(
            bkm, "test", vertex1, 2, specific_mac)

        # global masks set later so these fail until set
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.global_app_mask
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.has_global_app_masks
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.global_machine_mask
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.has_global_machine_masks
        with self.assertRaises(IrregularFixedMaskException):
            _ = info.global_app_shift

        # Regular stiff works right away
        self.assertEqual(info.mask, specific_app)
        self.assertEqual(info.key_and_mask, bkm)
        self.assertTrue(info.has_fixed_keys)
        self.assertEqual(info.machine_mask, specific_mac)
        self.assertEqual(info.machine_shift, 16)
        self.assertEqual(info.machine_index_mask, 0x000F0000)
        self.assertEqual(info.atom_mask, 0x0000FFFF)

        info.set_global_masks(global_app, global_mac)
        self.assertFalse(info.has_global_app_masks)
        self.assertEqual(info.global_app_mask, global_app)
        self.assertEqual(info.global_app_shift, 24)
        self.assertEqual(info.global_machine_mask, global_mac)
        self.assertFalse(info.has_global_machine_masks)

    def test_weird_app_vertex_routing_info(self) -> None:
        specific_app = 0xF000000F
        specific_mac = 0xF0F0000F
        bkm1 = BaseKeyAndMask(0x10000001, specific_app)
        vertex1 = SimpleTestVertex(4, "fixed")
        with self.assertRaises(IrregularFixedMaskException):
            FixedAppVertexRoutingInfo(
                key_and_mask=bkm1, partition_id="test", app_vertex=vertex1,
                machine_mask=specific_mac, max_machine_index=3)

    def test_specific_app_vertex_routing_info(self) -> None:
        unittest_setup()
        global_app = 0xff000000
        global_mac = 0xffffff00
        specific_mac = 0xFFFF0000
        vertex1 = SimpleTestVertex(4, "fixed")
        bkm1 = BaseKeyAndMask(0x11000000, global_app)
        info = SpecificAppVertexRoutingInfo(
            bkm1, "test", vertex1, 3, specific_mac, global_mac)
        bkm1 = BaseKeyAndMask(0x11000000, global_app)
        self.assertEqual(info.key_and_mask, bkm1)
        self.assertTrue(info.has_global_app_masks)
        self.assertFalse(info.has_global_machine_masks)
        self.assertFalse(info.has_fixed_keys)
        self.assertEqual(info.app_mask, global_app)
        self.assertEqual(info.global_app_shift, 24)
        self.assertEqual(info.machine_mask, specific_mac)
        self.assertEqual(info.machine_shift, 16)
        self.assertEqual(info.machine_index_mask, 0x00FF0000)
        self.assertEqual(info.atom_mask, 0x0000FFFF)

    def test_global_app_vertex_routing_info(self) -> None:
        global_app = 0xff000000
        global_mac = 0xffffff00
        vertex1 = SimpleTestVertex(4, "fixed")
        app_key = 0x11000000
        bkm1 = BaseKeyAndMask(0x11000000, global_app)
        info = GlobalAppVertexRoutingInfo(
            bkm1, "test", vertex1, 3, global_mac)
        self.assertEqual(info.key, app_key)
        self.assertEqual(info.mask, global_app)
        self.assertEqual(info.key_and_mask, bkm1)
        self.assertTrue(info.has_global_app_masks)
        self.assertTrue(info.has_global_machine_masks)
        self.assertFalse(info.has_fixed_keys)
        self.assertEqual(info.app_mask, global_app)
        self.assertEqual(info.global_app_shift, 24)
        self.assertEqual(info.machine_mask, global_mac)
        self.assertEqual(info.machine_shift, 8)
        self.assertEqual(info.machine_index_mask, 0x00FFFF00)
        self.assertEqual(info.atom_mask, 0x000000FF)


if __name__ == "__main__":
    unittest.main()
