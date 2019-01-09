import unittest
from pacman.model.constraints.placer_constraints import (
    BoardConstraint, ChipAndCoreConstraint, RadialPlacementFromChipConstraint,
    SameChipAsConstraint)
from pacman.model.graphs.machine import SimpleMachineVertex


class TestPlacementConstraints(unittest.TestCase):
    """ Tester for pacman.model.constraints.placer_constraints
    """

    def test_board_constraint(self):
        c1 = BoardConstraint("1.2.3.4")
        self.assertEqual(c1.board_address, "1.2.3.4")
        self.assertEqual(c1, BoardConstraint("1.2.3.4"))
        self.assertEqual(str(c1), 'BoardConstraint(board_address="1.2.3.4")')
        c2 = BoardConstraint("4.3.2.1")
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, "1.2.3.4")
        d = {}
        d[c1] = 1
        d[c2] = 2
        self.assertEqual(len(d), 2)

    def test_chip_and_core_constraint(self):
        c1 = ChipAndCoreConstraint(1, 2)
        self.assertEqual(c1.x, 1)
        self.assertEqual(c1.y, 2)
        self.assertEqual(c1.p, None)
        self.assertEqual(c1.location, {"x": 1, "y": 2, "p": None})
        self.assertEqual(c1, ChipAndCoreConstraint(1, 2))
        self.assertEqual(str(c1), 'ChipAndCoreConstraint(x=1, y=2, p=None)')
        c2 = ChipAndCoreConstraint(2, 1)
        c3 = ChipAndCoreConstraint(1, 2, 3)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertNotEqual(c1, "1.2.3.4")
        d = {}
        d[c1] = 1
        d[c2] = 2
        d[c3] = 3
        self.assertEqual(len(d), 3)

    def test_radial_placement_from_chip_constraint(self):
        c1 = RadialPlacementFromChipConstraint(1, 2)
        self.assertEqual(c1.x, 1)
        self.assertEqual(c1.y, 2)
        self.assertEqual(c1, RadialPlacementFromChipConstraint(1, 2))
        self.assertEqual(str(c1),
                         'RadialPlacementFromChipConstraint(x=1, y=2)')
        c2 = RadialPlacementFromChipConstraint(2, 1)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, "1.2.3.4")
        d = {}
        d[c1] = 1
        d[c2] = 2
        self.assertEqual(len(d), 2)

    def test_same_chip_as_constraint(self):
        v1 = SimpleMachineVertex(None, "v1")
        v2 = SimpleMachineVertex(None, "v2")
        c1 = SameChipAsConstraint(v1)
        c2 = SameChipAsConstraint(v1)
        c3 = SameChipAsConstraint(v2)
        c4 = SameChipAsConstraint(v2)

        self.assertEqual(c1.vertex, v1)
        self.assertEqual(str(c1), "SameChipAsConstraint(vertex=v1)")
        self.assertEqual(str(c4), "SameChipAsConstraint(vertex=v2)")

        self.assertEqual(c1, c2)
        self.assertEqual(c2, c1)
        self.assertEqual(c3, c4)
        self.assertNotEqual(c1, c3)
        self.assertNotEqual(c3, c1)
        self.assertNotEqual(c2, c4)

        d = {}
        d[c1] = 1
        d[c2] = 2
        d[c3] = 3
        d[c4] = 4
        self.assertEqual(len(d), 2)
        self.assertEqual(d[c1], 2)
        self.assertEqual(d[c3], 4)
