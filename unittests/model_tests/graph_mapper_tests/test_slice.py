"""
tests for slice
"""

# pacman imports
from pacman import exceptions
from pacman.model.graph.slice import Slice

# general imports
import unittest


class TestSliceFunctions(unittest.TestCase):
    """
    slice function tests
    """

    def test_create_slice_valid(self):
        """
        test creating a empty slice
        :return:
        """
        Slice(0, 1)

    def test_slice_invalid_neg(self):
        """
        test that a invlaid slice of engative value generates an error
        :return:
        """
        self.assertRaises(exceptions.PacmanValueError, Slice, -2, 0)

    def test_slice_invalid_lo_higher_than_hi(self):
        """
        test that a invlaid slice generates an error
        :return:
        """
        self.assertRaises(exceptions.PacmanValueError, Slice, 2, 0)


if __name__ == '__main__':
    unittest.main()
