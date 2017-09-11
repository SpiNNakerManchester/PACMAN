from pacman.utilities.utility_objs import ResourceTracker
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.placements import Placement, Placements
from pacman.model.constraints.placer_constraints import SameChipAsConstraint

from spinn_utilities.progress_bar import ProgressBar

import random as default_random


class RandomPlacer(object):

    def __call__(self, machine_graph, machine):

        # check that the algorithm can handle the constraints
        ResourceTracker.check_constraints(machine_graph.vertices)

        placements_copy = Placements()
        vertices = \
            placer_algorithm_utilities.sort_vertices_by_known_constraints(
                machine_graph.vertices)

        # Iterate over vertices and generate placements
        progress = ProgressBar(machine_graph.n_vertices,
                               "Placing graph vertices")
        resource_tracker = ResourceTracker(machine,
                                           self._generate_random_chips(
                                               machine))
        vertices_on_same_chip = \
            placer_algorithm_utilities.get_same_chip_vertex_groups(
                    machine_graph.vertices)
        all_vertices_placed = set()
        for vertex in progress.over(vertices):
            if vertex not in all_vertices_placed:
                vertices_placed = self._place_vertex(
                    vertex, resource_tracker, machine,
                    placements_copy,
                    # placements,
                    vertices_on_same_chip)
                all_vertices_placed.update(vertices_placed)
        return placements_copy
        # return placements

    def _check_constraints(
            self, vertices, additional_placement_constraints=None):
        placement_constraints = {SameChipAsConstraint}
        if additional_placement_constraints is not None:
            placement_constraints.update(additional_placement_constraints)
        ResourceTracker.check_constraints(
            vertices, additional_placement_constraints=placement_constraints)

    def _generate_random_chips(self, machine, random=default_random):
        """Generates the list of chips in a random order, with the option \
         to provide a starting point.

        :param machine: A SpiNNaker machine object.
        :type machine: :py:class:`SpiNNMachine.spinn_machine.machine.Machine`
        :param random: Python's random number generator
        :type random: :py:class:`random.Random`
        :return x, y coordinates of chips for placement
        :rtype (int, int)
        """

        chips = set()
        random.seed(2)

        for x in range(0, machine.max_chip_x):
            for y in range(0, machine.max_chip_y):
                chips.add((x, y))

        for _ in chips:
            randomized_chips = random.sample(chips, 1)[0]
            if machine.is_chip_at(randomized_chips[0], randomized_chips[1]):
                yield randomized_chips

    def _place_vertex(self, vertex, resource_tracker, machine,
                      placements, location):

        vertices = location[vertex]
        # random x and y value within the maximum of the machine
        chips = self._generate_random_chips(machine)

        if len(vertices) > 1:
            assigned_values = \
                resource_tracker.allocate_constrained_group_resources([
                    (vert.resources_required, vert.constraints)
                    for vert in vertices], chips)
            for (x, y, p, _, _), vert in zip(assigned_values, vertices):
                placement = Placement(vert, x, y, p)
                placements.add_placement(placement)
        else:
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                vertex.resources_required, vertex.constraints, chips)
            placement = Placement(vertex, x, y, p)
            placements.add_placement(placement)

        return vertices
