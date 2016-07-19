from pacman.model.constraints.tag_allocator_constraints.\
    abstract_tag_allocator_constraint import AbstractTagAllocatorConstraint


class TagAllocatorRequireReverseIptagConstraint(
        AbstractTagAllocatorConstraint):
    """ Constraint that indicates that a Reverse IP tag is required
    """

    def __init__(self, port, sdp_port=1, tag=None):
        """

        :param port: The target port of the tag
        :type port: int
        :param port: The UDP port to listen to on the board for this tag
        :type port: int
        :param sdp_port:\
            The SDP port number to be used when constructing SDP packets from\
            the received UDP packets for this tag
        :type sdp_port: int
        :param tag: A fixed tag id to assign, or None if any tag is OK
        :type tag: int
        """
        self._port = port
        self._sdp_port = sdp_port
        self._tag = tag

    @property
    def port(self):
        """ The port of the tag

        :return: The port of the tag
        :rtype: int
        """
        return self._port

    @property
    def sdp_port(self):
        """ The SDP port to use when constructing the SDP message from the\
            received UDP message
        """
        return self._sdp_port

    @property
    def tag(self):
        """ The tag required, or None if any tag is OK

        :return: The tag or None
        :rtype: int
        """
        return self._tag
