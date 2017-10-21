class HilbertState(object):
    """ A mutable self object for the hilbert placer algorithm.
    """

    def __init__(self, xpos=0, ypos=0, xchange=1, ychange=0):
        """
        Constructor
        :param xpos: the x coordinate on the generated curve
        :param ypos: the y coordinate on the generated curve
        :param xchange: the change in x coordinate on the generated curve
        :param ychange: the change in y coordinate on the generated curve
        :type xpos: int
        :type ypos: int
        :type xchange: int
        :type ychange: int
        """

        self._x_pos = xpos
        self._y_pos = ypos
        self._change_x = xchange
        self._change_y = ychange

    def turn_left(self, angle):
        """ method to turn left in the generation of a hilbert curve
        :param angle: determines the direction in which the curve turns
        :type angle: int
        :return: the x and y coordinates on the generated curve
        """

        self._change_x, self._change_y = (
            self._change_y * -angle, self._change_x * angle)
        return self._change_x, self._change_y

    def turn_right(self, angle):
        """ method to turn right in the generation of a hilbert curve
        :param angle: determines the direction in which the curve turns
        :type angle: int
        :return: the x and y coordinates on the generated curve
        """

        self._change_x, self._change_y = (
            self._change_y * angle, self._change_x * -angle)
        return self._change_x, self._change_y

    def move_forward(self):
        """ method to move forward in the generation of a hilbert curve
        :return: the x and y coordinates on the generated curve
        """

        xp = self._x_pos
        yp = self._y_pos
        self._x_pos = xp + self._change_x
        self._y_pos = yp + self._change_y
        return self._x_pos, self._y_pos

    @property
    def x_pos(self):
        return self._x_pos

    @x_pos.setter
    def x_pos(self, new_value):
        self._x_pos = new_value

    @property
    def y_pos(self):
        return self._y_pos

    @y_pos.setter
    def y_pos(self, new_value):
        self._y_pos = new_value
