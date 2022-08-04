# Copyright (c) 2022 The University of Manchester
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
from spinn_utilities.timer import Timer
from spinn_utilities.config_holder import set_config
from spinn_machine import virtual_machine
from pacman.data import PacmanDataView
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.graphs.application import (
    ApplicationVertex, ApplicationEdge,
    ApplicationSpiNNakerLinkVertex, ApplicationFPGAVertex)
from pacman.model.graphs.machine import MulticastEdgePartition, MachineEdge
from pacman.model.partitioner_splitters import SplitterFixedLegacy
from pacman.utilities.utility_objs import ChipCounter
from pacman.operations.placer_algorithms.application_placer import (
    place_application_graph)
from pacman.operations.router_algorithms.application_router import (
    route_application_graph, _path_without_errors)
from pacman.operations.router_algorithms.basic_dijkstra_routing import (
    basic_dijkstra_routing)
from pacman.operations.router_algorithms.ner_route import (
    ner_route, ner_route_traffic_aware)
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    longest_dimension_first, get_app_partitions, vertex_xy,
    vertex_xy_and_route)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.config_setup import unittest_setup
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placements, Placement
from pacman.model.resources import ConstantSDRAM
from pacman.model.graphs import AbstractFPGA, AbstractSpiNNakerLink

from collections import defaultdict
import math
import pytest


@pytest.fixture(params=[
    (route_application_graph, 10, 50),
    (basic_dijkstra_routing, 10, 10),
    (ner_route, 10, 50),
    (ner_route_traffic_aware, 10, 50)])
def params(request):
    return request.param


class TestSplitter(AbstractSplitterCommon):

    def __init__(self, n_machine_vertices):
        AbstractSplitterCommon.__init__(self)
        self.__n_machine_vertices = n_machine_vertices

    def create_machine_vertices(self, chip_counter):
        m_vertices = [
            SimpleMachineVertex(
                ConstantSDRAM(0), app_vertex=self._governed_app_vertex,
                label=f"{self._governed_app_vertex.label}_{i}")
            for i in range(self.__n_machine_vertices)]
        for m_vertex in m_vertices:
            self._governed_app_vertex.remember_machine_vertex(m_vertex)

    def get_out_going_slices(self):
        return None

    def get_in_coming_slices(self):
        return None

    def get_out_going_vertices(self, partition_id):
        return self._governed_app_vertex.machine_vertices

    def get_in_coming_vertices(self, partition_id):
        return self._governed_app_vertex.machine_vertices

    def machine_vertices_for_recording(self, variable_to_record):
        return []

    def reset_called(self):
        pass


class TestMultiInputSplitter(AbstractSplitterCommon):

    def __init__(self, n_incoming_machine_vertices,
                 n_outgoing_machine_vertices, n_groups,
                 internal_multicast=False):
        AbstractSplitterCommon.__init__(self)
        self.__n_incoming_machine_vertices = n_incoming_machine_vertices
        self.__n_outgoing_machine_vertices = n_outgoing_machine_vertices
        self.__n_groups = n_groups
        self.__internal_multicast = internal_multicast
        self.__same_chip_groups = list()
        self.__incoming_machine_vertices = [
            list() for _ in range(n_incoming_machine_vertices)]
        self.__outgoing_machine_vertices = list()
        self.__internal_multicast_partitions = list()

    def create_machine_vertices(self, chip_counter):
        last_incoming = None
        for i in range(self.__n_groups):
            incoming = [
                SimpleMachineVertex(
                    ConstantSDRAM(0), app_vertex=self._governed_app_vertex,
                    label=f"{self._governed_app_vertex.label}_{i}_{j}")
                for j in range(self.__n_incoming_machine_vertices)]
            outgoing = [
                SimpleMachineVertex(
                    ConstantSDRAM(0), app_vertex=self._governed_app_vertex,
                    label=f"{self._governed_app_vertex.label}_{i}_{j}")
                for j in range(self.__n_outgoing_machine_vertices)]
            self.__same_chip_groups.append(
                (incoming + outgoing, ConstantSDRAM(0)))
            self.__outgoing_machine_vertices.extend(outgoing)
            for out in outgoing:
                self._governed_app_vertex.remember_machine_vertex(out)
            for j in range(self.__n_incoming_machine_vertices):
                self._governed_app_vertex.remember_machine_vertex(incoming[j])
                self.__incoming_machine_vertices[j].append(incoming[j])
            if self.__internal_multicast:
                if last_incoming is not None:
                    for this_in in incoming:
                        in_part = MulticastEdgePartition(this_in, "internal")
                        self.__internal_multicast_partitions.append(in_part)
                        for last_in in last_incoming:
                            in_part.add_edge(
                                MachineEdge(this_in, last_in))
                last_incoming = incoming

    def get_out_going_slices(self):
        return None

    def get_in_coming_slices(self):
        return None

    def get_out_going_vertices(self, partition_id):
        return self.__outgoing_machine_vertices

    def get_in_coming_vertices(self, partition_id):
        return [v for lst in self.__incoming_machine_vertices for v in lst]

    def get_source_specific_in_coming_vertices(
            self, source_vertex, partition_id):
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

    def machine_vertices_for_recording(self, variable_to_record):
        return []

    def get_internal_multicast_partitions(self):
        return self.__internal_multicast_partitions

    def reset_called(self):
        pass

    def get_same_chip_groups(self):
        return self.__same_chip_groups


