"""
tests for placements
"""

# pacman imports
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placement, Placements

# general imports
import unittest


class TestPlacements(unittest.TestCase):
    """
    tester for placements object in pacman.model.placements.placements
    """

    def test_create_new_placements(self):
        """
        test creating a placements object
        """
        subv = SimpleMachineVertex(None, "")
        pl = Placement(subv, 0, 0, 1)
        Placements([pl])

    def test_create_new_empty_placements(self):
        """
        checks that creating an empty placements object is valid
        """
        pls = Placements()
        self.assertEqual(pls._placements, dict())
        self.assertEqual(pls._machine_vertices, dict())

    def test_get_placement_of_vertex(self):
        """
        checks the placements get placement method
        """
        subv = list()
        for i in range(5):
            subv.append(SimpleMachineVertex(None, ""))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        for i in range(4):
            self.assertEqual(pls.get_placement_of_vertex(subv[i]), pl[i])

    def test_get_vertex_on_processor(self):
        """
        checks that from a placements object, you can get to the correct
        vertex using the get_vertex_on_processor() method
        """
        subv = list()
        for i in range(5):
            subv.append(SimpleMachineVertex(None, ""))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        for i in range(4):
            self.assertEqual(pls.get_vertex_on_processor(0, 0, i), subv[i])

        self.assertEqual(pls.get_placement_of_vertex(subv[0]), pl[0])

    def test_get_placements(self):
        """
        tests the placements iterator functionality.
        """
        subv = list()
        for i in range(5):
            subv.append(SimpleMachineVertex(None, ""))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        container = pls.placements
        for i in range(4):
            self.assertIn(pl[i], container)


if __name__ == '__main__':
    unittest.main()
