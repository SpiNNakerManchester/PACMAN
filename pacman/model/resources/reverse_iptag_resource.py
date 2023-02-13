# Copyright (c) 2015-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


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
        if not isinstance(other, ReverseIPtagResource):
            return False
        return (self._port == other._port and
                self._sdp_port == other._sdp_port and
                self._tag == other._tag)

    def __hash__(self):
        return hash((self._port, self._sdp_port, self._tag))

    def __ne__(self, other):
        return not self.__eq__(other)
