"""A simple placing algorithm using the Hilbert space-filing curve,
translated from RIG."""

# pacman imports
from pacman.model.constraints.placer_constraints import SameChipAsConstraint
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.placements import Placement, Placements
from pacman.utilities.utility_calls import locate_constraints_of_type
from pacman.utilities.utility_objs import ResourceTracker
from pacman.exceptions import PacmanPlaceException
from pacman.operations.rigged_algorithms.hilbert_state import HilbertState


from spinn_utilities.progress_bar import ProgressBar

#general imports
from math import log, ceil
import logging


logger = logging.getLogger(__name__)

class HilbertPlacer(object):

    def __call__(self, machine_graph, machine):
        self._check_constraints(machine_graph.vertices)

        placements = Placements()
        vertices = \
            placer_algorithm_utilities.sort_vertices_by_known_constraints(
                machine_graph.vertices)

        # Iterate over vertices and generate placements
        progress = ProgressBar(machine_graph.n_vertices,
                               "Placing graph vertices")
        resource_tracker = ResourceTracker(machine,
                                self._generate_hilbert_chips(machine))
        vertices_on_same_chip = \
            placer_algorithm_utilities.get_same_chip_vertex_groups(
                    machine_graph.vertices)
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
        placement_constraints = {SameChipAsConstraint}
        if additional_placement_constraints is not None:
            placement_constraints.update(additional_placement_constraints)
        ResourceTracker.check_constraints(
            vertices, additional_placement_constraints=placement_constraints)

    def _hilbert_curve(self, level, angle=1, s=None):
        """Generator of points along a 2D Hilbert curve.

        This implements the L-system as described on
        `http://en.wikipedia.org/wiki/Hilbert_curve`.

        Parameters
        ----------
        level : int
            Number of levels of recursion to use in generating the curve. The
            resulting curve will be `(2**level)-1` wide/tall.
        angle : int
            **For internal use only.** `1` if this is the 'positive' expansion of
            the grammar and `-1` for the 'negative' expansion.
        s : HilbertState
            **For internal use only.** The current state of the system.
        """

        # Create state object first time we're called while also yielding first
        # position
        if s is None:
            s = HilbertState()
            yield s.x, s.y

        if level <= 0:
            return

        # Turn left
        s.dx, s.dy = s.dy * -angle, s.dx * angle

        # Recurse negative
        for s.x, s.y in self._hilbert_curve(level - 1, -angle, s):
            yield s.x, s.y

        # Move forward
        s.x, s.y = s.x + s.dx, s.y + s.dy
        yield s.x, s.y

        # Turn right
        s.dx, s.dy = s.dy * angle, s.dx * -angle

        # Recurse positive
        for s.x, s.y in self._hilbert_curve(level - 1, angle, s):
            yield s.x, s.y

        # Move forward
        s.x, s.y = s.x + s.dx, s.y + s.dy
        yield s.x, s.y

        # Recurse positive
        for s.x, s.y in self._hilbert_curve(level - 1, angle, s):
            yield s.x, s.y

        # Turn right
        s.dx, s.dy = s.dy * angle, s.dx * -angle

        # Move forward
        s.x, s.y = s.x + s.dx, s.y + s.dy
        yield s.x, s.y

        # Recurse negative
        for s.x, s.y in self._hilbert_curve(level - 1, -angle, s):
            yield s.x, s.y

        # Turn left
        s.dx, s.dy = s.dy * -angle, s.dx * angle

    def _generate_hilbert_chips(self, machine):
        """A generator which iterates over a set of chips in a machine in
        a hilbert path.

        For use as a chip ordering for the sequential placer.
        """
        max_dimen = max(machine.max_chip_x, machine.max_chip_y)
        hilbert_levels = int(ceil(log(max_dimen, 2.0))) if max_dimen >= 1 \
            else 0
        return self._hilbert_curve(hilbert_levels)

    def _place_vertex(self, vertex, resource_tracker, machine, placements,
            vertices_on_same_chip):

        vertices = vertices_on_same_chip[vertex]

        # Check for placement constraints
        hilbert_constraints = locate_constraints_of_type(
            vertices, SameChipAsConstraint)
        for constraint in hilbert_constraints:
            if isinstance(constraint):
                raise PacmanPlaceException("Non-matching constraints")
        chips = self._generate_hilbert_chips(machine)

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

