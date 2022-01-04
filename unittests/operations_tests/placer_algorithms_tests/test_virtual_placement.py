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
from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.graphs.machine import (
    MachineGraph, MachineSpiNNakerLinkVertex)
from pacman.operations.chip_id_allocator_algorithms import (
    malloc_based_chip_id_allocator)
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.operations.placer_algorithms import (
    connective_based_placer, one_to_one_placer, radial_placer, spreader_placer)


@pytest.mark.parametrize(
    "placer",
    ["ConnectiveBasedPlacer", "OneToOnePlacer", "RadialPlacer",
     "SpreaderPlacer"])
def test_virtual_placement(placer):
    unittest_setup()
    #PacmanDataWriter().set_machine(machine)
    graph = MachineGraph("Test")
    virtual_vertex = MachineSpiNNakerLinkVertex(spinnaker_link_id=0)
    graph.add_vertex(virtual_vertex)
    PacmanDataWriter().set_runtime_machine_graph(graph)
    malloc_based_chip_id_allocator()
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    if placer == "ConnectiveBasedPlacer":
        placements = connective_based_placer(None)
    elif placer == "OneToOnePlacer":
        placements = one_to_one_placer(None)
    elif placer == "RadialPlacer":
        placements = radial_placer(None)
    elif placer == "SpreaderPlacer":
        placements = spreader_placer(n_keys_map, None)
    else:
        raise NotImplementedError(placer)

    placement = placements.get_placement_of_vertex(virtual_vertex)
    chip = PacmanDataWriter().get_chip_at(placement.x, placement.y)
    assert chip.virtual
