# Copyright (c) 2022 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
        self.assertListEqual([rt2, "m_vertex1", rt1, "m_vertexA", "m_vertexB"],
                             list(iter(rt2)))
        self.assertListEqual(
            [(None, (4, 5), {2, 3}), (3, (3, 4), {1, 2})],
            list(rt2.traverse())
        )


if __name__ == '__main__':
    unittest.main()
