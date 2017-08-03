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

        self.x_pos = xpos
        self.y_pos = ypos
        self.change_x = xchange
        self.change_y = ychange

    def _turn_left(self, angle=1):
        self.change_x, self.change_y = (
            self.change_y * -angle, self.change_x * angle)

    def _turn_right(self, angle=1):
        self.change_x, self.change_y = (
            self.change_y * angle, self.change_x * -angle)

    def _move_forward(self):
        self.x_pos = self.x_pos + self.change_x
        self.y_pos = self.y_pos + self.change_y

    def get_turn_left(self):
        yield self.change_x, self.change_y in self._turn_left()

    def get_turn_right(self):
        yield self.change_x, self.change_y in self._turn_right()

    def get_move_forward(self):
        yield self.x_pos, self.y_pos in self._move_forward()

