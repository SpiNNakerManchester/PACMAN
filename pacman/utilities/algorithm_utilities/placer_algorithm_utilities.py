from pacman.model.constraints.placer_constraints import (
    ChipAndCoreConstraint, SameChipAsConstraint, BoardConstraint,
    RadialPlacementFromChipConstraint)
from pacman.model.graphs.common.edge_traffic_type import EdgeTrafficType
from pacman.utilities import VertexSorter, ConstraintOrder
import functools
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


def group_vertices(vertices, same_group_as_function):
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
    same_chip_vertices = dict()

    for vertex in vertices:
        # Find all vertices that should be grouped with this vertex
        same_chip_as_vertices = same_group_as_function(vertex)

        if same_chip_as_vertices:
            # Go through all the vertices that want to be on the same chip as
            # the top level vertex
            for same_as_chip_vertex in same_chip_as_vertices:
                # Neither vertex has been seen
                if (same_as_chip_vertex not in same_chip_vertices and
                        vertex not in same_chip_vertices):
                    # add both to a new group
                    group = {vertex, same_as_chip_vertex}
                    same_chip_vertices[vertex] = group
                    same_chip_vertices[same_as_chip_vertex] = group

                # Both vertices have been seen elsewhere
                elif (same_as_chip_vertex in same_chip_vertices and
                        vertex in same_chip_vertices):
                    # merge their groups
                    group_1 = same_chip_vertices[vertex]
                    group_2 = same_chip_vertices[same_as_chip_vertex]
                    group_1.update(group_2)
                    for vert in group_1:
                        same_chip_vertices[vert] = group_1

                # The current vertex has been seen elsewhere
                elif vertex in same_chip_vertices:
                    # add the new vertex to the existing group
                    group = same_chip_vertices[vertex]
                    group.add(same_as_chip_vertex)
                    same_chip_vertices[same_as_chip_vertex] = group

                # The other vertex has been seen elsewhere
                elif same_as_chip_vertex in same_chip_vertices:
                    #  so add this vertex to the existing group
                    group = same_chip_vertices[same_as_chip_vertex]
                    group.add(vertex)
                    same_chip_vertices[vertex] = group

        else:
            same_chip_vertices[vertex] = {vertex}

    return same_chip_vertices
