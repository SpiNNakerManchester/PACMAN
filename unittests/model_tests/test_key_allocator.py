import unittest
from pacman.model.constraints.key_allocator_constraints \
    import ContiguousKeyRangeContraint, FixedKeyAndMaskConstraint, \
    FixedKeyFieldConstraint, FixedMaskConstraint, FlexiKeyFieldConstraint


class TestKeyAllocatorConstraints(unittest.TestCase):
    def test_contiguous_key_range_constraint(self):
        c1 = ContiguousKeyRangeContraint()
        c2 = ContiguousKeyRangeContraint()
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, "c1")
        r = "KeyAllocatorContiguousRangeConstraint()"
        self.assertEqual(str(c1), r)
        self.assertEqual(repr(c1), r)
        d = {}
        d[c1] = 1
        d[c2] = 2
        self.assertEqual(len(d), 1)
        self.assertEqual(d[c1], 2)

    def test_fixed_key_and_mask_constraint(self):
        FixedKeyAndMaskConstraint([])

    def test_fixed_key_field_constraint(self):
        FixedKeyFieldConstraint([])

    def test_fixed_mask_constraint(self):
        FixedMaskConstraint(0)

    def test_flexi_key_constraint(self):
        FlexiKeyFieldConstraint([])
