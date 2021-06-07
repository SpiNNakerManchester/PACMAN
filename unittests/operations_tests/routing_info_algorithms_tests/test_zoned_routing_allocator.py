# Copyright (c) 2017-2020 The University of Manchester
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
from pacman.operations.routing_info_allocator_algorithms.\
    zoned_routing_info_allocator import (flexible_allocate, global_allocate)
from pacman.model.graphs.application.application_graph import ApplicationGraph
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.graphs.machine.machine_graph import MachineGraph
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.model.graphs.machine.machine_edge import MachineEdge
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.constraints.key_allocator_constraints \
    import FixedKeyAndMaskConstraint
from pacman_test_objects import SimpleTestVertex


def create_graphs1(with_fixed):
    app_graph = ApplicationGraph("Test")
    # An output vertex to aim things at (to make keys required)
    out_app_vertex = SimpleTestVertex(1)
    app_graph.add_vertex(out_app_vertex)
    # Create 5 application vertices (3 bits)
    app_vertices = list()
    for app_index in range(5):
        app_vertices.append(SimpleTestVertex(1))
    app_graph.add_vertices(app_vertices)

    mac_graph = MachineGraph("Test", app_graph)
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = out_app_vertex.create_machine_vertex(None, None)
    mac_graph.add_vertex(out_mac_vertex)

    # Create 5 application vertices (3 bits)
    for app_index, app_vertex in enumerate(app_vertices):

        # For each, create up to (5 x 4) + 1 = 21 machine vertices (5 bits)
        for mac_index in range((app_index * 4) + 1):
            mac_vertex = app_vertex.create_machine_vertex(None, None)
            mac_graph.add_vertex(mac_vertex)

            # For each machine vertex create up to
            # (20 x 2) + 1 = 81(!) partitions (6 bits)
            for mac_edge_index in range((mac_index * 2) + 1):
                mac_edge = MachineEdge(mac_vertex, out_mac_vertex)
                part_name = "Part{}".format(mac_edge_index)
                mac_graph.add_edge(mac_edge, part_name)

                # Give the partition up to (40 x 4) + 1 = 161 keys (8 bits)
                p = mac_graph.get_outgoing_edge_partition_starting_at_vertex(
                    mac_vertex, part_name)
                if with_fixed:
                    if (app_index == 2 and mac_index == 4 and
                            part_name == "Part7"):
                        p.add_constraint(FixedKeyAndMaskConstraint(
                            [BaseKeyAndMask(0xFE00000, 0xFFFFFFC0)]))
                    if (app_index == 2 and mac_index == 0 and
                            part_name == "Part1"):
                        p.add_constraint(FixedKeyAndMaskConstraint(
                            [BaseKeyAndMask(0x4c00000, 0xFFFFFFFE)]))
                    if (app_index == 2 and mac_index == 0 and
                            part_name == "Part1"):
                        p.add_constraint(FixedKeyAndMaskConstraint(
                            [BaseKeyAndMask(0x4c00000, 0xFFFFFFFF)]))
                    if (app_index == 3 and mac_index == 0 and
                            part_name == "Part1"):
                        p.add_constraint(FixedKeyAndMaskConstraint(
                            [BaseKeyAndMask(0x3300000, 0xFFFFFFFF)]))
                    if (app_index == 3 and mac_index == 0 and
                            part_name == "Part1"):
                        p.add_constraint(FixedKeyAndMaskConstraint(
                            [BaseKeyAndMask(0x3300001, 0)]))
                n_keys_map.set_n_keys_for_partition(
                    p, (mac_edge_index * 4) + 1)

    return app_graph, mac_graph, n_keys_map


