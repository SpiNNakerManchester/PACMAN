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
from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.operations.routing_info_allocator_algorithms.\
    zoned_routing_info_allocator import (flexible_allocate, global_allocate)
from pacman.model.graphs.application import (
    ApplicationGraph, ApplicationEdge, ApplicationVertex)
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.graphs.machine.machine_vertex import MachineVertex
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.model.constraints.key_allocator_constraints \
    import FixedKeyAndMaskConstraint


class TestSplitter(AbstractSplitterCommon):

    def create_machine_vertices(self, chip_counter):
        return 1

    def get_out_going_vertices(self, partition_id):
        return self._governed_app_vertex.machine_vertices

    def get_in_coming_vertices(self, partition_id):
        return self._governed_app_vertex.machine_vertices

    def machine_vertices_for_recording(self, variable_to_record):
        return list(self._governed_app_vertex.machine_vertices)

    def get_out_going_slices(self):
        return [m.slice for m in self._governed_app_vertex.machine_vertices]

    def get_in_coming_slices(self):
        return [m.slice for m in self._governed_app_vertex.machine_vertices]

    def reset_called(self):
        pass


class TestAppVertex(ApplicationVertex):

    @property
    def n_atoms(self):
        return 10


class TestMacVertex(MachineVertex):

    def __init__(
            self, label=None, constraints=None, app_vertex=None,
            vertex_slice=None, n_keys_required=None):
        super(TestMacVertex, self).__init__(
            label=label, constraints=constraints, app_vertex=app_vertex,
            vertex_slice=vertex_slice)
        self.__n_keys_required = n_keys_required

    def get_n_keys_for_partition(self, partition_id):
        return self.__n_keys_required[partition_id]

    @property
    def resources_required(self):
        # Not needed for test
        return None


def create_graphs1(with_fixed):
    app_graph = ApplicationGraph("Test")
    # An output vertex to aim things at (to make keys required)
    out_app_vertex = TestAppVertex(splitter=TestSplitter())
    app_graph.add_vertex(out_app_vertex)
    # Create 5 application vertices (3 bits)
    app_vertices = list()
    for app_index in range(5):
        app_vertices.append(TestAppVertex(splitter=TestSplitter()))
    app_graph.add_vertices(app_vertices)

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = TestMacVertex(label="out_vertex")
    out_app_vertex.remember_machine_vertex(out_mac_vertex)

    for app_index, app_vertex in enumerate(app_vertices):

        # Create up to (10 * 4) + 1 = 41 partitions (6 bits)
        for i in range((app_index * 10) + 1):
            app_graph.add_edge(
                ApplicationEdge(app_vertex, out_app_vertex), f"Part{i}")

        # For each, create up to (40 * 2) + 1 = 81 machine vertices (7 bits)
        for mac_index in range((app_index * 2 * 10) + 1):

            # Give the vertex up to (80 * 2) + 1 = 161 keys (8 bits)
            mac_vertex = TestMacVertex(
                label=f"Part{i}_vertex",
                n_keys_required={f"Part{i}": (mac_index * 2) + 1
                                 for i in range((app_index * 10) + 1)})
            app_vertex.remember_machine_vertex(mac_vertex)

        if with_fixed:
            if app_index == 2:
                app_vertex.add_constraint(FixedKeyAndMaskConstraint(
                    [BaseKeyAndMask(0xFE00000, 0xFFFFFFC0)],
                    partition="Part7"))
            if app_index == 2:
                app_vertex.add_constraint(FixedKeyAndMaskConstraint(
                    [BaseKeyAndMask(0x4c00000, 0xFFFFFFFE)],
                    partition="Part1"))
            if app_index == 3:
                app_vertex.add_constraint(FixedKeyAndMaskConstraint(
                    [BaseKeyAndMask(0x3300000, 0xFFFFFFFF)],
                    partition="Part1"))

    return app_graph


