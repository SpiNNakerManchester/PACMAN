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


class IPtagResource(object):
    """ Represents the ability to have a SpiNNaker machine send messages to\
        you during execution.
    """

    __slots__ = [
        # The host IP address that will receive the data from this tag
        "_ip_address",

        # the port number that data from this tag will be sent to, or None
        # if the port is to be assigned elsewhere
        "_port",

        # a boolean flag that indicates if the SDP headers are
        # stripped before transmission of data
        "_strip_sdp",

        #  A fixed tag ID to assign, or None if any tag is OK
        "_tag",

        # the identifier that states what type of data is being transmitted
        # through this IP tag
        "_traffic_identifier"
    ]

    def __init__(
            self, ip_address, port, strip_sdp, tag=None,
            traffic_identifier="DEFAULT"):
        """
        :param str ip_address:
            The IP address of the host that will receive data from this tag
        :param port: The port that will
        :type port: int or None
        :param bool strip_sdp: Whether the tag requires that SDP headers are
            stripped before transmission of data
        :param tag: A fixed tag ID to assign, or None if any tag is OK
        :type tag: int or None
        :param str traffic_identifier: The traffic to be sent using this tag;
            traffic with the same traffic_identifier can be sent using
            the same tag
        """
        # pylint: disable=too-many-arguments
        self._ip_address = ip_address
        self._port = port
        self._strip_sdp = strip_sdp
        self._tag = tag
        self._traffic_identifier = traffic_identifier

    @property
    def ip_address(self):
        """ The IP address to assign to the tag

        :rtype: str
        """
        return self._ip_address

    @property
    def port(self):
        """ The port of the tag

        :rtype: int
        """
        return self._port

    @property
    def traffic_identifier(self):
        """ The traffic identifier for this IP tag

        """
        return self._traffic_identifier

    @property
    def strip_sdp(self):
        """ Whether SDP headers should be stripped for this tag

        :rtype: bool
        """
        return self._strip_sdp

    @property
    def tag(self):
        """ The tag required, or None if any tag is OK

        :rtype: int or None
        """
        return self._tag

    def get_value(self):
        """
        :return: The description of the IP tag.
        """
        return [
            self._ip_address, self._port, self._strip_sdp, self._tag,
            self._traffic_identifier
        ]

    def __repr__(self):
        return (
            "IPTagResource(ip_address={}, port={}, strip_sdp={}, tag={}, "
            "traffic_identifier={})".format(
                self._ip_address, self._port, self._strip_sdp, self._tag,
                self._traffic_identifier))

    def __eq__(self, other):
        """
        For unit tests ONLY so __hash__ and __eq__ pairing not done!
        """
        return (self._ip_address == other._ip_address and
                self._port == other._port and
                self._strip_sdp == other._strip_sdp and
                self._tag == other._tag and
                self._traffic_identifier == other._traffic_identifier)
