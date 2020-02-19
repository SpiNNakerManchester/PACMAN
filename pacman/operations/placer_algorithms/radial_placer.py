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

from collections import deque
import logging
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.constraints.placer_constraints import (
    RadialPlacementFromChipConstraint, SameChipAsConstraint)
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    get_same_chip_vertex_groups, sort_vertices_by_known_constraints)
from pacman.model.placements import Placement, Placements
from pacman.utilities.utility_objs import ResourceTracker
from pacman.exceptions import PacmanPlaceException

logger = logging.getLogger(__name__)


class RadialPlacer(object):
    """ A placement algorithm that can place a machine graph onto a\
        machine choosing chips radiating in a circle from the boot chip

    :param MachineGraph machine_graph: The machine_graph to place
    :param ~spinn_machine.Machine machine:
        The machine with respect to which to partition the application\
        graph
    :param int minimum_simtime_in_us: simtime in us to plan for
    :return: A set of placements
    :rtype: Placements
    :raise PacmanPlaceException:
        If something goes wrong with the placement
    """

    def __call__(self, machine_graph, machine, minimum_simtime_in_us):
        # check that the algorithm can handle the constraints
        self._check_constraints(machine_graph.vertices)

        placements = Placements()
        vertices = sort_vertices_by_known_constraints(machine_graph.vertices)

        # Iterate over vertices and generate placements
        progress = ProgressBar(
            machine_graph.n_vertices, "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, minimum_simtime_in_us,
            self._generate_radial_chips(machine))
        vertices_on_same_chip = get_same_chip_vertex_groups(machine_graph)
        all_vertices_placed = set()
        for vertex in progress.over(vertices):
            if vertex not in all_vertices_placed:
                vertices_placed = self._place_vertex(
                    vertex, resource_tracker, machine, placements,
                    vertices_on_same_chip)
                all_vertices_placed.update(vertices_placed)
        return placements

    def _check_constraints(
            self, vertices, additional_placement_constraints=None):
        placement_constraints = {
            RadialPlacementFromChipConstraint, SameChipAsConstraint
        }
        if additional_placement_constraints is not None:
            placement_constraints.update(additional_placement_constraints)
        ResourceTracker.check_constraints(
            vertices, additional_placement_constraints=placement_constraints)

    def _place_vertex(
            self, vertex, resource_tracker, machine, placements,
            vertices_on_same_chip):
        """
        :param MachineVertex vertex:
        :param ResourceTracker resource_tracker:
        :param ~spinn_machine.Machine machine:
        :param Placements placements:
        :param vertices_on_same_chip:
        :type vertices_on_same_chip: dict(MachineVertex, set(MachineVertex))
        :rtype: set(MachineVertex)
        """
        vertices = vertices_on_same_chip[vertex]

        # Check for the radial placement constraint
        radial_constraints = [c for v in vertices for c in v.constraints if
                              isinstance(c, RadialPlacementFromChipConstraint)]
        start_x, start_y = self._get_start(radial_constraints)
        chips = None
        if start_x is not None and start_y is not None:
            chips = self._generate_radial_chips(
                machine, resource_tracker, start_x, start_y)

        if len(vertices) > 1:
            assigned_values = \
                resource_tracker.allocate_constrained_group_resources([
                    (vert.resources_required, vert.constraints)
                    for vert in vertices
                ], chips)
            for (x, y, p, _, _), vert in zip(assigned_values, vertices):
                placement = Placement(vert, x, y, p)
                placements.add_placement(placement)
        else:
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                vertex.resources_required, vertex.constraints, chips)
            placement = Placement(vertex, x, y, p)
            placements.add_placement(placement)

        return vertices

    @staticmethod
    def _get_start(radial_constraints):
        """
        :param list(RadialPlacementFromChipConstraint) radial_constraints:
        :rtype: tuple(int,int) or tuple(None,None)
        """
        x = None
        y = None
        for constraint in radial_constraints:
            if x is None:
                x = constraint.x
            elif x != constraint.x:
                raise PacmanPlaceException("Non-matching constraints")
            if y is None:
                y = constraint.y
            elif y != constraint.y:
                raise PacmanPlaceException("Non-matching constraints")
        return x, y

    @staticmethod
    def _generate_radial_chips(
            machine, resource_tracker=None, start_chip_x=None,
            start_chip_y=None):
        """ Generates the list of chips from a given starting point in a radial\
            format.

        :param ~spinn_machine.Machine machine: the SpiNNaker machine object
        :param resource_tracker:
            the resource tracker object which contains what resources of the
            machine have currently been used
        :type resource_tracker: ResourceTracker or None
        :param start_chip_x:
            The chip x coordinate to start with for radial iteration
        :type start_chip_x: int or None
        :param start_chip_y:
            the chip y coordinate to start with for radial iteration
        :type start_chip_y: int or None
        :return: list of chips.
        :rtype: iterable(tuple(int,int))
        """

        if start_chip_x is None or start_chip_y is None:
            first_chip = machine.boot_chip
        else:
            first_chip = machine.get_chip_at(start_chip_x, start_chip_y)
        done_chips = {first_chip}
        search = deque([first_chip])
        while search:
            chip = search.pop()
            if (resource_tracker is None or
                    resource_tracker.is_chip_available(chip.x, chip.y)):
                yield chip.x, chip.y

            # Examine the links of the chip to find the next chips
            for link in chip.router.links:
                next_chip = machine.get_chip_at(
                    link.destination_x, link.destination_y)

                # Don't search done chips again
                if next_chip not in done_chips:
                    search.appendleft(next_chip)
                    done_chips.add(next_chip)
