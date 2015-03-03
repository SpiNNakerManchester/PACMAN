from pacman.model.constraints.tag_allocator_constraints.\
    abstract_tag_allocator_constraint import AbstractTagAllocatorConstraint
import sys


class TagAllocatorRequireIptagConstraint(AbstractTagAllocatorConstraint):
    """ Constraint that indicates that an IP tag is required, and the\
        constraints of the tag required, if any.  Note that simply requiring\
        an IP tag creates a placement constraint, since only a fixed number\
        of tags are available on each board
    """

    def __init__(self, ip_address, port, strip_sdp, board_address=None,
                 tag_id=None):
        """

        :param ip_address: The IP address that the tag will cause data to be\
                    sent to
        :type ip_address: str
        :param port: The port that the tag will cause data to be sent to
        :type port: int
        :param strip_sdp: Whether the tag requires that SDP headers are\
                    stripped before transmission of data
        :type strip_sdp: bool
        :param board_address: Optional fixed board ip address
        :type board_address: str
        :param tag_id: Optional fixed tag id required
        :type tag_id: int
        """
        AbstractTagAllocatorConstraint.__init__(self, board_address, tag_id,
                                                port)
        self._ip_address = ip_address
        self._strip_sdp = strip_sdp

    @property
    def ip_address(self):
        """ The ip address to assign to the tag

        :return: An ip address
        :rtype: str
        """
        return self._ip_address

    @property
    def strip_sdp(self):
        """ Whether SDP headers should be stripped for this tag

        :return: True if the headers should be stripped, False otherwise
        :rtype: bool
        """
        return self._strip_sdp

    def is_tag_allocator_constraint(self):
        return True

    def rank(self):
        return sys.maxint - 4
