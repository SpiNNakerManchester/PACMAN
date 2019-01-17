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

    # Dict of vertex to list of vertices on same chip (repeated lists expected)
    # A None value indicates a set that is too big.
    same_chip_vertices = dict()
    for vertex in vertices:
        if vertex in same_chip_vertices:
            check = same_chip_vertices[vertex] is not None
        else:
            check = True
        if check:
            # Find all vertices that should be grouped with this vertex
            same_chip_as_vertices = same_group_as_function(vertex)
            if same_chip_as_vertices:
                # Make 100% sure we have a set
                same_chip_as_vertices = set(same_chip_as_vertices)
                # Make sure set includes original vertex
                same_chip_as_vertices.add(vertex)
                # Concat all the same chip groups known
                group = concat_all_groups(
                    same_chip_as_vertices, same_chip_vertices, cutoff)

                if group:
                    assert len(group) >= len(same_chip_as_vertices)
                    same_chip_as_vertices = group
                # Set all to this concat group
                for same_as_chip_vertex in same_chip_as_vertices:
                    same_chip_vertices[same_as_chip_vertex] = group
            else:
                same_chip_vertices[vertex] = {vertex}

    # Change the too big groups to just a group with self
    for vertex in vertices:
        if same_chip_vertices[vertex] is None:
            same_chip_vertices[vertex] = {vertex}

    return same_chip_vertices


def concat_all_groups(same_chip_as_vertices, same_chip_vertices, cutoff):
    """
    Will create a set which concatenate the vertixes in same_chip_as_vertices
    with all the vertices in sets already saved for each of the orignal
    vertices.

    If the resulting set is bigger than the cutoff None is returned.

    :param same_chip_as_vertices:
    :param same_chip_vertices:
    :param cutoff:
    :return:
    """
    if len(same_chip_as_vertices) >= cutoff:
        return None
    # clone so we can iterate over it and change result
    result = same_chip_as_vertices
    for vertex in same_chip_as_vertices:
        if vertex in same_chip_vertices:
            if same_chip_vertices[vertex] is None:
                return None
            result = result | same_chip_vertices[vertex]
            if len(result) >= cutoff:
                return None
    return result
