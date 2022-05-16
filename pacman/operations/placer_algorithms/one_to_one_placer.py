# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import deque
import functools
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet
from pacman.data import PacmanDataView
from pacman.exceptions import (
    PacmanException, PacmanInvalidParameterException, PacmanValueError,
    PacmanPlaceException)
from pacman.model.placements import Placement, Placements
from pacman.operations.placer_algorithms.radial_placer import _RadialPlacer
from pacman.utilities.utility_objs import ResourceTracker
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    create_vertices_groups, get_same_chip_vertex_groups,
    get_vertices_on_same_chip, create_requirement_collections)
from pacman.model.constraints.placer_constraints import (
    SameChipAsConstraint, ChipAndCoreConstraint,
    RadialPlacementFromChipConstraint)
from pacman.utilities.utility_calls import (
    is_single, locate_constraints_of_type)
from pacman.model.graphs import AbstractVirtual


def _conflict(x, y, post_x, post_y):
    if x is not None and post_x is not None and x != post_x:
        return True
    if y is not None and post_y is not None and y != post_y:
        return True
    return False


def one_to_one_placer():
    """ Placer that puts vertices which are directly connected to only its\
        destination on the same chip

    :return: A set of placements
    :rtype: Placements
    :raise PacmanPlaceException:
        If something goes wrong with the placement
    """
    placer = _OneToOnePlacer()
    # pylint:disable=protected-access
    return placer._run()


