# A mutable state object for the hilbert placer algorithm
class HilbertState(object):
    def __init__(self, x=0, y=0, dx=1, dy=0):
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
