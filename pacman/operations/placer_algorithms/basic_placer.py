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

import logging
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    sort_vertices_by_known_constraints)
from pacman.model.placements import Placement, Placements
from pacman.utilities.utility_objs import ResourceTracker

logger = logging.getLogger(__name__)


class BasicPlacer(object):
    """ A basic placement algorithm that can place a machine graph onto a
        machine using the chips as they appear in the machine.

    :param MachineGraph machine_graph: The machine_graph to place
    :param ~spinn_machine.Machine machine:
        The machine with respect to which to partition the application graph
    :param int plan_n_timesteps: number of timesteps to plan for
    :return: A set of placements
    :rtype: Placements
    :raise PacmanPlaceException: If something goes wrong with the placement
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, plan_n_timesteps):
        # check that the algorithm can handle the constraints
        ResourceTracker.check_constraints(machine_graph.vertices)

        placements = Placements()
        vertices = sort_vertices_by_known_constraints(machine_graph.vertices)

        # Iterate over vertices and generate placements
        progress = ProgressBar(vertices, "Placing graph vertices")
        resource_tracker = ResourceTracker(machine, plan_n_timesteps)
        for vertex in progress.over(vertices):
            # Create and store a new placement anywhere on the board
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                vertex.resources_required, vertex.constraints, None)
            placement = Placement(vertex, x, y, p)
            placements.add_placement(placement)
        return placements
