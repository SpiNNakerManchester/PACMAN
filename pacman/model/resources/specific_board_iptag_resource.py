from pacman.model.resources import AbstractResource
from spinn_utilities.overrides import overrides


class SpecificBoardTagResource(AbstractResource):
    """
    resource that allocates a tag on a specific board before the class needing
    it has been built
    """

    __slots__ = [

        # The host ip address that will receive the data from this tag
        "_ip_address",

        # the port number that data from this tag will be sent to, or None
        # if the port is to be assigned elsewhere
        "_port",

        # a boolean flag that indicates if the SDP headers are
        # stripped before transmission of data
        "_strip_sdp",

        #  A fixed tag id to assign, or None if any tag is OK
        "_tag",

        # the identifier that states what type of data is being transmitted
        # through this iptag
        "_traffic_identifier",

        # the board ip address that this tag is going to be placed upon
        "_board"

    ]

    def __init__(self, board, ip_address, port, strip_sdp, tag=None,
                 traffic_identifier="DEFAULT"):
        """
        :param board: the ip address of the board to which this tag is to be\
                associated with
        :type board: str
        :param ip_address: The ip address of the host that will receive data\
                    from this tag
        :type ip_address: str
        :param port: The port that will
        :type port: int or None
        :param strip_sdp: Whether the tag requires that SDP headers are\
                    stripped before transmission of data
        :type strip_sdp: bool
        :param tag: A fixed tag id to assign, or None if any tag is OK
        :type tag: int
        :param traffic_identifier: The traffic to be sent using this tag; \
                    traffic with the same traffic_identifier can be sent using\
                    the same tag
        :type traffic_identifier: str
        """
        self._board = board
        self._ip_address = ip_address
        self._port = port
        self._strip_sdp = strip_sdp
        self._tag = tag
        self._traffic_identifier = traffic_identifier

    @property
    def ip_address(self):
        """ The ip address to assign to the tag

        :return: An ip address
        :rtype: str
        """
        return self._ip_address

    @property
    def port(self):
        """ The port of the tag

        :return: The port of the tag
        :rtype: int
        """
        return self._port

    @property
    def traffic_identifier(self):
        """ the traffic identifier for this iptag

        """
        return self._traffic_identifier

    @property
    def strip_sdp(self):
        """ Whether SDP headers should be stripped for this tag

        :return: True if the headers should be stripped, False otherwise
        :rtype: bool
        """
        return self._strip_sdp

    @property
    def tag(self):
        """ The tag required, or None if any tag is OK

        :return: The tag or None
        :rtype: int
        """
        return self._tag

    @property
    def board(self):
        """ the board ip address that this tag is to reside on
        
        :return: ip address
        """
        return self._board

    @overrides(AbstractResource.get_value)
    def get_value(self):
        return [
            self._board, self._ip_address, self._port, self._strip_sdp,
            self._tag, self._traffic_identifier
        ]

    def __repr__(self):
        return (
            "IPTagResource(board_address={}, ip_address={}, port={}, "
            "strip_sdp={}, tag={}, traffic_identifier={})".format(
                self._board, self._ip_address, self._port, self._strip_sdp,
                self._tag, self._traffic_identifier)
        )
