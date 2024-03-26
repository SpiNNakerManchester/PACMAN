# Copyright (c) 2021 The University of Manchester
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

from typing import List, Optional, Tuple

from spinn_utilities.typing.coords import XY
from spinn_machine import Chip

from pacman.data import PacmanDataView
from pacman.model.graphs import AbstractVirtual
from pacman.model.graphs.application import (
    ApplicationEdgePartition, ApplicationVertex)
from pacman.model.graphs.machine import MachineVertex


def get_app_partitions() -> List[ApplicationEdgePartition]:
    """
    Find all application partitions.

    .. note::
        Where a vertex splitter indicates that it has internal
        partitions but is not the source of an external partition, a "fake"
        empty application partition is added.  This allows the calling
        algorithm to loop over the returned list and look at the set of
        edges *and* internal partitions to get a complete picture of *all*
        targets for each source machine vertex at once.

    :return: list of partitions

        .. note::
            Where there are only internal multicast partitions, the partition
            will have no edges.  Caller should use
            `vertex.splitter.get_internal_multicast_partitions` for details.
    :rtype: list(ApplicationEdgePartition)
    """
    # Find all partitions that need to be dealt with
    # Make a copy which we can edit
    partitions = list(PacmanDataView.iterate_partitions())
    sources = frozenset(p.pre_vertex for p in partitions)

    # Convert internal partitions to self-connected partitions
    for v in PacmanDataView.iterate_vertices():
        if not isinstance(v, ApplicationVertex) or not v.splitter:
            continue
        internal_partitions = v.splitter.get_internal_multicast_partitions()
        if v not in sources and internal_partitions:
            # guarantee order
            for identifier in dict.fromkeys(
                    p.identifier for p in internal_partitions):
                # Add a partition with no edges to identify this as internal
                partitions.append(ApplicationEdgePartition(identifier, v))
    return partitions


def longest_dimension_first(
        vector: Tuple[int, int, int], start: XY) -> List[Tuple[int, XY]]:
    """
    List the (x, y) steps on a longest-dimension first route.

    :param tuple(int,int,int) vector: (x, y, z)
        The vector which the path should cover.
    :param tuple(int,int) start: (x, y)
        The coordinates from which the path should start.

        .. note::
            This is a 2D coordinate.
    :return: min route
    :rtype: list(tuple(int,tuple(int, int)))
    """
    return vector_to_nodes(
        sorted(enumerate(vector), key=(lambda x: abs(x[1])), reverse=True),
        start)


def vector_to_nodes(dm_vector: List[XY], start: XY) -> List[Tuple[int, XY]]:
    """
    Convert a vector to a set of nodes.

    :param list(tuple(int,int)) dm_vector:
        A vector made up of a list of (dimension, magnitude), where dimensions
        are x=0, y=1, z=diagonal=2
    :param tuple(int,int) start: The x, y coordinates of the start
    :return: A list of (link_id, (target_x, target_y)) of nodes on a route
    :rtype: list(tuple(int,tuple(int, int)))
    """
    machine = PacmanDataView.get_machine()
    x, y = start

    out = []

    for dimension, magnitude in dm_vector:
        if magnitude == 0:
            continue

        if dimension == 0:  # x
            if magnitude > 0:
                # Move East (0) magnitude times
                for _ in range(magnitude):
                    x, y = machine.xy_over_link(x, y, 0)
                    out.append((0, (x, y)))
            else:
                # Move West (3) -magnitude times
                for _ in range(magnitude, 0):
                    x, y = machine.xy_over_link(x, y, 3)
                    out.append((3, (x, y)))
        elif dimension == 1:  # y
            if magnitude > 0:
                # Move North (2) magnitude times
                for _ in range(magnitude):
                    x, y = machine.xy_over_link(x, y, 2)
                    out.append((2, (x, y)))
            else:
                # Move South (5) -magnitude times
                for _ in range(magnitude, 0):
                    x, y = machine.xy_over_link(x, y, 5)
                    out.append((5, (x, y)))
        else:  # z
            if magnitude > 0:
                # Move SouthWest (4) magnitude times
                for _ in range(magnitude):
                    x, y = machine.xy_over_link(x, y, 4)
                    out.append((4, (x, y)))
            else:
                # Move NorthEast (1) -magnitude times
                for _ in range(magnitude, 0):
                    x, y = machine.xy_over_link(x, y, 1)
                    out.append((1, (x, y)))
    return out


def vertex_xy(vertex: MachineVertex) -> XY:
    """
    :param MachineVertex vertex:
    :rtype: tuple(int,int)
    """
    if not isinstance(vertex, AbstractVirtual):
        placement = PacmanDataView.get_placement_of_vertex(vertex)
        return placement.x, placement.y
    link_data = vertex.get_link_data(PacmanDataView.get_machine())
    return link_data.connected_chip_x, link_data.connected_chip_y


def vertex_chip(vertex: MachineVertex) -> Chip:
    """
    :param MachineVertex vertex:
    :rtype: ~spinn_machine.Chip
    """
    machine = PacmanDataView.get_machine()
    if not isinstance(vertex, AbstractVirtual):
        placement = PacmanDataView.get_placement_of_vertex(vertex)
        return machine[placement.x, placement.y]
    link_data = vertex.get_link_data(machine)
    return machine[link_data.connected_chip_x, link_data.connected_chip_y]


def vertex_xy_and_route(vertex: MachineVertex) -> Tuple[
        XY, Tuple[MachineVertex, Optional[int], Optional[int]]]:
    """
    Get the non-virtual chip coordinates, the vertex, and processor or
    link to follow to get to the vertex.

    :param MachineVertex vertex:
    :return: the (x,y) coordinates of the target vertex mapped to a tuple of
        the vertex, core and link.
        One of core or link is provided the other is `None`
    :rtype: tuple(tuple(int, int), tuple(MachineVertex, int, None)) or
        tuple(tuple(int, int), tuple(MachineVertex, None, int))
    """
    if not isinstance(vertex, AbstractVirtual):
        placement = PacmanDataView.get_placement_of_vertex(vertex)
        return (placement.x, placement.y), (vertex, placement.p, None)
    machine = PacmanDataView.get_machine()
    link_data = vertex.get_link_data(machine)
    return ((link_data.connected_chip_x, link_data.connected_chip_y),
            (vertex, None, link_data.connected_link))
