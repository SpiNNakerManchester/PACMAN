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

from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from spinn_utilities.overrides import overrides

from pacman.config_setup import unittest_setup
from pacman.data import PacmanDataView
from pacman.exceptions import (
    IrregularFixedMaskException,
    PacmanRouteInfoAllocationException,
)
from pacman.model.graphs.application import ApplicationEdge, ApplicationVertex
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine.machine_vertex import MachineVertex
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from pacman.model.resources import AbstractSDRAM
from pacman.model.routing_info import MachineVertexRoutingInfo, RoutingInfo
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.operations.routing_info_allocator_algorithms.\
    zoned_routing_info_allocator import ZonedRoutingInfoAllocator
from pacman.utilities.utility_objs.chip_counter import ChipCounter


class MockSplitter(AbstractSplitterCommon):

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        pass

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return self.governed_app_vertex.machine_vertices

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return self.governed_app_vertex.machine_vertices

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> Iterable[MachineVertex]:
        return list(self.governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        return [m.slice for m in self.governed_app_vertex.machine_vertices]

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        return [m.slice for m in self.governed_app_vertex.machine_vertices]

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass


class MockAppVertex(ApplicationVertex):

    def __init__(self, splitter: Optional[AbstractSplitterCommon] = None,
                 fixed_keys_by_partition: Optional[
                     Dict[str, BaseKeyAndMask]] = None,
                 fixed_key: Optional[BaseKeyAndMask] = None,
                 fixed_machine_keys_by_partition:  Optional[
                     Dict[Tuple[MachineVertex, str], BaseKeyAndMask]] = None):
        super(MockAppVertex, self).__init__(splitter=splitter)
        self.__fixed_keys_by_partition = fixed_keys_by_partition
        self.__fixed_key = fixed_key
        self.__fixed_machine_keys_by_partition = \
            fixed_machine_keys_by_partition

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self) -> int:
        return 10

    @overrides(ApplicationVertex.get_fixed_key_and_mask)
    def get_fixed_key_and_mask(
            self, partition_id: str) -> Optional[BaseKeyAndMask]:
        if self.__fixed_key is not None:
            return self.__fixed_key
        if self.__fixed_keys_by_partition is None:
            return None
        return self.__fixed_keys_by_partition.get(partition_id)

    @overrides(ApplicationVertex.get_machine_fixed_key_and_mask)
    def get_machine_fixed_key_and_mask(
            self, machine_vertex: MachineVertex,
            partition_id: str) -> Optional[BaseKeyAndMask]:
        if self.__fixed_machine_keys_by_partition is None:
            return None
        return self.__fixed_machine_keys_by_partition.get(
            (machine_vertex, partition_id))


class TestMacVertex(MachineVertex):

    def __init__(
            self, label: Optional[str] = None,
            app_vertex: Optional[ApplicationVertex] = None,
            vertex_slice: Optional[Slice] = None,
            n_keys_required: Optional[Dict[str, int]] = None):
        super(TestMacVertex, self).__init__(
            label=label, app_vertex=app_vertex, vertex_slice=vertex_slice)
        self.__n_keys_required = n_keys_required

    @overrides(MachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, partition_id: str) -> int:
        assert self.__n_keys_required is not None
        return self.__n_keys_required[partition_id]

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self) -> AbstractSDRAM:
        # Not needed for test
        raise NotImplementedError()


