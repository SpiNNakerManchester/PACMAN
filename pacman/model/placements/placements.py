from pacman.exceptions import (PacmanSubvertexAlreadyPlacedError,
                               PacmanSubvertexNotPlacedError,
                               PacmanProcessorAlreadyOccupiedError,
                               PacmanProcessorNotOccupiedError)


class Placements(object):
    """ Represents a list of placements
    """

    def __init__(self, placements=None):
        """

        :param placements: The initial list of placements
        :type placements: iterable of\
                    :py:class:`pacman.model.placements.placement.Placement`
        :raise PacmanSubvertexAlreadyPlacedError:
                If there is any subvertex with more than one placement.
        :raise PacmanProcessorAlreadyOccupiedError:
                If two placements are made to the same processor.
        """
        self._placements = dict()
        self._subvertices = dict()
        if placements is not None:
            self.add_placements(placements)

    def add_placements(self, placements):
        """
        :param placements: The list of placements
        :type placements: iterable of :py:class:`pacman.model.placements\
        .placement.Placement`
        :return: None
        :rtype: None
        """
        for placement in placements:
            self.add_placement(placement)

    def add_placement(self, placement):
        """ Add a placement

        :param placement: The placement to add
        :type placement:
            :py:class:`pacman.model.placements.placement.Placement`
        :return: None
        :rtype: None
        :raise PacmanSubvertexAlreadyPlacedError:
                If there is any subvertex with more than one placement.
        :raise PacmanProcessorAlreadyOccupiedError:
                If two placements are made to the same processor.
        """
        placement_id = (placement.x, placement.y, placement.p)
        if placement_id in self._placements:
            raise PacmanProcessorAlreadyOccupiedError(placement_id)
        if placement.subvertex in self._subvertices:
            raise PacmanSubvertexAlreadyPlacedError(placement.subvertex)

        self._placements[placement_id] = placement
        self._subvertices[placement.subvertex] = placement

    def get_subvertex_on_processor(self, x, y, p):
        """ Return the subvertex on a specific processor or None if the\
            processor has not been allocated

        :param x: the x coordinate of the chip
        :type x: int
        :param y: the y coordinate of the chip
        :type y: int
        :param p: the processor on the chip
        :type p: int
        :return: the subvertex placed on the given processor or None if no\
                    such placement has been made
        :rtype: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :raise None: does not raise any known exceptions
        """
        placement_id = (x, y, p)
        try:
            return self._placements[placement_id].subvertex
        except KeyError:
            raise PacmanProcessorNotOccupiedError(placement_id)

    def get_placement_of_subvertex(self, subvertex):
        """ Return the placement information for a subvertex

        :param subvertex: The subvertex to find the placement of
        :type subvertex:
            :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :return: The placement
        :rtype: :py:class:`pacman.model.placements.placement.Placement`
        :raise PacmanSubvertexNotPlacedError: If the subvertex has not been
            placed.
        """
        try:
            return self._subvertices[subvertex]
        except KeyError:
            raise PacmanSubvertexNotPlacedError(subvertex)

    def get_placed_processors(self):
        """Returns an iterable of processors with assigned subvertices.

        :return: Iterable of (x, y, p) tuples indicating processors with
                 assigned subvertices.
        :rtype: iterable
        """
        return self._placements.iterkeys()

    def is_subvertex_on_processor(self, x, y, p):
        """Returns whether a subvertex is assigned to a processor.

        :param int x: x co-ordinate of processor.
        :param int y: y co-ordinate of processor.
        :param int p: Index of processor.
        :return bool: Whether the processor has an assigned subvertex.
        """
        return (x, y, p) in self._placements

    @property
    def placements(self):
        """ All of the placements

        :return: iterable of placements
        :rtype: iterable of\
                    :py:class:`pacman.model.placements.placement.Placement`
        :raise None: does not raise any known exceptions
        """
        return self._placements.itervalues()

    def __repr__(self):
        output = ""
        for placement in self._placements:
            output += placement.__repr__()
        return output
