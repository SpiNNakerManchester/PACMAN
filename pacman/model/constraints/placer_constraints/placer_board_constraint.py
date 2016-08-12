from pacman.model.constraints.placer_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint
from pacman.model.decorators.overrides import overrides


class PlacerBoardConstraint(AbstractPlacerConstraint):
    """ A constraint on the board on which a placement is made
    """

    __slots__ = [
        #  The IP address of the Ethernet of the board to be used
        "_board_address"
    ]

    def __init__(self, board_address):
        """

        :param board_address:\
            The IP address of the Ethernet of the board to be used
        """
        self._board_address = board_address

    @property
    def board_address(self):
        """ The board of the constraint
        """
        return self._board_address

    def __repr__(self):
        return "PlacerBoardConstraint(board_address=\"{}\")".format(
            self._board_address)

    @overrides(AbstractPlacerConstraint.label)
    def label(self):
        return "placer constraint for board {}".format(self._board_address)