def create_graphs1(with_fixed: bool, shiftable: bool = True) -> None:
    # An output vertex to aim things at (to make keys required)
    out_app_vertex = MockAppVertex(splitter=MockSplitter())
    PacmanDataView.add_vertex(out_app_vertex)
    # Create 5 application vertices (3 bits)
    app_vertices = list()
    for app_index in range(5):
        fixed_keys_by_partition: Optional[Dict[str, BaseKeyAndMask]] = None
        fixed_machine_keys_by_partition: \
            Optional[Dict[Tuple[MachineVertex, str], BaseKeyAndMask]] = None
        if with_fixed:
            fixed_keys_by_partition = dict()
            fixed_machine_keys_by_partition = dict()
            if app_index == 2:
                fixed_keys_by_partition["Part7"] = BaseKeyAndMask(
                    0xFE000000, 0xFFFF0000)
                fixed_keys_by_partition["Part1"] = BaseKeyAndMask(
                    0x4c000000, 0xFFFF0000)
            if app_index == 3:
                fixed_keys_by_partition["Part1"] = BaseKeyAndMask(
                    0x33000000, 0xFFFF0000)

        app_vertex = MockAppVertex(
            splitter=MockSplitter(),
            fixed_keys_by_partition=fixed_keys_by_partition,
            fixed_machine_keys_by_partition=fixed_machine_keys_by_partition)

        if shiftable:
            max_index = (app_index * 2 * 10) + 1
        else:
            max_index = 4
        # For each, create up to (40 * 2) + 1 = 81 machine vertices (7 bits)
        for mac_index in range(max_index):

            # Give the vertex up to (80 * 2) + 1 = 161 keys (8 bits)
            mac_vertex = TestMacVertex(
                label=f"Part{mac_index}_vertex",
                app_vertex=app_vertex,
                n_keys_required={f"Part{i}": (mac_index * 2) + 1
                                 for i in range((app_index * 10) + 1)})
            if fixed_machine_keys_by_partition is not None:  # with_fixed:
                if app_index == 2:
                    fixed_machine_keys_by_partition[
                        mac_vertex, "Part7"] = BaseKeyAndMask(
                            0xFE000000 + (mac_index << 8), 0xFFFFFF00)
                    fixed_machine_keys_by_partition[
                        mac_vertex, "Part1"] = BaseKeyAndMask(
                            0x4c000000 + (mac_index << 8), 0xFFFFFF00)
                if app_index == 3:
                    if shiftable:
                        fixed_machine_keys_by_partition[
                            mac_vertex, "Part1"] = BaseKeyAndMask(
                                0x33000000 + (mac_index << 8), 0xFFFFFF00)
                    else:
                        fixed_machine_keys_by_partition[
                            mac_vertex, "Part1"] = BaseKeyAndMask(
                                0x33000000 + (mac_index << 8), 0xFFFF0F00)

            app_vertex.remember_machine_vertex(mac_vertex)

        app_vertices.append(app_vertex)
    for vertex in app_vertices:
        PacmanDataView.add_vertex(vertex)

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = TestMacVertex(
        label="out_vertex", app_vertex=out_app_vertex)
    out_app_vertex.remember_machine_vertex(out_mac_vertex)

    for app_index, app_vertex in enumerate(app_vertices):

        # Create up to (10 * 4) + 1 = 41 partitions (6 bits)
        for i in range((app_index * 10) + 1):
            PacmanDataView.add_edge(
                ApplicationEdge(app_vertex, out_app_vertex), f"Part{i}")


def create_graphs_only_fixed(
        fixed_keys_by_partition: Dict[str, BaseKeyAndMask]) -> None:
    # An output vertex to aim things at (to make keys required)
    out_app_vertex = MockAppVertex(splitter=MockSplitter())
    PacmanDataView.add_vertex(out_app_vertex)

    app_vertex = MockAppVertex(
        splitter=MockSplitter(),
        fixed_keys_by_partition=fixed_keys_by_partition)
    PacmanDataView.add_vertex(app_vertex)

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = TestMacVertex(
        label="out_mac_vertex", app_vertex=out_app_vertex)
    out_app_vertex.remember_machine_vertex(out_mac_vertex)

    mac_vertex = TestMacVertex(
        label="mac_vertex", app_vertex=app_vertex,
        n_keys_required={"Part0": 2, "Part1": 1})
    app_vertex.remember_machine_vertex(mac_vertex)

    PacmanDataView.add_edge(
        ApplicationEdge(app_vertex, out_app_vertex), "Part0")
    PacmanDataView.add_edge(
        ApplicationEdge(app_vertex, out_app_vertex), "Part1")


def create_graphs_no_edge() -> None:
    out_app_vertex = MockAppVertex(splitter=MockSplitter())
    PacmanDataView.add_vertex(out_app_vertex)
    app_vertex = MockAppVertex(splitter=MockSplitter())
    PacmanDataView.add_vertex(app_vertex)

    # An output vertex to aim things at (to make keys required)
    out_mac_vertex = TestMacVertex(app_vertex=out_app_vertex)
    out_app_vertex.remember_machine_vertex(out_mac_vertex)

    mac_vertex = TestMacVertex(app_vertex=app_vertex)
    app_vertex.remember_machine_vertex(mac_vertex)


def check_masks_all_the_same(routing_info: RoutingInfo) -> None:
    # Check the mask is the same for all, and allows for the space required
    # for the maximum number of keys in total
    mask = -1
    seen_keys = set()
    for r_info in routing_info:
        if isinstance(r_info.vertex, MachineVertex):
            assert isinstance(r_info, MachineVertexRoutingInfo)
            if r_info.machine_vertex.label != "RETINA":
                if mask == -1:
                    mask = r_info.mask
                else:
                    assert (hex(r_info.mask) == hex(mask))
            assert r_info.key not in seen_keys
            seen_keys.add(r_info.key)


