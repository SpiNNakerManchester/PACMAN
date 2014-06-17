__author__ = 'daviess'


class Placement(object):
    """
    Creates a new placement for a particular subvertex on a specific processor
    """

    def __init__(self, subvertex, processor):
        """

        :param subvertex: subvertex to be placed
        :param processor: processor on which the subvertex is to be placed
        :type subvertex: pacman.subgraph.subvertex.Subvertex
        :type processor: pacman.machine.processor.Processor
        :return: a new placement object
        :rtype: pacman.placements.placement.Placement
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def subvertex(self):
        """
        Returns the subvertex of this placement object

        :return: the subvertex of this placement object
        :rtype: pacman.subgraph.subvertex.Subvertex
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def processor(self):
        """
        Returns the processor on which the subvertex has been placed

        :return: the processor of this placement object
        :rtype: pacman.machine.processor.Processor
        :raises None: does not raise any known exceptions
        """
        pass
