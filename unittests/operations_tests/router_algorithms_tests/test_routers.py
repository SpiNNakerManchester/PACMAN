# Copyright (c) 2022 The University of Manchester
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

from collections import defaultdict
import math
from typing import (
    Any, Callable, cast, Dict, Iterable, Optional, List, Sequence, Set, Tuple)
from typing_extensions import TypeAlias

import pytest

from spinn_utilities.config_holder import set_config
from spinn_utilities.overrides import overrides
from spinn_utilities.timer import Timer
from spinn_utilities.typing.coords import XY

from spinn_machine import Machine, RoutingEntry
from spinn_machine.link_data_objects import AbstractLinkData
from spinn_machine.version import FIVE
from spinn_machine.version.version_strings import VersionStrings
from spinn_machine.virtual_machine import (
    virtual_machine_by_boards, virtual_machine_by_cores)

from pacman.data import PacmanDataView
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.exceptions import PacmanRoutingException
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.application import (
    ApplicationVertex, ApplicationEdge,
    ApplicationSpiNNakerLinkVertex, ApplicationFPGAVertex, FPGAConnection)
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import (
    MachineEdge, MachineVertex, MulticastEdgePartition)
from pacman.model.partitioner_splitters import (
    SplitterExternalDevice, AbstractSplitterCommon)
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition)
from pacman.utilities.utility_objs import ChipCounter
from pacman.operations.placer_algorithms.application_placer import (
    place_application_graph)
from pacman.operations.router_algorithms.application_router import (
    route_application_graph, _path_without_errors)
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    longest_dimension_first, get_app_partitions, vertex_xy,
    vertex_xy_and_route)
from pacman.config_setup import unittest_setup
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placements, Placement
from pacman.model.resources import AbstractSDRAM, ConstantSDRAM
from pacman.model.graphs.machine import (
    MachineFPGAVertex, MachineSpiNNakerLinkVertex)

Alr: TypeAlias = Callable[[], MulticastRoutingTableByPartition]
Params: TypeAlias = Tuple[Alr, int, int]


@pytest.fixture(params=[
    (route_application_graph, 10, 50)])
def params(request: Any) -> Params:
    return request.param


class MockSplitter(AbstractSplitterCommon):

    def __init__(self, n_machine_vertices: int):
        super().__init__()
        self.__n_machine_vertices = n_machine_vertices

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        m_vertices = [
            SimpleMachineVertex(
                ConstantSDRAM(0), app_vertex=self.governed_app_vertex,
                label=f"{self.governed_app_vertex.label}_{i}")
            for i in range(self.__n_machine_vertices)]
        for m_vertex in m_vertices:
            self.governed_app_vertex.remember_machine_vertex(m_vertex)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

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
        return []

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass


class MockMultiInputSplitter(AbstractSplitterCommon):

    def __init__(self, n_incoming_machine_vertices: int,
                 n_outgoing_machine_vertices: int, n_groups: int,
                 internal_multicast: bool = False):
        super().__init__()
        self.__n_incoming_machine_vertices = n_incoming_machine_vertices
        self.__n_outgoing_machine_vertices = n_outgoing_machine_vertices
        self.__n_groups = n_groups
        self.__internal_multicast = internal_multicast
        self.__same_chip_groups: List[Tuple[
            Sequence[MachineVertex], AbstractSDRAM]] = list()
        self.__incoming_machine_vertices: List[List[MachineVertex]] = [
            list() for _ in range(n_incoming_machine_vertices)]
        self.__outgoing_machine_vertices: List[MachineVertex] = list()
        self.__internal_multicast_partitions: List[
            MulticastEdgePartition] = list()

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        last_incoming = None
        for i in range(self.__n_groups):
            incoming = [
                SimpleMachineVertex(
                    ConstantSDRAM(0), app_vertex=self.governed_app_vertex,
                    label=f"{self.governed_app_vertex.label}_{i}_{j}")
                for j in range(self.__n_incoming_machine_vertices)]
            outgoing = [
                SimpleMachineVertex(
                    ConstantSDRAM(0), app_vertex=self.governed_app_vertex,
                    label=f"{self.governed_app_vertex.label}_{i}_{j}")
                for j in range(self.__n_outgoing_machine_vertices)]
            self.__same_chip_groups.append(
                (incoming + outgoing, ConstantSDRAM(0)))
            self.__outgoing_machine_vertices.extend(outgoing)
            for out in outgoing:
                self.governed_app_vertex.remember_machine_vertex(out)
            for j in range(self.__n_incoming_machine_vertices):
                self.governed_app_vertex.remember_machine_vertex(incoming[j])
                self.__incoming_machine_vertices[j].append(incoming[j])
            if self.__internal_multicast:
                if last_incoming is not None:
                    for this_in in incoming:
                        in_part = MulticastEdgePartition(this_in, "internal")
                        self.__internal_multicast_partitions.append(in_part)
                        for last_in in last_incoming:
                            in_part.add_edge(MachineEdge(this_in, last_in))
                last_incoming = incoming

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return self.__outgoing_machine_vertices

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return [v for lst in self.__incoming_machine_vertices for v in lst]

    @overrides(AbstractSplitterCommon.get_source_specific_in_coming_vertices)
    def get_source_specific_in_coming_vertices(
            self, source_vertex: ApplicationVertex,
            partition_id: str) -> Sequence[Tuple[
                MachineVertex, Sequence[AbstractVertex]]]:
        sources = source_vertex.splitter.get_out_going_vertices(partition_id)
        n_sources = len(sources)
        sources_per_incoming = int(math.ceil(
            n_sources / self.__n_incoming_machine_vertices))
        result = list()
        for i in range(self.__n_incoming_machine_vertices):
            start = sources_per_incoming * i
            end = start + sources_per_incoming
            if (i + 1) == self.__n_incoming_machine_vertices:
                end = n_sources
            source_range = sources[start:end]
            for i_vertex in self.__incoming_machine_vertices[i]:
                result.append((i_vertex, source_range))
        return result

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> Iterable[MachineVertex]:
        return []

    @overrides(AbstractSplitterCommon.get_internal_multicast_partitions)
    def get_internal_multicast_partitions(
            self) -> Sequence[MulticastEdgePartition]:
        return self.__internal_multicast_partitions

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass

    @overrides(AbstractSplitterCommon.get_same_chip_groups)
    def get_same_chip_groups(self) -> Sequence[
            Tuple[Sequence[MachineVertex], AbstractSDRAM]]:
        return self.__same_chip_groups


class MockOneToOneSplitter(AbstractSplitterCommon):

    def __init__(self, n_machine_vertices: int):
        super().__init__()
        self.__n_machine_vertices = n_machine_vertices

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        m_vertices = [
            SimpleMachineVertex(
                ConstantSDRAM(0), app_vertex=self.governed_app_vertex,
                label=f"{self.governed_app_vertex.label}_{i}")
            for i in range(self.__n_machine_vertices)]
        for m_vertex in m_vertices:
            self.governed_app_vertex.remember_machine_vertex(m_vertex)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

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
        return []

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass

    @overrides(AbstractSplitterCommon.get_source_specific_in_coming_vertices)
    def get_source_specific_in_coming_vertices(
            self, source_vertex: ApplicationVertex,
            partition_id: str) -> Sequence[Tuple[
                MachineVertex, Sequence[AbstractVertex]]]:
        return [
            (target, [source])
            for source, target in zip(
                source_vertex.splitter.get_out_going_vertices(partition_id),
                self.governed_app_vertex.machine_vertices)]


class MockNearestEthernetSplitter(AbstractSplitterCommon):

    def __init__(self) -> None:
        super().__init__()
        self.__placements = Placements()
        self.__m_vertex_by_ethernet: Dict[Tuple[int, int], MachineVertex]
        self.__m_vertex_by_ethernet = dict()

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        machine = PacmanDataView.get_machine()
        for chip in machine.ethernet_connected_chips:
            m_vertex = SimpleMachineVertex(
                ConstantSDRAM(0), app_vertex=self.governed_app_vertex,
                label=f"{self.governed_app_vertex.label}_{chip.x}_{chip.y}")
            self.governed_app_vertex.remember_machine_vertex(m_vertex)
            self.__placements.add_placement(
                Placement(m_vertex, chip.x, chip.y, 1))
            self.__m_vertex_by_ethernet[chip.x, chip.y] = m_vertex

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

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
        return []

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass

    @overrides(AbstractSplitterCommon.get_source_specific_in_coming_vertices)
    def get_source_specific_in_coming_vertices(
            self, source_vertex: ApplicationVertex,
            partition_id: str) -> Sequence[Tuple[
                MachineVertex, Sequence[AbstractVertex]]]:

        m_vertex = next(iter(source_vertex.splitter.get_out_going_vertices(
            partition_id)))
        x, y = vertex_xy(m_vertex)
        chip = PacmanDataView.get_chip_at(x, y)
        target_m_vertex = self.__m_vertex_by_ethernet[
            chip.nearest_ethernet_x, chip.nearest_ethernet_y]
        return [(target_m_vertex, [source_vertex])]

    @property
    def placements(self) -> Placements:
        return self.__placements