def create_graphs_only_fixed():
    app_graph = ApplicationGraph("Test")
    # An output vertex to aim things at (to make keys required)
    out_app_vertex = SimpleTestVertex(1)
    app_graph.add_vertex(out_app_vertex)
    # Create 5 application vertices (3 bits)
    app_vertex = SimpleTestVertex(1)
    app_graph.add_vertex(app_vertex)

    mac_graph = MachineGraph("Test", app_graph)
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = out_app_vertex.create_machine_vertex(None, None)
    mac_graph.add_vertex(out_mac_vertex)

    mac_vertex = app_vertex.create_machine_vertex(None, None)
    mac_graph.add_vertex(mac_vertex)
    for mac_edge_index in range(2):
        mac_edge = MachineEdge(mac_vertex, out_mac_vertex)
        part_name = "Part{}".format(mac_edge_index)
        mac_graph.add_edge(mac_edge, part_name)
        p = mac_graph.get_outgoing_edge_partition_starting_at_vertex(
            mac_vertex, part_name)
        if (mac_edge_index == 0):
            p.add_constraint(FixedKeyAndMaskConstraint(
                [BaseKeyAndMask(0x4c00000, 0xFFFFFFFE)]))
        if (mac_edge_index == 1):
            p.add_constraint(FixedKeyAndMaskConstraint(
                [BaseKeyAndMask(0x4c00000, 0xFFFFFFFF)]))
        n_keys_map.set_n_keys_for_partition(
                p, (mac_edge_index * 4) + 1)

    return app_graph, mac_graph, n_keys_map


def create_graphs_no_edge():
    app_graph = ApplicationGraph("Test")
    # An output vertex to aim things at (to make keys required)
    out_app_vertex = SimpleTestVertex(1)
    app_graph.add_vertex(out_app_vertex)
    # Create 5 application vertices (3 bits)
    app_vertex = SimpleTestVertex(1)
    app_graph.add_vertex(app_vertex)

    mac_graph = MachineGraph("Test", app_graph)
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = out_app_vertex.create_machine_vertex(None, None)
    mac_graph.add_vertex(out_mac_vertex)

    mac_vertex = app_vertex.create_machine_vertex(None, None)
    mac_graph.add_vertex(mac_vertex)

    return app_graph, mac_graph, n_keys_map


def create_app_less():
    app_graph = ApplicationGraph("Test")

    mac_graph = MachineGraph("Test", app_graph)
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = SimpleMachineVertex(None, None)
    mac_graph.add_vertex(out_mac_vertex)

    # Create 5 application vertices (3 bits)
    for app_index in range(5):

        # For each, create up to (5 x 4) + 1 = 21 machine vertices (5 bits)
        for mac_index in range((app_index * 4) + 1):
            mac_vertex = SimpleMachineVertex(None, None)
            mac_graph.add_vertex(mac_vertex)

            # For each machine vertex create up to
            # (20 x 2) + 1 = 81(!) partitions (6 bits)
            for mac_edge_index in range((mac_index * 2) + 1):
                mac_edge = MachineEdge(mac_vertex, out_mac_vertex)
                part_name = "Part{}".format(mac_edge_index)
                mac_graph.add_edge(mac_edge, part_name)

                # Give the partition up to (40 x 4) + 1 = 161 keys (8 bits)
                p = mac_graph.get_outgoing_edge_partition_starting_at_vertex(
                    mac_vertex, part_name)
                n_keys_map.set_n_keys_for_partition(
                    p, (mac_edge_index * 4) + 1)

    return app_graph, mac_graph, n_keys_map


def check_masks_all_the_same(routing_info, mask):
    # Check the mask is the same for all, and allows for the space required
    # for the maximum number of keys in total (bottom 8 bits)
    seen_keys = set()
    for r_info in routing_info:
        assert(len(r_info.keys_and_masks) == 1)
        if r_info.first_mask != mask:
            label = r_info.partition.pre_vertex.label
            assert(label == "RETINA")
        assert(r_info.first_key not in seen_keys)
        seen_keys.add(r_info.first_key)


def check_fixed(p, key):
    for constraint in p.constraints:
        if isinstance(constraint, FixedKeyAndMaskConstraint):
            assert key == constraint.keys_and_masks[0].key
            return True
    return False


