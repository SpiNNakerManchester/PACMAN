import unittest
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import \
    add_set


class TestUtilities(unittest.TestCase):

    def test_add_join(self):
        all_sets = list()
        all_sets.append({1, 2})
        all_sets.append({3, 4})
        all_sets.append({5, 6})
        new_set = {2, 4}
        add_set(all_sets, new_set)
        self.assertEqual(2, len(all_sets))
        self.assertIn({1, 2, 3, 4}, all_sets)
        self.assertIn({5, 6}, all_sets)

    def test_add_one(self):
        all_sets = list()
        all_sets.append({1, 2})
        all_sets.append({3, 4})
        all_sets.append({5, 6})
        new_set = {2, 7}
        add_set(all_sets, new_set)
        self.assertEqual(3, len(all_sets))
        self.assertIn({1, 2, 7}, all_sets)
        self.assertIn({3, 4}, all_sets)
        self.assertIn({5, 6}, all_sets)

    def test_add_new(self):
        all_sets = list()
        all_sets.append({1, 2})
        all_sets.append({3, 4})
        all_sets.append({5, 6})
        new_set = {8, 7}
        add_set(all_sets, new_set)
        self.assertEqual(4, len(all_sets))
        self.assertIn({1, 2}, all_sets)
        self.assertIn({3, 4}, all_sets)
        self.assertIn({5, 6}, all_sets)
        self.assertIn({7, 8}, all_sets)
