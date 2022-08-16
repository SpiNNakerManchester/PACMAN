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
from pacman.config_setup import unittest_setup
from pacman.model.resources import ConstantSDRAM
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException)
from pacman.model.routing_info import (
    RoutingInfo, BaseKeyAndMask, MachineVertexRoutingInfo)
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.utilities.constants import FULL_MASK


class TestRoutingInfo(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_routing_info(self):
        pre_vertex = SimpleMachineVertex(ConstantSDRAM(0))
        key = 12345
        info = MachineVertexRoutingInfo(
            [BaseKeyAndMask(key, FULL_MASK)], "Test", pre_vertex, 0)
        routing_info = RoutingInfo()
        routing_info.add_routing_info(info)

        with self.assertRaises(PacmanAlreadyExistsException):
            routing_info.add_routing_info(info)

        assert routing_info.get_routing_info_from_pre_vertex(
            pre_vertex, "Test") == info
        assert routing_info.get_routing_info_from_pre_vertex(
            None, "Test") is None
        assert routing_info.get_routing_info_from_pre_vertex(
            pre_vertex, "None") is None

        assert routing_info.get_first_key_from_pre_vertex(
            pre_vertex, "Test") == key
        assert routing_info.get_first_key_from_pre_vertex(
            None, "Test") is None
        assert routing_info.get_first_key_from_pre_vertex(
            pre_vertex, "None") is None

        assert next(iter(routing_info)) == info

        info2 = MachineVertexRoutingInfo(
            [BaseKeyAndMask(key, FULL_MASK)], "Test", pre_vertex, 0)

        with self.assertRaises(PacmanAlreadyExistsException):
            routing_info.add_routing_info(info2)
        assert info != info2

        info3 = MachineVertexRoutingInfo(
            [BaseKeyAndMask(key, FULL_MASK)], "Test2", pre_vertex, 0)
        routing_info.add_routing_info(info3)
        assert info != info3
        assert routing_info.get_routing_info_from_pre_vertex(
                pre_vertex, "Test2") !=\
            routing_info.get_routing_info_from_pre_vertex(
                pre_vertex, "Test")
        assert routing_info.get_routing_info_from_pre_vertex(
            pre_vertex, "Test2").get_keys().tolist() == [key]

    def test_base_key_and_mask(self):
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


if __name__ == "__main__":
    unittest.main()
