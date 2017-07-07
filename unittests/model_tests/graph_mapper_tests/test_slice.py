"""
tests for slice
"""

# pacman imports
from pacman.exceptions import PacmanValueError
from pacman.model.graphs.common import Slice

# general imports
import unittest


class TestSliceFunctions(unittest.TestCase):
    """
    slice function tests
    """

    def test_create_slice_valid(self):
        """
        test creating a empty slice
        """
        Slice(0, 1)

    def test_slice_invalid_neg(self):
        """
        test that a invalid slice of negative value generates an error
        """
        self.assertRaises(PacmanValueError, Slice, -2, 0)

    def test_slice_invalid_lo_higher_than_hi(self):
        """
        test that a invalid slice generates an error
        """
        self.assertRaises(PacmanValueError, Slice, 2, 0)


if __name__ == '__main__':
    unittest.main()
