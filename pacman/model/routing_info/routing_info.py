# Copyright (c) 2014 The University of Manchester
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

from pacman.exceptions import PacmanAlreadyExistsException


class RoutingInfo(object):
    """
    An association of machine vertices to a non-overlapping set of keys
    and masks.
    """

    __slots__ = [
        # Partition information indexed by edge pre vertex and partition ID\
        # name
        "_info"
    ]

    def __init__(self):
        # Partition information indexed by edge pre vertex and partition ID
        # name
        self._info = dict()

    def add_routing_info(self, info):
        """
        Add a routing information item.

        :param VertexRoutingInfo info:
            The routing information item to add
        :raise PacmanAlreadyExistsException:
            If the partition is already in the set of edges
        """
        key = (info.vertex, info.partition_id)
        if key in self._info:
            raise PacmanAlreadyExistsException(
                "Routing information", str(info))

        self._info[key] = info

    def get_routing_info_from_pre_vertex(self, vertex, partition_id):
        """
        Get routing information for a given partition_id from a vertex.

        :param AbstractVertex vertex: The vertex to search for
        :param str partition_id:
            The ID of the partition for which to get the routing information
        """
        return self._info.get((vertex, partition_id))

    def get_first_key_from_pre_vertex(self, vertex, partition_id):
        """
        Get the first key for the partition starting at a vertex.

        :param AbstractVertex vertex: The vertex which the partition starts at
        :param str partition_id:
            The ID of the partition for which to get the routing information
        :return: The routing key of the partition
        :rtype: int
        """
        if (vertex, partition_id) in self._info:
            return self._info[(vertex, partition_id)].key
        return None

    def __iter__(self):
        """
        Gets an iterator for the routing information.

        :return: a iterator of routing information
        """
        return iter(self._info.values())
