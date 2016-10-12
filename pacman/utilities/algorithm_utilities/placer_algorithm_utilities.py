from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_constraints\
    .placer_same_chip_as_constraint import PlacerSameChipAsConstraint
from pacman.utilities.vertex_sorter import VertexSorter
from pacman.utilities.vertex_sorter import ConstraintOrder
from pacman.model.constraints.placer_constraints.placer_board_constraint \
    import PlacerBoardConstraint
from pacman.model.constraints.placer_constraints\
    .placer_radial_placement_from_chip_constraint \
    import PlacerRadialPlacementFromChipConstraint


def sort_vertices_by_known_constraints(vertices):
    """ Sort vertices to be placed by constraint so that those with\
        more restrictive constraints come first.
    """
    sorter = VertexSorter([
        ConstraintOrder(PlacerChipAndCoreConstraint, 1, ["p"]),
        ConstraintOrder(PlacerChipAndCoreConstraint, 2),
        ConstraintOrder(PlacerSameChipAsConstraint, 3),
        ConstraintOrder(PlacerBoardConstraint, 4),
        ConstraintOrder(PlacerRadialPlacementFromChipConstraint, 5)])
    return sorter.sort(vertices)


def get_same_chip_vertex_groups(vertices):
    """ Get a dictionary of vertex to vertex that must be placed on the same\
        chip
    """

    # Dict of vertex to list of vertices on same chip
    # (repeated lists expected)
    same_chip_vertices = dict()

    for vertex in vertices:

        # Find all vertices that this vertex should be on the same chip as
        same_as_vertices = list()
        for constraint in vertex.constraints:
            if isinstance(constraint, PlacerSameChipAsConstraint):
                same_as_vertices.append(constraint.vertex)

        if len(same_as_vertices) > 0:

            # Go through vertices that this vertex should be on the same
            # chip as
            for same_as_vertex in same_as_vertices:

                if (same_as_vertex not in same_chip_vertices and
                        vertex not in same_chip_vertices):

                    # Neither vertex has been seen, so add both to a new group
                    group = [vertex, same_as_vertex]
                    same_chip_vertices[vertex] = group
                    same_chip_vertices[same_as_vertex] = group

                elif vertex in same_chip_vertices:

                    # The current vertex has been seen elsewhere, so add the
                    # new vertex to the existing group
                    group = same_chip_vertices[vertex]
                    group.append(same_as_vertex)
                    same_chip_vertices[same_as_vertex] = group

                elif same_as_vertex in same_chip_vertices:

                    # The other vertex has been seen elsewhere, so add this
                    # vertex to the existing group
                    group = same_chip_vertices[same_as_vertex]
                    group.append(vertex)
                    same_chip_vertices[vertex] = group

                else:

                    # Both vertices have been seen elsewhere, so merge
                    # their groups
                    group_1 = same_chip_vertices[vertex]
                    group_2 = same_chip_vertices[same_as_vertex]
                    if group_1 != group_2:
                        group_1.extend(group_2)
                        for vert in group_2:
                            same_chip_vertices[vert] = group_1
        else:
            same_chip_vertices[vertex] = [vertex]

    return same_chip_vertices
