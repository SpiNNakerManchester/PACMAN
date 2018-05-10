from collections import OrderedDict
from six import iterkeys, itervalues, raise_from
from pacman.exceptions import (
    PacmanAlreadyPlacedError, PacmanNotPlacedError,
    PacmanProcessorAlreadyOccupiedError, PacmanProcessorNotOccupiedError)


class Placements(object):
    """ The placements of vertices on the chips of the machine
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

        :param placements: Any initial placements
        :type placements:\
            iterable of :py:class:`pacman.model.placements.Placement`
        :raise PacmanAlreadyPlacedError:\
            If there is any vertex with more than one placement.
        :raise PacmanProcessorAlreadyOccupiedError:\
            If two placements are made to the same processor.
        """
        self._placements = OrderedDict()
        self._machine_vertices = OrderedDict()
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

        :param placements: The placements to add
        :type placements:\
            iterable of :py:class:`pacman.model.placements.Placement`
        """
        for placement in placements:
            self.add_placement(placement)

    def add_placement(self, placement):
        """ Add a placement

        :param placement: The placement to add
        :type placement:\
            :py:class:`pacman.model.placements.placement.Placement`
        :raise PacmanAlreadyPlacedError:\
            If there is any vertex with more than one placement.
        :raise PacmanProcessorAlreadyOccupiedError:\
            If two placements are made to the same processor.
        """
        placement_id = (placement.x, placement.y, placement.p)
        if placement_id in self._placements:
            raise PacmanProcessorAlreadyOccupiedError(placement_id)
        if placement.vertex in self._machine_vertices:
            raise PacmanAlreadyPlacedError(placement.vertex)

        self._placements[placement_id] = placement
        self._machine_vertices[placement.vertex] = placement

    def get_vertex_on_processor(self, x, y, p):
        """ Return the vertex on a specific processor or None if the\
            processor has not been allocated

        :param x: the x coordinate of the chip
        :type x: int
        :param y: the y coordinate of the chip
        :type y: int
        :param p: the processor on the chip
        :type p: int
        :return: the vertex placed on the given processor
        :rtype:\
            :py:class:`pacman.model.graphs.machine.MachineVertex`
        :raise PacmanProcessorNotOccupiedError:\
            If the processor is not occupied
        """
        placement_id = (x, y, p)
        try:
            return self._placements[placement_id].vertex
        except KeyError as e:
            raise_from(PacmanProcessorNotOccupiedError(placement_id), e)

    def get_placement_of_vertex(self, vertex):
        """ Return the placement information for a vertex

        :param vertex: The vertex to find the placement of
        :type vertex:\
            :py:class:`pacman.model.graphs.machine.MachineVertex`
        :return: The placement
        :rtype: :py:class:`pacman.model.placements.Placement`
        :raise PacmanNotPlacedError: If the vertex has not been placed.
        """
        try:
            return self._machine_vertices[vertex]
        except KeyError as e:
            raise_from(PacmanNotPlacedError(vertex), e)

    def get_placed_processors(self):
        """ Return an iterable of processors with assigned vertices.

        :return: Iterable of (x, y, p) tuples
        :rtype: iterable of (int, int, int)
        """
        return iterkeys(self._placements)

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
        :rtype: iterable of\
            :py:class:`pacman.model.placements.Placement`
        :raise None: does not raise any known exceptions
        """
        return itervalues(self._placements)

    def __repr__(self):
        output = ""
        for placement in self._placements:
            output += placement.__repr__()
        return output

    def __iter__(self):
        """ An iterator for the placements object within

        """
        return iter(self.placements)

    def __len__(self):
        return len(self._placements)