class TestOneToOneSplitter(AbstractSplitterCommon):

    def __init__(self, n_machine_vertices):
        AbstractSplitterCommon.__init__(self)
        self.__n_machine_vertices = n_machine_vertices

    def create_machine_vertices(self, chip_counter):
        m_vertices = [
            SimpleMachineVertex(
                ConstantSDRAM(0), app_vertex=self._governed_app_vertex,
                label=f"{self._governed_app_vertex.label}_{i}")
            for i in range(self.__n_machine_vertices)]
        for m_vertex in m_vertices:
            self._governed_app_vertex.remember_machine_vertex(m_vertex)

    def get_out_going_slices(self):
        return None

    def get_in_coming_slices(self):
        return None

    def get_out_going_vertices(self, partition_id):
        return self._governed_app_vertex.machine_vertices

    def get_in_coming_vertices(self, partition_id):
        return self._governed_app_vertex.machine_vertices

    def machine_vertices_for_recording(self, variable_to_record):
        return []

    def reset_called(self):
        pass

    def get_source_specific_in_coming_vertices(
            self, source_vertex, partition_id):
        return [
            (target, [source])
            for source, target in zip(
                source_vertex.splitter.get_out_going_vertices(partition_id),
                self._governed_app_vertex.machine_vertices)]


class TestAppVertex(ApplicationVertex):
    def __init__(self, n_atoms, label):
        super(TestAppVertex, self).__init__(label)
        self.__n_atoms = n_atoms

    @property
    def n_atoms(self):
        return self.__n_atoms


def _make_vertices(writer, n_atoms, n_machine_vertices, label):
    vertex = TestAppVertex(n_atoms, label)
    vertex.splitter = TestSplitter(n_machine_vertices)
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(None)
    return vertex


def _make_one_to_one_vertices(writer, n_atoms, n_machine_vertices, label):
    vertex = TestAppVertex(n_atoms, label)
    vertex.splitter = TestOneToOneSplitter(n_machine_vertices)
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(None)
    return vertex


def _make_vertices_split(
        writer, n_atoms, n_incoming, n_outgoing, n_groups, label,
        internal_multicast=False):
    vertex = TestAppVertex(n_atoms, label)
    vertex.splitter = TestMultiInputSplitter(
        n_incoming, n_outgoing, n_groups, internal_multicast)
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(None)
    return vertex


def _get_entry(routing_tables, x, y, source_vertex, partition_id, allow_none):
    app_entry = routing_tables.get_entry_on_coords_for_edge(
        source_vertex.app_vertex, partition_id, x, y)
    entry = routing_tables.get_entry_on_coords_for_edge(
        source_vertex, partition_id, x, y)

    if entry is None and app_entry is None:
        if allow_none:
            return None
        raise Exception(
            f"No entry found on {x}, {y} for {source_vertex}, {partition_id}")
    if entry is not None and app_entry is not None:
        raise Exception(
            f"App-entry and non-app-entry found on {x}, {y} for"
            f" {source_vertex}, {partition_id}: {app_entry}: {entry}")
    if app_entry is not None:
        return app_entry
    return entry


