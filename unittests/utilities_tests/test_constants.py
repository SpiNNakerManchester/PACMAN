import unittest
from pacman.utilities import constants


class TestConstants(unittest.TestCase):

    def test_edges_enum(self):
        self.assertEquals(constants.EDGES.EAST.value, 0)
        self.assertEquals(constants.EDGES.NORTH_EAST.value, 1)
        self.assertEquals(constants.EDGES.NORTH.value, 2)
        self.assertEquals(constants.EDGES.WEST.value, 3)
        self.assertEquals(constants.EDGES.SOUTH_WEST.value, 4)
        self.assertEquals(constants.EDGES.SOUTH.value, 5)


if __name__ == '__main__':
    unittest.main()
