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

from pacman.exceptions import (
    PacmanAlreadyPlacedError, PacmanNotPlacedError,
    PacmanProcessorAlreadyOccupiedError, PacmanProcessorNotOccupiedError)


class Placements(object):
    """ The placements of vertices on the chips of the machine.
    """

    __slots__ = [
        # dict of [(x,y,p)] -> placement object. used for fast lookup of a
        # vertex given a set of coordinates
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
        self._placements = dict()
        self._machine_vertices = dict()
        if placements is not None:
            self.add_placements(placements)

    @property
    def n_placements(self):
        """ The number of placements

        :rtype: int
        """
        return len(self._placements)

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
        placement_id = placement.location
        if placement_id in self._placements:
            raise PacmanProcessorAlreadyOccupiedError(placement_id)
        if placement.vertex in self._machine_vertices:
            raise PacmanAlreadyPlacedError(placement.vertex)

        self._placements[placement_id] = placement
        self._machine_vertices[placement.vertex] = placement

    def get_vertex_on_processor(self, x, y, p):
        """ Return the vertex on a specific processor or raises an exception
            if the processor has not been allocated

        :param int x: the x coordinate of the chip
        :param int y: the y coordinate of the chip
        :param int p: the processor on the chip
        :return: the vertex placed on the given processor
        :rtype: MachineVertex
        :raise PacmanProcessorNotOccupiedError:
            If the processor is not occupied
        """
        placement_id = (x, y, p)
        try:
            return self._placements[placement_id].vertex
        except KeyError as e:
            raise PacmanProcessorNotOccupiedError(placement_id) from e

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
        placement_id = (x, y, p)
        try:
            return self._placements[placement_id]
        except KeyError as e:
            raise PacmanProcessorNotOccupiedError(placement_id) from e

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

    def get_placed_processors(self):
        """ Return an iterable of processors with assigned vertices.

        :return: Iterable of (x, y, p) tuples
        :rtype: iterable(tuple(int, int, int))
        """
        return iter(self._placements.keys())

    def is_processor_occupied(self, x, y, p):
        """ Determine if a processor has a vertex on it

        :param int x: x coordinate of processor.
        :param int y: y coordinate of processor.
        :param int p: Index of processor.
        :return bool: Whether the processor has an assigned vertex.
        """
        return (x, y, p) in self._placements

    @property
    def placements(self):
        """ All of the placements
        :return: iterable of placements
        :rtype: iterable(Placement)
        """
        return self._placements.values()

    def __repr__(self):
        output = ""
        for placement in self._placements:
            output += placement.__repr__()
        return output

    def __iter__(self):
        """ An iterator for the placements object within
        """
        return iter(self._placements)

    def __len__(self):
        return len(self._placements)
