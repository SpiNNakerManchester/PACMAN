__author__ = 'daviess'

from pacman.placements.placement import Placement
from pacman.exceptions import InvalidChipException, InvalidProcessorException,\
    ProcessorAlreadyInUseException


class Placements(object):
    """
    This object stores information related to the placement of subvertices\
    of the subgraph onto the machine
    """

    def __init__(self, machine):
        """

        :param machine: the machine on which the subvertex should be placed
        :type machine: pacman.machine.machine.Machine
        :return: a new placements object
        :rtype: pacman.placements.placements.Placements
        :raise None: does not raise any known exceptions
        """
        self._machine = machine
        self._placements = dict()

    def add_placement(self, subvertex, x, y, p):
        """
        Adds the placement of the subvertex on a processor to the list of\
        placements related to the specific machine and subgraph

        :param subvertex: the subvertex to be placed
        :param x: the x coordinate of the chip on which the subvertex is placed
        :param y: the y coordinate of the chip on which the subvertex is placed
        :param p: the processor on which the subvertex is placed
        :type subvertex: pacman.subgraph.subvertex.Subvertex
        :type x: int
        :type y: int
        :type p: int
        :return: None
        :rtype: None
        :raise pacman.exceptions.InvalidChipException: when the specified\
        chip does not exist in the current machine configuration
        :raise pacman.exceptions.InvalidProcessorException: when the\
        specified processor does not exist in the current machine configuration
        :raise pacman.exceptions.ProcessorAlreadyInUseException: when a\
        subvertex is mapped to a processor which is already target of the\
        placement for a different subvertex
        """
        if not self._machine.does_chip_exist_at_xy(x, y):
            raise InvalidChipException

        if not self._machine.get_chip_at_xy(x, y).does_processor_exist_at_id(p):
            raise InvalidProcessorException

        temp = Placement(subvertex, x, y, p)

        if temp.__repr__() not in self._placements:
            self._placements[temp.__repr__()] = temp
        else:
            raise ProcessorAlreadyInUseException

    def get_subvertex_placement(self, subvertex):
        """
        Returns the placement of a specific subvertex as a dictionary with keys\
        "x", "y" and "p", or None if the vertex has not been placed

        :param subvertex: the subvertex to search for
        :type subvertex: pacman.subgraph.subvertex.Subvertex
        :return: the placement of the given subvertex
        :rtype: pacman.placements.placement.Placement or None
        :raise None: does not raise any known exceptions
        """
        for temp_placement in self._placements:
            if temp_placement.subvertex == subvertex:
                return temp_placement

        return None

    def get_subvertex_on_processor(self, x, y, p):
        """Returns the subvertex on a specific processor or None if the\
        processor has not been allocated

        :param x: the x coordinate of the chip
        :param y: the y coordinate of the chip
        :param p: the processor on the chip
        :type x: int
        :type y: int
        :type p: int
        :return: the vertex placed on the given processor
        :rtype: pacman.subgraph.subvertex.Subvertex or None
        :raise None: does not raise any known exceptions
        """
        temp_placement = Placement.to_string(x, y, p)
        if temp_placement in self._placements:
            return self._placements[temp_placement]
        else:
            return None

    @property
    def placements(self):
        """
        Returns the list of placements of the current subgraph onto the\
        specific machine

        :return: list of placements
        :rtype: pacman.placements.placement.Placement
        :raise None: does not raise any known exceptions
        """
        return self._placements
