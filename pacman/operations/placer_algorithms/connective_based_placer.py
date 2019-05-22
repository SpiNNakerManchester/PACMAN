import logging
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.constraints.placer_constraints import (
    AbstractPlacerConstraint)
from pacman.model.placements import Placements
from pacman.operations.placer_algorithms import RadialPlacer
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    sort_vertices_by_known_constraints)
from pacman.utilities.utility_calls import locate_constraints_of_type
from pacman.utilities.utility_objs import ResourceTracker

logger = logging.getLogger(__name__)


class ConnectiveBasedPlacer(RadialPlacer):
    """ A radial algorithm that can place a machine graph onto a\
        machine using a circle out behaviour from a Ethernet at a given point\
        and which will place things that are most connected closest to each\
        other
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, plan_n_timesteps):
        """

        :param machine_graph: The machine_graph to place
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param machine:\
            The machine with respect to which to partition the application\
            graph
        :type machine: :py:class:`spinn_machine.Machine`
        :param plan_n_timesteps: number of timesteps to plan for
        :type  plan_n_timesteps: int
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: \
            If something goes wrong with the placement
        """
        # check that the algorithm can handle the constraints
        self._check_constraints(machine_graph.vertices)

        # Sort the vertices into those with and those without
        # placement constraints
        placements = Placements()
        constrained = list()
        unconstrained = set()
        for vertex in machine_graph.vertices:
            if locate_constraints_of_type(
                    vertex.constraints, AbstractPlacerConstraint):
                constrained.append(vertex)
            else:
                unconstrained.add(vertex)

        # Iterate over constrained vertices and generate placements
        progress = ProgressBar(
            machine_graph.n_vertices, "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, plan_n_timesteps, self._generate_radial_chips(machine))
        constrained = sort_vertices_by_known_constraints(constrained)
        for vertex in progress.over(constrained, False):
            self._place_vertex(vertex, resource_tracker, machine, placements)

        while unconstrained:
            # Place the subgraph with the overall most connected vertex
            max_connected_vertex = self._find_max_connected_vertex(
                unconstrained, machine_graph)
            self._place_unconstrained_subgraph(
                max_connected_vertex, machine_graph, unconstrained,
                machine, placements, resource_tracker, progress)

        # finished, so stop progress bar and return placements
        progress.end()
        return placements, resource_tracker.chips_used

    def _place_unconstrained_subgraph(
            self, starting_vertex, machine_graph, unplaced_vertices,
            machine, placements, resource_tracker, progress):
        # pylint: disable=too-many-arguments
        # Keep track of all unplaced_vertices connected to the currently
        # placed ones
        to_do = set()
        to_do.add(starting_vertex)

        while to_do:
            # Find the vertex most connected of the currently-to-be-placed ones
            vertex = self._find_max_connected_vertex(to_do, machine_graph)

            # Place the vertex
            self._place_vertex(vertex, resource_tracker, machine, placements)
            progress.update()

            # Remove from collections of unplaced_vertices to work on
            unplaced_vertices.remove(vertex)
            to_do.remove(vertex)

            # Add all unplaced_vertices connected to this one to the set
            for edge in machine_graph.get_edges_ending_at_vertex(vertex):
                if edge.pre_vertex in unplaced_vertices:
                    to_do.add(edge.pre_vertex)
            for edge in machine_graph.get_edges_starting_at_vertex(vertex):
                if edge.post_vertex in unplaced_vertices:
                    to_do.add(edge.post_vertex)

    def _find_max_connected_vertex(self, vertices, graph):
        max_connected_vertex = None
        max_weight = 0
        for vertex in vertices:
            in_weight = sum(
                edge.weight
                for edge in graph.get_edges_starting_at_vertex(vertex))
            out_weight = sum(
                edge.weight
                for edge in graph.get_edges_ending_at_vertex(vertex))
            weight = in_weight + out_weight

            if max_connected_vertex is None or weight > max_weight:
                max_connected_vertex = vertex
                max_weight = weight
        return max_connected_vertex
