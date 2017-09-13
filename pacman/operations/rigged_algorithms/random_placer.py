from pacman.utilities.utility_objs import ResourceTracker
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.placements import Placement, Placements

from spinn_utilities.progress_bar import ProgressBar

import random
import numpy


class RandomPlacer(object):

    def __call__(self, machine_graph, machine):

        # check that the algorithm can handle the constraints
        ResourceTracker.check_constraints(machine_graph.vertices)

        placements = Placements()
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
        vertices_placed = set()
        for vertex in progress.over(vertices):
            if vertex not in vertices_placed:
                vertices_placed = self._place_vertex(
                    vertex, resource_tracker, machine,
                    placements,
                    # placements,
                    vertices_on_same_chip)
                vertices_placed.update(vertices_placed)
        return placements
        # return placements

    @staticmethod
    def _generate_random_chips(machine, np=numpy, random_generator=random):
        """Generates the list of chips in a random order, with the option \
         to provide a starting point.

        :param machine: A SpiNNaker machine object.
        :type machine: :py:class:`SpiNNMachine.spinn_machine.machine.Machine`
        :param random: Python's random number generator
        :type random: :py:class:`random.Random`
        :return x, y coordinates of chips for placement
        :rtype (int, int)
        """

        # Create a numpy array of size equal or greater to size of machine,
        # populated with all false values
        rand_array = np.ones((machine.max_chip_x, machine.max_chip_y),
                             dtype=bool)
        tries = 0
        threshold = 3
        max_x = machine.max_chip_x - 1
        max_y = machine.max_chip_y - 1

        # The following method is used to optimise the runtime of this
        # algorithm for large machines:
        # Choose an arbitrary number of times the generator is allowed to
        # pick an already used chip. Once past this threshold (the array
        # begins to run out of unused chips), create a list of the
        # remainder and shuffle it.
        while tries < threshold:
            x = random_generator.randint(0, max_x)
            y = random_generator.randint(0, max_y)
            if rand_array[x][y]:
                tries = 0
                rand_array[x][y] = 0
                if machine.is_chip_at(x, y):
                    yield x, y
            else:
                tries += 1

        # Array is running out of unused chips. Create a list of those
        # remaining (still are True, or nonzero)
        remaining_chips = list()
        (xs, ys) = rand_array.nonzero()
        for (x, y) in zip(xs, ys):
            remaining_chips.append((x, y))

        # Shuffle list of unused chips for randomness
        random_generator.shuffle(remaining_chips)
        for (x, y) in remaining_chips:
            yield x, y

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
