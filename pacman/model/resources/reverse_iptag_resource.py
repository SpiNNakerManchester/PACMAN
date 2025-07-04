# Copyright (c) 2016 The University of Manchester
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


class ReverseIPtagResource(object):
    """
    Represents the ability to talk to a SpiNNaker machine by sending UDP
    packets to it during execution.
    """

    __slots__ = (
        # The target port of the tag or None if this is to be assigned
        # elsewhere
        "_port",
        # The SDP port number to be used when constructing SDP packets from
        # the received UDP packets for this tag
        "_sdp_port",
        # A fixed tag ID to assign, or None if any tag is OK
        "_tag")

    def __init__(self, port: Optional[int] = None, sdp_port: int = 1,
                 tag: Optional[int] = None):
        """
        :param port: The UDP port to listen to on the board for this tag
            or `None` for a default
        :param sdp_port:
            The SDP port number to be used when constructing SDP packets from
            the received UDP packets for this tag
        :param tag: A fixed tag ID to assign, or `None` if any tag is OK
        """
        self._port = port
        self._sdp_port = sdp_port
        self._tag = tag

    @property
    def port(self) -> Optional[int]:
        """
        The port of the tag.
        """
        return self._port

    @property
    def sdp_port(self) -> int:
        """
        The SDP port to use when constructing the SDP message from the
        received UDP message.
        """
        return self._sdp_port

    @property
    def tag(self) -> Optional[int]:
        """
        The tag required, or `None` if any tag is OK.
        """
        return self._tag

    def __repr__(self) -> str:
        return (f"ReverseIPTagResource(port={self._port}, "
                f"sdp_port={self._sdp_port}, tag={self._tag})")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ReverseIPtagResource):
            return False
        return (self._port == other._port and
                self._sdp_port == other._sdp_port and
                self._tag == other._tag)

    def __hash__(self) -> int:
        return hash((self._port, self._sdp_port, self._tag))

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)
