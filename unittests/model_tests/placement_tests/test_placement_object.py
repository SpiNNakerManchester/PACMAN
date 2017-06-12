"""
tests for placement
"""
# pacman imports
from pacman import exceptions
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placement, Placements

# general imports
import unittest


class TestPlacement(unittest.TestCase):
    """
    tester for placement object in pacman.model.placements.placement
    """

    def test_create_new_placement(self):
        """
        test that creating a new placement puts stuff in the right place
        """
        subv = SimpleMachineVertex(None, "")
        pl = Placement(subv, 0, 0, 1)
        self.assertEqual(pl.x, 0)
        self.assertEqual(pl.y, 0)
        self.assertEqual(pl.p, 1)
        self.assertEqual(subv, pl.vertex)

    def test_create_new_placements_duplicate_vertex(self):
        """
        check that you cant put a vertex in multiple placements
        """
        subv = SimpleMachineVertex(None, "")
        pl = list()
        for i in range(4):
            pl.append(Placement(subv, 0, 0, i))
        with self.assertRaises(exceptions.PacmanAlreadyPlacedError):
            Placements(pl)


if __name__ == '__main__':
    unittest.main()