def check_fixed(m_vertex: MachineVertex, part_id: str, key: int) -> bool:
    app_vertex = m_vertex.app_vertex
    key_and_mask = app_vertex.get_machine_fixed_key_and_mask(
        m_vertex, part_id)
    if key_and_mask is None:
        return False
    assert key == key_and_mask.key
    return True


def check_keys_for_application_partition_pairs(
        routing_info: RoutingInfo) -> None:
    # Check the key for each application vertex/ parition pair is the same
    # The bits that should be the same are all but the bottom 12
    app_mask = routing_info.global_app_mask
    for part in PacmanDataView.iterate_partitions():
        mapped_key = None
        for m_vertex in part.pre_vertex.splitter.get_out_going_vertices(
                part.identifier):
            key = routing_info.get_key_from(
                m_vertex, part.identifier)
            if check_fixed(m_vertex, part.identifier, key):
                continue

            if mapped_key is not None:
                assert (mapped_key & app_mask) == (key & app_mask)
            else:
                mapped_key = key
            if key != 0:
                assert (key & app_mask) != 0


def test_allocator_no_fixed() -> None:
    unittest_setup()

    # Allocate something and check it does the right thing
    create_graphs1(False)

    # The number of bits is 7 + 5 + 8 = 20, so it shouldn't fail
    routing_info = ZonedRoutingInfoAllocator().allocate()

    assert routing_info.min_bits_machine_and_atoms == 15
    assert routing_info.max_bits_machine == 7
    assert routing_info.max_bits_atoms == 8
    assert routing_info.size_app_part_bits == 7
    assert routing_info.target_app_bits == 17
    assert routing_info.target_machine_bits == 7
    assert routing_info.target_atom_bits == 8
    assert routing_info.has_global_app_masks
    assert routing_info.has_global_machine_masks
    assert not routing_info.has_fixed_keys
    assert not routing_info.has_app_keys_overlap
    assert routing_info.is_machine_shiftable

    check_masks_all_the_same(routing_info)
    check_keys_for_application_partition_pairs(routing_info)


def test_fixed_only() -> None:
    unittest_setup()
    fixed_keys_by_partition = {
        "Part0": BaseKeyAndMask(0x0, 0xFFFFFF00),
        "Part1": BaseKeyAndMask(0x4c00000, 0xFFFF0000)
    }
    create_graphs_only_fixed(fixed_keys_by_partition)
    routing_info = ZonedRoutingInfoAllocator().allocate()
    assert len(list(routing_info)) == 4

    assert routing_info.min_bits_machine_and_atoms == 0
    assert routing_info.max_bits_machine == 0
    assert routing_info.max_bits_atoms == 0
    assert routing_info.size_app_part_bits == 1
    assert routing_info.target_app_bits == 16
    assert routing_info.target_machine_bits == 0
    assert routing_info.target_atom_bits == 16
    assert not routing_info.has_global_app_masks
    assert not routing_info.has_global_machine_masks
    assert routing_info.has_fixed_keys
    assert not routing_info.has_app_keys_overlap
    assert routing_info.is_machine_shiftable


def test_weird() -> None:
    unittest_setup()
    fixed_keys_by_partition = {
        "Part0": BaseKeyAndMask(0x0, 0xffff0000),
        "Part1": BaseKeyAndMask(0x1000, 0xfffff800)
    }
    create_graphs_only_fixed(fixed_keys_by_partition)
    routing_info = ZonedRoutingInfoAllocator().allocate()
    assert routing_info.min_bits_machine_and_atoms == 0
    assert routing_info.max_bits_machine == 0
    assert routing_info.max_bits_atoms == 0
    assert routing_info.size_app_part_bits == 1
    assert routing_info.target_app_bits == 16
    assert routing_info.target_machine_bits == 0
    assert routing_info.target_atom_bits == 16
    assert not routing_info.has_global_app_masks
    assert not routing_info.has_global_machine_masks
    assert routing_info.has_fixed_keys
    assert routing_info.has_app_keys_overlap
    assert routing_info.is_machine_shiftable


