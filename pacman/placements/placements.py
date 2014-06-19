__author__ = 'daviess'


class Placements(object):
    """
    This object stores information related to the placement of subvertices\
    of the subgraph onto the machine
    """

    def __init__(self):
        """

        :return: a new placements object
        :rtype: pacman.placements.placements.Placements
        :raise None: does not raise any known exceptions
        """
        pass

#    def __init__(self, subgraph, machine):
#        """
#
#        :param subgraph: subgraph to which the placements refers
#        :param machine: machine on which the placements is performed
#        :type subgraph: pacman.subgraph.subgraph.Subgraph
#        :type machine: pacman.machine.machine.Machine
#        :return: a new placements object
#        :rtype: pacman.placements.placements.Placements
#        :raise None: does not raise any known exceptions
#        """
#        pass

    def add_placement(self, subvertex, chip, processor):
        """
        Adds the placement of the subvertex on a processor to the list of\
        placements related to the specific machine and subgraph

        :param subvertex: the subvertex to be placed
        :type subvertex: pacman.subgraph.subvertex.Subvertex
        :param chip: the chip on which the subvertex is placed
        :type chip: pacman.machine.chip.Chip
        :param processor: the processor on which the subvertex is placed
        :type processor: pacman.machine.processor.Processor
        :return: None
        :rtype: None
        :raise pacman.exceptions.InvalidChipException: if the specified\
        chip does not exist in the current machine configuration
        :raise pacman.exceptions.InvalidProcessorException: if the\
        specified processor does not exist in the current machine configuration
        """
        pass

    @property
    def placements(self):
        """
        Returns the list of placements of the current subgraph onto the specific machine

        :return: list of placements
        :rtype: pacman.placements.placement.Placement
        :raise None: does not raise any known exceptions
        """
        pass
