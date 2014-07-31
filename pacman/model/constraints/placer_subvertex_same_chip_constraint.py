from pacman.model.constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint

import sys


class PlacerSubvertexSameChipConstraint(AbstractPlacerConstraint):
    """ A constraint that indicates that a subvertex should be placed on the\
        same chip as the given subvertex
    """
    
    def __init__(self, subvertex):
        """

        :param subvertex: The subvertex to place on the same chip
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :raise None: does not raise any known exceptions
        """
        AbstractPlacerConstraint.__init__(
            self, label="placer same chip constraint with subvertex {}"
                        .format(subvertex))
        self._subvertex = subvertex

    @property
    def rank(self):
        return sys.maxint - 2

    @property
    def subvertex(self):
        """ The subvertex to place on the same chip

        :return: a subvertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :raise None: does not raise any known exceptions
        """
        return self._subvertex

