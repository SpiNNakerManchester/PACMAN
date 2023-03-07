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

from collections import defaultdict
from pacman.exceptions import (
    PacmanAlreadyPlacedError, PacmanNotPlacedError,
    PacmanProcessorAlreadyOccupiedError, PacmanProcessorNotOccupiedError)


class Placements(object):
    """ The placements of vertices on the chips of the machine.
    """

    __slots__ = [
        # dict of [(x,y)] -> dict of p->placement object. used for fast lookup
        # of a vertex given a set of coordinates
        "_placements",

        # dict of [machine_vertex] -> placement object. used for fast lookup of
        # the placement of a machine vertex.
        "_machine_vertices",
    ]

    def __init__(self, placements=None):
        """
        :param iterable(Placement) placements: Any initial placements
        :raise PacmanAlreadyPlacedError:
            If there is any vertex with more than one placement.
        :raise PacmanProcessorAlreadyOccupiedError:
            If two placements are made to the same processor.
        """
        self._placements = defaultdict(dict)
        self._machine_vertices = dict()
        if placements is not None:
            self.add_placements(placements)

    @property
    def n_placements(self):
        """ The number of placements

        :rtype: int
        """
        return len(self._machine_vertices)

    def add_placements(self, placements):
        """ Add some placements

        :param iterable(Placement) placements: The placements to add
        """
        for placement in placements:
            self.add_placement(placement)

    def add_placement(self, placement):
        """ Add a placement

        :param Placement placement: The placement to add
        :raise PacmanAlreadyPlacedError:
            If there is any vertex with more than one placement.
        :raise PacmanProcessorAlreadyOccupiedError:
            If two placements are made to the same processor.
        """
        x, y, p = placement.location
        if (x, y) in self._placements:
            if p in self._placements[(x, y)]:
                raise PacmanProcessorAlreadyOccupiedError((x, y, p))
        if placement.vertex in self._machine_vertices:
            raise PacmanAlreadyPlacedError(placement.vertex)

        self._placements[x, y][p] = placement
        self._machine_vertices[placement.vertex] = placement

    def get_placement_on_processor(self, x, y, p):
        """ Return the placement on a specific processor or raises an exception
            if the processor has not been allocated

        :param int x: the x coordinate of the chip
        :param int y: the y coordinate of the chip
        :param int p: the processor on the chip
        :return: the placement on the given processor
        :rtype: Placement
        :raise PacmanProcessorNotOccupiedError:
            If the processor is not occupied
        """
        try:
            return self._placements[x, y][p]
        except KeyError as e:
            raise PacmanProcessorNotOccupiedError((x, y, p)) from e

    def is_vertex_placed(self, vertex):
        """ Determine if a vertex has been placed

        :param MachineVertex vertex: The vertex to determine the status of
        :rtype: bool
        """
        return vertex in self._machine_vertices

    def get_placement_of_vertex(self, vertex):
        """ Return the placement information for a vertex

        :param MachineVertex vertex: The vertex to find the placement of
        :return: The placement
        :rtype: Placement
        :raise PacmanNotPlacedError: If the vertex has not been placed.
        """
        try:
            return self._machine_vertices[vertex]
        except KeyError as e:
            raise PacmanNotPlacedError(vertex) from e

    def is_processor_occupied(self, x, y, p):
        """ Determine if a processor has a vertex on it

        :param int x: x coordinate of processor.
        :param int y: y coordinate of processor.
        :param int p: Index of processor.
        :return bool: Whether the processor has an assigned vertex.
        """
        return (x, y) in self._placements and p in self._placements[x, y]

    def iterate_placements_on_core(self, x, y):
        """
        Iterate over placements with this x, y and this type

        :param int x: x coordinate to find placements for.
        :param int y: y coordinate  to find placements for.
        :rtype: Placement
        """
        return self._placements[x, y].values()

    def iterate_placements_by_xy_and_type(self, x, y, vertex_type):
        """
        Iterate over placements with this x, y and this vertex_type

        :param int x: x coordinate to find placements for.
        :param int y: y coordinate  to find placements for.
        :param class vertex_type: Class of vertex to find
        :rtype: Placement
        """
        for placement in self._placements[x, y].values():
            if isinstance(placement.vertex, vertex_type):
                yield placement

    def iterate_placements_by_vertex_type(self, vertex_type):
        """
        Iterate over placements on any chip with this vertex_type

        :param class vertex_type: Class of vertex to find
        :rtype: Placement
        """
        for placement in self._machine_vertices.values():
            if isinstance(placement.vertex, vertex_type):
                yield placement

    def n_placements_on_chip(self, x, y):
        """ The number of placements on the given chip
        :param int x: x coordinate of chip.
        :param int y: y coordinate of chip.
        """
        if (x, y) not in self._placements:
            return 0
        return len(self._placements[x, y])

    @property
    def placements(self):
        """ All of the placements
        :return: iterable of placements
        :rtype: iterable(Placement)
        """
        return iter(self._machine_vertices.values())

    def placements_on_chip(self, x, y):
        """ Get the placements on a specific chip

        :param int x: The x-coordinate of the chip
        :param int y: The y-coordinate of the chip
        :rtype: iterable(Placement)
        """
        return self._placements[x, y].values()

    @property
    def chips_with_placements(self):
        """ Get the chips with placements on them

        :rtype: iterable(tuple(int,int))
        """
        return self._placements.keys()

    def __repr__(self):
        output = ""
        for placement in self._placements:
            output += placement.__repr__()
        return output

    def __iter__(self):
        """ An iterator for the placements object within
        """
        return iter(self._machine_vertices.values())

    def __len__(self):
        return len(self._machine_vertices)
