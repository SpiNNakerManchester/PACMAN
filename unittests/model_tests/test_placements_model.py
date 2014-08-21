import unittest
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.exceptions import PacmanAlreadyExistsException


class TestPlacements(unittest.TestCase):
    def test_create_new_placement(self):
        subv = PartitionedVertex(0, 100, None)
        pl = Placement(subv, 0, 0, 1)
        self.assertEqual(pl.x, 0)
        self.assertEqual(pl.y, 0)
        self.assertEqual(pl.p, 1)
        self.assertEqual(subv, pl.subvertex)

    def test_create_new_placements_duplicate_subvertex(self):
        with self.assertRaises(PacmanAlreadyExistsException):
            subv = PartitionedVertex(0, 100, None)
            pl = list()
            for i in range(4):
                pl.append(Placement(subv, 0, 0, i))

            Placements(pl)

    def test_create_new_placements(self):
        subv = PartitionedVertex(0, 100, None)
        pl = Placement(subv, 0, 0, 1)
        Placements([pl])

    def test_create_new_empty_placements(self):
        pls = Placements()
        self.assertEqual(pls._placements, dict())
        self.assertEqual(pls._subvertices, dict())

    def test_get_placement_of_subvertex(self):
        subv = list()
        for i in range(5):
            subv.append(PartitionedVertex(i, 2 * i, None))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        for i in range(4):
            self.assertEqual(pls.get_placement_of_subvertex(subv[i]), pl[i])

    def test_get_subvertex_on_processor(self):
        subv = list()
        for i in range(5):
            subv.append(PartitionedVertex(i, 2 * i, None))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        for i in range(4):
            self.assertEqual(pls.get_subvertex_on_processor(0, 0, i), subv[i])

        self.assertEqual(pls.get_placement_of_subvertex(subv[0]), pl[0])

    def test_get_placements(self):
        subv = list()
        for i in range(5):
            subv.append(PartitionedVertex(i, 2 * i, None))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        container = pls.placements
        for i in range(4):
            self.assertIn(pl[i], container)


if __name__ == '__main__':
    unittest.main()
