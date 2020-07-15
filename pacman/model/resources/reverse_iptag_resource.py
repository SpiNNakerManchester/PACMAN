# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class ReverseIPtagResource(object):
    """ Represents the ability to talk to a SpiNNaker machine by sending UDP\
        packets to it during execution.
    """

    __slots__ = [
        # The target port of the tag or None if this is to be assigned
        # elsewhere
        "_port",

        # The SDP port number to be used when constructing SDP packets from
        # the received UDP packets for this tag
        "_sdp_port",

        # A fixed tag ID to assign, or None if any tag is OK
        "_tag"
    ]

    def __init__(
            self, port=None, sdp_port=1, tag=None):
        """
        :param port: The UDP port to listen to on the board for this tag
            or None for a default
        :type port: int or None
        :param int sdp_port:
            The SDP port number to be used when constructing SDP packets from
            the received UDP packets for this tag
        :param tag: A fixed tag ID to assign, or None if any tag is OK
        :type tag: int or None
        """
        self._port = port
        self._sdp_port = sdp_port
        self._tag = tag

    @property
    def port(self):
        """ The port of the tag

        :rtype: int
        """
        return self._port

    @property
    def sdp_port(self):
        """ The SDP port to use when constructing the SDP message from the\
            received UDP message

        :rtype: int
        """
        return self._sdp_port

    @property
    def tag(self):
        """ The tag required, or None if any tag is OK

        :rtype: int or None
        """
        return self._tag

    def get_value(self):
        """
        :return: The description of the reverse IP tag.
        :rtype: list(int, int, int)
        """
        return [self._port, self._sdp_port, self._tag]

    def __repr__(self):
        return (
            "ReverseIPTagResource(port={}, sdp_port={}, tag={})"
            .format(self._port, self._sdp_port, self._tag)
        )

    def __eq__(self, other):
        return (self._port == other._port and
                self._sdp_port == other._sdp_port and
                self._tag == other._tag)

    def __hash__(self):
        return hash((self._port, self._sdp_port, self._tag))

    def __ne__(self, other):
        return not self.__eq__(other)