def test_overlap() -> None:
    # This should work here; overlap is allowed provided routes don't overlap
    # (which is found elsewhere)
    unittest_setup()
    fixed_keys_by_partition = {
        "Part0": BaseKeyAndMask(0x4c00000, 0xFFFFFF00),
        "Part1": BaseKeyAndMask(0x4c00000, 0xFFFF0000)
    }
    create_graphs_only_fixed(fixed_keys_by_partition)
    routing_info = ZonedRoutingInfoAllocator().allocate()

    assert routing_info.min_bits_machine_and_atoms == 0
    assert routing_info.max_bits_machine == 0
    assert routing_info.max_bits_atoms == 0
    assert routing_info.size_app_part_bits == 1
    assert routing_info.target_app_bits == 16
    assert routing_info.target_machine_bits == 0
    assert routing_info.target_atom_bits == 16
    assert not routing_info.has_global_app_masks
    assert not routing_info.has_global_machine_masks
    assert routing_info.has_fixed_keys
    assert routing_info.has_app_keys_overlap


def test_no_edge() -> None:
    unittest_setup()
    create_graphs_no_edge()
    routing_info = ZonedRoutingInfoAllocator().allocate()
    assert len(list(routing_info)) == 0

    assert routing_info.min_bits_machine_and_atoms == 0
    assert routing_info.max_bits_machine == 0
    assert routing_info.max_bits_atoms == 0
    assert routing_info.size_app_part_bits == 0
    assert routing_info._target_app_bits == 32
    assert routing_info.target_machine_bits == 0
    assert routing_info.target_atom_bits == 0
    assert routing_info.has_global_app_masks
    assert routing_info.has_global_machine_masks
    assert not routing_info.has_fixed_keys
    assert not routing_info.has_app_keys_overlap
    assert routing_info.is_machine_shiftable


def test_allocator_with_fixed() -> None:
    unittest_setup()
    # Allocate something and check it does the right thing
    create_graphs1(True)

    # The number of bits is 6 + 7 + 8 = 21, so it should fit
    routing_info = ZonedRoutingInfoAllocator().allocate()

    check_keys_for_application_partition_pairs(routing_info)

    assert routing_info.min_bits_machine_and_atoms == 15
    assert routing_info.max_bits_machine == 7
    assert routing_info.max_bits_atoms == 8
    assert routing_info.size_app_part_bits == 7
    assert routing_info.target_app_bits == 16
    assert routing_info.target_machine_bits == 8
    assert routing_info.target_atom_bits == 8
    assert routing_info.has_global_app_masks
    assert routing_info.has_global_machine_masks
    assert routing_info.has_fixed_keys
    assert not routing_info.has_app_keys_overlap
    assert routing_info.is_machine_shiftable

    for partition in PacmanDataView.iterate_partitions():
        partition_id = partition.identifier
        vertex = partition.pre_vertex
        info = routing_info.get_info_from(vertex, partition_id)
        assert hex(info.atom_mask) == hex(0x000000ff)
        assert hex(info.machine_mask) == hex(0xffffff00)


def test_allocator_not_shiftable() -> None:
    unittest_setup()
    # Allocate something and check it does the right thing
    create_graphs1(True, shiftable=False)

    # The number of bits is 6 + 7 + 8 = 21, so it should fit
    routing_info = ZonedRoutingInfoAllocator().allocate()

    assert routing_info.min_bits_machine_and_atoms == 5
    assert routing_info.max_bits_machine == 2
    assert routing_info.max_bits_atoms == 3
    assert routing_info.size_app_part_bits == 7
    assert routing_info.target_app_bits == 16
    assert routing_info.target_machine_bits == 8
    assert routing_info.target_atom_bits == 8
    assert routing_info.has_global_app_masks
    assert not routing_info.has_global_machine_masks
    assert routing_info.has_fixed_keys
    assert not routing_info.has_app_keys_overlap
    assert not routing_info.is_machine_shiftable


def create_big(fixed_mask: Optional[int]) -> None:
    # This test shows how easy it is to trip up the allocator with a retina
    # Create a single "big" vertex
    if fixed_mask is None:
        fixed_key = None
    else:
        fixed_key = BaseKeyAndMask(0x0, fixed_mask)
    big_app_vertex = MockAppVertex(
        splitter=MockSplitter(), fixed_key=fixed_key)
    PacmanDataView.add_vertex(big_app_vertex)
    # Create a single output vertex (which won't send)
    out_app_vertex = MockAppVertex(splitter=MockSplitter())
    PacmanDataView.add_vertex(out_app_vertex)
    # Create a load of middle vertex
    mid_app_vertex = MockAppVertex(splitter=MockSplitter())
    PacmanDataView.add_vertex(mid_app_vertex)

    PacmanDataView.add_edge(
        ApplicationEdge(big_app_vertex, mid_app_vertex), "Test")
    PacmanDataView.add_edge(
        ApplicationEdge(mid_app_vertex, out_app_vertex), "Test")

    # Create a single big machine vertex
    big_mac_vertex = TestMacVertex(
        label="RETINA", n_keys_required={"Test": 1024 * 768 * 2},
        app_vertex=big_app_vertex)
    big_app_vertex.remember_machine_vertex(big_mac_vertex)

    # Create a single output vertex (which won't send)
    out_mac_vertex = TestMacVertex(
        label="OutMacVertex", app_vertex=out_app_vertex)
    out_app_vertex.remember_machine_vertex(out_mac_vertex)

    # Create a load of middle vertices and connect them up
    for i in range(2000):  # 2000 needs 11 bits
        mid_mac_vertex = TestMacVertex(
            label=f"MidMacVertex{i}", n_keys_required={"Test": 100},
            app_vertex=mid_app_vertex)
        mid_app_vertex.remember_machine_vertex(mid_mac_vertex)


