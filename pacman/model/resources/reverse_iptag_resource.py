from pacman.model.resources.abstract_resource import AbstractResource
from pacman.model.decorators.overrides import overrides


class ReverseIPtagResource(AbstractResource):
    """ Represents the amount of local core memory available or used on a core\
        on a chip of the machine
    """

    __slots__ = [
        # The target port of the tag
        "_port",

        # The SDP port number to be used when constructing SDP packets from
        # the received UDP packets for this tag
        "_sdp_port",

        # A fixed tag id to assign, or None if any tag is OK
        "_tag"
    ]

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

    @overrides(AbstractResource.get_value)
    def get_value(self):
        return [self._port, self._sdp_port, self._tag]
