"""
tests for placements
"""
# pacman imports
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

# general imports
import unittest


class TestPlacements(unittest.TestCase):
    """
    tester for placements object in pacman.model.placements.placements
    """

    def test_create_new_placements(self):
        """
        test creating a placements object
        :return:
        """
        subv = PartitionedVertex(None, "")
        pl = Placement(subv, 0, 0, 1)
        Placements([pl])

    def test_create_new_empty_placements(self):
        """
        checks that creating an empty placements object is valid
        :return:
        """
        pls = Placements()
        self.assertEqual(pls._placements, dict())
        self.assertEqual(pls._subvertices, dict())

    def test_get_placement_of_subvertex(self):
        """
        checks the placements get placement method
        :return:
        """
        subv = list()
        for i in range(5):
            subv.append(PartitionedVertex(None, ""))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        for i in range(4):
            self.assertEqual(pls.get_placement_of_subvertex(subv[i]), pl[i])

    def test_get_subvertex_on_processor(self):
        """
        checks that from a placements object, you can get to the correct
        subvertex using the get_subvertex_on_processor() method
        :return:
        """
        subv = list()
        for i in range(5):
            subv.append(PartitionedVertex(None, ""))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        for i in range(4):
            self.assertEqual(pls.get_subvertex_on_processor(0, 0, i), subv[i])

        self.assertEqual(pls.get_placement_of_subvertex(subv[0]), pl[0])

    def test_get_placements(self):
        """
        tests the placements iterator functionality.
        :return:
        """
        subv = list()
        for i in range(5):
            subv.append(PartitionedVertex(None, ""))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        container = pls.placements
        for i in range(4):
            self.assertIn(pl[i], container)


if __name__ == '__main__':
    unittest.main()
