from pacman.model.constraints.placer_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint


class PlacerBoardConstraint(AbstractPlacerConstraint):
    """ A constraint on the board on which a placement is made
    """

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
