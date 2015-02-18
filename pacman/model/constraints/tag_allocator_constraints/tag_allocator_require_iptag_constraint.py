from pacman.model.constraints.tag_allocator_constraints.\
    abstract_tag_allocator_constraint import AbstractTagAllocatorConstraint
import sys


class TagAllocatorRequireIptagConstraint(AbstractTagAllocatorConstraint):

    def __init__(self, tag_id, board_address, address, strip_sdp, port):
        AbstractTagAllocatorConstraint.__init__(self, board_address, port,
                                                tag_id)
        self._address = address
        self._stripe_sdp = strip_sdp

    @property
    def address(self):
        return self._address

    @property
    def strip_sdp(self):
        return self._stripe_sdp

    def is_placer_constraint(self):
        return True

    def is_tag_allocator_constraint(self):
        return True

    def rank(self):
        return sys.maxint - 4