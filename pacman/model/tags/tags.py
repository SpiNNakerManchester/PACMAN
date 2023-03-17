# Copyright (c) 2015 The University of Manchester
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

from collections import defaultdict
from spinn_machine.tags import IPTag, ReverseIPTag
from pacman.exceptions import PacmanInvalidParameterException
from pacman.utilities import utility_calls


class Tags(object):
    """ Represents assigned IP Tag and Reverse IP Tags.
    """

    __slots__ = [
        # Mapping of (board address, tag) to IPTag
        "_ip_tags",
        # Mapping of (board address, tag) to ReverseIPTag
        "_reverse_ip_tags",
        # Mapping of vertex to list of IPTag
        "_ip_tags_by_vertex",
        # Mapping of vertex to list of ReverseIPTag
        "_reverse_ip_tags_by_vertex",
        # Set of ports already assigned on a board
        "_ports_assigned"
    ]

    def __init__(self):

        # Mapping of (board address, tag) to IPTag
        self._ip_tags = dict()

        # Mapping of (board address, tag) to ReverseIPTag
        self._reverse_ip_tags = dict()

        # Mapping of vertex to list of IPTag
        self._ip_tags_by_vertex = defaultdict(list)

        # Mapping of vertex to list of ReverseIPTag
        self._reverse_ip_tags_by_vertex = defaultdict(list)

        # Set of ports already assigned on a board
        self._ports_assigned = set()

    def add_ip_tag(self, ip_tag, vertex):
        """ Add an IP tag.

        :param ~spinn_machine.tags.IPTag ip_tag: The tag to add
        :param MachineVertex vertex:
            The machine vertex by which the tag is to be used
        :raises PacmanInvalidParameterException:
            * If the combination of (board-address, tag) has already been\
              assigned to an IP tag with different properties
            * If the combination of (board-address, tag) has already been\
              assigned to a reverse IP tag
        """
        if not isinstance(ip_tag, IPTag):
            raise PacmanInvalidParameterException(
                "ip_tag", str(ip_tag), "Only add IP tags with this method.")
        existing_tag = None
        if (ip_tag.board_address, ip_tag.tag) in self._ip_tags:
            existing_tag = self._ip_tags[(ip_tag.board_address, ip_tag.tag)]
            if (existing_tag.ip_address != ip_tag.ip_address or
                    not utility_calls.is_equal_or_None(
                        existing_tag.port, ip_tag.port) or
                    existing_tag.strip_sdp != ip_tag.strip_sdp):
                raise PacmanInvalidParameterException(
                    "ip_tag", str(ip_tag),
                    "The tag specified has already been assigned with"
                    f" different properties: {existing_tag}")

        if (ip_tag.board_address, ip_tag.tag) in self._reverse_ip_tags:
            raise PacmanInvalidParameterException(
                "ip_tag", str(ip_tag),
                "The tag has already been assigned to a reverse IP tag on"
                " the given board")

        if existing_tag is None:
            self._ip_tags[(ip_tag.board_address, ip_tag.tag)] = ip_tag
            self._ip_tags_by_vertex[vertex].append(ip_tag)
        else:
            self._ip_tags_by_vertex[vertex].append(existing_tag)

            # Update the port number if necessary
            if existing_tag.port is None and ip_tag.port is not None:
                existing_tag.port = ip_tag.port

    def add_reverse_ip_tag(self, reverse_ip_tag, vertex):
        """ Add a reverse IP tag.

        :param ~spinn_machine.tags.ReverseIPTag reverse_ip_tag: The tag to add
        :param MachineVertex vertex: The vertex by which the tag is to be used
        :raises PacmanInvalidParameterException:
            * If the combination of (board-address, tag) has already been\
              assigned to an IP tag or Reverse IP tag
            * If the port of the tag has already been assigned on the given\
              board-address
        """
        if not isinstance(reverse_ip_tag, ReverseIPTag):
            raise PacmanInvalidParameterException(
                "reverse_ip_tag", str(reverse_ip_tag),
                "Only add reverse IP tags with this method.")
        if ((reverse_ip_tag.board_address, reverse_ip_tag.tag) in
                self._ip_tags or
                (reverse_ip_tag.board_address, reverse_ip_tag.tag) in
                self._reverse_ip_tags):
            raise PacmanInvalidParameterException(
                "reverse_ip_tag", reverse_ip_tag,
                "The tag has already been assigned on the given board")

        if reverse_ip_tag.port is not None:
            if (reverse_ip_tag.board_address,
                    reverse_ip_tag.port) in self._ports_assigned:
                raise PacmanInvalidParameterException(
                    "reverse_ip_tag", reverse_ip_tag,
                    "The port has already been assigned on the given board")

        self._reverse_ip_tags[
            (reverse_ip_tag.board_address,
             reverse_ip_tag.tag)] = reverse_ip_tag
        self._reverse_ip_tags_by_vertex[vertex].append(reverse_ip_tag)
        if reverse_ip_tag.port is not None:
            self._ports_assigned.add(
                (reverse_ip_tag.board_address, reverse_ip_tag.port))

    @property
    def ip_tags_vertices(self):
        """ List the (IPTag, vertex) pairs stored.

        :rtype: iterable(tuple(IPTag, MachineVertex))
        """
        yield from [(tag, vert)
                    for vert, tags in self._ip_tags_by_vertex.items()
                    for tag in tags]

    @property
    def ip_tags(self):
        """ The IP tags assigned.

        :rtype: iterable(~spinn_machine.tags.IPTag)
        """
        return iter(self._ip_tags.values())

    @property
    def reverse_ip_tags(self):
        """ The reverse IP tags assigned.

        :rtype: iterable(~spinn_machine.tags.ReverseIPTag)
        """
        return iter(self._reverse_ip_tags.values())

    def get_ip_tags_for_vertex(self, vertex):
        """ Get the IP Tags assigned to a given machine vertex.

        :param MachineVertex vertex: The vertex to get the tags for
        :return: An iterable of IPTag, or `None` if the vertex has no tags
        :rtype: iterable(~spinn_machine.tags.IPTag) or None
        """
        return self._ip_tags_by_vertex.get(vertex, None)

    def get_reverse_ip_tags_for_vertex(self, vertex):
        """ Get the Reverse IP Tags assigned to a given machine vertex.

        :param MachineVertex vertex: The vertex to get the tags for
        :return:
            An iterable of ReverseIPTag, or `None` if the vertex has no tags
        :rtype: iterable(~spinn_machine.tags.ReverseIPTag) or None
        """
        return self._reverse_ip_tags_by_vertex.get(vertex, None)