class MockInputOutputSplitter(AbstractSplitterCommon):
    def __init__(self, n_incoming: int, n_outgoing: int):
        super().__init__()
        self.__n_incoming: int = n_incoming
        self.__n_outgoing: int = n_outgoing
        self.__incoming_machine_vertices: List[MachineVertex] = list()
        self.__outgoing_machine_vertices: List[MachineVertex] = list()
        self.__internal_multicast_partitions: List[
            MulticastEdgePartition] = list()

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        self.__incoming_machine_vertices = [
            SimpleMachineVertex(
                ConstantSDRAM(0), app_vertex=self.governed_app_vertex,
                label=f"{self.governed_app_vertex.label}_input_{j}")
            for j in range(self.__n_incoming)]
        self.__outgoing_machine_vertices = [
            SimpleMachineVertex(
                ConstantSDRAM(0), app_vertex=self.governed_app_vertex,
                label=f"{self.governed_app_vertex.label}_output_{j}")
            for j in range(self.__n_outgoing)]
        for out_v in self.__outgoing_machine_vertices:
            self.governed_app_vertex.remember_machine_vertex(out_v)
        for in_v in self.__incoming_machine_vertices:
            self.governed_app_vertex.remember_machine_vertex(in_v)

        # The partition is from outgoing to incoming
        for start_v in self.__outgoing_machine_vertices:
            part = MulticastEdgePartition(start_v, "internal")
            self.__internal_multicast_partitions.append(part)
            for end_v in self.__incoming_machine_vertices:
                part.add_edge(MachineEdge(start_v, end_v))

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return self.__outgoing_machine_vertices

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return self.__incoming_machine_vertices

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> Iterable[MachineVertex]:
        return []

    @overrides(AbstractSplitterCommon.get_internal_multicast_partitions)
    def get_internal_multicast_partitions(
            self) -> Sequence[MulticastEdgePartition]:
        return self.__internal_multicast_partitions

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass


class MockAppVertex(ApplicationVertex):
    def __init__(self, n_atoms: int, label: str):
        super(MockAppVertex, self).__init__(label)
        self.__n_atoms = n_atoms

    @property
    def n_atoms(self) -> int:
        return self.__n_atoms


def _make_vertices(writer: PacmanDataWriter, n_atoms: int,
                   n_machine_vertices: int, label: str) -> MockAppVertex:
    vertex = MockAppVertex(n_atoms, label)
    vertex.splitter = MockSplitter(n_machine_vertices)
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(ChipCounter())
    return vertex


def _make_one_to_one_vertices(
        writer: PacmanDataWriter, n_atoms: int, n_machine_vertices: int,
        label: str) -> MockAppVertex:
    vertex = MockAppVertex(n_atoms, label)
    vertex.splitter = MockOneToOneSplitter(n_machine_vertices)
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(ChipCounter())
    return vertex


def _make_ethernet_vertices(
        writer: PacmanDataWriter, n_atoms: int, label: str) -> MockAppVertex:
    vertex = MockAppVertex(n_atoms, label)
    vertex.splitter = MockNearestEthernetSplitter()
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(ChipCounter())
    return vertex


def _make_vertices_split(
        writer: PacmanDataWriter, n_atoms: int, n_incoming: int,
        n_outgoing: int, n_groups: int, label: str,
        internal_multicast: bool = False) -> MockAppVertex:
    vertex = MockAppVertex(n_atoms, label)
    vertex.splitter = MockMultiInputSplitter(
        n_incoming, n_outgoing, n_groups, internal_multicast)
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(ChipCounter())
    return vertex


def _make_input_output_vertices(
        writer: PacmanDataWriter, n_atoms: int, n_incoming: int,
        n_outgoing: int, label: str) -> MockAppVertex:
    vertex = MockAppVertex(n_atoms, label)
    vertex.splitter = MockInputOutputSplitter(n_incoming, n_outgoing)
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(ChipCounter())
    return vertex


