from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet

# pacman imports
from pacman.exceptions import \
    PacmanException, PacmanInvalidParameterException, PacmanValueError
from pacman.model.placements import Placement, Placements
from pacman.operations.placer_algorithms import RadialPlacer
from pacman.utilities.utility_objs import ResourceTracker
from pacman.utilities.algorithm_utilities \
    import placer_algorithm_utilities as placer_utils
from pacman.model.constraints.placer_constraints\
    import SameChipAsConstraint
from pacman.utilities.utility_calls import is_single


def _conflict(x, y, post_x, post_y):
    if x is not None and post_x is not None and x != post_x:
        return True
    if y is not None and post_y is not None and y != post_y:
        return True
    return False


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
        same_chip_vertex_groups = placer_utils.get_same_chip_vertex_groups(
            machine_graph.vertices)
        sorted_vertices = self._sort_vertices_for_one_to_one_connection(
            machine_graph, same_chip_vertex_groups)

        return self._do_allocation(
            sorted_vertices, machine, plan_n_timesteps,
            same_chip_vertex_groups, machine_graph)

    def _do_allocation(
            self, vertices, machine, plan_n_timesteps,
            same_chip_vertex_groups, machine_graph):
        placements = Placements()

        # Iterate over vertices and generate placements
        progress = ProgressBar(
            machine_graph.n_vertices, "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, plan_n_timesteps, self._generate_radial_chips(machine))
        all_vertices_placed = set()

        # iterate over vertices
        for vertex_list in vertices:
            # if too many one to ones to fit on a chip, allocate individually
            if len(vertex_list) > machine.maximum_user_cores_on_chip:
                for vertex in progress.over(vertex_list, False):
                    self._allocate_individual(
                        vertex, placements, resource_tracker,
                        same_chip_vertex_groups, all_vertices_placed)
                continue
            allocations = self._get_allocations(resource_tracker, vertex_list)
            if allocations is not None:
                # allocate cores to vertices
                for vertex, (x, y, p, _, _) in progress.over(zip(
                        vertex_list, allocations), False):
                    placements.add_placement(Placement(vertex, x, y, p))
            else:
                # Something went wrong, try to allocate each individually
                for vertex in progress.over(vertex_list, False):
                    self._allocate_individual(
                        vertex, placements, resource_tracker,
                        same_chip_vertex_groups, all_vertices_placed)
        progress.end()
        return placements

    @staticmethod
    def _get_allocations(resource_tracker, vertices):
        try:
            return resource_tracker.allocate_constrained_group_resources(
                [(v.resources_required, v.constraints) for v in vertices])
        except (PacmanValueError, PacmanException,
                PacmanInvalidParameterException):
            return None

    @staticmethod
    def _allocate_individual(
            vertex, placements, tracker, same_chip_vertex_groups,
            all_vertices_placed):
        if vertex not in all_vertices_placed:
            vertices = same_chip_vertex_groups[vertex]

            if len(vertices) > 1:
                resources = tracker.allocate_constrained_group_resources([
                    (v.resources_required, v.constraints) for v in vertices])
                for (x, y, p, _, _), v in zip(resources, vertices):
                    placements.add_placement(Placement(v, x, y, p))
                    all_vertices_placed.add(v)
            else:
                (x, y, p, _, _) = tracker.\
                    allocate_constrained_resources(
                        vertex.resources_required, vertex.constraints)
                placements.add_placement(Placement(vertex, x, y, p))
                all_vertices_placed.add(vertex)

    def _sort_vertices_for_one_to_one_connection(
            self, machine_graph, same_chip_vertex_groups):
        """

        :param machine_graph: the graph to place
        :return: list of sorted vertices
        """
        sorted_vertices = list()
        found_list = set()

        # order vertices based on constraint priority
        vertices = placer_utils.sort_vertices_by_known_constraints(
            machine_graph.vertices)

        for vertex in vertices:
            if vertex not in found_list:

                # vertices that are one to one connected with vertex and are
                # not forced off chip
                connected_vertices = self._find_one_to_one_vertices(
                    vertex, machine_graph)

                # create list for each vertex thats connected haven't already
                #  been seen before
                new_list = OrderedSet()
                for found_vertex in connected_vertices:
                    if found_vertex not in found_list:
                        new_list.add(found_vertex)

                # looks for vertices that have same chip constraints but not
                # found by the one to one connection search.
                same_chip_vertices = list()
                for found_vertex in new_list:
                    for same_chip_constrained_vertex in \
                            same_chip_vertex_groups[found_vertex]:
                        if same_chip_constrained_vertex not in new_list:
                            same_chip_vertices.append(
                                same_chip_constrained_vertex)

                # add these newly found vertices to the list
                new_list.update(same_chip_vertices)

                sorted_vertices.append(new_list)
                found_list.update(new_list)

        # locate vertices which have no output or input, and add them for
        # placement
        for vertex in vertices:
            if vertex not in found_list:
                sorted_vertices.append([vertex])
        return sorted_vertices

    @staticmethod
    def _find_one_to_one_vertices(vertex, graph):
        """ Find vertices which have one to one connections with the given\
            vertex, and where their constraints don't force them onto\
            different chips.

        :param vertex: the vertex to use as a basis for one to one connections
        :param graph: the graph to look for other one to one vertices
        :return: set of one to one vertices
        """
        x, y, _ = ResourceTracker.get_chip_and_core(vertex.constraints)
        found_vertices = [vertex]
        vertices_seen = {vertex}

        # look for one to ones leaving this vertex
        outgoing = graph.get_edges_starting_at_vertex(vertex)
        vertices_to_try = [edge.post_vertex for edge in outgoing]
        while vertices_to_try:
            next_vertex = vertices_to_try.pop()
            if next_vertex not in vertices_seen:
                vertices_seen.add(next_vertex)
                post_x, post_y, _ = ResourceTracker.get_chip_and_core(
                    next_vertex.constraints)
                edges = graph.get_edges_ending_at_vertex(next_vertex)
                if is_single(edges) and not _conflict(x, y, post_x, post_y):
                    found_vertices.append(next_vertex)
                    if post_x is not None:
                        x = post_x
                    if post_y is not None:
                        y = post_y
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
                pre_x, pre_y, _ = ResourceTracker.get_chip_and_core(
                    next_vertex.constraints)
                edges = graph.get_edges_starting_at_vertex(next_vertex)
                if is_single(edges) and not _conflict(x, y, pre_x, pre_y):
                    found_vertices.append(next_vertex)
                    if pre_x is not None:
                        x = pre_x
                    if pre_y is not None:
                        y = pre_y
                    incoming = graph.get_edges_ending_at_vertex(next_vertex)
                    vertices_to_try.extend([
                        edge.pre_vertex for edge in incoming
                        if edge.pre_vertex not in vertices_seen])

        return found_vertices
