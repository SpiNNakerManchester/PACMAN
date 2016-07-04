
# pacman imports
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint \
    import TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_reverse_iptag_constraint \
    import TagAllocatorRequireReverseIptagConstraint
from pacman.model.constraints.placer_constraints.\
    placer_radial_placement_from_chip_constraint \
    import PlacerRadialPlacementFromChipConstraint
from pacman.model.constraints.abstract_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint
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
    """ A placement algorithm that can place a partitioned graph onto a
        machine choosing chips radiating in a circle from 0, 0
    """

    def __call__(self, partitioned_graph, machine):

        # check that the algorithm can handle the constraints
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=partitioned_graph.subvertices,
            supported_constraints=[
                PlacerRadialPlacementFromChipConstraint,
                TagAllocatorRequireIptagConstraint,
                TagAllocatorRequireReverseIptagConstraint,
                PlacerChipAndCoreConstraint],
            abstract_constraint_type=AbstractPlacerConstraint)

        placements = Placements()
        ordered_subverts = utility_calls.sort_objects_by_constraint_authority(
            partitioned_graph.subvertices)

        # Iterate over subvertices and generate placements
        progress_bar = ProgressBar(len(ordered_subverts),
                                   "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, self._generate_radial_chips(machine))
        for vertex in ordered_subverts:
            self._place_vertex(vertex, resource_tracker, machine, placements)
            progress_bar.update()
        progress_bar.end()
        return {'placements': placements}

    def _place_vertex(self, vertex, resource_tracker, machine, placements):

        # Check for the radial placement constraint
        radial_constraints = utility_calls.locate_constraints_of_type(
            [vertex], PlacerRadialPlacementFromChipConstraint)
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
            chips = self._generate_radial_chips(machine, resource_tracker,
                                                start_x, start_y)

        # Create and store a new placement
        (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
            vertex.resources_required, vertex.constraints, chips)
        placement = Placement(vertex, x, y, p)
        placements.add_placement(placement)

    @staticmethod
    def _generate_radial_chips(
            machine, resource_tracker=None, start_chip_x=None,
            start_chip_y=None):
        """ Generates the list of chips from a given starting point in a radial
         format.

        :param machine: the spinnaker machine object
        :param resource_tracker:
        the resource tracker object which contains what resoruces of the
        machine have currently been used
        :param start_chip_x: The chip x coordinate to start with for
        radial iteration
        :param start_chip_y: the chip y coordinate to start with for radial
        iteration
        :return: list of chips.
        """

        if start_chip_x is None or start_chip_y is None:
            first_chip = machine.boot_chip
        else:
            first_chip = machine.get_chip_at(start_chip_x, start_chip_y)
        done_chips = set([first_chip])
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
