from spinn_utilities.progress_bar import ProgressBar
from pacman.exceptions import (
    PacmanException, PacmanInvalidParameterException, PacmanValueError)
from pacman.model.placements import Placement, Placements
from pacman.operations.placer_algorithms import RadialPlacer
from pacman.utilities.utility_objs import ResourceTracker
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    get_same_chip_vertex_groups, get_vertices_on_same_chip, group_vertices)
from pacman.model.constraints.placer_constraints import (
    SameChipAsConstraint, ChipAndCoreConstraint)
from pacman.utilities.utility_calls import (
    is_single, locate_constraints_of_type)
from pacman.model.graphs import AbstractVirtualVertex
import functools


def _conflict(x, y, post_x, post_y):
    if x is not None and post_x is not None and x != post_x:
        return True
    if y is not None and post_y is not None and y != post_y:
        return True
    return False


def _find_one_to_one_vertices(vertex, graph):
    """ Find vertices which have one to one connections with the given\
        vertex, and where their constraints don't force them onto\
        different chips.

    :param graph: the graph to look for other one to one vertices
    :param vertex: the vertex to use as a basis for one to one connections
    :return: set of one to one vertices
    """
    # Virtual vertices can't be forced on other chips
    if isinstance(vertex, AbstractVirtualVertex):
        return []
    found_vertices = set()
    vertices_seen = {vertex}

    # look for one to ones leaving this vertex
    outgoing = graph.get_edges_starting_at_vertex(vertex)
    vertices_to_try = [
        edge.post_vertex for edge in outgoing
        if edge.post_vertex not in vertices_seen]
    while vertices_to_try:
        next_vertex = vertices_to_try.pop()
        if next_vertex not in vertices_seen:
            vertices_seen.add(next_vertex)
            edges = graph.get_edges_ending_at_vertex(next_vertex)
            if is_single(edges):
                found_vertices.add(next_vertex)
                outgoing = graph.get_edges_starting_at_vertex(next_vertex)
                vertices_to_try.extend([
                    edge.post_vertex for edge in outgoing
                    if edge.post_vertex not in vertices_seen])

    # look for one to ones entering this vertex
    incoming = graph.get_edges_ending_at_vertex(vertex)
    vertices_to_try = [
        edge.pre_vertex for edge in incoming
        if edge.pre_vertex not in vertices_seen]
    while vertices_to_try:
        next_vertex = vertices_to_try.pop()
        if next_vertex not in vertices_seen:
            vertices_seen.add(next_vertex)
            edges = graph.get_edges_starting_at_vertex(next_vertex)
            if is_single(edges):
                found_vertices.add(next_vertex)
                incoming = graph.get_edges_ending_at_vertex(next_vertex)
                vertices_to_try.extend([
                    edge.pre_vertex for edge in incoming
                    if edge.pre_vertex not in vertices_seen])

    extra_vertices = get_vertices_on_same_chip(vertex, graph)
    for vertex in extra_vertices:
        found_vertices.add(vertex)
    return found_vertices


class OneToOnePlacer(RadialPlacer):
    """ Placer that puts vertices which are directly connected to only its\
        destination on the same chip
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
        self._check_constraints(
            machine_graph.vertices,
            additional_placement_constraints={SameChipAsConstraint})

        # Get which vertices must be placed on the same chip as another vertex
        same_chip_vertex_groups = get_same_chip_vertex_groups(machine_graph)

        # Work out the vertices that should be on the same chip by one-to-one
        # connectivity
        one_to_one_groups = group_vertices(
            machine_graph.vertices, functools.partial(
                _find_one_to_one_vertices, graph=machine_graph))

        return self._do_allocation(one_to_one_groups, same_chip_vertex_groups,
                                   machine, plan_n_timesteps, machine_graph)

    def _do_allocation(
            self, one_to_one_groups, same_chip_vertex_groups,
            machine, plan_n_timesteps, machine_graph):
        placements = Placements()

        # Iterate over vertices and generate placements
        progress = ProgressBar(
            machine_graph.n_vertices, "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, plan_n_timesteps, self._generate_radial_chips(machine))
        all_vertices_placed = set()

        # Find vertices with harder constraints
        constrained = list()
        unconstrained = list()
        for vertex in machine_graph.vertices:
            if locate_constraints_of_type(
                    vertex.constraints, ChipAndCoreConstraint):
                constrained.append(vertex)
            else:
                unconstrained.append(vertex)

        # Place vertices with hard constraints
        for vertex in constrained:
            self._allocate_same_chip_as_group(
                vertex, placements, resource_tracker, same_chip_vertex_groups,
                all_vertices_placed, progress)

        # iterate over the remaining unconstrained (or less constrained)
        # vertices
        for vertex in unconstrained:

            # If the vertex has been placed, skip it
            if vertex in all_vertices_placed:
                continue

            # Find vertices that are one-to-one connected to this one
            one_to_one_vertices = one_to_one_groups[vertex]

            # Get unallocated vertices and placements of allocated vertices
            unallocated = list()
            chips = list()
            for vert in one_to_one_vertices:
                if vert in all_vertices_placed:
                    placement = placements.get_placement_of_vertex(vert)
                    chips.append((placement.x, placement.y))
                else:
                    unallocated.append(vert)

            # if too many one to ones to fit on a chip, allocate individually
            if len(unallocated) > \
                    resource_tracker.get_maximum_cores_available_on_a_chip():
                for vert in unallocated:
                    self._allocate_same_chip_as_group(
                        vert, placements, resource_tracker,
                        same_chip_vertex_groups, all_vertices_placed,
                        progress)
                continue

            # Try to allocate all vertices to the same chip
            success = self._allocate_one_to_one_group(
                resource_tracker, unallocated, progress, placements, chips,
                all_vertices_placed)

            if not success:

                # Something went wrong, try to allocate each individually
                for vertex in unallocated:
                    self._allocate_same_chip_as_group(
                        vertex, placements, resource_tracker,
                        same_chip_vertex_groups, all_vertices_placed,
                        progress)
        progress.end()
        return placements

    @staticmethod
    def _allocate_one_to_one_group(
            resource_tracker, vertices, progress, placements, chips,
            all_vertices_placed):
        try:
            allocs = resource_tracker.allocate_constrained_group_resources(
                [(v.resources_required, v.constraints) for v in vertices],
                chips)

            # allocate cores to vertices
            for vertex, (x, y, p, _, _) in progress.over(
                    zip(vertices, allocs), False):
                placements.add_placement(Placement(vertex, x, y, p))
                all_vertices_placed.add(vertex)
            return True
        except (PacmanValueError, PacmanException,
                PacmanInvalidParameterException):
            return False

    @staticmethod
    def _allocate_same_chip_as_group(
            vertex, placements, tracker, same_chip_vertex_groups,
            all_vertices_placed, progress):
        if vertex not in all_vertices_placed:
            vertices = same_chip_vertex_groups[vertex]
            resources = tracker.allocate_constrained_group_resources([
                (v.resources_required, v.constraints) for v in vertices])
            for (x, y, p, _, _), v in progress.over(
                    zip(resources, vertices), False):
                placements.add_placement(Placement(v, x, y, p))
                all_vertices_placed.add(v)
