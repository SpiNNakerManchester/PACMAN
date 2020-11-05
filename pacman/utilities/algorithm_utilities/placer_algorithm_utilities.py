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

import functools
from collections import OrderedDict
from spinn_utilities.ordered_set import OrderedSet
from pacman.model.constraints.placer_constraints import (
    ChipAndCoreConstraint, SameChipAsConstraint, BoardConstraint,
    RadialPlacementFromChipConstraint)
from pacman.model.graphs.common.edge_traffic_type import EdgeTrafficType
from pacman.utilities import VertexSorter, ConstraintOrder
from pacman.model.graphs.abstract_virtual import AbstractVirtual


def sort_vertices_by_known_constraints(vertices):
    """ Sort vertices to be placed by constraint so that those with\
        more restrictive constraints come first.

    :param list(ApplicationVertex) vertices:
    :rtype: list(ApplicationVertex)
    """
    sorter = VertexSorter([
        ConstraintOrder(ChipAndCoreConstraint, 1, ["p"]),
        ConstraintOrder(ChipAndCoreConstraint, 2),
        ConstraintOrder(SameChipAsConstraint, 3),
        ConstraintOrder(BoardConstraint, 4),
        ConstraintOrder(RadialPlacementFromChipConstraint, 5)])
    return sorter.sort(vertices)


def get_vertices_on_same_chip(vertex, graph):
    """ Get the vertices that must be on the same chip as the given vertex

    :param AbstractVertex vertex: The vertex to search with
    :param Graph graph: The graph containing the vertex
    :rtype: set(AbstractVertex)
    """
    # Virtual vertices can't be forced on different chips
    if isinstance(vertex, AbstractVirtual):
        return []
    same_chip_as_vertices = OrderedSet()
    for constraint in vertex.constraints:
        if isinstance(constraint, SameChipAsConstraint):
            same_chip_as_vertices.add(constraint.vertex)

    same_chip_as_vertices.update(
        edge.post_vertex
        for edge in graph.get_edges_starting_at_vertex(vertex)
        if edge.traffic_type == EdgeTrafficType.SDRAM)
    return same_chip_as_vertices


def get_same_chip_vertex_groups(graph):
    """ Get a dictionary of vertex to list of vertices that must be placed on\
       the same chip

    :param Graph graph: The graph containing the vertices
    :rtype: dict(AbstractVertex, set(AbstractVertex))
    """
    groups = create_vertices_groups(graph.vertices, functools.partial(
        get_vertices_on_same_chip, graph=graph))
    # Dict of vertex to set of vertices on same chip (repeated lists expected)
    # A empty set value indicates a set that is too big.
    same_chip_vertices = OrderedDict()
    for group in groups:
        for vertex in group:
            same_chip_vertices[vertex] = group
    for vertex in graph.vertices:
        if vertex not in same_chip_vertices:
            same_chip_vertices[vertex] = {vertex}
    return same_chip_vertices


def add_set(all_sets, new_set):
    """
    Adds a new set into the list of sets, concatenating sets if required.

    If the new set does not overlap any existing sets it is added.

    However if the new sets overlaps one or more existing sets, a superset is
    created combining all the overlapping sets.
    Existing overlapping sets are removed and only the new superset is added.

    :param list(set) all_sets: List of non-overlapping sets
    :param set new_set:
        A new set which may or may not overlap the previous sets.
    """

    union = OrderedSet()
    removes = []
    for a_set in all_sets:
        if not new_set.isdisjoint(a_set):
            removes.append(a_set)
            union |= a_set
    union |= new_set
    if removes:
        for a_set in removes:
            all_sets.remove(a_set)
    all_sets.append(union)


def create_vertices_groups(vertices, same_group_as_function):
    """
    :param iterable(AbstractVertex) vertices:
    :param same_group_as_function:
    :type same_group_as_function:
        callable(AbstractVertex, set(AbstractVertex))
    """
    groups = list()
    done = set()
    for vertex in vertices:
        if vertex in done:
            continue
        same_chip_as_vertices = same_group_as_function(vertex)
        if same_chip_as_vertices:
            same_chip_as_vertices.add(vertex)
            # Singletons on interesting and added later if needed
            if len(same_chip_as_vertices) > 1:
                add_set(groups, same_chip_as_vertices)
            done.update(same_chip_as_vertices)
    return groups
