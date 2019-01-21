import functools
import sys
from pacman.model.constraints.placer_constraints import (
    ChipAndCoreConstraint, SameChipAsConstraint, BoardConstraint,
    RadialPlacementFromChipConstraint)
from pacman.model.graphs.common.edge_traffic_type import EdgeTrafficType
from pacman.utilities import VertexSorter, ConstraintOrder
from pacman.model.graphs.abstract_virtual_vertex import AbstractVirtualVertex


def sort_vertices_by_known_constraints(vertices):
    """ Sort vertices to be placed by constraint so that those with\
        more restrictive constraints come first.
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

    :param vertex: The vertex to search with
    :param graph: The graph containing the vertex
    """
    # Virtual vertices can't be forced on different chips
    if isinstance(vertex, AbstractVirtualVertex):
        return []
    same_chip_as_vertices = list()
    for constraint in vertex.constraints:
        if isinstance(constraint, SameChipAsConstraint):
            same_chip_as_vertices.append(constraint.vertex)

    for edge in filter(
            lambda edge: edge.traffic_type == EdgeTrafficType.SDRAM,
            graph.get_edges_starting_at_vertex(vertex)):
        same_chip_as_vertices.append(edge.post_vertex)
    return same_chip_as_vertices


def get_same_chip_vertex_groups(graph):
    """ Get a dictionary of vertex to list of vertices that must be placed on\
       the same chip

    :param graph: The graph containing the vertices
    """
    return group_vertices(graph.vertices, functools.partial(
        get_vertices_on_same_chip, graph=graph))


def group_vertices(vertices, same_group_as_function, cutoff=sys.maxsize):
    """ Group vertices according to some function that can indicate the groups\
        that any vertex can be contained within

    :param vertices: The vertices to group
    :param same_group_as_function:\
        A function which takes a vertex and returns vertices that should be in\
        the same group (excluding the original vertex)
    :return:\
        A dictionary of vertex to list of vertices that are grouped with it
    """

    groups = create_vertices_groups(vertices, same_group_as_function)
    # Dict of vertex to setof vertices on same chip (repeated lists expected)
    # A empty set value indicates a set that is too big.
    same_chip_vertices = dict()
    for group in groups:
        for vertex in group:
            same_chip_vertices[vertex] = group
    for vertex in vertices:
        if vertex not in same_chip_vertices:
            same_chip_vertices[vertex] = {vertex}
    return same_chip_vertices


def add_set(all_sets, new_set):
    for a_set in all_sets:
        intersection =  new_set & a_set
        if intersection:
            all_sets.remove(a_set)
            union = a_set | new_set
            add_set(all_sets, union)
            return
    all_sets.append(new_set)
    return


def create_vertices_groups(vertices, same_group_as_function):
    groups = list()
    for vertex in vertices:
        same_chip_as_vertices = same_group_as_function(vertex)
        if same_chip_as_vertices:
            same_chip_as_vertices = set(same_chip_as_vertices)
            same_chip_as_vertices.add(vertex)
            # Singletons on interesting and added later if needed
            if len(same_chip_as_vertices) > 1:
                add_set(groups, same_chip_as_vertices)
    return groups


def concat_all_groups(same_chip_as_vertices, same_chip_vertices, cutoff):
    """
    Will create a set which concatenate the vertixes in same_chip_as_vertices
    with all the vertices in sets already saved for each of the orignal
    vertices.

    If the resulting set is bigger than the cutoff empty is returned.

    :param same_chip_as_vertices:
    :param same_chip_vertices:
    :param cutoff:
    :return:
    """
    if len(same_chip_as_vertices) >= cutoff:
        return set()
    # clone so we can iterate over it and change result
    result = same_chip_as_vertices
    for vertex in same_chip_as_vertices:
        if vertex in same_chip_vertices:
            if same_chip_vertices[vertex]:
                result = result | same_chip_vertices[vertex]
                if len(result) >= cutoff:
                    return set()
            else:
                return set()
    return result