def _find_targets(
        routing_tables, expected_virtual, source_vertex, partition_id):
    found_targets = set()
    to_follow = list()
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
        if not machine.is_chip_at(x, y):
            raise Exception(
                f"Route goes through {x}, {y} but that doesn't exist!")
        if (x, y) in visited:
            raise Exception(
                f"Potential loop found when going through {x}, {y}")
        visited.add((x, y))
        for p in next_to_follow.processor_ids:
            if (x, y, p) in found_targets:
                raise Exception(
                    f"Potential Loop found when adding routes at {x}, {y}")
            found_targets.add(((x, y), p, None))
        for link in next_to_follow.link_ids:
            if (x, y, link) in expected_virtual:
                found_targets.add(((x, y), None, link))
            else:
                if not machine.is_link_at(x, y, link):
                    raise Exception(
                        f"Route from {source_vertex}, {partition_id} uses link"
                        f" {x}, {y}, {link} but that doesn't exist!")
                next_x, next_y = machine.xy_over_link(x, y, link)
                to_follow.append((next_x, next_y, _get_entry(
                        routing_tables, next_x, next_y, source_vertex,
                        partition_id, False)))
    return found_targets


def _add_virtual(expected_virtual, vertex):
    link_data = None
    if isinstance(vertex, AbstractFPGA):
        link_data = PacmanDataView.get_machine().get_fpga_link_with_id(
            vertex.fpga_id, vertex.fpga_link_id, vertex.board_address)
    elif isinstance(vertex, AbstractSpiNNakerLink):
        link_data = PacmanDataView.get_machine().get_spinnaker_link_with_id(
            vertex.spinnaker_link_id, vertex.board_address)
    if link_data is not None:
        expected_virtual.add((
            link_data.connected_chip_x, link_data.connected_chip_y,
            link_data.connected_link))


def _check_edges(routing_tables):
    for part in get_app_partitions():

        # Find the required targets
        required_targets = defaultdict(set)
        expected_virtual = set()
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


def _route_and_time(algorithm):
    timer = Timer()
    with timer:
        result = algorithm()
    print(f"Routing took {timer.measured_interval}")
    return result


