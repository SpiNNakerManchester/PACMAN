# Copyright (c) 2021 The University of Manchester
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
from pacman.model.graphs.application import (
    ApplicationVertex, ApplicationGraph, ApplicationEdge)
from pacman.operations.placer_algorithms.application_placer import (
    place_application_graph)
from pacman.operations.router_algorithms.application_router import (
    route_application_graph, _path_without_errors)
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    longest_dimension_first)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.config_setup import unittest_setup
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placements
from pacman.model.resources import ResourceContainer, ConstantSDRAM

from collections import defaultdict
import math


class TestSplitter(AbstractSplitterCommon):

    def __init__(self, n_machine_vertices):
        AbstractSplitterCommon.__init__(self)
        self.__n_machine_vertices = n_machine_vertices

    def create_machine_vertices(self, chip_counter):
        m_vertices = [
            SimpleMachineVertex(
                ResourceContainer(), app_vertex=self._governed_app_vertex,
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
                 n_outgoing_machine_vertices, n_groups):
        AbstractSplitterCommon.__init__(self)
        self.__n_incoming_machine_vertices = n_incoming_machine_vertices
        self.__n_outgoing_machine_vertices = n_outgoing_machine_vertices
        self.__n_groups = n_groups
        self.__same_chip_groups = list()
        self.__incoming_machine_vertices = [
            list() for _ in range(n_incoming_machine_vertices)]
        self.__outgoing_machine_vertices = list()

    def create_machine_vertices(self, chip_counter):
        for i in range(self.__n_groups):
            incoming = [
                SimpleMachineVertex(
                    ResourceContainer(), app_vertex=self._governed_app_vertex,
                    label=f"{self._governed_app_vertex.label}_{i}_{j}")
                for j in range(self.__n_incoming_machine_vertices)]
            outgoing = [
                SimpleMachineVertex(
                    ResourceContainer(), app_vertex=self._governed_app_vertex,
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

    def reset_called(self):
        pass

    def get_same_chip_groups(self):
        return self.__same_chip_groups


class TestAppVertex(ApplicationVertex):
    def __init__(self, n_atoms, label):
        super(TestAppVertex, self).__init__(label)
        self.__n_atoms = n_atoms

    @property
    def n_atoms(self):
        return self.__n_atoms


def _make_vertices(app_graph, n_atoms, n_machine_vertices, label):
    vertex = TestAppVertex(n_atoms, label)
    vertex.splitter = TestSplitter(n_machine_vertices)
    app_graph.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(None)
    return vertex


def _make_vertices_split(
        app_graph, n_atoms, n_incoming, n_outgoing, n_groups, label):
    vertex = TestAppVertex(n_atoms, label)
    vertex.splitter = TestMultiInputSplitter(n_incoming, n_outgoing, n_groups)
    app_graph.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(None)
    return vertex


def _get_entry(routing_tables, x, y, source_vertex, partition_id):
    app_entry = routing_tables.get_entry_on_coords_for_edge(
        source_vertex.app_vertex, partition_id, x, y)
    entry = routing_tables.get_entry_on_coords_for_edge(
        source_vertex, partition_id, x, y)

    if entry is None and app_entry is None:
        raise Exception(
            f"No entry found on {x}, {y} for {source_vertex}, {partition_id}")
    if entry is not None and app_entry is not None:
        raise Exception(
            f"Multiple entries found on {x}, {y} for"
            f" {source_vertex}, {partition_id}: {app_entry}: {entry}")
    if app_entry is not None:
        return app_entry
    return entry


def _find_targets(
        routing_tables, machine, placements, source_vertex, partition_id):
    found_targets = set()
    to_follow = list()
    x, y = placements.get_placement_of_vertex(source_vertex).chip
    to_follow.append((x, y, _get_entry(
        routing_tables, x, y, source_vertex, partition_id)))
    visited = set()
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
            found_targets.add((x, y, p))
        for link in next_to_follow.link_ids:
            if not machine.is_link_at(x, y, link):
                raise Exception(
                    f"Route uses link {x}, {y}, {link} but that doesn't"
                    " exist!")
            next_x, next_y = machine.xy_over_link(x, y, link)
            to_follow.append((next_x, next_y, _get_entry(
                    routing_tables, next_x, next_y, source_vertex,
                    partition_id)))
    return found_targets


def _check_edges(routing_tables, machine, placements, app_graph):
    for part in app_graph.outgoing_edge_partitions:

        # Find the required targets
        required_targets = defaultdict(set)
        for edge in part.edges:
            post = edge.post_vertex
            targets = post.splitter.get_source_specific_in_coming_vertices(
                    edge.pre_vertex, part.identifier)
            for tgt, srcs in targets:
                place = placements.get_placement_of_vertex(tgt)
                for src in srcs:
                    if isinstance(src, ApplicationVertex):
                        for m_vertex in src.splitter.get_out_going_vertices(
                                part.identifier):
                            required_targets[m_vertex].add(place.location)
                    else:
                        required_targets[src].add(place.location)

        for m_vertex in part.pre_vertex.splitter.get_out_going_vertices(
                part.identifier):
            actual_targets = _find_targets(
                routing_tables, machine, placements, m_vertex,
                part.identifier)
            assert(not actual_targets.difference(required_targets[m_vertex]))


def _route_and_time(machine, app_graph, placements):
    timer = Timer()
    with timer:
        result = route_application_graph(machine, app_graph, placements)
    print(f"Routing took {timer.measured_interval}")
    return result


def test_application_router_simple():
    unittest_setup()
    app_graph = ApplicationGraph("Test")
    source_vertex = _make_vertices(app_graph, 1000, 50, "source")
    target_vertex = _make_vertices(app_graph, 1000, 50, "target")
    app_graph.add_edge(ApplicationEdge(source_vertex, target_vertex), "Test")

    machine = virtual_machine(8, 8)
    placements = place_application_graph(machine, app_graph, 100, Placements())
    routing_tables = _route_and_time(machine, app_graph, placements)
    _check_edges(routing_tables, machine, placements, app_graph)


def test_application_router_self():
    unittest_setup()
    app_graph = ApplicationGraph("Test")
    source_vertex = _make_vertices(app_graph, 1000, 50, "self")
    app_graph.add_edge(ApplicationEdge(source_vertex, source_vertex), "Test")

    machine = virtual_machine(8, 8)
    placements = place_application_graph(machine, app_graph, 100, Placements())
    routing_tables = _route_and_time(machine, app_graph, placements)
    _check_edges(routing_tables, machine, placements, app_graph)


def test_application_router_simple_self():
    unittest_setup()
    app_graph = ApplicationGraph("Test")
    source_vertex = _make_vertices(app_graph, 1000, 50, "source")
    target_vertex = _make_vertices(app_graph, 1000, 50, "target")
    app_graph.add_edge(ApplicationEdge(source_vertex, source_vertex), "Test")
    app_graph.add_edge(ApplicationEdge(target_vertex, target_vertex), "Test")
    app_graph.add_edge(ApplicationEdge(source_vertex, target_vertex), "Test")

    machine = virtual_machine(8, 8)
    placements = place_application_graph(machine, app_graph, 100, Placements())
    routing_tables = _route_and_time(machine, app_graph, placements)
    _check_edges(routing_tables, machine, placements, app_graph)


def test_application_router_multi():
    unittest_setup()
    app_graph = ApplicationGraph("Test")
    for i in range(10):
        _make_vertices(app_graph, 1000, 50, f"app_vertex_{i}")
    for source in app_graph.vertices:
        for target in app_graph.vertices:
            if source != target:
                app_graph.add_edge(ApplicationEdge(source, target), "Test")

    machine = virtual_machine(8, 8)
    placements = place_application_graph(machine, app_graph, 100, Placements())
    routing_tables = _route_and_time(machine, app_graph, placements)
    _check_edges(routing_tables, machine, placements, app_graph)


def test_application_router_multi_self():
    unittest_setup()
    app_graph = ApplicationGraph("Test")
    for i in range(10):
        _make_vertices(app_graph, 1000, 50, f"app_vertex_{i}")
    for source in app_graph.vertices:
        for target in app_graph.vertices:
            app_graph.add_edge(ApplicationEdge(source, target), "Test")

    machine = virtual_machine(8, 8)
    placements = place_application_graph(machine, app_graph, 100, Placements())
    routing_tables = _route_and_time(machine, app_graph, placements)
    _check_edges(routing_tables, machine, placements, app_graph)


def test_application_router_multi_split():
    unittest_setup()
    app_graph = ApplicationGraph("Test")
    for i in range(10):
        _make_vertices_split(app_graph, 1000, 3, 2, 50, f"app_vertex_{i}")
    for source in app_graph.vertices:
        for target in app_graph.vertices:
            if source != target:
                app_graph.add_edge(ApplicationEdge(source, target), "Test")

    machine = virtual_machine(24, 24)
    placements = place_application_graph(machine, app_graph, 100, Placements())
    routing_tables = _route_and_time(machine, app_graph, placements)
    _check_edges(routing_tables, machine, placements, app_graph)


def test_application_router_multi_self_split():
    unittest_setup()
    app_graph = ApplicationGraph("Test")
    for i in range(10):
        _make_vertices_split(app_graph, 1000, 3, 2, 50, f"app_vertex_{i}")
    for source in app_graph.vertices:
        for target in app_graph.vertices:
            app_graph.add_edge(ApplicationEdge(source, target), "Test")

    machine = virtual_machine(24, 24)
    placements = place_application_graph(machine, app_graph, 100, Placements())
    routing_tables = _route_and_time(machine, app_graph, placements)
    _check_edges(routing_tables, machine, placements, app_graph)


def test_application_router_multi_down_chips_and_links():
    unittest_setup()
    app_graph = ApplicationGraph("Test")
    for i in range(10):
        _make_vertices(app_graph, 1000, 50, f"app_vertex_{i}")
    for source in app_graph.vertices:
        for target in app_graph.vertices:
            app_graph.add_edge(ApplicationEdge(source, target), "Test")

    machine = virtual_machine(8, 8)
    placements = place_application_graph(machine, app_graph, 100, Placements())
    routing_tables = _route_and_time(machine, app_graph, placements)

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
    for i, (x, y, entry) in enumerate(chosen_entries):
        if entry.link_ids:
            link = list(entry.link_ids)[i % len(entry.link_ids)]
            down_links += f"{x},{y},{link}:"
        else:
            down_chips += f"{x},{y}:"

    print("Down chips:", down_chips[:-1].split(":"))
    print("Down links:", down_links[:-1].split(":"))
    set_config("Machine", "down_chips", down_chips[:-1])
    set_config("Machine", "down_links", down_links[:-1])
    machine_down = virtual_machine(8, 8)
    placements = place_application_graph(
        machine_down, app_graph, 100, Placements())
    routing_tables = _route_and_time(machine_down, app_graph, placements)
    _check_edges(routing_tables, machine_down, placements, app_graph)


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
    nodes = longest_dimension_first(vector, (0, 0), machine)
    nodes_fixed = _path_without_errors((0, 0), nodes, machine)
    _check_path((0, 0), nodes_fixed, machine, (6, 6))

    vector = machine.get_vector((2, 2), (6, 6))
    nodes = longest_dimension_first(vector, (2, 2), machine)
    nodes_fixed = _path_without_errors((2, 2), nodes, machine)
    _check_path((2, 2), nodes_fixed, machine, (6, 6))

    print(nodes)
    print(nodes_fixed)
