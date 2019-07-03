import pytest

from pacman.operations.placer_algorithms import (
    OneToOnePlacer, BasicPlacer, RadialPlacer)
from pacman.model.graphs.machine import (
    MachineGraph, MachineSpiNNakerLinkVertex)
from pacman.operations.chip_id_allocator_algorithms import (
    MallocBasedChipIdAllocator)

from spinn_machine import virtual_machine


@pytest.mark.parametrize(
    "placer", [OneToOnePlacer(), BasicPlacer(), RadialPlacer()])
def test_virtual_placement(placer):
    machine = virtual_machine(version=5)
    graph = MachineGraph("Test")
    virtual_vertex = MachineSpiNNakerLinkVertex(spinnaker_link_id=0)
    graph.add_vertex(virtual_vertex)
    extended_machine = MallocBasedChipIdAllocator()(machine, graph)
    placements = placer(graph, extended_machine, plan_n_timesteps=1000)

    placement = placements.get_placement_of_vertex(virtual_vertex)
    chip = extended_machine.get_chip_at(placement.x, placement.y)
    assert chip.virtual
