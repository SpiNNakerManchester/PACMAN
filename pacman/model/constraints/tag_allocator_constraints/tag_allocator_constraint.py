from pacman.model.constraints.abstract_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint

import sys


class TagAllocatorConstraint(AbstractPlacerConstraint):

    def __init__(self, tag_id, board_address, is_reverse):
        AbstractPlacerConstraint.__init__(
            self, "Placement vertex near ethernet on board {} ass it needs an "
                  "entry in the IPTAG table with tag {}"
            .format(board_address, tag_id))
        self._board_address = board_address
        self._is_reverse_ip = is_reverse
        self._tag_id = tag_id

    @property
    def board_address(self):
        return self._board_address

    @property
    def tag_id(self):
        return self._tag_id

    @property
    def is_reverse(self):
        return self._is_reverse_ip

    def is_placer_constraint(self):
        return True

    def rank(self):
        return sys.maxint - 3