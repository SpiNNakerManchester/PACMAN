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

from pacman.operations.routing_info_allocator_algorithms import (
    GlobalZonedRoutingInfoAllocator, ZonedRoutingInfoAllocator)
from pacman.model.graphs.application.application_vertex import (
    ApplicationVertex)
from pacman.model.graphs.machine.machine_vertex import MachineVertex
from pacman.model.graphs.application.application_graph import ApplicationGraph
from pacman.model.graphs.machine.machine_graph import MachineGraph
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.model.graphs.machine.machine_edge import MachineEdge
from pacman.exceptions import PacmanRouteInfoAllocationException
import pytest


class SimpleAppVertex(ApplicationVertex):

    @property
    def n_atoms(self):
        return 1

    def get_resources_used_by_atoms(self, vertex_slice):
        return None

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        return SimpleMacVertex()


class SimpleMacVertex(MachineVertex):

    @property
    def resources_required(self):
        return None

def create_graphs():
    app_graph = ApplicationGraph("Test")
    # An output vertex to aim things at (to make keys required)
    out_app_vertex = SimpleAppVertex()
    app_graph.add_vertex(out_app_vertex)
    # Create 5 application vertices (3 bits)
    app_vertices = list()
    for app_index in range(5):
        app_vertices.append(SimpleAppVertex())
    app_graph.add_vertices(app_vertices)

    mac_graph = MachineGraph("Test", app_graph)
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = SimpleMacVertex(app_vertex=out_app_vertex)
    mac_graph.add_vertex(out_mac_vertex)

    # Create 5 application vertices (3 bits)
    for app_index, app_vertex in enumerate(app_vertices):

        # For each, create up to (5 x 4) + 1 = 21 machine vertices (5 bits)
        for mac_index in range((app_index * 4) + 1):
            mac_vertex = SimpleMacVertex(app_vertex=app_vertex)
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

def test_global_allocator():
    # Allocate something and check it does the right thing

    app_graph, mac_graph, n_keys_map = create_graphs()

    # The number of bits is 7 + 5 + 8 = 20, so it shouldn't fail
    routing_info, _ = ZonedRoutingInfoAllocator.global_allocate(
        mac_graph, n_keys_map)

    # Check the mask is the same for all, and allows for the space required
    # for the maximum number of keys in total (bottom 8 bits)
    mask = 0xFFFFFF00
    seen_keys = set()
    for r_info in routing_info:
        assert(len(r_info.keys_and_masks) == 1)
        assert(r_info.first_mask == mask)
        assert(r_info.first_key not in seen_keys)
        seen_keys.add(r_info.first_key)

    # Check the key for each application vertex is the same
    # The bits that should be the same are the top 3 of the 22
    #app_mask = 0x380000
    # The bits that should be the same are all but the bottom 12
    app_mask = 0xFFFFF000
    key_check = dict()
    for app_vertex in app_graph.vertices:
        for m_vertex in app_vertex.machine_vertices:
            for p in mac_graph.get_outgoing_edge_partitions_starting_at_vertex(
                    m_vertex):
                key = routing_info.get_first_key_from_partition(p)
                if (app_vertex, p.label) in key_check:
                    if (key_check[(app_vertex, p.identifier)] & app_mask) != (key & app_mask):
                        a = key_check[(app_vertex, p.label)]
                        ah = hex(a)
                        b = a & app_mask
                        bh = hex(b)
                        c = key & app_mask
                        kh = hex(key)
                        chex = hex(c)
                        print("foo")
                    assert((key_check[(app_vertex, p.identifier)] & app_mask) == (key & app_mask))
                else:
                    if key != 0:
                        if (key & app_mask) == 0:
                            kh = hex(key)
                            aph = hex(app_mask)
                            print("n")

                        assert((key & app_mask) != 0)
                    key_check[(app_vertex, p.identifier)] = key

def test_zoned_allocator():
    # Allocate something and check it does the right thing
    app_graph, mac_graph, n_keys_map = create_graphs()

    # The number of bits is 3 + 5 + 6 + 8 = 22, so it shouldn't fail
    ZonedRoutingInfoAllocator.flexible_allocate(mac_graph, n_keys_map)


def test_too_big():
    # This test shows how easy it is to trip up the allocator with a retina
    alloc = GlobalZonedRoutingInfoAllocator()
    app_graph = ApplicationGraph("Test")
    # Create a single "big" vertex
    big_app_vertex = SimpleAppVertex()
    app_graph.add_vertex(big_app_vertex)
    # Create a single output vertex (which won't send)
    out_app_vertex = SimpleAppVertex()
    app_graph.add_vertex(out_app_vertex)
    # Create a load of middle vertex
    mid_app_vertex = SimpleAppVertex()
    app_graph.add_vertex(mid_app_vertex)

    mac_graph = MachineGraph("Test", app_graph)
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    # Create a single big machine vertex
    big_mac_vertex = SimpleMacVertex(app_vertex=big_app_vertex)
    mac_graph.add_vertex(big_mac_vertex)

    # Create a single output vertex (which won't send)
    out_mac_vertex = SimpleMacVertex(app_vertex=out_app_vertex)
    mac_graph.add_vertex(out_mac_vertex)

    # Create a load of middle vertices and connect them up
    for _ in range(2000):  # 2000 needs 11 bits
        mid_mac_vertex = SimpleMacVertex(app_vertex=mid_app_vertex)
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

    # Make the "retina" need 21 bits, so total is now 21 + 11 = 32 bits,
    # but the application vertices need some bits too
    n_keys_map.set_n_keys_for_partition(big_mac_part, 1024 * 768 * 2)

    # Make the call, and it should fail
    with pytest.raises(PacmanRouteInfoAllocationException):
        routing_info, _ = ZonedRoutingInfoAllocator.global_allocate(
            mac_graph, n_keys_map)
