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

    @staticmethod
    def _generate_random_chips(
            machine, resource_tracker=None, random=default_random):
        """ Generates the list of chips in a random order, with the option \
         to provide a starting point.

        :param machine: the spinnaker machine object
        :type machine: :py:class:`SpiNNMachine.spinn_machine.machine.py`
        :param resource_tracker: object which tracks which resources of \
            the machine have been used
        :type resource_tracker: None or :py:class:`ResourceTracker`
        :param chips: a set of
        :return: list of chips.
        """


        location = []

        for (x, y) in machine.chips():
            if (resource_tracker is None or
                    resource_tracker.is_chip_available(x, y)):
                location.append(random.sample(machine.chips, 1))


    def _place_vertex(self, vertex, resource_tracker, machine,
                      placements, random=default_random):

        vertices = location[vertex]
        chips = self._generate_random_chips(machine)

        if len(vertices) > 1:
            assigned_values = \
                resource_tracker.allocate_constrained_group_resources([
                    (vert.resources_required, vert.constraints)
                    for vert in vertices], chips)
            for (x, y, p, _, _), vert in zip(assigned_values, vertices):
                if not placements.is_processor_occupied(x, y, p):
                    placement = random.sample(Placement(vert, x, y, p),1)
                    placements.add_placement(placement)
        else:
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                vertex.resources_required, vertex.constraints, chips)
            placement = random.sample(Placement(vertex, x, y, p))
            placements.add_placement(placement)

        return vertices