def create_graphs_only_fixed():
    app_graph = ApplicationGraph("Test")
    # An output vertex to aim things at (to make keys required)
    out_app_vertex = TestAppVertex(splitter=TestSplitter())
    app_graph.add_vertex(out_app_vertex)
    app_vertex = TestAppVertex(splitter=TestSplitter())
    app_graph.add_vertex(app_vertex)

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = TestMacVertex(label="out_mac_vertex")
    out_app_vertex.remember_machine_vertex(out_mac_vertex)

    mac_vertex = TestMacVertex(label="mac_vertex")
    app_vertex.remember_machine_vertex(mac_vertex)

    app_graph.add_edge(ApplicationEdge(app_vertex, out_app_vertex), "Part0")
    app_graph.add_edge(ApplicationEdge(app_vertex, out_app_vertex), "Part1")

    app_vertex.add_constraint(FixedKeyAndMaskConstraint(
                [BaseKeyAndMask(0x4c00000, 0xFFFFFFFE)],
                partition="Part0"))
    app_vertex.add_constraint(FixedKeyAndMaskConstraint(
                [BaseKeyAndMask(0x4c00000, 0xFFFFFFFF)],
                partition="Part1"))

    return app_graph


def create_graphs_no_edge():
    app_graph = ApplicationGraph("Test")
    out_app_vertex = TestAppVertex(splitter=TestSplitter())
    app_graph.add_vertex(out_app_vertex)
    app_vertex = TestAppVertex(splitter=TestSplitter())
    app_graph.add_vertex(app_vertex)

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = TestMacVertex()
    out_app_vertex.remember_machine_vertex(out_mac_vertex)

    mac_vertex = TestMacVertex()
    app_vertex.remember_machine_vertex(mac_vertex)

    return app_graph


def check_masks_all_the_same(routing_info, mask):
    # Check the mask is the same for all, and allows for the space required
    # for the maximum number of keys in total
    seen_keys = set()
    for r_info in routing_info:
        if isinstance(r_info.vertex, MachineVertex):
            assert(len(r_info.keys_and_masks) == 1)
            assert(r_info.first_mask == mask or
                   r_info.machine_vertex.label == "RETINA")
            assert(r_info.first_key not in seen_keys)
            seen_keys.add(r_info.first_key)


def check_fixed(m_vertex, part_id, key):
    for constraint in m_vertex.constraints:
        if isinstance(constraint, FixedKeyAndMaskConstraint):
            if constraint.applies_to_partition(part_id):
                assert key == constraint.keys_and_masks[0].key
                return True
    return False


def check_keys_for_application_partition_pairs(
        app_graph, routing_info, app_mask):
    # Check the key for each application vertex/ parition pair is the same
    # The bits that should be the same are all but the bottom 12
    for part in app_graph.outgoing_edge_partitions:
        mapped_key = None
        for m_vertex in part.pre_vertex.splitter.get_out_going_vertices(
                part.identifier):
            key = routing_info.get_first_key_from_pre_vertex(
                m_vertex, part.identifier)
            if check_fixed(m_vertex, part.identifier, key):
                continue

            if mapped_key is not None:
                assert((mapped_key & app_mask) == (key & app_mask))
            else:
                mapped_key = key
            if key != 0:
                assert((key & app_mask) != 0)


def test_global_allocator():
    unittest_setup()
    writer = PacmanDataWriter.mock()

    # Allocate something and check it does the right thing
    app_graph = create_graphs1(False)
    writer._set_runtime_graph(app_graph)

    # The number of bits is 7 + 5 + 8 = 20, so it shouldn't fail
    routing_info = global_allocate([])

    # Last 8 for atom id
    mask = 0xFFFFFF00
    check_masks_all_the_same(routing_info,  mask)

    # all but the bottom 8 + 7 = 15 bits should be the same
    app_mask = 0xFFFF8000
    check_keys_for_application_partition_pairs(
        app_graph, routing_info, app_mask)


def test_flexible_allocator_no_fixed():
    unittest_setup()

    # Allocate something and check it does the right thing
    writer = PacmanDataWriter.mock()
    app_graph = create_graphs1(False)
    writer._set_runtime_graph(app_graph)

    # The number of bits is 8 + 7 + 6 = 21, so it shouldn't fail
    routing_info = flexible_allocate([])

    # all but the bottom 8 + 7 = 15 bits should be the same
    app_mask = 0xFFFF8000
    check_keys_for_application_partition_pairs(
        app_graph, routing_info, app_mask)


def test_fixed_only():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    app_graph = create_graphs_only_fixed()
    writer._set_runtime_graph(app_graph)
    flexible_allocate([])
    routing_info = global_allocate([])
    assert len(list(routing_info)) == 4


def test_no_edge():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    app_graph = create_graphs_no_edge()
    writer._set_runtime_graph(app_graph)
    flexible_allocate([])
    routing_info = global_allocate([])
    assert len(list(routing_info)) == 0


