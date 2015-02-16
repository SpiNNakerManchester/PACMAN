from pacman.model.constraints.tag_allocator_constraints.\
    abstract_tag_allocator_constraint import AbstractTagAllocatorConstraint
import sys


class TagAllocatorRequireIptagConstraint(AbstractTagAllocatorConstraint):

    def __init__(self, tag_id, board_address, is_reverse, address, stripe_sdp):
        AbstractTagAllocatorConstraint.__init__(self)
        self._board_address = board_address
        self._is_reverse_ip = is_reverse
        self._tag_id = tag_id
        self._address = address
        self._stripe_sdp = stripe_sdp

    @property
    def board_address(self):
        return self._board_address

    @property
    def tag_id(self):
        return self._tag_id

    @property
    def is_reverse(self):
        return self._is_reverse_ip

    @property
    def address(self):
        return self._address

    @property
    def stripe_sdp(self):
        return self._stripe_sdp

    def is_placer_constraint(self):
        return True

    def rank(self):
        return sys.maxint - 3