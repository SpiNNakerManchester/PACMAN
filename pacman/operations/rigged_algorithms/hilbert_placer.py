# pacman imports
from pacman.model.constraints.placer_constraints import SameChipAsConstraint
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.placements import Placement, Placements
from pacman.utilities.utility_objs import ResourceTracker
from pacman.operations.rigged_algorithms.hilbert_state import HilbertState

# spinn_utils imports
from spinn_utilities.progress_bar import ProgressBar

# general imports
from math import log, ceil
import logging

logger = logging.getLogger(__name__)


class HilbertPlacer(object):
    """A simple placing algorithm using the Hilbert space-filling curve,
    translated from RIG."""

    def __call__(self, machine_graph, machine):
        """ Place each vertex in a machine graph on a core in the machine.

        :param machine_graph: The machine_graph to place
        :type machine_graph:\
            :py:class:`pacman.model.graph.machine.machine_graph.MachineGraph`
        :param machine: A SpiNNaker machine object.
        :type machine: :py:class:`SpiNNMachine.spinn_machine.machine.Machine`
        :return placements: Placements of vertices on the machine
        :rtype :py:class:`pacman.model.placements.placements.Placements`
        """

        # check that the algorithm can handle the constraints
        self._check_constraints(
            machine_graph.vertices,
            additional_placement_constraints={SameChipAsConstraint})

        # in order to test isomorphism include:
        # placements_copy = Placements()
        placements = Placements()
        vertices = \
            placer_algorithm_utilities.sort_vertices_by_known_constraints(
                machine_graph.vertices)

        progress = ProgressBar(
            machine_graph.n_vertices, "Placing graph vertices")
        resource_tracker = ResourceTracker(machine,
                                           self._generate_hilbert_chips(
                                               machine))

        # get vertices which must be placed on the same chip
        vertices_on_same_chip = \
            placer_algorithm_utilities.get_same_chip_vertex_groups(
                machine_graph.vertices)

        # iterate over vertices and generate placements
        all_vertices_placed = set()
        for vertex in progress.over(vertices):
            if vertex not in all_vertices_placed:
                vertices_placed = self._place_vertex(
                    vertex, resource_tracker, machine,
                    placements,
                    vertices_on_same_chip)
                all_vertices_placed.update(vertices_placed)
        return placements

    def _check_constraints(
            self, vertices, additional_placement_constraints=None):
        """ Ensure that the algorithm conforms to any required constraints.
        :param vertices: The vertices for which to check the constraints
        :type vertices: dictionary object of vertices and associated \
            constraints
        :param additional_placement_constraints:\
            Additional placement constraints supported by the algorithm doing\
            this check
        :type additional_placement_constraints: set of \
            :py:class:`pacman.model.constraints.placer_constraints.abstract_placer_constraint`
        """

        placement_constraints = {SameChipAsConstraint}
        if additional_placement_constraints is not None:
            placement_constraints.update(additional_placement_constraints)
        ResourceTracker.check_constraints(
            vertices, additional_placement_constraints=placement_constraints)

    def _generate_hilbert_chips(self, machine):
        """ A generator which iterates over a set of chips in a machine in
        a hilbert path.

        For use as a chip ordering for the sequential placer.

        :param machine: A SpiNNaker machine object.
        :type machine: :py:class:`SpiNNMachine.spinn_machine.machine.Machine`
        :return x, y coordinates of chips to place
        :rtype int, int
        """

        # set size of curve based on number of chips on machine
        max_dimen = max(machine.max_chip_x, machine.max_chip_y)
        if max_dimen >= 1:
            hilbert_levels = int(ceil(log(max_dimen, 2.0)))
        else:
            hilbert_levels = 0

        for x, y in self._hilbert_curve(hilbert_levels):
            if machine.is_chip_at(x, y):
                yield x, y

    def _place_vertex(self, vertex, resource_tracker, machine, placements,
                      vertices_on_same_chip):
        """ Creates placements and returns list of vertices placed.

        :param vertex: the vertex that is placed
        :type vertex: \
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.impl.MachineVertex`
        :param resource_tracker: tracks the usage of resources of a machine
        :type resource_tracker: \
            :py:class:`pacman.utilities.utility_objs.resource_tracker.ResourceTracker`
        :param machine: A SpiNNaker machine object.
        :type machine: :py:class:`SpiNNMachine.spinn_machine.machine.Machine`
        :param placements: Placements of vertices on the machine
        :type :py:class:`pacman.model.placements.placements.Placements`
        :param vertices_on_same_chip: a dictionary where keys are a vertex \
            and values are a list of vertices
        :type vertices_on_same_chip: dict
        :return vertices: an iterable of vertices to be placed
        :rtype vertices: list
        """

        vertices = vertices_on_same_chip[vertex]
        chips = self._generate_hilbert_chips(machine)

        # prioritize vertices that should be on the same chip
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

        # returns list of vertices placed
        return vertices

    def _hilbert_curve(self, level, angle=1, state=None):
        """Generator of points along a 2D Hilbert curve.

        This implements the L-system as described on
        `http://en.wikipedia.org/wiki/Hilbert_curve`.

        :param level: Number of levels of recursion to use in generating \
            the curve. The resulting curve will be `(2**level)-1` wide/tall.
        :type level: int
        :param angle: `1` if this is the 'positive' \
            expansion of the grammar and `-1` for the 'negative' expansion.
        :type angle: int
        :param state: The current state of the system in a Hilbert curve.
        :type state: \
            :py:class:`pacman.operations.rigged_algorithms.hilbert_state.HilbertState`
        :return the x and y positions in a Hilbert curve as a state object.
        :rtype HilbertState object \
            :py:class:`pacman.operations.rigged_algorithms.hilbert_state.HilbertState`
        """

        # Create state object first time we're called while also yielding
        # first position
        if state is None:
            state = HilbertState()
            yield state.x_pos, state.y_pos

        # escape condition
        if level <= 0:
            return

        state.turn_left(angle)

        # Recurse negative
        for state.x_pos, state.y_pos in self._hilbert_curve(
                        level - 1, -angle, state):
            yield state.x_pos, state.y_pos

        yield state.move_forward()

        state.turn_right(angle)

        # Recurse positive
        for state.x_pos, state.y_pos in self._hilbert_curve(
                        level - 1, angle, state):
            yield state.x_pos, state.y_pos

        yield state.move_forward()

        # Recurse positive
        for state.x_pos, state.y_pos in self._hilbert_curve(
                        level - 1, angle, state):
            yield state.x_pos, state.y_pos

        state.turn_right(angle)

        yield state.move_forward()

        # Recurse negative
        for state.x_pos, state.y_pos in self._hilbert_curve(
                        level - 1, -angle, state):
            yield state.x_pos, state.y_pos

        state.turn_left(angle)
