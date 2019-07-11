import pytest

from pacman.operations.placer_algorithms import (
    OneToOnePlacer, BasicPlacer, RadialPlacer, SpreaderPlacer)
from pacman.model.graphs.machine import (
    MachineGraph, MachineSpiNNakerLinkVertex)
from pacman.operations.chip_id_allocator_algorithms import (
    MallocBasedChipIdAllocator)
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.executor import PACMANAlgorithmExecutor

from spinn_machine import virtual_machine


@pytest.mark.parametrize(
    "placer",
    ["OneToOnePlacer", "BasicPlacer", "RadialPlacer", "SpreaderPlacer"])
def test_virtual_placement(placer):
    machine = virtual_machine(version=5)
    graph = MachineGraph("Test")
    virtual_vertex = MachineSpiNNakerLinkVertex(spinnaker_link_id=0)
    graph.add_vertex(virtual_vertex)
    extended_machine = MallocBasedChipIdAllocator()(machine, graph)
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    inputs = {
        "MemoryExtendedMachine": machine,
        "MemoryMachine": machine,
        "MemoryMachineGraph": graph,
        "PlanNTimeSteps": 1000,
        "MemoryMachinePartitionNKeysMap": n_keys_map
    }
    algorithms = [placer]
    xml_paths = []
    executor = PACMANAlgorithmExecutor(
        algorithms, [], inputs, [], [], [], xml_paths)
    executor.execute_mapping()
    placements = executor.get_item("MemoryPlacements")

    placement = placements.get_placement_of_vertex(virtual_vertex)
    chip = extended_machine.get_chip_at(placement.x, placement.y)
    assert chip.virtual