def _get_entry(
        routing_tables: MulticastRoutingTableByPartition, x: int, y: int,
        source_vertex: MachineVertex, partition_id: str,
        allow_none: bool) -> Optional[RoutingEntry]:
    app_vertex = source_vertex.app_vertex
    app_entry = routing_tables.get_entry_on_coords_for_edge(
        app_vertex, partition_id, x, y)
    entry = routing_tables.get_entry_on_coords_for_edge(
        source_vertex, partition_id, x, y)

    if entry is None and app_entry is None:
        if allow_none:
            return None
        raise PacmanRoutingException(
            f"No entry found on {x}, {y} for {source_vertex}, {partition_id}")
    if entry is not None and app_entry is not None:
        raise PacmanRoutingException(
            f"App-entry and non-app-entry found on {x}, {y} for"
            f" {source_vertex}, {partition_id}: {app_entry}: {entry}")
    if app_entry is not None:
        return app_entry
    return entry


def _find_targets(
        routing_tables: MulticastRoutingTableByPartition,
        expected_virtual: Set[Tuple[int, int, int]],
        source_vertex: MachineVertex, partition_id: str) -> Set[
            Tuple[XY, Optional[int], Optional[int]]]:
    found_targets: Set[Tuple[XY, Optional[int], Optional[int]]] = set()
    to_follow: List[Tuple[int, int, Optional[RoutingEntry]]] = list()
    x, y = vertex_xy(source_vertex)
    first_entry = _get_entry(
        routing_tables, x, y, source_vertex, partition_id, True)
    if first_entry is None:
        return found_targets
    to_follow.append((x, y, first_entry))
    visited = set()
    machine = PacmanDataView.get_machine()
    while to_follow:
        x, y, next_to_follow = to_follow.pop()
        assert next_to_follow is not None
        if not machine.is_chip_at(x, y):
            raise PacmanRoutingException(
                f"Route goes through {x}, {y} but that doesn't exist!")
        if (x, y) in visited:
            raise PacmanRoutingException(
                f"Potential loop found when going through {x}, {y}")
        visited.add((x, y))
        for p in next_to_follow.processor_ids:
            if (x, y, p) in found_targets:
                raise PacmanRoutingException(
                    f"Potential Loop found when adding routes at {x}, {y}")
            found_targets.add(((x, y), p, None))
        for link in next_to_follow.link_ids:
            if (x, y, link) in expected_virtual:
                found_targets.add(((x, y), None, link))
            else:
                if not machine.is_link_at(x, y, link):
                    raise PacmanRoutingException(
                        f"Route from {source_vertex}, {partition_id} uses link"
                        f" {x}, {y}, {link} but that doesn't exist!")
                next_x, next_y = machine.xy_over_link(x, y, link)
                to_follow.append((next_x, next_y, _get_entry(
                        routing_tables, next_x, next_y, source_vertex,
                        partition_id, False)))
    return found_targets


def _add_virtual(expected_virtual: Set[Tuple[int, int, int]],
                 vertex: MachineVertex) -> None:
    link_data: Optional[AbstractLinkData] = None
    if isinstance(vertex, MachineFPGAVertex):
        link_data = PacmanDataView.get_machine().get_fpga_link_with_id(
            vertex.fpga_id, vertex.fpga_link_id, vertex.board_address)
    elif isinstance(vertex, MachineSpiNNakerLinkVertex):
        link_data = PacmanDataView.get_machine().get_spinnaker_link_with_id(
            vertex.spinnaker_link_id, vertex.board_address)
    if link_data is not None:
        expected_virtual.add((
            link_data.connected_chip_x, link_data.connected_chip_y,
            link_data.connected_link))


