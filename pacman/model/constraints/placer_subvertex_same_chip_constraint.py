from pacman.model.constraints.abstract_placer_constraint import AbstractPlacerConstraint


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
        pass
        
    def is_placer_constraint(self):
        """ Overridden method to indicate that this is a placer constraint
        """
        return True

    @property
    def subvertex(self):
        """ The subvertex to place on the same chip

        :return: a subvertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :raise None: does not raise any known exceptions
        """
        return self._x

