from pacman.exceptions import PacmanAlreadyExistsException


def _get_dict_id_for_placement(x, y, p):
    """ Get an id that can be used in a dictionary of placements
    
    :param x: The x-coordinate of the placement
    :type x: int
    :param y: The y-coordinate of the placement
    :type y: int
    :param p: The processor of the placement
    :type p: int
    :return: A string to use as the dictionary id
    :rtype: str
    """
    return "{}.{}.{}".format(x, y, p)


class Placements(object):
    """ Represents a list of placements
    """

    def __init__(self, placements=None):
        """

        :param placements: The initial list of placements
        :type placements: iterable of\
                    :py:class:`pacman.model.placements.placement.Placement`
        :raise pacman.exceptions.PacmanAlreadyExistsException:
                * If there are any two placements to the same processor on the\
                  same chip
                * If there is any subvertex with more than one placement
        """
        self._placements = dict()
        self._subvertices = dict()
        self.add_placements(placements)

    def add_placements(self, placements):
        """
        :param placements: The list of placements
        :type placements: iterable of :py:class:`pacman.model.placements.placement.Placement`
        :return: None
        :rtype: None
        """
        for placement in placements:
            self.add_placement(placement)

    def add_placement(self, placement):
        """ Add a placement

        :param placement: The placement to add
        :type placement: :py:class:`pacman.model.placements.placement.Placement`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: 
                * If there is already a placement for the given processor on\
                  the given chip
                * If the subvertex has been placed elsewhere
        """
        placement_id_string_representation = _get_dict_id_for_placement(placement.x, placement.y, placement.p)
        placement_id = (placement.x, placement.y, placement.p)
        if placement_id in self._placements:
            raise PacmanAlreadyExistsException("placement", placement_id_string_representation)
        if placement.subvertex in self._subvertices:
            raise PacmanAlreadyExistsException("subvertex", str(placement.subvertex))
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
        :rtype: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :raise None: does not raise any known exceptions
        """
        placement_id = (x, y, p)
        if placement_id in self._placements:
            return self._placements[placement_id]
        return None
    
    def get_placement_of_subvertex(self, subvertex):
        """ Return the placement information for a subvertex
        
        :param subvertex: The subvertex to find the placement of
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :return: The placement, or None if the subvertex has no placement
        :rtype: :py:class:`pacman.model.placements.placement.Placement`
        :raise None: No known exceptions are raised
        """
        if subvertex in self._subvertices:
            return self._subvertices[subvertex]
        return None

    @property
    def placements(self):
        """ All of the placements

        :return: iterable of placements
        :rtype: iterable of\
                    :py:class:`pacman.model.placements.placement.Placement`
        :raise None: does not raise any known exceptions
        """
        return self._placements.itervalues()
