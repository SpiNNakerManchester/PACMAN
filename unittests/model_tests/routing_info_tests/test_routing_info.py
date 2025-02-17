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
from pacman.model.resources import ConstantSDRAM
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException)
from pacman.model.routing_info import (
    RoutingInfo, BaseKeyAndMask, MachineVertexRoutingInfo)
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.utilities.constants import FULL_MASK


class TestRoutingInfo(unittest.TestCase):

    def setUp(self) -> None:
        unittest_setup()

    # TODO: Replace (currently temporarily broken to make sure we don't
    # call it)
    # def test_routing_info_deprecated(self) -> None:
    #     pre_vertex = SimpleMachineVertex(ConstantSDRAM(0))
    #     key = 12345
    #     info = MachineVertexRoutingInfo(
    #         BaseKeyAndMask(key, FULL_MASK), "Test", pre_vertex, 0)
    #     routing_info = RoutingInfo()
    #     routing_info.add_routing_info(info)
    #
    #     with self.assertRaises(PacmanAlreadyExistsException):
    #         routing_info.add_routing_info(info)
    #
    #     assert routing_info.get_routing_info_from_pre_vertex(
    #         pre_vertex, "Test") == info
    #     assert routing_info.get_routing_info_from_pre_vertex(
    #         None, "Test") is None
    #     assert routing_info.get_routing_info_from_pre_vertex(
    #         pre_vertex, "None") is None
    #
    #     assert routing_info.get_first_key_from_pre_vertex(
    #         pre_vertex, "Test") == key
    #     assert routing_info.get_first_key_from_pre_vertex(
    #         None, "Test") is None
    #     assert routing_info.get_first_key_from_pre_vertex(
    #         pre_vertex, "None") is None
    #
    #     assert next(iter(routing_info)) == info
    #
    #     info2 = MachineVertexRoutingInfo(
    #         BaseKeyAndMask(key, FULL_MASK), "Test", pre_vertex, 0)
    #
    #     with self.assertRaises(PacmanAlreadyExistsException):
    #         routing_info.add_routing_info(info2)
    #     assert info != info2
    #
    #     info3 = MachineVertexRoutingInfo(
    #         BaseKeyAndMask(key, FULL_MASK), "Test2", pre_vertex, 0)
    #     routing_info.add_routing_info(info3)
    #     assert info != info3
    #     assert routing_info.get_routing_info_from_pre_vertex(
    #             pre_vertex, "Test2") !=\
    #         routing_info.get_routing_info_from_pre_vertex(
    #             pre_vertex, "Test")
    #     assert routing_info.get_routing_info_from_pre_vertex(
    #         pre_vertex, "Test2").get_keys().tolist() == [key]

    def test_routing_info(self) -> None:
        pre_vertex = SimpleMachineVertex(ConstantSDRAM(0))
        key = 12345
        info = MachineVertexRoutingInfo(
            BaseKeyAndMask(key, FULL_MASK), "Test", pre_vertex, 0)
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
        #with self.assertRaises(KeyError):
        #    routing_info.get_info_from(
        #        pre_vertex, None)  # type: ignore[arg-type]

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

        info2 = MachineVertexRoutingInfo(
            BaseKeyAndMask(key, FULL_MASK), "Test", pre_vertex, 0)

        with self.assertRaises(PacmanAlreadyExistsException):
            routing_info.add_routing_info(info2)
        assert info != info2

        info3 = MachineVertexRoutingInfo(
            BaseKeyAndMask(key, FULL_MASK), "Test2", pre_vertex, 0)
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


if __name__ == "__main__":
    unittest.main()