def test_big_no_fixed() -> None:
    unittest_setup()
    create_big(None)
    routing_info = ZonedRoutingInfoAllocator().allocate()

    assert routing_info.min_bits_machine_and_atoms == 21
    assert routing_info.max_bits_machine == 11
    assert routing_info.max_bits_atoms == 21
    assert routing_info.size_app_part_bits == 1
    assert routing_info.target_app_bits == 1
    assert routing_info.target_machine_bits == 11
    assert routing_info.target_atom_bits == 20
    assert routing_info.has_global_app_masks
    assert not routing_info.has_global_machine_masks
    assert not routing_info.has_fixed_keys
    assert not routing_info.has_app_keys_overlap
    assert routing_info.is_machine_shiftable

    check_masks_all_the_same(routing_info)
    check_keys_for_application_partition_pairs(routing_info)


def test_big_fixed_high() -> None:
    unittest_setup()
    create_big(0x180000)
    try:
        ZonedRoutingInfoAllocator().allocate()
        raise AssertionError("Should go boom")
    except IrregularFixedMaskException:
        pass


def test_big_fixed_low() -> None:
    unittest_setup()
    fixed_app_mask = 0xFFF00000
    create_big(fixed_app_mask)
    routing_info = ZonedRoutingInfoAllocator().allocate()

    check_masks_all_the_same(routing_info)

    check_keys_for_application_partition_pairs(routing_info)

    assert routing_info.min_bits_machine_and_atoms == 18
    assert routing_info.max_bits_machine == 11
    assert routing_info.max_bits_atoms == 7  # Big is fixed
    assert routing_info.size_app_part_bits == 1
    assert routing_info.target_app_bits == 12
    assert routing_info.target_machine_bits == 11
    assert routing_info.target_atom_bits == 9
    assert routing_info.has_global_app_masks
    assert not routing_info.has_global_machine_masks
    assert routing_info.has_fixed_keys
    assert not routing_info.has_app_keys_overlap
    assert routing_info.is_machine_shiftable


def create_many_machine_mask() -> None:
    fixed_machine_keys_by_partition: Any = dict()
    fixed_app_vertex = MockAppVertex(
        splitter=MockSplitter(), fixed_key=BaseKeyAndMask(0, 0xffffff00),
        fixed_machine_keys_by_partition=fixed_machine_keys_by_partition)
    PacmanDataView.add_vertex(fixed_app_vertex)
    # Create a single output vertex (which won't send)
    out_app_vertex = MockAppVertex(splitter=MockSplitter())
    PacmanDataView.add_vertex(out_app_vertex)

    PacmanDataView.add_edge(
        ApplicationEdge(fixed_app_vertex, out_app_vertex), "Test")

    # Create a single big machine vertex
    fixed_mac_vertex1 = TestMacVertex(
        label="fixed 1", n_keys_required={"Test": 8},
        app_vertex=fixed_app_vertex)
    fixed_app_vertex.remember_machine_vertex(fixed_mac_vertex1)
    fixed_machine_keys_by_partition[
        fixed_mac_vertex1, "Test"] = BaseKeyAndMask(0, 0xfffffff0)

    fixed_mac_vertex2 = TestMacVertex(
        label="fixed 2", n_keys_required={"Test": 8},
        app_vertex=fixed_app_vertex)
    fixed_app_vertex.remember_machine_vertex(fixed_mac_vertex2)
    fixed_machine_keys_by_partition[
        fixed_mac_vertex2, "Test"] = BaseKeyAndMask(0, 0xffffff0f)


def test_many_machine_mask() -> None:
    unittest_setup()
    create_many_machine_mask()
    try:
        ZonedRoutingInfoAllocator().allocate()
        raise Exception("PacmanRouteInfoAllocationExceptio not raise")
    except PacmanRouteInfoAllocationException:
        pass
