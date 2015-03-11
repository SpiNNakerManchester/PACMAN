import sys
from pacman.model.constraints.abstract_constraints.\
    abstract_tag_allocator_constraint import \
    AbstractTagAllocatorConstraint


class TagAllocatorRequireReverseIptagConstraint(
        AbstractTagAllocatorConstraint):
    """ Constraint that indicates that a Reverse IP tag is required, and the\
        constraints of the tag required, if any.  Note that simply requiring\
        an IP tag creates a placement constraint, since only a fixed number\
        of tags are available on each board
    """

    def __init__(self, port, sdp_port=1, board_address=None, tag_id=None):
        """

        :param port: The UDP port to listen to on the board for this tag
        :type port: int
        :param sdp_port: The SDP port number to be used when constructing SDP\
                    packets from the received UDP packets for this tag
        :type sdp_port: int
        :param board_address: Optional fixed board ip address
        :type board_address: str
        :param tag_id: Optional fixed tag id required
        :type tag_id: int
        """
        AbstractTagAllocatorConstraint.__init__(self, board_address, tag_id,
                                                port)
        self._sdp_port = sdp_port

    @property
    def sdp_port(self):
        """ The SDP port to use when constructing the SDP message from the\
            received UDP message
        """
        return self._sdp_port

    def is_tag_allocator_constraint(self):
        return True

    def get_rank(self):
        if self._tag is not None and self._board_address is not None:
            return sys.maxint - 2
        elif self._tag is not None:
            return sys.maxint - 3
        elif self._board_address is not None:
            return sys.maxint - 4
        return sys.maxint - 6
