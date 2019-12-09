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


class SpecificBoardTagResource(object):
    """ A resource that allocates a tag on a specific board before the class\
        needing it has been built.
    """

    __slots__ = [
        # The host IP address that will receive the data from this tag
        "_ip_address",

        # The port number that data from this tag will be sent to, or None
        # if the port is to be assigned elsewhere
        "_port",

        # A boolean flag that indicates if the SDP headers are stripped before
        # transmission of data
        "_strip_sdp",

        # A fixed tag ID to assign, or None if any tag is OK
        "_tag",

        # The identifier that states what type of data is being transmitted
        # through this IP tag
        "_traffic_identifier",

        # The board IP address that this tag is going to be placed upon
        "_board"
    ]

    def __init__(self, board, ip_address, port, strip_sdp, tag=None,
                 traffic_identifier="DEFAULT"):
        """
        :param str board:
            The IP address of the board to which this tag is to be associated
            with
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
        self._board = board
        self._ip_address = ip_address
        self._port = port
        self._strip_sdp = strip_sdp
        self._tag = tag
        self._traffic_identifier = traffic_identifier

    @property
    def ip_address(self):
        """ The IP address to assign to the tag.

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

        :rtype: str
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
        """ The tag required, or None if any tag is OK.

        :rtype: int or None
        """
        return self._tag

    @property
    def board(self):
        """ The board IP address that this tag is to reside on

        :rtype: str
        """
        return self._board

    def get_value(self):
        """
        :return: A description of the specific board's IP tag required.
        :rtype: list
        """
        return [
            self._board, self._ip_address, self._port, self._strip_sdp,
            self._tag, self._traffic_identifier]

    def __repr__(self):
        return (
            "IPTagResource(board_address={}, ip_address={}, port={}, "
            "strip_sdp={}, tag={}, traffic_identifier={})".format(
                self._board, self._ip_address, self._port, self._strip_sdp,
                self._tag, self._traffic_identifier))