def test_flexible_allocator_with_fixed():
    unittest_setup()
    # Allocate something and check it does the right thing
    writer = PacmanDataWriter.mock()
    app_graph = create_graphs1(True)
    writer._set_runtime_graph(app_graph)

    # The number of bits is 6 + 7 + 8 = 21, so it shouldn't fail
    routing_info = flexible_allocate([])

    # all but the bottom 8 + 7 = 15 bits should be the same
    app_mask = 0xFFFF8000
    check_keys_for_application_partition_pairs(
        app_graph, routing_info, app_mask)


def create_big(with_fixed):
    # This test shows how easy it is to trip up the allocator with a retina
    app_graph = ApplicationGraph("Test")
    # Create a single "big" vertex
    big_app_vertex = TestAppVertex(label="Retina", splitter=TestSplitter())
    app_graph.add_vertex(big_app_vertex)
    # Create a single output vertex (which won't send)
    out_app_vertex = TestAppVertex(
        label="Destination", splitter=TestSplitter())
    app_graph.add_vertex(out_app_vertex)
    # Create a load of middle vertex
    mid_app_vertex = TestAppVertex(label="Population", splitter=TestSplitter())
    app_graph.add_vertex(mid_app_vertex)

    app_graph.add_edge(ApplicationEdge(big_app_vertex, mid_app_vertex), "Test")
    app_graph.add_edge(ApplicationEdge(mid_app_vertex, out_app_vertex), "Test")

    # Create a single big machine vertex
    big_mac_vertex = TestMacVertex(
        label="RETINA", n_keys_required={"Test": 1024 * 768 * 2})
    big_app_vertex.remember_machine_vertex(big_mac_vertex)

    # Create a single output vertex (which won't send)
    out_mac_vertex = TestMacVertex(label="OutMacVertex")
    out_app_vertex.remember_machine_vertex(out_mac_vertex)

    # Create a load of middle vertices and connect them up
    for i in range(2000):  # 2000 needs 11 bits
        mid_mac_vertex = TestMacVertex(label=f"MidMacVertex{i}",
                                       n_keys_required={"Test": 100})
        mid_app_vertex.remember_machine_vertex(mid_mac_vertex)

    if with_fixed:
        big_app_vertex.add_constraint(FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0x0, 0x180000)]))
    return app_graph


def test_big_flexible_no_fixed():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    app_graph = create_big(False)
    writer._set_runtime_graph(app_graph)

    # The number of bits is 1 + 11 + 21 = 33, so it shouldn't fail
    routing_info = flexible_allocate([])

    # The number of bits is 1 + 21 = 22, so it shouldn't fail
    # all but the bottom 21 bits should be the same
    app_mask = 0xFFE00000
    check_keys_for_application_partition_pairs(
        app_graph, routing_info, app_mask)


def test_big_global_no_fixed():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    app_graph = create_big(False)
    writer._set_runtime_graph(app_graph)
    routing_info = global_allocate([])

    # 1 for app 11 for machine so where possible use 20 for atoms
    mask = 0xFFF00000
    check_masks_all_the_same(routing_info, mask)

    # The number of bits is 1 + 11 + 21, so it will not fit
    # So flexible for the retina
    # Others mask all bit minimum app bits (1)
    # all but the top 1 bits should be the same
    app_mask = 0x80000000
    check_keys_for_application_partition_pairs(
        app_graph, routing_info, app_mask)


def test_big_flexible_fixed():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    app_graph = create_big(True)
    writer._set_runtime_graph(app_graph)

    # The number of bits is 1 + 11 + 21 = 33, so it shouldn't fail
    routing_info = flexible_allocate([])

    # all but the bottom 18 bits should be the same
    app_mask = 0xFFFC0000
    check_keys_for_application_partition_pairs(
        app_graph, routing_info, app_mask)


def test_big_global_fixed():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    app_graph = create_big(True)
    writer._set_runtime_graph(app_graph)
    routing_info = global_allocate([])

    # 7 bit atoms is 7 as it ignore the retina
    mask = 0xFFFFFF80
    check_masks_all_the_same(routing_info, mask)

    # The number of bits is 1 + 11 + 21, so it will not fit
    # So flexible for the retina
    # Others mask all bit minimum app bits (1)
    # all but the top 1 bits should be the same
    app_mask = 0xFFFC0000
    check_keys_for_application_partition_pairs(
        app_graph, routing_info, app_mask)
