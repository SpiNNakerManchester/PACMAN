import unittest
from pacman.model.graph.slice import Slice


class TestSlice(unittest.TestCase):
    """Tests that Slices expose the correct options and are immutable."""
    def test_basic(self):
        s = Slice(0, 10)
        assert s.n_atoms == 11  # 10 - 0 + 1
        assert s.lo_atom == 0   # As specified
        assert s.hi_atom == 10  # As specified
        assert s.as_slice == slice(0, 11)  # Slice object supported by arrays

    def test_check_lo_atom_sanity(self):
        # Check for value sanity
        with self.assertRaises(ValueError):
            # Check for negative atom
            Slice(-1, 10)

    def test_check_hi_atom_sanity(self):
        with self.assertRaises(ValueError):
            # Check for slice which goes backwards
            Slice(5, 4)

    def test_equal_hi_lo_atoms(self):
        # This should be fine...
        Slice(4, 4)

    def test_immutability_lo_atom(self):
        s = Slice(0, 10)
        with self.assertRaises(AttributeError):
            s.lo_atom = 3

    def test_immutability_hi_atom(self):
        s = Slice(0, 10)
        with self.assertRaises(AttributeError):
            s.hi_atom = 3

    def test_immutability_n_atoms(self):
        s = Slice(0, 10)
        with self.assertRaises(AttributeError):
            s.n_atoms = 3

    def test_immutability_as_slice(self):
        s = Slice(0, 10)
        with self.assertRaises(AttributeError):
            s.as_slice = slice(2, 10)