def test_simple(params):
    algorithm, _n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    source_vertex = _make_vertices(writer, 1000, n_m_vertices, "source")
    target_vertex = _make_vertices(writer, 1000, n_m_vertices, "target")
    writer.add_edge(ApplicationEdge(source_vertex, target_vertex), "Test")

    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_self(params):
    algorithm, _n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    source_vertex = _make_vertices(writer, 1000, n_m_vertices, "self")
    writer.add_edge(ApplicationEdge(source_vertex, source_vertex), "Test")

    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_simple_self(params):
    algorithm, _n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    source_vertex = _make_vertices(writer, 1000, n_m_vertices, "source")
    target_vertex = _make_vertices(writer, 1000, n_m_vertices, "target")
    writer.add_edge(ApplicationEdge(source_vertex, source_vertex), "Test")
    writer.add_edge(ApplicationEdge(target_vertex, target_vertex), "Test")
    writer.add_edge(ApplicationEdge(source_vertex, target_vertex), "Test")

    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi(params):
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices(writer, 1000, n_m_vertices, f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            if source != target:
                writer.add_edge(ApplicationEdge(source, target), "Test")

    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi_self(params):
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices(writer, 1000, n_m_vertices, f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            writer.add_edge(ApplicationEdge(source, target), "Test")

    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi_split(params):
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices_split(writer, 1000, 3, 2, n_m_vertices,
                             f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            if source != target:
                writer.add_edge(ApplicationEdge(source, target), "Test")

    writer.set_machine(virtual_machine(24, 24))
    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi_self_split(params):
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices_split(writer, 1000, 3, 2, n_m_vertices,
                             f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            writer.add_edge(ApplicationEdge(source, target), "Test")

    writer.set_machine(virtual_machine(24, 24))
    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_multi_down_chips_and_links(params):
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices(writer, 1000, n_m_vertices, f"app_vertex_{i}")
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            writer.add_edge(ApplicationEdge(source, target), "Test")

    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)

    # Pick a few of the chips and links used and take them out
    chosen_entries = list()
    count = 2
    for x, y in routing_tables.get_routers():
        if len(chosen_entries) >= 10:
            break

        if count != 0:
            count -= 1
        else:
            entries = routing_tables.get_entries_for_router(x, y)
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
    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_internal_only(params):
    algorithm, _n_vertices, _n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    _make_vertices_split(
        writer, 1000, 3, 2, 2, "app_vertex",
        internal_multicast=True)

    writer.set_machine(virtual_machine(24, 24))
    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_internal_and_split(params):
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    for i in range(n_vertices):
        _make_vertices_split(
            writer, 1000, 3, 2, n_m_vertices, f"app_vertex_{i}",
            internal_multicast=True)
    for source in writer.iterate_vertices():
        for target in writer.iterate_vertices():
            if source != target:
                writer.add_edge(ApplicationEdge(source, target), "Test")

    writer.set_machine(virtual_machine(24, 24))
    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_spinnaker_link(params):
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    in_device = ApplicationSpiNNakerLinkVertex(100, 0)
    in_device.splitter = SplitterFixedLegacy()
    in_device.splitter.create_machine_vertices(ChipCounter())
    writer.add_vertex(in_device)
    out_device = ApplicationSpiNNakerLinkVertex(100, 0)
    out_device.splitter = SplitterFixedLegacy()
    out_device.splitter.create_machine_vertices(ChipCounter())
    writer.add_vertex(out_device)
    for i in range(n_vertices):
        app_vertex = _make_vertices(
            writer, 1000, n_m_vertices, f"app_vertex_{i}")
        writer.add_edge(ApplicationEdge(in_device, app_vertex), "Test")
        writer.add_edge(ApplicationEdge(app_vertex, out_device), "Test")

    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_fpga_link(params):
    algorithm, n_vertices, n_m_vertices = params
    unittest_setup()
    writer = PacmanDataWriter.mock()
    in_device = ApplicationFPGAVertex(100, 0, 0)
    in_device.splitter = SplitterFixedLegacy()
    in_device.splitter.create_machine_vertices(ChipCounter())
    writer.add_vertex(in_device)
    out_device = ApplicationFPGAVertex(100, 0, 1)
    out_device.splitter = SplitterFixedLegacy()
    out_device.splitter.create_machine_vertices(ChipCounter())
    writer.add_vertex(out_device)
    for i in range(n_vertices):
        app_vertex = _make_vertices(
            writer, 1000, n_m_vertices, f"app_vertex_{i}")
        writer.add_edge(ApplicationEdge(in_device, app_vertex), "Test")
        writer.add_edge(ApplicationEdge(app_vertex, out_device), "Test")

    writer.set_placements(place_application_graph(Placements()))
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def test_odd_case(params):
    algorithm, _n_vertices, _n_m_vertices = params
    unittest_setup()
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

    writer.set_placements(placements)
    routing_tables = _route_and_time(algorithm)
    _check_edges(routing_tables)


def _check_path(source, nodes_fixed, machine, target):
    c_x, c_y = source
    seen = set()
    for direction, (n_x, n_y) in nodes_fixed:
        if (c_x, c_y) in seen:
            raise Exception(f"Loop detected at {c_x}, {c_y}: {nodes_fixed}")
        if not machine.is_chip_at(c_x, c_y):
            raise Exception(
                f"Route through down chip {c_x}, {c_y}: {nodes_fixed}")
        if not machine.is_link_at(c_x, c_y, direction):
            raise Exception(
                f"Route through down link {c_x}, {c_y}, {direction}:"
                f" {nodes_fixed}")
        if not machine.xy_over_link(c_x, c_y, direction) == (n_x, n_y):
            raise Exception(
                f"Invalid route from {c_x}, {c_y}, {direction} to {n_x}, {n_y}"
                f": {nodes_fixed}")
        seen.add((c_x, c_y))
        c_x, c_y = n_x, n_y

    if (c_x, c_y) != target:
        raise Exception(f"Route doesn't end at (5, 5): {nodes_fixed}")


def test_route_around():
    unittest_setup()
    # Take out all the chips around 3,3 except one then make a path that goes
    # through it
    #      3,4 4,4
    #  2,3 3,3 4,3
    #  2,2 3,2
    set_config("Machine", "down_chips", "2,3:3,2:3,4:4,4:4,3")
    machine = virtual_machine(8, 8)
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