def _check_edges(routing_tables: MulticastRoutingTableByPartition) -> None:
    for part in get_app_partitions():

        # Find the required targets
        required_targets = defaultdict(set)
        expected_virtual: Set[Tuple[int, int, int]] = set()
        for edge in part.edges:
            post = edge.post_vertex
            targets = post.splitter.get_source_specific_in_coming_vertices(
                    edge.pre_vertex, part.identifier)
            for tgt, srcs in targets:
                _add_virtual(expected_virtual, tgt)
                xy, (m_vertex, core, link) = vertex_xy_and_route(tgt)
                for src in srcs:
                    if isinstance(src, ApplicationVertex):
                        for m_vertex in src.splitter.get_out_going_vertices(
                                part.identifier):
                            required_targets[m_vertex].add((xy, core, link))
                    else:
                        required_targets[src].add((xy, core, link))

        splitter = part.pre_vertex.splitter
        outgoing = set(splitter.get_out_going_vertices(part.identifier))
        for in_part in splitter.get_internal_multicast_partitions():
            if in_part.identifier == part.identifier:
                outgoing.add(in_part.pre_vertex)
                for edge in in_part.edges:
                    xy, (m_vertex, core, link) = vertex_xy_and_route(
                        edge.post_vertex)
                    required_targets[in_part.pre_vertex].add((xy, core, link))
                    _add_virtual(expected_virtual, edge.post_vertex)

        for m_vertex in outgoing:
            actual_targets = _find_targets(
                routing_tables, expected_virtual, m_vertex, part.identifier)
            assert not actual_targets.difference(required_targets[m_vertex])


def _route_and_time(algorithm: Alr) -> MulticastRoutingTableByPartition:
    timer = Timer()
    with timer:
        result = algorithm()
    print(f"Routing took {timer.measured_interval}")
    return result


