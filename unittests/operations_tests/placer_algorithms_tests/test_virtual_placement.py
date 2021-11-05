# Copyright (c) 2017-2019 The University of Manchester
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

import pytest
from spinn_machine import virtual_machine
from pacman.config_setup import unittest_setup
from pacman.model.graphs.machine import (
    MachineGraph, MachineSpiNNakerLinkVertex)
from pacman.operations.chip_id_allocator_algorithms import (
    malloc_based_chip_id_allocator)
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.operations.placer_algorithms import (
    connective_based_placer, OneToOnePlacer, radial_placer, SpreaderPlacer)


@pytest.mark.parametrize(
    "placer",
    ["ConnectiveBasedPlacer", "OneToOnePlacer", "RadialPlacer",
     "SpreaderPlacer"])
def test_virtual_placement(placer):
    unittest_setup()
    machine = virtual_machine(width=8, height=8)
    graph = MachineGraph("Test")
    virtual_vertex = MachineSpiNNakerLinkVertex(spinnaker_link_id=0)
    graph.add_vertex(virtual_vertex)
    extended_machine = malloc_based_chip_id_allocator(machine, graph)
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    if placer == "ConnectiveBasedPlacer":
        placer = connective_based_placer()
        placements = placer(graph, machine, None)
    elif placer == "OneToOnePlacer":
        placer = OneToOnePlacer()
        placements = placer(graph, machine, None)
    elif placer == "RadialPlacer":
        placer = radial_placer()
        placements = placer(graph, machine, None)
    elif placer == "SpreaderPlacer":
        placer = SpreaderPlacer()
        placements = placer(graph, machine, n_keys_map, None)
    else:
        raise NotImplementedError(placer)

    placement = placements.get_placement_of_vertex(virtual_vertex)
    chip = extended_machine.get_chip_at(placement.x, placement.y)
    assert chip.virtual
