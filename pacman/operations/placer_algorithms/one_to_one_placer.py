
# pacman imports
from pacman import exceptions
from pacman.model.placements.placements import Placements
from pacman.model.placements.placement import Placement
from pacman.operations.placer_algorithms import RadialPlacer
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker

from spinn_machine.utilities.progress_bar import ProgressBar
import traceback
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities


class OneToOnePlacer(RadialPlacer):
    """ Placer that puts vertices which are directly connected to only its\
        destination on the same chip
    """

    def __init__(self):
        RadialPlacer.__init__(self)

    def __call__(self, machine_graph, machine):

        # check that the algorithm can handle the constraints
        self._check_constraints(machine_graph.vertices)

        sorted_vertices = self._sort_vertices_for_one_to_one_connection(
            machine_graph)

        placements = Placements()

        self._do_allocation(sorted_vertices, placements, machine)

        return placements

    def _do_allocation(self, vertices, placements, machine):

        # Iterate over vertices and generate placements
        progress_bar = ProgressBar(
            len(vertices), "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, self._generate_radial_chips(machine))

        # iterate over vertices
        for vertex_list in vertices:

            # ensure largest cores per chip is divisible by 2
            # (for one to one placement)
            max_cores_on_chip = \
                resource_tracker.most_avilable_cores_on_a_chip()
            if max_cores_on_chip % 2 != 0:
                max_cores_on_chip -= 1

            # if too many one to ones to fit on a chip, allocate individually
            if len(vertex_list) > max_cores_on_chip:
                for vertex in vertex_list:
                    self._allocate_individual(
                        vertex, placements, progress_bar, resource_tracker)
            else:

                try:
                    allocations = \
                        resource_tracker.allocate_constrained_group_resources(
                            vertex_list)

                    # allocate cores to vertices
                    for vertex, (x, y, p, _, _) in zip(
                            vertex_list, allocations):
                        placement = Placement(vertex, x, y, p)
                        placements.add_placement(placement)
                        progress_bar.update()
                except exceptions.PacmanValueError or \
                        exceptions.PacmanException or \
                        exceptions.PacmanInvalidParameterException:
                    traceback.print_exc()

                    # If something goes wrong, try to allocate each
                    # individually
                    for vertex in vertex_list:
                        self._allocate_individual(
                            vertex, placements, progress_bar,
                            resource_tracker)
        progress_bar.end()

    @staticmethod
    def _allocate_individual(
            vertex, placements, progress_bar, resource_tracker):

        # Create and store a new placement anywhere on the board
        (x, y, p, _, _) = resource_tracker.\
            allocate_constrained_resources(vertex.resources_required, vertex)
        placement = Placement(vertex, x, y, p)
        placements.add_placement(placement)
        progress_bar.update()

    def _sort_vertices_for_one_to_one_connection(
            self, machine_graph):
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
                connected_vertices = self._find_one_to_one_vertices(
                    vertex, machine_graph)
                new_list = [
                    v for v in connected_vertices if v not in found_list]
                sorted_vertices.append(new_list)
                found_list.update(set(new_list))

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
                edges = graph.get_edges_ending_at_vertex(
                    next_vertex)
                if len(edges) == 1 and not conflict:
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
                edges = graph.get_edges_starting_at_vertex(
                    next_vertex)
                if len(edges) == 1 and not conflict:
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
