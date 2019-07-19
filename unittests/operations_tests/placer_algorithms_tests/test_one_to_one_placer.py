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

from pacman.exceptions import PacmanException
from pacman.model.graphs.common import EdgeTrafficType
from spinn_machine.virtual_machine import virtual_machine
from pacman.model.graphs.machine import (
    MachineGraph, SimpleMachineVertex, MachineSpiNNakerLinkVertex, MachineEdge)
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from pacman.operations.chip_id_allocator_algorithms import (
    MallocBasedChipIdAllocator)
from pacman.operations.placer_algorithms import OneToOnePlacer


def test_virtual_vertices_one_to_one():
    """ Test that the placer works with a virtual vertex
    """

    # Create a graph with a virtual vertex
    machine_graph = MachineGraph("Test")
    virtual_vertex = MachineSpiNNakerLinkVertex(
        spinnaker_link_id=0, label="Virtual")
    machine_graph.add_vertex(virtual_vertex)

    # These vertices are fixed on 0, 0
    misc_vertices = list()
    for i in range(3):
        misc_vertex = SimpleMachineVertex(
            resources=ResourceContainer(), constraints=[
                ChipAndCoreConstraint(0, 0)],
            label="Fixed_0_0_{}".format(i))
        machine_graph.add_vertex(misc_vertex)
        misc_vertices.append(misc_vertex)

    # These vertices are 1-1 connected to the virtual vertex
    one_to_one_vertices = list()
    for i in range(16):
        one_to_one_vertex = SimpleMachineVertex(
            resources=ResourceContainer(),
            label="Vertex_{}".format(i))
        machine_graph.add_vertex(one_to_one_vertex)
        edge = MachineEdge(virtual_vertex, one_to_one_vertex)
        machine_graph.add_edge(edge, "SPIKES")
        one_to_one_vertices.append(one_to_one_vertex)

    # Get and extend the machine for the virtual chip
    machine = virtual_machine(version=5)
    extended_machine = MallocBasedChipIdAllocator()(machine, machine_graph)

    # Do placements
    placements = OneToOnePlacer()(
        machine_graph, extended_machine, plan_n_timesteps=1000)

    # The virtual vertex should be on a virtual chip
    placement = placements.get_placement_of_vertex(virtual_vertex)
    assert machine.get_chip_at(placement.x, placement.y).virtual

    # The 0, 0 vertices should be on 0, 0
    for vertex in misc_vertices:
        placement = placements.get_placement_of_vertex(vertex)
        assert placement.x == placement.y == 0

    # The other vertices should *not* be on a virtual chip
    for vertex in one_to_one_vertices:
        placement = placements.get_placement_of_vertex(vertex)
        assert not machine.get_chip_at(placement.x, placement.y).virtual


def test_one_to_one():
    """ Test normal 1-1 placement
    """

    # Create a graph
    machine_graph = MachineGraph("Test")

    # Connect a set of vertices in a chain of length 3
    one_to_one_chains = list()
    for i in range(10):
        last_vertex = None
        chain = list()
        for j in range(3):
            vertex = SimpleMachineVertex(
                resources=ResourceContainer(),
                label="Vertex_{}_{}".format(i, j))
            machine_graph.add_vertex(vertex)
            if last_vertex is not None:
                edge = MachineEdge(last_vertex, vertex)
                machine_graph.add_edge(edge, "SPIKES")
            last_vertex = vertex
            chain.append(vertex)
        one_to_one_chains.append(chain)

    # Connect a set of 20 vertices in a chain
    too_many_vertices = list()
    last_vertex = None
    for i in range(20):
        vertex = SimpleMachineVertex(
            resources=ResourceContainer(), label="Vertex_{}".format(i))
        machine_graph.add_vertex(vertex)
        if last_vertex is not None:
            edge = MachineEdge(last_vertex, vertex)
            machine_graph.add_edge(edge, "SPIKES")
        too_many_vertices.append(vertex)
        last_vertex = vertex

    # Do placements
    machine = virtual_machine(version=5)
    placements = OneToOnePlacer()(
        machine_graph, machine, plan_n_timesteps=1000)

    # The 1-1 connected vertices should be on the same chip
    for chain in one_to_one_chains:
        first_placement = placements.get_placement_of_vertex(chain[0])
        for i in range(1, 3):
            placement = placements.get_placement_of_vertex(chain[i])
            assert placement.x == first_placement.x
            assert placement.y == first_placement.y

    # The other vertices should be on more than one chip
    too_many_chips = set()
    for vertex in too_many_vertices:
        placement = placements.get_placement_of_vertex(vertex)
        too_many_chips.add((placement.x, placement.y))
    assert len(too_many_chips) > 1


def test_sdram_links():
    """ Test sdram edges which should explode
        """

    # Create a graph
    machine_graph = MachineGraph("Test")

    # Connect a set of vertices in a chain of length 3
    last_vertex = None
    for x in range(20):
        vertex = SimpleMachineVertex(
            resources=ResourceContainer(),
            label="Vertex_{}".format(x))
        machine_graph.add_vertex(vertex)
        last_vertex = vertex

    for vertex in machine_graph.vertices:
        edge = MachineEdge(vertex, last_vertex,
                           traffic_type=EdgeTrafficType.SDRAM)
        machine_graph.add_edge(edge, "SDRAM")

    # Do placements
    machine = virtual_machine(version=5)
    try:
        OneToOnePlacer()(machine_graph, machine, plan_n_timesteps=1000)
        raise Exception("should blow up here")
    except PacmanException:
        pass
