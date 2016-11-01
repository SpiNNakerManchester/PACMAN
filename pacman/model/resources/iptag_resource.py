from pacman.model.resources.abstract_resource import AbstractResource
from pacman.model.decorators.overrides import overrides


class IPtagResource(AbstractResource):
    """ Represents the amount of local core memory available or used on a core\
        on a chip of the machine
    """

    __slots__ = [
        # the string representation of the ip address of the SpiNNaker machine
        # used by this iptag
        "_ip_address",

        # the port number used by the socket for this iptag
        "_port",

        # a boolean flag that indicates if the SDP headers are
        #  stripped before transmission of data
        "_strip_sdp",

        #  A fixed tag id to assign, or None if any tag is OK
        "_tag",

        # the identifier that states what type of data is being transmitted
        # through this iptag
        "_traffic_identifier",

        # The connection type needed to build the connection for this iptag
        "_connection_type"


    ]

    def __init__(self, ip_address, port, strip_sdp,
                 traffic_identifier, connection_type, tag=None):
        """

        :param ip_address: The IP address that the tag will cause data to be\
                    sent to
        :type ip_address: str
        :param port: The target port of the tag
        :type port: int or None
        :param strip_sdp: Whether the tag requires that SDP headers are\
                    stripped before transmission of data
        :type strip_sdp: bool
        :param tag: A fixed tag id to assign, or None if any tag is OK
        :type tag: int
        """
        self._ip_address = ip_address
        self._port = port
        self._strip_sdp = strip_sdp
        self._tag = tag
        self._traffic_identifier = traffic_identifier
        self._connection_type = connection_type

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

        :return:
        """
        return self._traffic_identifier

    @property
    def connection_type(self):
        """ the connection type needed for this iptag

        :return:
        """
        return self._connection_type

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

    @overrides(AbstractResource.get_value)
    def get_value(self):
        return [self._ip_address, self._port, self._strip_sdp, self._tag]

    def __repr__(self):
        return (
            "IPTagResource(ip_address={}, port={}, strip_sdp={}, tag={}, "
            "traffic_identifier={}, connection_type={})"
            .format(self._ip_address, self._port, self._strip_sdp, self._tag,
                    self._traffic_identifier, self._connection_type)
        )