def test_simple(params: Params) -> None:
    algorithm, _n_vertices, n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    source_vertex = _make_vertices(writer, 1000, n_m_vertices, "source")
    target_vertex = _make_vertices(writer, 1000, n_m_vertices, "target")
    writer.add_edge(ApplicationEdge(source_vertex, target_vertex), "Test")

    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_self(params: Params) -> None:
    algorithm, _n_vertices, n_m_vertices = params
    unittest_setup()
    set_config("Machine", "version", "5")
    writer = PacmanDataWriter.mock()
    source_vertex = _make_vertices(writer, 1000, n_m_vertices, "self")
    writer.add_edge(ApplicationEdge(source_vertex, source_vertex), "Test")

    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_simple_self(params: Params) -> None:
    algorithm, _n_vertices, n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    source_vertex = _make_vertices(writer, 1000, n_m_vertices, "source")
    target_vertex = _make_vertices(writer, 1000, n_m_vertices, "target")
    writer.add_edge(ApplicationEdge(source_vertex, source_vertex), "Test")
    writer.add_edge(ApplicationEdge(target_vertex, target_vertex), "Test")
    writer.add_edge(ApplicationEdge(source_vertex, target_vertex), "Test")

    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi(params: Params) -> None:
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices(writer, 1000, n_m_vertices, f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            if source != target:
                writer.add_edge(ApplicationEdge(source, target), "Test")

    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi_self(params: Params) -> None:
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices(writer, 1000, n_m_vertices, f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            writer.add_edge(ApplicationEdge(source, target), "Test")

    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi_split(params: Params) -> None:
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices_split(writer, 1000, 3, 2, n_m_vertices,
                             f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            if source != target:
                writer.add_edge(ApplicationEdge(source, target), "Test")

    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi_self_split(params: Params) -> None:
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices_split(writer, 1000, 3, 2, n_m_vertices,
                             f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            writer.add_edge(ApplicationEdge(source, target), "Test")

    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi_down_chips_and_links(params: Params) -> None:
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices(writer, 1000, n_m_vertices, f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            writer.add_edge(ApplicationEdge(source, target), "Test")

    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)

    # Pick a few of the chips and links used and take them out
    chosen_entries: List[Tuple[int, int, RoutingEntry]] = list()
    count = 2
    for x, y in routing_tables.get_routers():
        if len(chosen_entries) >= 10:
            break

        if count != 0:
            count -= 1
        else:
            entries = routing_tables.get_entries_for_router(x, y)
            assert entries is not None
            count = 11 - len(chosen_entries)
            for entry in entries.values():
                if count != 0:
                    count -= 1
                else:
                    chosen_entries.append((x, y, entry))
                    break
            count = 2

    down_links = ""
    down_chips = ""
    machine = PacmanDataView.get_machine()
    for i, (x, y, entry) in enumerate(chosen_entries):
        if entry.link_ids:
            link = list(entry.link_ids)[i % len(entry.link_ids)]
            t_x, t_y = machine.xy_over_link(x, y, link)
            t_l = (link + 3) % 6
            down_links += f"{x},{y},{link}:"
            down_links += f"{t_x},{t_y},{t_l}:"
        else:
            down_chips += f"{x},{y}:"

    print("Down chips:", down_chips[:-1].split(":"))
    print("Down links:", down_links[:-1].split(":"))
    set_config("Machine", "down_chips", down_chips[:-1])
    set_config("Machine", "down_links", down_links[:-1])
    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_internal_only(params: Params) -> None:
    algorithm, _n_vertices, _n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.ANY.text)
    writer = PacmanDataWriter.mock()
    _make_vertices_split(
        writer, 1000, 3, 2, 2, "app_vertex",
        internal_multicast=True)

    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_internal_and_split(params: Params) -> None:
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices_split(
            writer, 1000, 3, 2, n_m_vertices, f"app_vertex_{i}",
            internal_multicast=True)
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            if source != target:
                writer.add_edge(ApplicationEdge(source, target), "Test")

    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_spinnaker_link(params: Params) -> None:
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    # TODO SPIN2 spinnaker links
    set_config("Machine", "version", str(FIVE))
    writer = PacmanDataWriter.mock()
    in_device = ApplicationSpiNNakerLinkVertex(100, 0)
    in_device.splitter = SplitterExternalDevice()
    in_device.splitter.create_machine_vertices(ChipCounter())
    writer.add_vertex(in_device)
    out_device = ApplicationSpiNNakerLinkVertex(100, 0)
    out_device.splitter = SplitterExternalDevice()
    out_device.splitter.create_machine_vertices(ChipCounter())
    writer.add_vertex(out_device)
    for i in range(n_vertices):
        app_vertex = _make_vertices(
            writer, 1000, n_m_vertices, f"app_vertex_{i}")
        writer.add_edge(ApplicationEdge(in_device, app_vertex), "Test")
        writer.add_edge(ApplicationEdge(app_vertex, out_device), "Test")

    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_fpga_link(params: Params) -> None:
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    # TODO spin2 fpga
    set_config("Machine", "version", "5")
    writer = PacmanDataWriter.mock()
    in_device = ApplicationFPGAVertex(
        100, [FPGAConnection(0, 0, None, None)], None)
    in_device.splitter = SplitterExternalDevice()
    in_device.splitter.create_machine_vertices(ChipCounter())
    writer.add_vertex(in_device)
    out_device = ApplicationFPGAVertex(
        100, [FPGAConnection(0, 1, None, None)],
        FPGAConnection(0, 1, None, None))
    out_device.splitter = SplitterExternalDevice()
    out_device.splitter.create_machine_vertices(ChipCounter())
    writer.add_vertex(out_device)
    for i in range(n_vertices):
        app_vertex = _make_vertices(
            writer, 1000, n_m_vertices, f"app_vertex_{i}")
        writer.add_edge(ApplicationEdge(in_device, app_vertex), "Test")
        writer.add_edge(ApplicationEdge(app_vertex, out_device), "Test")

    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_fpga_link_overlap(params: Params) -> None:
    algorithm, _n_vertices, _n_m_vertices = params
    unittest_setup()
    # TODO Spin2 links
    set_config("Machine", "version", "5")
    writer = PacmanDataWriter.mock()
    set_config("Machine", "down_chips", "6,1")
    in_device = ApplicationFPGAVertex(
        100, [FPGAConnection(0, i, None, None) for i in range(15, 0, -2)],
        None)
    in_device.splitter = SplitterExternalDevice()
    in_device.splitter.create_machine_vertices(ChipCounter())
    writer.add_vertex(in_device)
    app_vertex = _make_vertices(
        writer, 1000, 60 * 16, "app_vertex")
    writer.add_edge(ApplicationEdge(in_device, app_vertex), "Test")

    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    placements = Placements()
    writer.set_placements(placements)
    place_application_graph(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_odd_case(params: Params) -> None:
    algorithm, _n_vertices, _n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    target_vertex = _make_vertices(writer, 200, 20, "app_vertex")
    delay_vertex = _make_one_to_one_vertices(writer, 200, 20, "delay_vtx")
    writer.add_edge(ApplicationEdge(target_vertex, target_vertex), "Test")
    writer.add_edge(ApplicationEdge(target_vertex, delay_vertex), "Test")
    writer.add_edge(ApplicationEdge(delay_vertex, target_vertex), "Test")

    cores = [(x, y, p) for x, y in [(0, 3), (1, 3)] for p in range(3, 18)]
    placements = Placements()
    core_iter = iter(cores)
    for m_vertex in delay_vertex.machine_vertices:
        x, y, p = next(core_iter)
        placements.add_placement(Placement(m_vertex, x, y, p))
    cores = [(0, 0, 3)]
    cores.extend(
        [(x, y, p)
         for x, y in [(1, 0), (1, 1), (0, 1), (2, 0), (2, 1), (2, 2),
                      (1, 2), (0, 2), (3, 0), (3, 1), (3, 2)]
         for p in range(2, 4)])
    core_iter = iter(cores)
    for m_vertex in target_vertex.machine_vertices:
        x, y, p = next(core_iter)
        placements.add_placement(Placement(m_vertex, x, y, p))

    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    writer.set_placements(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_with_ethernet_system_placements(params: Params) -> None:
    # This is a test of LPG-style functionality, where an application vertex
    # is placed on multiple ethernet chips, but the source is only connected
    # to one of them
    algorithm, _n_vertices, _n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    writer.set_machine(virtual_machine_by_boards(4))
    source_vertex = _make_vertices(writer, 200, 3, "app_vertex")
    target_vertex = _make_ethernet_vertices(writer, 1, "eth_vertex")
    writer.add_edge(ApplicationEdge(source_vertex, target_vertex), "Test")
    splitter = cast(MockNearestEthernetSplitter, target_vertex.splitter)
    placements = splitter.placements
    chips_to_use = [(7, 8), (7, 7), (8, 7)]
    for m_vertex, chip in zip(source_vertex.machine_vertices, chips_to_use):
        placements.add_placement(Placement(m_vertex, chip[0], chip[1], 2))
    writer.set_placements(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def _check_path(source: XY, nodes_fixed: List[Tuple[int, XY]],
                machine: Machine, target: XY) -> None:
    c_x, c_y = source
    seen = set()
    for direction, (n_x, n_y) in nodes_fixed:
        if (c_x, c_y) in seen:
            raise PacmanRoutingException(
                f"Loop detected at {c_x}, {c_y}: {nodes_fixed}")
        if not machine.is_chip_at(c_x, c_y):
            raise PacmanRoutingException(
                f"Route through down chip {c_x}, {c_y}: {nodes_fixed}")
        if not machine.is_link_at(c_x, c_y, direction):
            raise PacmanRoutingException(
                f"Route through down link {c_x}, {c_y}, {direction}:"
                f" {nodes_fixed}")
        if not machine.xy_over_link(c_x, c_y, direction) == (n_x, n_y):
            raise PacmanRoutingException(
                f"Invalid route from {c_x}, {c_y}, {direction} to {n_x}, {n_y}"
                f": {nodes_fixed}")
        seen.add((c_x, c_y))
        c_x, c_y = n_x, n_y

    if (c_x, c_y) != target:
        raise PacmanRoutingException(
            f"Route doesn't end at (5, 5): {nodes_fixed}")


def test_route_around() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    # Take out all the chips around 3,3 except one then make a path that goes
    # through it
    #      3,4 4,4
    #  2,3 3,3 4,3
    #  2,2 3,2
    set_config("Machine", "down_chips", "2,3:3,2:3,4:4,4:4,3")
    machine = PacmanDataView.get_machine()
    vector = machine.get_vector((0, 0), (6, 6))
    PacmanDataWriter.mock().set_machine(machine)
    nodes = longest_dimension_first(vector, (0, 0))
    nodes_fixed = _path_without_errors((0, 0), nodes, machine)
    _check_path((0, 0), nodes_fixed, machine, (6, 6))

    vector = machine.get_vector((2, 2), (6, 6))
    nodes = longest_dimension_first(vector, (2, 2))
    nodes_fixed = _path_without_errors((2, 2), nodes, machine)
    _check_path((2, 2), nodes_fixed, machine, (6, 6))

    print(nodes)
    print(nodes_fixed)


def test_internal_io_routes(params: Params) -> None:
    algorithm, _n_vertices, _n_m_vertices = params
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    machine = PacmanDataView.get_machine()
    writer = PacmanDataWriter.mock()
    writer.set_machine(machine)
    vertex = _make_input_output_vertices(writer, 1, 1, 3, "app_vertex")
    placements = Placements()
    for i, m_vertex in enumerate(vertex.splitter.get_out_going_vertices("")):
        placements.add_placement(Placement(m_vertex, 0, 1, i))

    for i, m_vertex in enumerate(
            vertex.splitter.get_in_coming_vertices("")):
        placements.add_placement(Placement(m_vertex, 0, 0, i))
    writer.set_placements(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)
