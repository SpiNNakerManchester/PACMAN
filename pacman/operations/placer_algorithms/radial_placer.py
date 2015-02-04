from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
import logging

logger = logging.getLogger(__name__)


class RadialPlacer(BasicPlacer):
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

    #overloaded method from basicPlacer
    def _deal_with_non_constrained_placement(self, subvertex, used_resources,
                                             chips, start_chip_x=0,
                                             start_chip_y=0):
        """overloaded method of basic placer that changes the ordering in which
        chips are handed to the search algorithm.

        :param subvertex: the subvertex to place
        :param used_resources: the used_resources required by the subvertex
        :param chips: the machines chips.
        :param start_chip_x: the x position of the chip to start the radial from
        :type start_chip_x: int
        :param start_chip_y: the y position of the chip to start the radial from
        :type start_chip_y: int
        :type subvertex:
        :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex'
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
            self, subvertex, used_resources, processors_new_order)