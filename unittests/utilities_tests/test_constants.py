import unittest
from pacman.utilities import constants


class TestConstants(unittest.TestCase):

    def test_edges_enum(self):
        self.assertEqual(constants.EDGES.EAST.value, 0)
        self.assertEqual(constants.EDGES.NORTH_EAST.value, 1)
        self.assertEqual(constants.EDGES.NORTH.value, 2)
        self.assertEqual(constants.EDGES.WEST.value, 3)
        self.assertEqual(constants.EDGES.SOUTH_WEST.value, 4)
        self.assertEqual(constants.EDGES.SOUTH.value, 5)


if __name__ == '__main__':
    unittest.main()
