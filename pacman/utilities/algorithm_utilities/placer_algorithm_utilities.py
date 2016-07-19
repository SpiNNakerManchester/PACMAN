from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_constraints\
    .placer_same_chip_as_constraint import PlacerSameChipAsConstraint
from pacman.utilities.vertex_sorter import VertexSorter
from pacman.utilities.vertex_sorter import ConstraintOrder
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_iptag_constraint \
    import TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_reverse_iptag_constraint \
    import TagAllocatorRequireReverseIptagConstraint
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
        ConstraintOrder(TagAllocatorRequireIptagConstraint, 5, ["tag"]),
        ConstraintOrder(TagAllocatorRequireReverseIptagConstraint, 5, ["tag"]),
        ConstraintOrder(TagAllocatorRequireIptagConstraint, 6),
        ConstraintOrder(TagAllocatorRequireReverseIptagConstraint, 6),
        ConstraintOrder(PlacerRadialPlacementFromChipConstraint, 7)
    ])
    return sorter.sort(vertices)
