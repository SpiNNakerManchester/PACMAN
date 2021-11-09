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
from spinn_machine.virtual_machine import virtual_machine
from pacman.config_setup import unittest_setup
from pacman.exceptions import PacmanException
from pacman.model.graphs.machine import (
    MachineGraph, SimpleMachineVertex, MachineSpiNNakerLinkVertex,
    MachineEdge, SDRAMMachineEdge)
from pacman.model.graphs.machine import ConstantSDRAMMachinePartition
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from pacman.operations.placer_algorithms import spreader_placer
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.operations.chip_id_allocator_algorithms import (
    malloc_based_chip_id_allocator)
from pacman_test_objects import MockMachineVertex


def test_virtual_vertices_spreader():
    """ Test that the placer works with a virtual vertex
    """
    unittest_setup()

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

    n_keys_map = DictBasedMachinePartitionNKeysMap()
    partition = machine_graph.get_outgoing_edge_partition_starting_at_vertex(
        virtual_vertex, "SPIKES")
    n_keys_map.set_n_keys_for_partition(partition, 1)

    # Get and extend the machine for the virtual chip
    machine = virtual_machine(width=8, height=8)
    extended_machine = malloc_based_chip_id_allocator(machine, machine_graph)

    # Do placements
    placements = spreader_placer(
        machine_graph, extended_machine, n_keys_map, plan_n_timesteps=1000)

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
    unittest_setup()

    # Create a graph
    machine_graph = MachineGraph("Test")

    # Connect a set of vertices in a chain of length 3
    n_keys_map = DictBasedMachinePartitionNKeysMap()
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
                partition = machine_graph\
                    .get_outgoing_edge_partition_starting_at_vertex(
                        last_vertex, "SPIKES")
                n_keys_map.set_n_keys_for_partition(partition, 1)
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
            partition = machine_graph\
                .get_outgoing_edge_partition_starting_at_vertex(
                    last_vertex, "SPIKES")
            n_keys_map.set_n_keys_for_partition(partition, 1)
        too_many_vertices.append(vertex)
        last_vertex = vertex

    # Do placements
    machine = virtual_machine(width=8, height=8)
    placements = spreader_placer(
        machine_graph, machine, n_keys_map, plan_n_timesteps=1000)

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
    unittest_setup()

    # Create a graph
    machine_graph = MachineGraph("Test")

    # Connect a set of vertices in a chain of length 3
    last_vertex = None
    for x in range(20):
        vertex = MockMachineVertex(
            resources=ResourceContainer(),
            label="Vertex_{}".format(x), sdram_requirement=20)
        machine_graph.add_vertex(vertex)
        last_vertex = vertex

    for vertex in machine_graph.vertices:
        machine_graph.add_outgoing_edge_partition(
            ConstantSDRAMMachinePartition(
                identifier="SDRAM", pre_vertex=vertex, label="bacon"))
        edge = SDRAMMachineEdge(vertex, last_vertex, "bacon", app_edge=None)
        machine_graph.add_edge(edge, "SDRAM")
    n_keys_map = DictBasedMachinePartitionNKeysMap()

    # Do placements
    machine = virtual_machine(width=8, height=8)
    with pytest.raises(PacmanException):
        spreader_placer(
            machine_graph, machine, n_keys_map, plan_n_timesteps=1000)
