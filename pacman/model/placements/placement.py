class Placement(object):
    """ Represents a placement of a subvertex on a specific processor on a\
        specific chip in the machine
    """

    def __init__(self, subvertex, x, y, p):
        """

        :param subvertex: The subvertex that has been placed
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :param x: the x-oordinate of the chip on which the subvertex is placed
        :type x: int
        :param y: the y-coordinate of the chip on which the subvertex is placed
        :type y: int
        :param p: the id of the processor on which the subvertex is placed
        :type p: int
        :raise None: does not raise any known exceptions
        """
        self._subvertex = subvertex
        self._x = x
        self._y = y
        self._p = p

    @property
    def subvertex(self):
        """ The subvertex that was placed

        :return: a subvertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :raise None: does not raise any known exceptions
        """
        return self._subvertex
    
    @property
    def x(self):
        """ The x-coordinate of the chip where the subvertex is placed
        
        :return: The x-coordinate
        :rtype: int
        """
        return self._x
    
    @property
    def y(self):
        """ The y-coordinate of the chip where the subvertex is placed
        
        :return: The y-coordinate
        :rtype: int
        """
        return self._y
    
    @property
    def p(self):
        """ The id of the processor of the chip where the subvertex is placed
        
        :return: The processor id
        :rtype: int
        """
        return self._p
