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
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.graphs.machine import (
    MachineGraph, MachineEdge, SimpleMachineVertex)
from pacman.model.placements import Placement, Placements
from pacman.operations.router_algorithms.ner_route import ner_route


def test_ner_route_default():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    graph = MachineGraph("Test")
    placements = Placements()

    source_vertex = SimpleMachineVertex(None)
    graph.add_vertex(source_vertex)
    placements.add_placement(Placement(source_vertex, 0, 0, 1))
    target_vertex = SimpleMachineVertex(None)
    graph.add_vertex(target_vertex)
    placements.add_placement(Placement(target_vertex, 0, 2, 1))
    edge = MachineEdge(source_vertex, target_vertex)
    graph.add_edge(edge, "Test")
    partition = graph.get_outgoing_partition_for_edge(edge)

    writer.set_runtime_machine_graph(graph)
    writer.set_placements(placements)
    routes = ner_route()

    source_route = routes.get_entries_for_router(0, 0)[partition]
    assert(not source_route.defaultable)
    mid_route = routes.get_entries_for_router(0, 1)[partition]
    print(mid_route.incoming_link, mid_route.link_ids)
    assert(mid_route.defaultable)
    end_route = routes.get_entries_for_router(0, 2)[partition]
    assert(not end_route.defaultable)
