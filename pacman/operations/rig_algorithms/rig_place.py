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

from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.rig_converters import (
    convert_from_rig_placements, convert_to_rig_graph, convert_to_rig_machine,
    create_rig_graph_constraints, create_rig_machine_constraints)
from rig.place_and_route.place.sa import place
from rig.place_and_route.allocate.greedy import allocate


class RigPlace(object):
    """ Performs placement and routing using rig algorithms; both are done\
        to save conversion time
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, plan_n_timesteps):
        progress_bar = ProgressBar(7, "Placing")

        vertices_resources, nets, _ = \
            convert_to_rig_graph(machine_graph, plan_n_timesteps)
        progress_bar.update()

        rig_machine = convert_to_rig_machine(machine)
        progress_bar.update()

        rig_constraints = create_rig_machine_constraints(machine)
        progress_bar.update()

        rig_constraints.extend(create_rig_graph_constraints(
            machine_graph, rig_machine))
        progress_bar.update()

        rig_placements = place(
            vertices_resources, nets, rig_machine, rig_constraints)
        progress_bar.update()

        rig_allocations = allocate(
            vertices_resources, nets, rig_machine, rig_constraints,
            rig_placements)
        progress_bar.update()

        placements = convert_from_rig_placements(
            rig_placements, rig_allocations, machine_graph)
        progress_bar.update()
        progress_bar.end()

        return placements
