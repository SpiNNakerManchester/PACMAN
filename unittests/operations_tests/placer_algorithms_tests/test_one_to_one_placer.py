from spinn_machine.virtual_machine import VirtualMachine

from pacman.model.graphs.machine import (
    MachineGraph, SimpleMachineVertex, MachineSpiNNakerLinkVertex, MachineEdge)
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.operations.chip_id_allocator_algorithms \
    import MallocBasedChipIdAllocator
from pacman.operations.placer_algorithms import OneToOnePlacer


def test_virtual_vertices_one_to_one():
    machine_graph = MachineGraph("Test")
    virtual_vertex = MachineSpiNNakerLinkVertex(spinnaker_link_id=0)
    machine_graph.add_vertex(virtual_vertex)
    for _ in range(3):
        misc_vertex = SimpleMachineVertex(
            resources=ResourceContainer(), constraints=[
                ChipAndCoreConstraint(0, 0)])
        machine_graph.add_vertex(misc_vertex)
    for _ in range(16):
        one_to_one_vertex = SimpleMachineVertex(
            resources=ResourceContainer(sdram=SDRAMResource(10)))
        machine_graph.add_vertex(one_to_one_vertex)
        edge = MachineEdge(virtual_vertex, one_to_one_vertex)
        machine_graph.add_edge(edge, "SPIKES")

    machine = VirtualMachine(version=5)
    extended_machine = MallocBasedChipIdAllocator()(machine, machine_graph)

    placements = OneToOnePlacer()(machine_graph, extended_machine)
