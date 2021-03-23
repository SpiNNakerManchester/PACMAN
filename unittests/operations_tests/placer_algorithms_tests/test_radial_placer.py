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

import unittest
from spinn_machine import virtual_machine
from pacman.model.graphs.machine import MachineGraph
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from pacman.exceptions import PacmanValueError
from pacman.model.constraints.placer_constraints import (
    ChipAndCoreConstraint, RadialPlacementFromChipConstraint)
from pacman.operations.placer_algorithms import RadialPlacer
from pacman_test_objects import (
    get_resources_used_by_atoms, T_MachineVertex,)


class TestRadialPlacer(unittest.TestCase):
    def setUp(self):

        self.machine = virtual_machine(8, 8)
        self.mach_graph = MachineGraph("machine")
        self.vertices = list()
        self.vertex1 = T_MachineVertex(
            0, 1, get_resources_used_by_atoms(0, 1, []), "First vertex")
        self.vertex2 = T_MachineVertex(
            1, 5, get_resources_used_by_atoms(1, 5, []), "Second vertex")
        self.vertex3 = T_MachineVertex(
            5, 10, get_resources_used_by_atoms(5, 10, []), "Third vertex")
        self.vertex4 = T_MachineVertex(
            10, 100, get_resources_used_by_atoms(10, 100, []),
            "Fourth vertex")
        self.vertices.append(self.vertex1)
        self.mach_graph.add_vertex(self.vertex1)
        self.vertices.append(self.vertex2)
        self.mach_graph.add_vertex(self.vertex2)
        self.vertices.append(self.vertex3)
        self.mach_graph.add_vertex(self.vertex3)
        self.vertices.append(self.vertex4)
        self.mach_graph.add_vertex(self.vertex4)
        self.edges = list()

        self.plan_n_timesteps = 100

    def test_simple(self):
        placements = RadialPlacer()(self.mach_graph, self.machine, 100)
        self.assertEqual(len(self.vertices), len(placements))

    def test_place_vertex_too_big_with_vertex(self):
        cpu_cycles = 1000
        dtcm_requirement = 1000
        sdram_requirement = self.machine.get_chip_at(0, 0).sdram.size * 20
        rc = ResourceContainer(
            cpu_cycles=CPUCyclesPerTickResource(cpu_cycles),
            dtcm=DTCMResource(dtcm_requirement),
            sdram=ConstantSDRAM(sdram_requirement))

        large_machine_vertex = T_MachineVertex(
            0, 499, rc, "Second vertex")
        self.mach_graph.add_vertex(large_machine_vertex)
        with self.assertRaises(PacmanValueError):
            RadialPlacer()(self.mach_graph, self.machine, 100)

    def test_deal_with_constraint_placement_vertices_dont_have_vertex(self):
        self.vertex2.add_constraint(ChipAndCoreConstraint(3, 5, 7))
        self.vertex3.add_constraint(RadialPlacementFromChipConstraint(2, 4))
        placements = RadialPlacer()(self.mach_graph, self.machine, 100)
        for placement in placements.placements:
            if placement.vertex == self.vertex2:
                self.assertEqual(placement.x, 3)
                self.assertEqual(placement.y, 5)
                self.assertEqual(placement.p, 7)
            if placement.vertex == self.vertex3:
                self.assertEqual(placement.x, 2)
                self.assertEqual(placement.y, 4)
        self.assertEqual(len(self.vertices), len(placements))

    def test_fill_machine(self):
        graph = MachineGraph("machine")
        cores = sum(chip.n_user_processors for chip in self.machine.chips)
        for i in range(cores):  # 50 atoms per each processor on 20 chips
            graph.add_vertex(T_MachineVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "vertex " + str(i)))
        placements = RadialPlacer()(graph, self.machine, 100)
        self.assertEqual(len(placements), cores)
        # One more vertex should be too many
        graph.add_vertex(T_MachineVertex(
            0, 50, get_resources_used_by_atoms(0, 50, []), "toomany"))
        with self.assertRaises(PacmanValueError):
            RadialPlacer()(graph, self.machine, 100)


if __name__ == '__main__':
    unittest.main()
