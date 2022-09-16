# Copyright (c) 2022 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from pacman.config_setup import unittest_setup
from pacman.utilities.algorithm_utilities.routing_tree import RoutingTree


class TestRoutingTre(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_call(self):
        # Note Vertices as string is incorrect but easier to do for test

        rt1 = RoutingTree((3, 4))
        self.assertIsNone(rt1.label)
        self.assertEqual(rt1.chip, (3, 4))
        self.assertTrue(rt1.is_leaf)
        self.assertIsNotNone(repr(rt1))
        rt1.append_child((1, "m_vertexA"))
        rt1.append_child((2, "m_vertexB"))
        self.assertFalse(rt1.is_leaf)
        self.assertListEqual([(1, "m_vertexA"), (2, "m_vertexB")],
                             list(rt1.children))
        self.assertListEqual([rt1, "m_vertexA", "m_vertexB"],
                             list(iter(rt1)))

        rt2 = RoutingTree((4, 5), "foo")
        self.assertEqual("foo", rt2.label)
        rt2.append_child((2, "m_vertex1"))
        self.assertFalse(rt2.is_leaf)
        rt2.append_child((1, "m_vertex2"))
        rt2.append_child((3, rt1))

        self.assertListEqual([(2, "m_vertex1"), (1, "m_vertex2"), (3, rt1)],
                             list(rt2.children))
        self.assertIsNotNone(str(rt2))
        rt2.remove_child((1, "m_vertex2"))
        self.assertListEqual([(2, "m_vertex1"), (3, rt1)], list(rt2.children))
        a = list(iter(rt2))
        self.assertListEqual([rt2, "m_vertex1", rt1, "m_vertexA", "m_vertexB"],
                             list(iter(rt2)))
        self.assertListEqual(
            [(None, (4, 5), {2, 3}), (3, (3, 4), {1, 2})],
            list(rt2.traverse())
        )


if __name__ == '__main__':
    unittest.main()
