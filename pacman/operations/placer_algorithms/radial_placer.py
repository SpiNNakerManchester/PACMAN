
# pacman imports
from pacman.model.constraints.placer_constraints.\
    placer_radial_placement_from_chip_constraint \
    import PlacerRadialPlacementFromChipConstraint
from pacman.model.constraints.placer_constraints\
    .placer_same_chip_as_constraint\
    import PlacerSameChipAsConstraint
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.placements.placements import Placements
from pacman.model.placements.placement import Placement
from pacman.utilities import utility_calls
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker
from pacman.exceptions import PacmanPlaceException

from spinn_machine.utilities.progress_bar import ProgressBar
from spinn_machine.utilities.ordered_set import OrderedSet

# general imports
from collections import deque
import logging


logger = logging.getLogger(__name__)


class RadialPlacer(object):
    """ A placement algorithm that can place a machine graph onto a\
        machine choosing chips radiating in a circle from the boot chip
    """

    def __call__(self, machine_graph, machine):

        # check that the algorithm can handle the constraints
        self._check_constraints(machine_graph.vertices)

        placements = Placements()
        vertices = \
            placer_algorithm_utilities.sort_vertices_by_known_constraints(
                machine_graph.vertices)

        # Iterate over vertices and generate placements
        progress_bar = ProgressBar(len(vertices), "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, self._generate_radial_chips(machine))
        vertices_on_same_chip = placer_algorithm_utilities\
            .get_same_chip_vertex_groups(machine_graph.vertices)
        all_vertices_placed = set()
        for vertex in vertices:
            if vertex not in all_vertices_placed:
                vertices_placed = self._place_vertex(
                    vertex, resource_tracker, machine, placements,
                    vertices_on_same_chip)
                all_vertices_placed.update(vertices_placed)
            progress_bar.update()
        progress_bar.end()
        return placements

    def _check_constraints(
            self, vertices, additional_placement_constraints=None):
        placement_constraints = {
            PlacerRadialPlacementFromChipConstraint, PlacerSameChipAsConstraint
        }
        if additional_placement_constraints is not None:
            placement_constraints.update(additional_placement_constraints)
        ResourceTracker.check_constraints(
            vertices, additional_placement_constraints=placement_constraints)

    def _place_vertex(
            self, vertex, resource_tracker, machine, placements,
            vertices_on_same_chip):

        vertices = vertices_on_same_chip[vertex]

        # Check for the radial placement constraint
        radial_constraints = utility_calls.locate_constraints_of_type(
            vertices, PlacerRadialPlacementFromChipConstraint)
        start_x = None
        start_y = None
        for constraint in radial_constraints:
            if start_x is None:
                start_x = constraint.x
            elif start_x != constraint.x:
                raise PacmanPlaceException("Non-matching constraints")
            if start_y is None:
                start_y = constraint.y
            elif start_y != constraint.y:
                raise PacmanPlaceException("Non-matching constraints")
        chips = None
        if start_x is not None and start_y is not None:
            chips = self._generate_radial_chips(
                machine, resource_tracker, start_x, start_y)

        if len(vertices) > 1:
            assigned_values = \
                resource_tracker.allocate_constrained_group_resources([
                    (vert.resources_required, vert.constraints)
                    for vert in vertices
                ])
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
    def _generate_radial_chips(
            machine, resource_tracker=None, start_chip_x=None,
            start_chip_y=None):
        """ Generates the list of chips from a given starting point in a radial\
            format.

        :param machine: the spinnaker machine object
        :param resource_tracker:\
            the resource tracker object which contains what resources of the\
            machine have currently been used
        :param start_chip_x:\
            The chip x coordinate to start with for radial iteration
        :param start_chip_y:\
            the chip y coordinate to start with for radial iteration
        :return: list of chips.
        """

        if start_chip_x is None or start_chip_y is None:
            first_chip = machine.boot_chip
        else:
            first_chip = machine.get_chip_at(start_chip_x, start_chip_y)
        done_chips = {first_chip}
        found_chips = OrderedSet([(first_chip.x, first_chip.y)])
        search = deque([first_chip])
        while len(search) > 0:
            chip = search.pop()
            if (resource_tracker is None or
                    resource_tracker.is_chip_available(chip.x, chip.y)):
                found_chips.add((chip.x, chip.y))

            # Examine the links of the chip to find the next chips
            for link in chip.router.links:
                next_chip = machine.get_chip_at(link.destination_x,
                                                link.destination_y)

                # Don't search done chips again
                if next_chip not in done_chips:
                    search.appendleft(next_chip)
                    done_chips.add(next_chip)
        return found_chips
