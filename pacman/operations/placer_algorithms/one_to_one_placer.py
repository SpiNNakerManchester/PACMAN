
# pacman imports
from pacman import exceptions
from pacman.model.placements import Placement, Placements
from pacman.operations.placer_algorithms import RadialPlacer
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.constraints.placer_constraints\
    import PlacerSameChipAsConstraint
from pacman.utilities import utility_calls

from spinn_machine.utilities.progress_bar import ProgressBar


class OneToOnePlacer(RadialPlacer):
    """ Placer that puts vertices which are directly connected to only its\
        destination on the same chip
    """

    __slots__ = []

    def __init__(self):
        RadialPlacer.__init__(self)

    def __call__(self, machine_graph, machine):

        # check that the algorithm can handle the constraints
        self._check_constraints(
            machine_graph.vertices,
            additional_placement_constraints={PlacerSameChipAsConstraint})

        # Get which vertices must be placed on the same chip as another vertex
        same_chip_vertex_groups = placer_algorithm_utilities\
            .get_same_chip_vertex_groups(machine_graph.vertices)
        sorted_vertices = self._sort_vertices_for_one_to_one_connection(
            machine_graph, same_chip_vertex_groups)

        placements = self._do_allocation(
            sorted_vertices, machine, same_chip_vertex_groups, machine_graph)

        return placements

    def _do_allocation(
            self, vertices, machine, same_chip_vertex_groups, machine_graph):

        placements = Placements()

        # Iterate over vertices and generate placements
        progress_bar = ProgressBar(
            len(machine_graph.vertices), "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, self._generate_radial_chips(machine))
        all_vertices_placed = set()

        # iterate over vertices
        for vertex_list in vertices:

            # if too many one to ones to fit on a chip, allocate individually
            if len(vertex_list) > machine.maximum_user_cores_on_chip:
                for vertex in vertex_list:
                    self._allocate_individual(
                        vertex, placements, resource_tracker,
                        same_chip_vertex_groups, all_vertices_placed)
                progress_bar.update()
            else:

                try:
                    resource_and_constraint_list = [
                        (vertex.resources_required, vertex.constraints)
                        for vertex in vertex_list]
                    allocations = \
                        resource_tracker.allocate_constrained_group_resources(
                            resource_and_constraint_list)

                    # allocate cores to vertices
                    for vertex, (x, y, p, _, _) in zip(
                            vertex_list, allocations):
                        placement = Placement(vertex, x, y, p)
                        placements.add_placement(placement)
                    progress_bar.update()
                except exceptions.PacmanValueError or \
                        exceptions.PacmanException or \
                        exceptions.PacmanInvalidParameterException:

                    # If something goes wrong, try to allocate each
                    # individually
                    for vertex in vertex_list:
                        self._allocate_individual(
                            vertex, placements, resource_tracker,
                            same_chip_vertex_groups, all_vertices_placed)
                    progress_bar.update()
        progress_bar.end()
        return placements

    @staticmethod
    def _allocate_individual(
            vertex, placements, resource_tracker, same_chip_vertex_groups,
            all_vertices_placed):
        if vertex not in all_vertices_placed:
            vertices = same_chip_vertex_groups[vertex]

            if len(vertices) > 1:
                resources = \
                    resource_tracker.allocate_constrained_group_resources([
                        (vert.resources_required, vert.constraints)
                        for vert in vertices
                    ])
                for (x, y, p, _, _), vert in zip(resources, vertices):
                    placement = Placement(vert, x, y, p)
                    placements.add_placement(placement)
                    all_vertices_placed.add(vert)
            else:
                (x, y, p, _, _) = resource_tracker.\
                    allocate_constrained_resources(
                        vertex.resources_required, vertex.constraints)
                placement = Placement(vertex, x, y, p)
                placements.add_placement(placement)
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
        vertices = placer_algorithm_utilities\
            .sort_vertices_by_known_constraints(machine_graph.vertices)

        for vertex in vertices:
            if vertex not in found_list:

                # vertices that are one to one connected with vertex and are
                # not forced off chip
                connected_vertices = self._find_one_to_one_vertices(
                    vertex, machine_graph)

                # create list for each vertex thats connected haven't already
                #  been seen before
                new_list = set()
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

        :param vertex:  the vertex to use as a basis for one to one connections
        :param graph: \
            the graph to look for other one to one vertices
        :return: set of one to one vertices
        """
        x, y, _ = ResourceTracker.get_chip_and_core(vertex.constraints)
        found_vertices = [vertex]
        vertices_seen = {vertex}

        # look for one to ones leaving this vertex
        outgoing = graph.get_edges_starting_at_vertex(vertex)
        vertices_to_try = [edge.post_vertex for edge in outgoing]
        while len(vertices_to_try) != 0:
            next_vertex = vertices_to_try.pop()
            if next_vertex not in vertices_seen:
                vertices_seen.add(next_vertex)
                post_x, post_y, _ = ResourceTracker.get_chip_and_core(
                    next_vertex.constraints)
                conflict = False
                if x is not None and post_x is not None and x != post_x:
                    conflict = True
                if y is not None and post_y is not None and y != post_y:
                    conflict = True
                edges = graph.get_edges_ending_at_vertex(next_vertex)

                if utility_calls.is_single(edges) and not conflict:
                    found_vertices.append(next_vertex)
                    if post_x is not None:
                        x = post_x
                    if post_y is not None:
                        y = post_y
                    outgoing = \
                        graph.get_edges_starting_at_vertex(
                            next_vertex)
                    vertices_to_try.extend([
                        edge.post_vertex for edge in outgoing
                        if edge.post_vertex not in vertices_seen])

        # look for one to ones entering this vertex
        incoming = graph.get_edges_ending_at_vertex(
            vertex)
        vertices_to_try = [
            edge.pre_vertex for edge in incoming
            if edge.pre_vertex not in vertices_seen]
        while len(vertices_to_try) != 0:
            next_vertex = vertices_to_try.pop()
            if next_vertex not in vertices_seen:
                vertices_seen.add(next_vertex)
                pre_x, pre_y, _ = ResourceTracker.get_chip_and_core(
                    next_vertex.constraints)
                conflict = False
                if x is not None and pre_x is not None and x != pre_x:
                    conflict = True
                if y is not None and pre_y is not None and y != pre_y:
                    conflict = True
                edges = graph.get_edges_starting_at_vertex(next_vertex)

                if utility_calls.is_single(edges) and not conflict:
                    found_vertices.append(next_vertex)
                    if pre_x is not None:
                        x = pre_x
                    if pre_y is not None:
                        y = pre_y
                    incoming = \
                        graph.get_edges_ending_at_vertex(
                            next_vertex)
                    vertices_to_try.extend([
                        edge.pre_vertex for edge in incoming
                        if edge.pre_vertex not in vertices_seen])

        return found_vertices
