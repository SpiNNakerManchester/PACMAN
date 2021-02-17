from pacman.model.graphs.machine import (
    MachineGraph, MachineEdge, SimpleMachineVertex)
from spinn_machine import virtual_machine
from pacman.model.placements import Placement, Placements
from pacman.operations.router_algorithms.ner_route import NerRoute


def test_ner_route_default():
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
    partition = graph.get_outgoing_partition_for_edge(edge)

    router = NerRoute()
    routes = router.__call__(graph, machine, placements)

    source_route = routes.get_entries_for_router(0, 0)[partition]
    assert(not source_route.defaultable)
    mid_route = routes.get_entries_for_router(0, 1)[partition]
    print(mid_route.incoming_link, mid_route.link_ids)
    assert(mid_route.defaultable)
    end_route = routes.get_entries_for_router(0, 2)[partition]
    assert(not end_route.defaultable)
