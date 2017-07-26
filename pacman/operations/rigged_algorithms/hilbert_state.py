class HilbertState(object):
    """ A mutable state object for the hilbert placer algorithm.
            :param xpos: the x coordinate on the generated curve
            :param ypos: the y coordinate on the generated curve
            :param xchange: the change in x coordinate on the generated curve
            :param ychange: the change in y coordinate on the generated curve
            :type xpos: int
            :type ypos: int
            :type xchange: int
            :type ychange: int
    """
    def __init__(self, xpos=0, ypos=0, xchange=1, ychange=0):
        self.x_pos = xpos
        self.y_pos = ypos
        self.change_x = xchange
        self.change_y = ychange