class _OneToOnePlacer(_RadialPlacer):
    """ Placer that puts vertices which are directly connected to only its\
        destination on the same chip
    """

    __slots__ = []

    def _run(self):
        """
        :return: A set of placements
        :rtype: Placements
        :raise PacmanPlaceException:
            If something goes wrong with the placement
        """
        machine_graph = PacmanDataView.get_runtime_machine_graph()
        # Iterate over vertices and generate placements
        # +3 covers check_constraints, get_same_chip_vertex_groups and
        #    create_vertices_groups
        progress = ProgressBar(
            machine_graph.n_vertices + 3, "Placing graph vertices")
        # check that the algorithm can handle the constraints
        self._check_constraints(
            machine_graph.vertices,
            additional_placement_constraints={SameChipAsConstraint})
        progress.update()

        # Get which vertices must be placed on the same chip as another vertex
        same_chip_vertex_groups = get_same_chip_vertex_groups(machine_graph)
        progress.update()

        # Work out the vertices that should be on the same chip by one-to-one
        # connectivity
        one_to_one_groups = create_vertices_groups(
            machine_graph.vertices,
            functools.partial(
                self._find_one_to_one_vertices, graph=machine_graph))
        progress.update()

        return self._do_allocation(
            one_to_one_groups, same_chip_vertex_groups,
            machine_graph, progress)

    @staticmethod
    def _find_one_to_one_vertices(vertex, graph):
        """ Find vertices which have one to one connections with the given\
            vertex, and where their constraints don't force them onto\
            different chips.

        :param MachineGraph graph:
            the graph to look for other one to one vertices
        :param MachineVertex vertex:
            the vertex to use as a basis for one to one connections
        :return: set of one to one vertices
        :rtype: set(MachineVertex)
        """
        # Virtual vertices can't be forced on other chips
        if isinstance(vertex, AbstractVirtual):
            return []
        found_vertices = OrderedSet()
        vertices_seen = {vertex}

        # look for one to ones leaving this vertex
        outgoing = graph.get_edges_starting_at_vertex(vertex)
        vertices_to_try = deque(
            edge.post_vertex for edge in outgoing
            if edge.post_vertex not in vertices_seen)
        while vertices_to_try:
            next_vertex = vertices_to_try.pop()
            if next_vertex not in vertices_seen and \
                    not isinstance(next_vertex, AbstractVirtual):
                vertices_seen.add(next_vertex)
                if is_single(graph.get_edges_ending_at_vertex(next_vertex)):
                    found_vertices.add(next_vertex)
                    outgoing = graph.get_edges_starting_at_vertex(next_vertex)
                    vertices_to_try.extend(
                        edge.post_vertex for edge in outgoing
                        if edge.post_vertex not in vertices_seen)

        # look for one to ones entering this vertex
        incoming = graph.get_edges_ending_at_vertex(vertex)
        vertices_to_try = deque(
            edge.pre_vertex for edge in incoming
            if edge.pre_vertex not in vertices_seen)
        while vertices_to_try:
            next_vertex = vertices_to_try.pop()
            if next_vertex not in vertices_seen:
                vertices_seen.add(next_vertex)
                if is_single(graph.get_edges_starting_at_vertex(next_vertex)):
                    found_vertices.add(next_vertex)
                    incoming = graph.get_edges_ending_at_vertex(next_vertex)
                    vertices_to_try.extend(
                        edge.pre_vertex for edge in incoming
                        if edge.pre_vertex not in vertices_seen)

        found_vertices.update(get_vertices_on_same_chip(vertex, graph))
        return found_vertices

    def _do_allocation(
            self, one_to_one_groups, same_chip_vertex_groups,
            machine_graph, progress):
        """
        :param list(set(MachineVertex)) one_to_one_groups:
            Groups of vertexes that would be nice on same chip
        :param same_chip_vertex_groups:
            Mapping of Vertex to the Vertex that must be on the same Chip
        :type same_chip_vertex_groups:
            dict(MachineVertex, collection(MachineVertex))
        :param MachineGraph machine_graph: The machine_graph to place
        :param ~spinn_utilities.progress_bar.ProgressBar progress:
        :rtype: Placements
        """

        placements = Placements()

        resource_tracker = ResourceTracker(self._generate_radial_chips())
        all_vertices_placed = set()

        # RadialPlacementFromChipConstraint won't work here
        for vertex in machine_graph.vertices:
            for constraint in vertex.constraints:
                if isinstance(constraint, RadialPlacementFromChipConstraint):
                    raise PacmanPlaceException(
                        "A RadialPlacementFromChipConstraint will not work "
                        "with the OneToOnePlacer algorithm; use the "
                        "RadialPlacer algorithm instead")

        # Find and place vertices with hard constraints
        for vertex in machine_graph.vertices:
            if isinstance(vertex, AbstractVirtual):
                virtual_p = 0
                while placements.is_processor_occupied(
                        vertex.virtual_chip_x, vertex.virtual_chip_y,
                        virtual_p):
                    virtual_p += 1
                placements.add_placement(Placement(
                    vertex, vertex.virtual_chip_x, vertex.virtual_chip_y,
                    virtual_p))
                all_vertices_placed.add(vertex)
            elif locate_constraints_of_type(
                    vertex.constraints, ChipAndCoreConstraint):
                self._allocate_same_chip_as_group(
                    vertex, placements, resource_tracker,
                    same_chip_vertex_groups, all_vertices_placed, progress,
                    machine_graph)

        for grouped_vertices in one_to_one_groups:
            # Get unallocated vertices and placements of allocated vertices
            unallocated = list()
            chips = list()
            for vert in grouped_vertices:
                if vert in all_vertices_placed:
                    placement = placements.get_placement_of_vertex(vert)
                    chips.append((placement.x, placement.y))
                else:
                    unallocated.append(vert)
            if not chips:
                chips = None

            if 0 < len(unallocated) <=\
                    resource_tracker.get_maximum_cores_available_on_a_chip():
                # Try to allocate all vertices to the same chip
                self._allocate_one_to_one_group(
                    resource_tracker, unallocated, progress, placements, chips,
                    all_vertices_placed, machine_graph)
            # if too big or failed go on to other groups first

        # check all have been allocated if not do so now.
        for vertex in machine_graph.vertices:
            if vertex not in all_vertices_placed:
                self._allocate_same_chip_as_group(
                    vertex, placements, resource_tracker,
                    same_chip_vertex_groups, all_vertices_placed,
                    progress, machine_graph)

        progress.end()
        return placements

    @staticmethod
    def _allocate_one_to_one_group(
            resource_tracker, vertices, progress, placements, chips,
            all_vertices_placed, machine_graph):
        """
        :param ResourceTracker resource_tracker:
        :param list(MachineVertex) vertices:
        :param ~spinn_utilities.progress_bar.ProgressBar progress:
        :param Placements placements:
        :param chips:
        :type chips: iterable(tuple(int, int)) or None
        :param MachineGraph machine_graph: machine graph
        :param set(MachineVertex) all_vertices_placed:
        :rtype: bool
        """
        try:
            allocs = resource_tracker.allocate_constrained_group_resources(
                create_requirement_collections(vertices, machine_graph),
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
            all_vertices_placed, progress, machine_graph):
        """
        :param MachineVertex vertex:
        :param Placements placements:
        :param ResourceTracker tracker:
        :param dict(MachineVertex,set(MachineVertex)) same_chip_vertex_groups:
        :param ~spinn_utilities.progress_bar.ProgressBar progress:
        :param MachineGraph machine_graph:
        """
        if vertex not in all_vertices_placed:
            # get vert's
            vertices = same_chip_vertex_groups[vertex]

            resources = tracker.allocate_constrained_group_resources(
                create_requirement_collections(vertices, machine_graph))

            for (x, y, p, _, _), v in progress.over(
                    zip(resources, vertices), False):
                placements.add_placement(Placement(v, x, y, p))
                all_vertices_placed.add(v)
