from .abstract_placer_constraint import AbstractPlacerConstraint


class BoardConstraint(AbstractPlacerConstraint):
    """ A constraint on the board on which a placement is made.
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
        return "BoardConstraint(board_address=\"{}\")".format(
            self._board_address)

    def __eq__(self, other):
        if not isinstance(other, BoardConstraint):
            return False
        return self._board_address == other.board_address

    def __hash__(self):
        return hash((self._board_address,))
