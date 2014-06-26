__author__ = 'daviess'

from pacman.structures.constraints.abstract_placer_constraint import AbstractPlacerConstraint


class BasicPlacerConstraint(AbstractPlacerConstraint):
    """
    Creates a constraint object to place a vertex or a subvertex in a particular location
    """
    
    def __init__(self, x, y, p=None):
        """

        :param x: the x coordinate to which the constraint refers
        :param y: the y coordinate to which the constraint refers
        :param p: the processor (if any) to which the constraint refers
        :type x: int
        :type y: int
        :type p: int or None
        :return: the constraint object created
        :rtype: pacman.constraints.basic_placer_constraint.BasicPlacerConstraint
        :raise None: does not raise any known exceptions
        """
        self._x = x
        self._y = y
        self._p = p

    @property
    def x(self):
        """
        Returns the x coordinate to which the constraint refers

        :return: the x coordinate to which the constraint refers
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._x


    @property
    def y(self):
        """
        Returns the y coordinate to which the constraint refers

        :return: the y coordinate to which the constraint refers
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._y

    @property
    def p(self):
        """
        Returns the processor (if any) to which the constraint refers

        :return: the processor to which the constraint refers or None
        :rtype: int or None
        :raise None: does not raise any known exceptions
        """
        return self._p

    @property
    def location(self):
        """
        Returns the location to which the constraint refers\
        as a dictionary with three keys: "x", "y" and "p"

        :return: the dictionary containing the location to which\
        this placement refers
        :rtype: {"x": int, "y": int, "p": int or None}
        :raise None: does not raise any known exceptions
        """
        return {"x": self._x, "y": self._y, "p": self._p}
