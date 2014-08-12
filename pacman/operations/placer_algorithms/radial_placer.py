from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
import logging

logger = logging.getLogger(__name__)


class RadialPlacer(BasicPlacer):
    """ An radial algorithm that can place a partitioned_graph onto a machine based off a
    circle out behaviour from a ethernet at 0 0
    """

    def __init__(self, machine, graph):
        """constructor to build a
        pacman.operations.placer_algorithms.RadialPlacer.RadialPlacer
        :param machine: The machine on which to place the partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        """
        BasicPlacer.__init__(self, machine, graph)

    #overloaded method from basicPlacer
    def _deal_with_non_constrainted_placement(self, subvertex, resources,
                                              chips):
        """overlaoded method of basic placer that changs the ordering in which
        chips are handed to the search alorirthm.

        :param subvertex: the subvert to place
        :param resources: the resources reuqired by the subvertex
        :param chips: the machines chips.
        :type subvertex: py:class'pacman.model.partitioned_graph.subvertex.SubVertex'
    :type resources: py:class'pacman.model.resource_container.ResourceContainer'
        :type chips: iterable of spinmachine.machine.Machine
        :return: a placement object
        :rtype: a py:class'pacman.model.placements.placements.Placements'
        :raise None: this class does not raise any known exceptions
        """
        processors_new_order = list()
        chips_to_check = list()

        for chip in chips:
            chips_to_check.append(chip)

        current_chip_list_to_check = list()

        current_chip_list_to_check.append(self._machine.get_chip_at(0, 0))

        while len(chips_to_check) != 0:
            next_chip_list_to_check = list()
            for chip in current_chip_list_to_check:
                if chip in chips_to_check:
                    processors_new_order.append(chip)
                    chips_to_check.remove(chip)
                    neabuoring_chip_coords = \
                        chip.router.get_neighbouring_chips_coords()
                    for neabour_data in neabuoring_chip_coords:
                        if neabour_data is not None:
                            neaubour_chip = \
                                self._machine.get_chip_at(neabour_data['x'],
                                                          neabour_data['y'])
                            if(neaubour_chip in chips_to_check and
                               not neaubour_chip in next_chip_list_to_check):
                                next_chip_list_to_check.append(neaubour_chip)
            current_chip_list_to_check = next_chip_list_to_check


        return BasicPlacer._deal_with_non_constrainted_placement(
            self, subvertex, resources, processors_new_order)