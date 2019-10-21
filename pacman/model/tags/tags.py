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

from collections import defaultdict
from six import itervalues
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
        """ Add an IP tag

        :param ip_tag: The tag to add
        :type ip_tag: :py:class:`spinn_machine.tags.IPTag`
        :param vertex: The machine vertex by which the tag is to be used
        :type vertex:\
            :py:class:`pacman.model.graphs.machine.MachineVertex`
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
                    " different properties: {}".format(existing_tag))

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
        """ Add a reverse IP tag

        :param reverse_ip_tag: The tag to add
        :type reverse_ip_tag:\
            :py:class:`spinn_machine.tags.ReverseIPTag`
        :param vertex: The vertex by which the tag is to be used
        :type vertex:\
            :py:class:`pacman.model.graphs.machine.MachineVertex`
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
    def ip_tags(self):
        """ The IP tags assigned

        :return: iterable of IPTag
        :rtype: iterable(:py:class:`spinn_machine.tags.IPTag`)
        """
        return itervalues(self._ip_tags)

    @property
    def reverse_ip_tags(self):
        """ The reverse IP tags assigned

        :return: iterable of ReverseIPTag
        :rtype: iterable(:py:class:`spinn_machine.tags.ReverseIPTag`)
        """
        return itervalues(self._reverse_ip_tags)

    def get_ip_tags_for_vertex(self, vertex):
        """ Get the IP Tags assigned to a given machine vertex

        :param vertex: The vertex to get the tags for
        :type vertex:\
            :py:class:`pacman.model.graphs.machine.MachineVertex`
        :return: An iterable of IPTag, or None if the vertex has no tags
        :rtype: iterable(:py:class:`spinn_machine.tags.IPTag`) or None
        """
        return self._ip_tags_by_vertex.get(vertex, None)

    def get_reverse_ip_tags_for_vertex(self, vertex):
        """ Get the Reverse IP Tags assigned to a given machine vertex

        :param vertex: The vertex to get the tags for
        :type vertex:\
            :py:class:`pacman.model.graphs.AbstractVertex`
        :return: An iterable of ReverseIPTag, or None if the vertex has no tags
        :rtype: iterable(:py:class:`spinn_machine.tags.ReverseIPTag`) or None
        """
        return self._reverse_ip_tags_by_vertex.get(vertex, None)
