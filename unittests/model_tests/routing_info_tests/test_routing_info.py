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

import unittest
from pacman.config_setup import unittest_setup
from pacman.model.graphs.machine import MulticastEdgePartition
from pacman.model.resources import ResourceContainer
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException)
from pacman.model.routing_info import (
    RoutingInfo, BaseKeyAndMask, PartitionRoutingInfo,
    DictBasedMachinePartitionNKeysMap)
from pacman.model.graphs.machine import MachineEdge, SimpleMachineVertex
from pacman.utilities.constants import FULL_MASK


class TestRoutingInfo(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_routing_info(self):
        # mock to avoid having to create a graph for this test
        graph_code = 123
        pre_vertex = SimpleMachineVertex(resources=ResourceContainer())
        partition = MulticastEdgePartition(pre_vertex, "Test")
        partition.register_graph_code(graph_code)  # This is a hack
        post_vertex = SimpleMachineVertex(resources=ResourceContainer())
        edge = MachineEdge(pre_vertex, post_vertex)
        key = 12345
        partition_info = PartitionRoutingInfo(
            [BaseKeyAndMask(key, FULL_MASK)], partition)
        partition.add_edge(edge, graph_code)
        routing_info = RoutingInfo([partition_info])

        with self.assertRaises(PacmanAlreadyExistsException):
            routing_info.add_partition_info(partition_info)

        assert routing_info.get_first_key_from_partition(partition) == key
        assert routing_info.get_first_key_from_partition(None) is None

        assert routing_info.get_routing_info_from_partition(partition) == \
            partition_info
        assert routing_info.get_routing_info_from_partition(None) is None

        assert routing_info.get_routing_info_from_pre_vertex(
            pre_vertex, "Test") == partition_info
        assert routing_info.get_routing_info_from_pre_vertex(
            post_vertex, "Test") is None
        assert routing_info.get_routing_info_from_pre_vertex(
            pre_vertex, "None") is None

        assert routing_info.get_first_key_from_pre_vertex(
            pre_vertex, "Test") == key
        assert routing_info.get_first_key_from_pre_vertex(
            post_vertex, "Test") is None
        assert routing_info.get_first_key_from_pre_vertex(
            pre_vertex, "None") is None

        assert routing_info.get_routing_info_for_edge(edge) == partition_info
        assert routing_info.get_routing_info_for_edge(None) is None

        assert routing_info.get_first_key_for_edge(edge) == key
        assert routing_info.get_first_key_for_edge(None) is None

        assert next(iter(routing_info)) == partition_info

        partition2 = MulticastEdgePartition(pre_vertex, "Test")
        partition2.register_graph_code(graph_code)  # This is a hack
        partition2.add_edge(MachineEdge(pre_vertex, post_vertex), graph_code)

        with self.assertRaises(PacmanAlreadyExistsException):
            routing_info.add_partition_info(PartitionRoutingInfo(
                [BaseKeyAndMask(key, FULL_MASK)], partition2))
        assert partition != partition2

        partition3 = MulticastEdgePartition(pre_vertex, "Test2")
        partition3.register_graph_code(graph_code)  # This is a hack
        partition3.add_edge(MachineEdge(pre_vertex, post_vertex), graph_code)
        routing_info.add_partition_info(PartitionRoutingInfo(
            [BaseKeyAndMask(key, FULL_MASK)], partition3))

        assert routing_info.get_routing_info_from_partition(partition) != \
            routing_info.get_routing_info_from_partition(partition3)
        assert partition != partition3
        assert routing_info.get_routing_info_from_partition(
            partition3).get_keys().tolist() == [key]

        partition4 = MulticastEdgePartition(pre_vertex, "Test4")
        partition4.register_graph_code(graph_code)  # This is a hack
        partition4.add_edge(MachineEdge(pre_vertex, post_vertex), graph_code)
        routing_info.add_partition_info(PartitionRoutingInfo(
            [BaseKeyAndMask(key, FULL_MASK),
             BaseKeyAndMask(key * 2, FULL_MASK)], partition4))

        assert routing_info.get_routing_info_from_partition(
            partition4).get_keys().tolist() == [key, key * 2]

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

    def test_dict_based_machine_partition_n_keys_map(self):
        pmap = DictBasedMachinePartitionNKeysMap()
        p1 = MulticastEdgePartition(None, "foo")
        p2 = MulticastEdgePartition(None, "bar")
        pmap.set_n_keys_for_partition(p1, 1)
        pmap.set_n_keys_for_partition(p2, 2)
        assert pmap.n_keys_for_partition(p1) == 1
        assert pmap.n_keys_for_partition(p2) == 2


if __name__ == "__main__":
    unittest.main()
