import unittest
from pacman.model.routing_info import BaseKeyAndMask
from pacman.utilities.utility_objs import Field, FlexiField
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint, FixedKeyAndMaskConstraint,
    FixedKeyFieldConstraint, FixedMaskConstraint, FlexiKeyFieldConstraint)


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
        c1 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF8)])
        km = BaseKeyAndMask(0xFF0, 0xFF8)
        c2 = FixedKeyAndMaskConstraint([km])
        c3 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFE0, 0xFF8)])
        c4 = FixedKeyAndMaskConstraint([
            km, BaseKeyAndMask(0xFE0, 0xFF8)])
        self.assertEqual(c1, c2)
        self.assertIsNone(c1.key_list_function)
        self.assertEqual(c1.keys_and_masks, [km])
        r = ("FixedKeyAndMaskConstraint(keys_and_masks=[KeyAndMask:0xff0:"
             "0xff8], key_list_function=None)")
        self.assertEqual(str(c1), r)
        d = {}
        d[c1] = 1
        d[c2] = 2
        d[c3] = 3
        self.assertEqual(len(d), 2)
        self.assertEqual(d[c1], 2)
        self.assertNotEqual(c4, c1)
        self.assertNotEqual(c1, c4)

    def test_fixed_key_field_constraint(self):
        c1 = FixedKeyFieldConstraint([
            Field(1, 2, 3, name="foo")])
        c1a = FixedKeyFieldConstraint([
            Field(1, 2, 3, name="foo")])
        c2 = FixedKeyFieldConstraint([
            Field(1, 2, 7)])
        c3 = FixedKeyFieldConstraint([
            Field(1, 2, 3), Field(1, 2, 96), Field(1, 2, 12)])
        self.assertEqual(c1, c1a)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertNotEqual(c3, c1)
        r = ("FixedKeyFieldConstraint(fields=["
             "Field(lo=1, hi=2, value=3, tag=3, name=foo)])")
        self.assertEqual(str(c1), r)
        self.assertEqual([f.value for f in c3.fields], [96, 12, 3])
        d = {}
        d[c1] = 1
        d[c1a] = 2
        d[c2] = 3
        d[c3] = 4
        self.assertEqual(len(d), 3)
        self.assertEqual(d[c1], 2)

    def test_fixed_mask_constraint(self):
        c1 = FixedMaskConstraint(0xFF0)
        self.assertEqual(c1.mask, 4080)
        c2 = FixedMaskConstraint(0xFF0)
        c3 = FixedMaskConstraint(0xFE0)
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertNotEqual(c3, c1)
        r = "FixedMaskConstraint(mask=4080)"
        self.assertEqual(str(c1), r)
        d = {}
        d[c1] = 1
        d[c2] = 2
        d[c3] = 3
        self.assertEqual(len(d), 2)
        self.assertEqual(d[c1], 2)

    def test_flexi_key_constraint(self):
        f = FlexiField("foo")
        c1 = FlexiKeyFieldConstraint([f])
        self.assertEqual(c1.fields, [f])
        c1a = FlexiKeyFieldConstraint([
            FlexiField("foo")])
        c2 = FlexiKeyFieldConstraint([
            FlexiField("bar")])
        c3 = FlexiKeyFieldConstraint([
            FlexiField("foo"), FlexiField("bar")])
        self.assertEqual(c1, c1a)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertNotEqual(c3, c1)
        r = ("FlexiKeyFieldConstraint(fields=["
             "ID:foo:IV:None:INK:None:TAG:None])")
        self.assertEqual(str(c1), r)
        d = {}
        d[c1] = 1
        d[c1a] = 2
        d[c2] = 3
        d[c3] = 4
        self.assertEqual(len(d), 3)
        self.assertEqual(d[c1], 2)
