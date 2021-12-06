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
from pacman.config_setup import unittest_setup
from pacman.model.graphs.machine import (
    MachineGraph, MachineEdge, SimpleMachineVertex)
from spinn_machine import virtual_machine
from pacman.model.placements import Placement, Placements
from pacman.operations.router_algorithms.ner_route import ner_route


def test_ner_route_default():
    unittest_setup()
    graph = MachineGraph("Test")
    machine = virtual_machine(8, 8)
    placements = Placements()

    source_vertex = SimpleMachineVertex(None)
    graph.add_vertex(source_vertex)
    placements.add_placement(Placement(source_vertex, 0, 0, 1))
    target_vertex = SimpleMachineVertex(None)
    graph.add_vertex(target_vertex)
    placements.add_placement(Placement(target_vertex, 0, 2, 1))
    edge = MachineEdge(source_vertex, target_vertex)
    graph.add_edge(edge, "Test")
    partition = graph.get_outgoing_edge_partition_starting_at_vertex(
        source_vertex, "Test")

    routes = ner_route(graph, machine, placements)

    source_route = routes.get_entries_for_router(0, 0)[
        partition.pre_vertex, partition.identifier]
    assert(not source_route.defaultable)
    mid_route = routes.get_entries_for_router(0, 1)[
        partition.pre_vertex, partition.identifier]
    print(mid_route.incoming_link, mid_route.link_ids)
    assert(mid_route.defaultable)
    end_route = routes.get_entries_for_router(0, 2)[
        partition.pre_vertex, partition.identifier]
    assert(not end_route.defaultable)
