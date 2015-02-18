import logging
from pacman import exceptions
from pacman.model.constraints.placer_constraints.\
    placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_constraints.\
    placer_subvertex_same_chip_constraint import \
    PlacerSubvertexSameChipConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    abstract_tag_allocator_constraint import \
    AbstractTagAllocatorConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_reverse_iptag_constraint import \
    TagAllocatorRequireReverseIptagConstraint

from pacman.operations.abstract_algorithms.\
    abstract_requires_tag_allocator import \
    AbstractRequiresTagAllocator

from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
from pacman.model.constraints.placer_constraints.\
    placer_radial_placement_from_chip_constraint \
    import PlacerRadialPlacementFromChipConstraint


logger = logging.getLogger(__name__)


class RadialPlacer(BasicPlacer, AbstractRequiresTagAllocator):
    """ An radial algorithm that can place a partitioned_graph onto a
     machine based off a circle out behaviour from a ethernet at 0 0
    """

    def __init__(self, machine):
        """constructor to build a
        pacman.operations.placer_algorithms.RadialPlacer.RadialPlacer
        :param machine: The machine on which to place the partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        """
        BasicPlacer.__init__(self, machine)
        AbstractRequiresTagAllocator.__init__(self)
        self._supported_constraints.append(
            PlacerRadialPlacementFromChipConstraint)
        self._supported_constraints.append(TagAllocatorRequireIptagConstraint)
        self._supported_constraints.append(
            TagAllocatorRequireReverseIptagConstraint)

    def _reduce_constraints(self, constraints, subvertex_label, placements):
        """ tries to reduce the placement constraints into one manageable one.\
        NOT CALLABLE OUTSIDE CLASSES THAT INHERIT FROM THIS ONE

        :param constraints: the constraints placed on a vertex
        :param subvertex_label: the label from a given subvertex
        :param placements: the current list of placements
        :type constraints: iterable list of pacman.model.constraints.AbstractConstraints
        :type subvertex_label: str
        :type placements: iterable of pacman.model.placements.placement.Placement
        :return a reduced placement constraint
        :rtype: pacman.model.constraints.PlacerChipAndCoreConstraint
        :raise None: does not raise any known exception
        """
        returned_constraints = list()
        x = None
        y = None
        p = None
        sorted(constraints, key=lambda const: const.rank)
        for constraint in constraints:
            # fixed constraint
            if isinstance(constraint, PlacerChipAndCoreConstraint):
                x = self._check_param(constraint.x, x, subvertex_label)
                y = self._check_param(constraint.y, y, subvertex_label)
                p = self._check_param(constraint.p, p, subvertex_label)

            # tied to fixed constraint if exists
            elif isinstance(constraint, PlacerSubvertexSameChipConstraint):
                other_subvertex = constraint.subvertex
                other_placement = \
                    placements.get_placement_of_subvertex(other_subvertex)
                if other_placement is not None:
                    x = self._check_param(x, other_placement.x, subvertex_label)
                    y = self._check_param(y, other_placement.y, subvertex_label)
                    p = self._check_param(p, other_placement.p, subvertex_label)
                x = self._check_param(other_placement.x, x, subvertex_label)
                y = self._check_param(other_placement.y, y, subvertex_label)
                p = self._check_param(other_placement.p, p, subvertex_label)

            # check fixed constraint over taggable constraint
            if isinstance(constraint, AbstractTagAllocatorConstraint):

                # if theres a fixed constraint, locate the board id needed to
                #  meet that one
                if x is not None and y is not None:
                    chip = self._machine.get_chip_at(x, y)
                    ethernet_chip = \
                        self._machine.get_chip_at(chip.nearest_ethernet_x,
                                                  chip.nearest_ethernet_y)

                    if (constraint.board_address is not None
                            and constraint.board_address
                            != ethernet_chip.ip_address):
                        raise exceptions.PacmanConfigurationException(
                            "The fixed placement constraint of {}:{}:{} does"
                            "not work with the board address {} as set by the "
                            "tagable constrant {}"
                            .format(x, y, p, constraint.board_address))
                else:
                    # check that tag allocator is happy with placement
                    ethernet_area_code = self._tag_allocator.locate_board_for(
                        constraint, self._placement_tracker)
                    constraint.board_address = ethernet_area_code
                    returned_constraints.append(constraint)

            #if radial, then just add
            if isinstance(constraint, PlacerRadialPlacementFromChipConstraint):
                returned_constraints.append(constraint)

        #check combinations of radial with fixed
        if x is not None and y is not None:
            for constraint in returned_constraints:
                if (isinstance(constraint,
                               PlacerRadialPlacementFromChipConstraint)
                        and constraint.x != x and constraint.y != y):
                    raise exceptions.PacmanConfigurationException(
                        "you have set two constriants which conflict each "
                        "other. These are a radial constraint at {}:{} and a "
                        "chip_and_core / same-chip constraint at coords {}:{}"
                        .format(constraint.x, constraint.y, x, y)
                    )

            returned_constraints.append(PlacerChipAndCoreConstraint(x, y, p))
        return returned_constraints

    def _deal_with_constraint_placement(
            self, placement_constraints, subvertex_label, subvertex_resources):
        """ used to handle radial placement constraints in a radial form
        from a given chip

        :param placement_constraints:
        :param subvertex_label:
        :param subvertex_resources:
        :return:
        """
        chip_and_core = None
        taggable = None
        radial = None
        for constraint in placement_constraints:
            if isinstance(constraint, PlacerChipAndCoreConstraint):
                chip_and_core = constraint
            elif isinstance(constraint, PlacerRadialPlacementFromChipConstraint):
                radial = constraint
            elif isinstance(constraint, AbstractTagAllocatorConstraint):
                taggable = constraint
            else:
                raise exceptions.PacmanConfigurationException(
                    "I do not know what to do with this constraint! AHHHG")
        x, y, p = None, None, None
        if chip_and_core is not None:
            x, y, p = BasicPlacer._deal_with_constraint_placement(
                self, chip_and_core, subvertex_label, subvertex_resources)
        elif radial is not None:
            x, y, p = self._deal_with_non_constrained_placement(
                subvertex_label, subvertex_resources, self._machine.chips,
                radial.x, radial.y)

        # check for taggable constraints

        if taggable is not None:
            self._tag_allocator.allocate_for_constraint(taggable,
                                                        subvertex_label)
            if x is None and y is None and p is None:
                chips = self._placement_tracker.\
                    get_chips_in_ethernet_area_code(taggable.board_address)
                return self._deal_with_non_constrained_placement(
                    subvertex_label, subvertex_resources, chips, chips[0].x,
                    chips[0].y)
        return x, y, p

    #overloaded method from basicPlacer
    def _deal_with_non_constrained_placement(
            self, subvertex_label, used_resources, chips, start_chip_x=0,
            start_chip_y=0):
        """overloaded method of basic placer that changes the ordering in which
        chips are handed to the search algorithm.

        :param subvertex_label: the subvertex_label for placement
        :param used_resources: the used_resources required by the subvertex
        :param chips: the machines chips.
        :param start_chip_x: the x position of the chip to start the radial from
        :type start_chip_x: int
        :param start_chip_y: the y position of the chip to start the radial from
        :type start_chip_y: int
        :type used_resources:
        py:class'pacman.model.resource_container.ResourceContainer'
        :type chips: iterable of spinn_machine.chip.Chip
        :return: a placement object
        :rtype: a py:class'pacman.model.placements.placements.Placements'
        :raise None: this class does not raise any known exceptions
        """
        processors_new_order = list()
        chips_to_check = list()

        for chip in chips:
            chips_to_check.append(chip)

        current_chip_list_to_check = list()

        current_chip_list_to_check.append(
            self._machine.get_chip_at(start_chip_x, start_chip_y))

        while len(chips_to_check) != 0:
            next_chip_list_to_check = list()
            for chip in current_chip_list_to_check:
                if chip in chips_to_check:
                    processors_new_order.append(chip)
                    chips_to_check.remove(chip)
                    neighbouring_chip_coordinates = \
                        chip.router.get_neighbouring_chips_coords()
                    for neighbour_data in neighbouring_chip_coordinates:
                        if neighbour_data is not None:
                            neighbour_chip = \
                                self._machine.get_chip_at(neighbour_data['x'],
                                                          neighbour_data['y'])
                            if(neighbour_chip in chips_to_check and
                               not neighbour_chip in next_chip_list_to_check):
                                next_chip_list_to_check.append(neighbour_chip)
            current_chip_list_to_check = next_chip_list_to_check

        return BasicPlacer._deal_with_non_constrained_placement(
            self, subvertex_label, used_resources, processors_new_order)

    def requires_tag_allocator(self):
        """ method from requires tag allcoator component

        :return:
        """
        return True