def check_keys_for_application_partition_pairs(
        app_graph, m_graph, routing_info, app_mask):
    # Check the key for each application vertex/ parition pair is the same
    # The bits that should be the same are all but the bottom 12
    mapped_base = dict()
    for app_vertex in app_graph.vertices:
        for m_vertex in app_vertex.machine_vertices:
            for p in m_graph.get_multicast_edge_partitions_starting_at_vertex(
                    m_vertex):
                key = routing_info.get_first_key_from_partition(p)
                if check_fixed(p, key):
                    continue
                if (app_vertex, p.identifier) in mapped_base:
                    mapped_key = mapped_base[(app_vertex, p.identifier)]
                    assert((mapped_key & app_mask) == (key & app_mask))
                else:
                    mapped_base[(app_vertex, p.identifier)] = key
                if key != 0:
                    assert((key & app_mask) != 0)


def test_global_allocator():
    # Allocate something and check it does the right thing

    app_graph, mac_graph, n_keys_map = create_graphs1(False)

    # The number of bits is 7 + 5 + 8 = 20, so it shouldn't fail
    routing_info = global_allocate(mac_graph, n_keys_map)

    # Last 8 for buts
    mask = 0xFFFFFF00
    check_masks_all_the_same(routing_info,  mask)

    # all but the bottom 13 bits should be the same
    app_mask = 0xFFFFE000
    check_keys_for_application_partition_pairs(
        app_graph, mac_graph, routing_info, app_mask)


def test_flexible_allocator_no_fixed():
    # Allocate something and check it does the right thing
    app_graph, mac_graph, n_keys_map = create_graphs1(False)

    # The number of bits is 7 + 11 = 20, so it shouldn't fail
    routing_info = flexible_allocate(mac_graph, n_keys_map)

    # all but the bottom 11 bits should be the same
    app_mask = 0xFFFFF800
    check_keys_for_application_partition_pairs(
        app_graph, mac_graph, routing_info, app_mask)


def test_fixed_only():
    app_graph, mac_graph, n_keys_map = create_graphs_only_fixed()
    flexible_allocate(mac_graph, n_keys_map)
    routing_info = global_allocate(mac_graph, n_keys_map)
    assert len(list(routing_info)) == 2


def test_no_edge():
    app_graph, mac_graph, n_keys_map = create_graphs_no_edge()
    flexible_allocate(mac_graph, n_keys_map)
    routing_info = global_allocate(mac_graph, n_keys_map)
    assert len(list(routing_info)) == 0


def test_flexible_allocator_with_fixed():
    # Allocate something and check it does the right thing
    app_graph, mac_graph, n_keys_map = create_graphs1(True)

    # The number of bits is 7 + 11 = 20, so it shouldn't fail
    routing_info = flexible_allocate(mac_graph, n_keys_map)

    # all but the bottom 11 bits should be the same
    app_mask = 0xFFFFF800
    check_keys_for_application_partition_pairs(
        app_graph, mac_graph, routing_info, app_mask)


def create_big(with_fixed):
    # This test shows how easy it is to trip up the allocator with a retina
    app_graph = ApplicationGraph("Test")
    # Create a single "big" vertex
    big_app_vertex = SimpleTestVertex(1, label="Retina")
    app_graph.add_vertex(big_app_vertex)
    # Create a single output vertex (which won't send)
    out_app_vertex = SimpleTestVertex(1, label="Destination")
    app_graph.add_vertex(out_app_vertex)
    # Create a load of middle vertex
    mid_app_vertex = SimpleTestVertex(1, "Population")
    app_graph.add_vertex(mid_app_vertex)

    mac_graph = MachineGraph("Test", app_graph)
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    # Create a single big machine vertex
    big_mac_vertex = big_app_vertex.create_machine_vertex(
        None, None, label="RETINA")
    mac_graph.add_vertex(big_mac_vertex)

    # Create a single output vertex (which won't send)
    out_mac_vertex = out_app_vertex.create_machine_vertex(None, None)
    mac_graph.add_vertex(out_mac_vertex)

    # Create a load of middle vertices and connect them up
    for _ in range(2000):  # 2000 needs 11 bits
        mid_mac_vertex = mid_app_vertex.create_machine_vertex(None, None)
        mac_graph.add_vertex(mid_mac_vertex)
        edge = MachineEdge(big_mac_vertex, mid_mac_vertex)
        mac_graph.add_edge(edge, "Test")
        edge_2 = MachineEdge(mid_mac_vertex, out_mac_vertex)
        mac_graph.add_edge(edge_2, "Test")
        mid_part = mac_graph.get_outgoing_edge_partition_starting_at_vertex(
            mid_mac_vertex, "Test")
        n_keys_map.set_n_keys_for_partition(mid_part, 100)

    big_mac_part = mac_graph.get_outgoing_edge_partition_starting_at_vertex(
        big_mac_vertex, "Test")
    if with_fixed:
        big_mac_part.add_constraint(FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0x0, 0x180000)]))
    # Make the "retina" need 21 bits, so total is now 21 + 11 = 32 bits,
    # but the application vertices need some bits too
    n_keys_map.set_n_keys_for_partition(big_mac_part, 1024 * 768 * 2)
    return app_graph, mac_graph, n_keys_map


