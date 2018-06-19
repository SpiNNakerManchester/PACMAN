class ReverseIPtagResource(object):
    """ Represents the amount of local core memory available or used on a core\
        on a chip of the machine
    """

    __slots__ = [
        # The target port of the tag or None if this is to be assigned
        # elsewhere
        "_port",

        # The SDP port number to be used when constructing SDP packets from
        # the received UDP packets for this tag
        "_sdp_port",

        # A fixed tag ID to assign, or None if any tag is OK
        "_tag",

        # A board IP address which is where this reverse IPTag is to be \
        # placed
        "_board"
    ]

    def __init__(self, board, port=None, sdp_port=1, tag=None):
        """

        :param board: A board IP address which is where this reverse IPTag is\
            to be placed
        :type board: str
        :param port: The target port of the tag or None to assign elsewhere
        :type port: int or None
        :param port: The UDP port to listen to on the board for this tag
        :type port: int
        :param sdp_port: The SDP port number to be used when constructing \
            SDP packets from the received UDP packets for this tag.
        :type sdp_port: int
        :param tag: A fixed tag ID to assign, or None if any tag is OK
        :type tag: int or None
        """
        self._port = port
        self._sdp_port = sdp_port
        self._tag = tag
        self._board = board

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
            received UDP message.
        """
        return self._sdp_port

    @property
    def tag(self):
        """ The tag required, or None if any tag is OK

        :return: The tag or None
        :rtype: int
        """
        return self._tag

    @property
    def board(self):
        """
        A board IP address which is where this reverse IPTag is to be placed

        :return: str
        """
        return self._board

    def get_value(self):
        return [self._board, self._port, self._sdp_port, self._tag]

    def __repr__(self):
        return ("ReverseIPTagResource(board={}, port={}, sdp_port={}, tag={})"
                .format(self._board, self._port, self._sdp_port, self._tag))
