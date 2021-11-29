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
import pytest
from pacman.config_setup import unittest_setup
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.constraints.key_allocator_constraints import (
    FixedKeyAndMaskConstraint, ShareKeyConstraint)
from pacman.model.graphs.machine import (
    MachineGraph, SimpleMachineVertex, MachineEdge)
from pacman.model.graphs.machine import MulticastEdgePartition
from pacman.model.resources import ResourceContainer
from pacman.operations.routing_info_allocator_algorithms\
    .malloc_based_routing_allocator.malloc_based_routing_info_allocator\
    import (_MallocBasedRoutingInfoAllocator,
            malloc_based_routing_info_allocator)
from pacman.model.routing_info import (
    BaseKeyAndMask, DictBasedMachinePartitionNKeysMap)


class MyTestCase(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_allocate_fixed_key_and_mask(self):
        allocator = _MallocBasedRoutingInfoAllocator(None)
        allocator._allocate_fixed_keys_and_masks(
            [BaseKeyAndMask(0x800, 0xFFFFF800)], None)
        error = ("Allocation has not resulted in the expected free space"
                 " being available")
        print(allocator._free_space_tracker)
        self.assertEqual(len(allocator._free_space_tracker), 2, error)
        self.assertEqual(allocator._free_space_tracker[0].start_address, 0,
                         error)
        self.assertEqual(allocator._free_space_tracker[0].size, 2048,
                         error)
        self.assertEqual(allocator._free_space_tracker[1].start_address,
                         0x1000, error)
        self.assertEqual(allocator._free_space_tracker[1].size, 0xFFFFF000,
                         error)

    def _print_keys_and_masks(self, keys_and_masks):
        for key_and_mask in keys_and_masks:
            print("key =", hex(key_and_mask.key),
                  "mask =", hex(key_and_mask.mask))

    def test_allocate_fixed_mask(self):
        allocator = _MallocBasedRoutingInfoAllocator(None)
        self._print_keys_and_masks(allocator._allocate_keys_and_masks(
            0xFFFFFF00, None, 20))
        error = ("Allocation has not resulted in the expected free space"
                 " being available")
        print(allocator._free_space_tracker)
        self.assertEqual(len(allocator._free_space_tracker), 1, error)
        self.assertEqual(allocator._free_space_tracker[0].start_address, 0x100,
                         error)
        self.assertEqual(allocator._free_space_tracker[0].size, 0xFFFFFF00,
                         error)

    def test_allocate_n_keys(self):
        allocator = _MallocBasedRoutingInfoAllocator(None)
        self._print_keys_and_masks(allocator._allocate_keys_and_masks(
            None, None, 20))
        error = ("Allocation has not resulted in the expected free space"
                 " being available")
        print(allocator._free_space_tracker)
        self.assertEqual(len(allocator._free_space_tracker), 1, error)
        self.assertEqual(allocator._free_space_tracker[0].start_address, 32,
                         error)
        self.assertEqual(allocator._free_space_tracker[0].size,
                         0x100000000 - 32, error)

    def test_allocate_mixed_keys(self):
        fixed_masks = [None, None, 0xFFFFFF00, 0xFFFFF800]
        n_keys = [200, 20, 20, 256]

        allocator = _MallocBasedRoutingInfoAllocator(None)

        allocator._allocate_fixed_keys_and_masks(
            [BaseKeyAndMask(0x800, 0xFFFFF800)], None)

        print(allocator._free_space_tracker)

        for mask, keys in zip(fixed_masks, n_keys):
            self._print_keys_and_masks(
                allocator._allocate_keys_and_masks(mask, None, keys))
            print(allocator._free_space_tracker)

        print(allocator._free_space_tracker)

        error = ("Allocation has not resulted in the expected free space"
                 " being available")
        self.assertEqual(len(allocator._free_space_tracker), 3, error)
        self.assertEqual(allocator._free_space_tracker[0].start_address,
                         0x120, error)
        self.assertEqual(allocator._free_space_tracker[0].size,
                         224, error)
        self.assertEqual(allocator._free_space_tracker[1].start_address,
                         0x300, error)
        self.assertEqual(allocator._free_space_tracker[1].size,
                         1280, error)
        self.assertEqual(allocator._free_space_tracker[2].start_address,
                         0x1800, error)
        self.assertEqual(allocator._free_space_tracker[2].size,
                         0x100000000 - 0x1800, error)

    def _integration_setup(self):
        machine_graph = MachineGraph(label="test me you git")
        n_keys_map = DictBasedMachinePartitionNKeysMap()
        v1 = SimpleMachineVertex(ResourceContainer())
        v2 = SimpleMachineVertex(ResourceContainer())
        v3 = SimpleMachineVertex(ResourceContainer())
        v4 = SimpleMachineVertex(ResourceContainer())
        machine_graph.add_vertex(v1)
        machine_graph.add_vertex(v2)
        machine_graph.add_vertex(v3)
        machine_graph.add_vertex(v4)

        e1 = MachineEdge(v1, v2, label="e1")
        e2 = MachineEdge(v1, v3, label="e2")
        e3 = MachineEdge(v2, v3, label="e3")
        e4 = MachineEdge(v1, v4, label="e4")

        machine_graph.add_outgoing_edge_partition(
            MulticastEdgePartition(identifier="part1", pre_vertex=v1))
        machine_graph.add_outgoing_edge_partition(
            MulticastEdgePartition(identifier="part2", pre_vertex=v2))
        machine_graph.add_outgoing_edge_partition(
            MulticastEdgePartition(identifier="part2", pre_vertex=v1))

        machine_graph.add_edge(e1, "part1")
        machine_graph.add_edge(e2, "part1")
        machine_graph.add_edge(e3, "part2")
        machine_graph.add_edge(e4, "part2")

        for partition in machine_graph.outgoing_edge_partitions:
            n_keys_map.set_n_keys_for_partition(partition, 24)

        return machine_graph, n_keys_map, v1, v2, v3, v4, e1, e2, e3, e4

    @pytest.mark.skip("Disabled until fixed")
    def test_share_key_with_2_nests(self):
        machine_graph, n_keys_map, v1, v2, _v3, v4, e1, e2, e3, e4 = (
            self._integration_setup())
        e5 = MachineEdge(v4, v2, label="e1")
        machine_graph.add_outgoing_edge_partition(
            MulticastEdgePartition(identifier="part3", pre_vertex=v4))

        machine_graph.add_edge(e5, "part3")
        partition2 = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v4, "part3")
        n_keys_map.set_n_keys_for_partition(partition2, 24)

        partition1 = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
        partition4 = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v1, "part2")
        partition3 = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v2, "part2")

        partition1.add_constraint(ShareKeyConstraint([partition4]))
        partition2.add_constraint(ShareKeyConstraint([partition3]))
        partition3.add_constraint(ShareKeyConstraint([partition1]))

        results = malloc_based_routing_info_allocator(
            machine_graph, n_keys_map)

        key = results.get_first_key_from_partition(
            machine_graph.get_outgoing_edge_partition_starting_at_vertex(
                v1, "part1"))

        edge1_key = results.get_first_key_for_edge(e1)
        edge2_key = results.get_first_key_for_edge(e2)
        edge3_key = results.get_first_key_for_edge(e3)
        edge4_key = results.get_first_key_for_edge(e4)
        edge5_key = results.get_first_key_for_edge(e5)

        self.assertEqual(edge1_key, key)
        self.assertEqual(edge2_key, key)
        self.assertEqual(edge3_key, key)
        self.assertEqual(edge4_key, key)
        self.assertEqual(edge5_key, key)

    def test_share_key_with_conflicting_fixed_key_on_partitions(self):
        machine_graph, n_keys_map, v1, v2, _v3, _v4, _e1, _e2, _e3, _e4 = \
            self._integration_setup()

        partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
        other_partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v2, "part2")
        other_partition.add_constraint(ShareKeyConstraint([partition]))

        other_partition.add_constraint(FixedKeyAndMaskConstraint(
            [BaseKeyAndMask(base_key=30, mask=0xFFFFFFF)]))
        partition.add_constraint(FixedKeyAndMaskConstraint(
            [BaseKeyAndMask(base_key=25, mask=0xFFFFFFF)]))

        with self.assertRaises(PacmanRouteInfoAllocationException):
            malloc_based_routing_info_allocator(machine_graph, n_keys_map)

    @pytest.mark.skip("Disabled until fixed")
    def test_share_key_with_fixed_key_on_new_partitions_other_order(self):
        machine_graph, n_keys_map, v1, v2, _v3, _v4, e1, e2, e3, e4 = \
            self._integration_setup()

        partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
        other_partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v2, "part2")
        other_partition.add_constraint(ShareKeyConstraint([partition]))
        partition.add_constraint(FixedKeyAndMaskConstraint(
            [BaseKeyAndMask(base_key=25, mask=0xFFFFFFF)]))

        results = malloc_based_routing_info_allocator(
            machine_graph, n_keys_map)

        key = results.get_first_key_from_partition(
            machine_graph.get_outgoing_edge_partition_starting_at_vertex(
                v1, "part1"))
        edge1_key = results.get_first_key_for_edge(e1)
        edge2_key = results.get_first_key_for_edge(e2)
        edge3_key = results.get_first_key_for_edge(e3)
        edge4_key = results.get_first_key_for_edge(e4)

        self.assertEqual(key, 25)
        self.assertEqual(edge1_key, key)
        self.assertEqual(edge2_key, key)
        self.assertEqual(edge3_key, key)
        self.assertNotEqual(edge4_key, key)

    @pytest.mark.skip("Disabled until fixed")
    def test_share_key_with_fixed_key_on_new_partitions(self):
        machine_graph, n_keys_map, v1, v2, _v3, _v4, e1, e2, e3, e4 = \
            self._integration_setup()

        partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
        other_partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v2, "part2")
        partition.add_constraint(ShareKeyConstraint([other_partition]))
        other_partition.add_constraint(FixedKeyAndMaskConstraint(
            [BaseKeyAndMask(base_key=25, mask=0xFFFFFFF)]))

        results = malloc_based_routing_info_allocator(
            machine_graph, n_keys_map)

        key = results.get_first_key_from_partition(
            machine_graph.get_outgoing_edge_partition_starting_at_vertex(
                v1, "part1"))
        edge1_key = results.get_first_key_for_edge(e1)
        edge2_key = results.get_first_key_for_edge(e2)
        edge3_key = results.get_first_key_for_edge(e3)
        edge4_key = results.get_first_key_for_edge(e4)

        self.assertEqual(key, 25)
        self.assertEqual(edge1_key, key)
        self.assertEqual(edge2_key, key)
        self.assertEqual(edge3_key, key)
        self.assertNotEqual(edge4_key, key)

    @pytest.mark.skip("Disabled until fixed")
    def test_share_key_on_own_partition(self):
        machine_graph, n_keys_map, v1, _v2, _v3, _v4, e1, e2, e3, e4 = \
            self._integration_setup()

        partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
        other_partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v1, "part2")
        partition.add_constraint(ShareKeyConstraint([other_partition]))

        results = malloc_based_routing_info_allocator(
            machine_graph, n_keys_map)

        key = results.get_first_key_from_partition(
            machine_graph.get_outgoing_edge_partition_starting_at_vertex(
                v1, "part1"))
        edge1_key = results.get_first_key_for_edge(e1)
        edge2_key = results.get_first_key_for_edge(e2)
        edge3_key = results.get_first_key_for_edge(e3)
        edge4_key = results.get_first_key_for_edge(e4)

        self.assertEqual(edge1_key, key)
        self.assertEqual(edge2_key, key)
        self.assertNotEqual(edge3_key, key)
        self.assertEqual(edge4_key, key)

    @pytest.mark.skip("Disabled until fixed")
    def test_share_key_on_new_partitions(self):
        machine_graph, n_keys_map, v1, v2, _v3, _v4, e1, e2, e3, e4 = \
            self._integration_setup()

        partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v1, "part1")
        other_partition = machine_graph.\
            get_outgoing_edge_partition_starting_at_vertex(v2, "part2")
        partition.add_constraint(ShareKeyConstraint([other_partition]))

        results = malloc_based_routing_info_allocator(
            machine_graph, n_keys_map)

        key = results.get_first_key_from_partition(
            machine_graph.get_outgoing_edge_partition_starting_at_vertex(
                v1, "part1"))
        edge1_key = results.get_first_key_for_edge(e1)
        edge2_key = results.get_first_key_for_edge(e2)
        edge3_key = results.get_first_key_for_edge(e3)
        edge4_key = results.get_first_key_for_edge(e4)

        self.assertEqual(edge1_key, key)
        self.assertEqual(edge2_key, key)
        self.assertEqual(edge3_key, key)
        self.assertNotEqual(edge4_key, key)

    @pytest.mark.skip("Disabled until fixed")
    def test_no_share_key_on_partitions(self):
        machine_graph, n_keys_map, v1, _v2, _v3, _v4, e1, e2, e3, e4 = \
            self._integration_setup()

        results = malloc_based_routing_info_allocator(
            machine_graph, n_keys_map)

        key = results.get_first_key_from_partition(
            machine_graph.get_outgoing_edge_partition_starting_at_vertex(
                v1, "part1"))

        edge1_key = results.get_first_key_for_edge(e1)
        edge2_key = results.get_first_key_for_edge(e2)
        edge3_key = results.get_first_key_for_edge(e3)
        edge4_key = results.get_first_key_for_edge(e4)

        self.assertEqual(edge1_key, key)
        self.assertEqual(edge2_key, key)
        self.assertNotEqual(edge3_key, key)
        self.assertNotEqual(edge4_key, key)


if __name__ == '__main__':
    unittest.main()