def test_big_flexible_no_fixed():
    app_graph, mac_graph, n_keys_map = create_big(False)

    # The number of bits is 1 + 11 + 21 = 33, so it shouldn't fail
    routing_info = flexible_allocate(mac_graph, n_keys_map)

    # The number of bits is 1 + 21 = 22, so it shouldn't fail
    # all but the bottom 21 bits should be the same
    app_mask = 0xFFE00000
    check_keys_for_application_partition_pairs(
        app_graph, mac_graph, routing_info, app_mask)


def test_big_global_no_fixed():
    app_graph, mac_graph, n_keys_map = create_big(False)
    # Make the call, and it should fail
    routing_info = global_allocate(mac_graph, n_keys_map)

    # 1 for app 11 for machine so where possible use 20 for atoms
    mask = 0xFFF00000
    check_masks_all_the_same(routing_info, mask)

    # The number of bits is 1 + 11 + 21, so it will not fit
    # So flexible for the retina
    # Others mask all bit minimum app bits (1)
    # all but the top 1 bits should be the same
    app_mask = 0x80000000
    check_keys_for_application_partition_pairs(
        app_graph, mac_graph, routing_info, app_mask)


def test_big_flexible_fixed():
    app_graph, mac_graph, n_keys_map = create_big(True)

    # The number of bits is 1 + 11 + 21 = 33, so it shouldn't fail
    routing_info = flexible_allocate(mac_graph, n_keys_map)

    # all but the bottom 18 bits should be the same
    app_mask = 0xFFFC0000
    check_keys_for_application_partition_pairs(
        app_graph, mac_graph, routing_info, app_mask)


def test_big_global_fixed():
    app_graph, mac_graph, n_keys_map = create_big(True)
    # Make the call, and it should fail
    routing_info = global_allocate(mac_graph, n_keys_map)

    # 7 bit atoms is 7 as it ignore the retina
    mask = 0xFFFFFF80
    check_masks_all_the_same(routing_info, mask)

    # The number of bits is 1 + 11 + 21, so it will not fit
    # So flexible for the retina
    # Others mask all bit minimum app bits (1)
    # all but the top 1 bits should be the same
    app_mask = 0xFFFC0000
    check_keys_for_application_partition_pairs(
        app_graph, mac_graph, routing_info, app_mask)


def test_no_app_level_flexible():
    app_graph, mac_graph, n_keys_map = create_app_less()
    # The number of bits is 1 + 11 + 21 = 33, so it shouldn't fail
    routing_info = flexible_allocate(mac_graph, n_keys_map)

    # all but the bottom 8 bits should be the same
    app_mask = 0xFFFFFF00
    check_keys_for_application_partition_pairs(
        app_graph, mac_graph, routing_info, app_mask)


def test_no_app_level_global():
    app_graph, mac_graph, n_keys_map = create_app_less()
    # The number of bits is 1 + 11 + 21 = 33, so it shouldn't fail
    routing_info = global_allocate(mac_graph, n_keys_map)
    # Last 8 for masks
    mask = 0xFFFFFF00
    check_masks_all_the_same(routing_info,  mask)

    # all but the bottom 8 bits should be the same
    app_mask = 0xFFFFFF00
    check_keys_for_application_partition_pairs(
        app_graph, mac_graph, routing_info, app_mask)
