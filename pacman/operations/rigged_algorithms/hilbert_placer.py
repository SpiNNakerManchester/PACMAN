"""A simple placing algorithm using the Hilbert space-filling curve,
translated from RIG."""

# pacman imports
from pacman.model.constraints.placer_constraints import SameChipAsConstraint
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.placements import Placement, Placements
from pacman.utilities.utility_objs import ResourceTracker
from pacman.operations.rigged_algorithms.hilbert_state import HilbertState

from spinn_utilities.progress_bar import ProgressBar

# general imports
from math import log, ceil


class HilbertPlacer(object):

    def __call__(self, machine_graph, machine):

        # check that the algorithm can handle the constraints
        self._check_constraints(machine_graph.vertices)

        # in order to test isomorphism:
        # placements_copy = Placements()
        placements = Placements()
        vertices = \
            placer_algorithm_utilities.sort_vertices_by_known_constraints(
                machine_graph.vertices)

        # Iterate over vertices and generate placements
        progress = ProgressBar(machine_graph.n_vertices,
                               "Placing graph vertices")
        resource_tracker = ResourceTracker(machine,
                                           self._generate_hilbert_chips(
                                               machine))
        vertices_on_same_chip = \
            placer_algorithm_utilities.get_same_chip_vertex_groups(
                    machine_graph.vertices)
        all_vertices_placed = set()
        for vertex in progress.over(vertices):
            if vertex not in all_vertices_placed:
                vertices_placed = self._place_vertex(
                    vertex, resource_tracker, machine,
                    # placements_copy,
                    placements,
                    vertices_on_same_chip)
                all_vertices_placed.update(vertices_placed)
        # return placements_copy
        return placements

    def _check_constraints(
            self, vertices, additional_placement_constraints=None):
        placement_constraints = {SameChipAsConstraint}
        if additional_placement_constraints is not None:
            placement_constraints.update(additional_placement_constraints)
        ResourceTracker.check_constraints(
            vertices, additional_placement_constraints=placement_constraints)

    def _hilbert_curve(self, level, angle=1, state=None):
        """Generator of points along a 2D Hilbert curve.

        This implements the L-system as described on
        `http://en.wikipedia.org/wiki/Hilbert_curve`.

        :param level: Number of levels of recursion to use in generating
            the curve. The resulting curve will be `(2**level)-1` wide/tall.
        :type level: int
        :param angle: `1` if this is the 'positive'
            expansion of the grammar and `-1` for the 'negative' expansion.
        :type angle: int
        :param state: The current state of the system in a Hilbert curve.
        :type state: \
            :py:class:`pacman.operations.rigged_algorithms.hilbert_state.py`
        """

        # Create state object first time we're called while also yielding first
        # position
        if state is None:
            state = HilbertState()
            yield state.x_pos, state.y_pos

        if level <= 0:
            return

        # Turn left
        state.change_x, state.change_y = state.change_y * -angle, \
                                         state.change_x * angle

        # Recurse negative
        for state.x_pos, state.y_pos in self._hilbert_curve(level - 1,
                                                            -angle, state):
            yield state.x_pos, state.y_pos

        # Move forward
        state.x_pos, state.y_pos = state.x_pos + state.change_x, \
                                   state.y_pos + state.change_y
        yield state.x_pos, state.y_pos

        # Turn right
        state.change_x, state.change_y = state.change_y * angle, \
                                         state.change_x * -angle

        # Recurse positive
        for state.x_pos, state.y_pos in self._hilbert_curve(level - 1,
                                                            angle, state):
            yield state.x_pos, state.y_pos

        # Move forward
        state.x_pos, state.y_pos = state.x_pos + state.change_x, \
                                   state.y_pos + state.change_y
        yield state.x_pos, state.y_pos

        # Recurse positive
        for state.x_pos, state.y_pos in self._hilbert_curve(level - 1,
                                                            angle, state):
            yield state.x_pos, state.y_pos

        # Turn right
        state.change_x, state.change_y = state.change_y * angle, \
                                         state.change_x * -angle

        # Move forward
        state.x_pos, state.y_pos = state.x_pos + state.change_x, \
                                   state.y_pos + state.change_y
        yield state.x_pos, state.y_pos

        # Recurse negative
        for state.x_pos, state.y_pos in self._hilbert_curve(level - 1,
                                                            -angle, state):
            yield state.x_pos, state.y_pos

        # Turn left
        state.change_x, state.change_y = state.change_y * -angle, \
                                         state.change_x * angle

    def _generate_hilbert_chips(self, machine):
        """A generator which iterates over a set of chips in a machine in
        a hilbert path.

        For use as a chip ordering for the sequential placer.
        """
        max_dimen = max(machine.max_chip_x, machine.max_chip_y)
        hilbert_levels = int(ceil(log(max_dimen, 2.0))) if max_dimen >= 1 \
            else 0
        for x, y in self._hilbert_curve(hilbert_levels):
            if machine.is_chip_at(x, y):
                yield x, y

    def _place_vertex(self, vertex, resource_tracker, machine, placements,
                      vertices_on_same_chip):

        vertices = vertices_on_same_chip[vertex]
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
