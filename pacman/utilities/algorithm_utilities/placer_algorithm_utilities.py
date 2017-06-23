from pacman.model.constraints.placer_constraints\
    import PlacerChipAndCoreConstraint, PlacerSameChipAsConstraint
from pacman.model.constraints.placer_constraints \
    import PlacerBoardConstraint, PlacerRadialPlacementFromChipConstraint
from pacman.utilities import VertexSorter, ConstraintOrder


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

    # Dict of vertex to list of vertices on same chip (repeated lists expected)
    same_chip_vertices = dict()

    for vertex in vertices:
        # Find all vertices that have a same chip constraint associated with
        #  this vertex
        same_chip_as_vertices = list()
        for constraint in vertex.constraints:
            if isinstance(constraint, PlacerSameChipAsConstraint):
                same_chip_as_vertices.append(constraint.vertex)

        if same_chip_as_vertices:
            # Go through all the verts that want to be on the same chip as
            # the top level vert
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
