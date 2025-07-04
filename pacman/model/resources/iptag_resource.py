# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any, Optional


class IPtagResource(object):
    """
    Represents the ability to have a SpiNNaker machine send messages to
    you during execution.
    """
    __slots__ = (
        # The host IP address that will receive the data from this tag
        "_ip_address",
        # the port number that data from this tag will be sent to, or None
        # if the port is to be assigned elsewhere
        "_port",
        # a Boolean flag that indicates if the SDP headers are
        # stripped before transmission of data
        "_strip_sdp",
        #  A fixed tag ID to assign, or None if any tag is OK
        "_tag",

        # the identifier that states what type of data is being transmitted
        # through this IP tag
        "_traffic_identifier")

    def __init__(
            self, ip_address: str, port: int,
            strip_sdp: bool, tag: Optional[int] = None,
            traffic_identifier: str = "DEFAULT"):
        """
        :param ip_address:
            The IP address of the host that will receive data from this tag
        :param port: The port that will
        :param strip_sdp: Whether the tag requires that SDP headers are
            stripped before transmission of data
        :param tag: A fixed tag ID to assign, or `None` if any tag is OK
        :param traffic_identifier: The traffic to be sent using this tag;
            traffic with the same traffic_identifier can be sent using
            the same tag
        """
        self._ip_address = ip_address
        self._port = port
        self._strip_sdp = strip_sdp
        self._tag = tag
        self._traffic_identifier = traffic_identifier

    @property
    def ip_address(self) -> str:
        """
        The IP address to assign to the tag.
        """
        return self._ip_address

    @property
    def port(self) -> int:
        """
        The port of the tag.
        """
        return self._port

    @property
    def traffic_identifier(self) -> str:
        """
        The traffic identifier for this IP tag.
        """
        return self._traffic_identifier

    @property
    def strip_sdp(self) -> bool:
        """
        Whether SDP headers should be stripped for this tag.
        """
        return self._strip_sdp

    @property
    def tag(self) -> Optional[int]:
        """
        The tag required, or `None` if any tag is OK.
        """
        return self._tag

    def __repr__(self) -> str:
        return (
            f"IPTagResource(ip_address={self._ip_address}, port={self._port}, "
            f"strip_sdp={self._strip_sdp}, tag={self._tag}, "
            f"traffic_identifier={self._traffic_identifier})")

    def __eq__(self, other: Any) -> bool:
        """
        For unit tests *only* so __hash__ and __eq__ pairing not done!
        """
        return (self._ip_address == other._ip_address and
                self._port == other._port and
                self._strip_sdp == other._strip_sdp and
                self._tag == other._tag and
                self._traffic_identifier == other._traffic_identifier)

    def __hash__(self) -> int:
        return hash((
            self._ip_address, self._port, self._strip_sdp, self._tag,
            self._traffic_identifier))

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)
