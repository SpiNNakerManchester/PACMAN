# Copyright (c) 2022 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from pacman.config_setup import unittest_setup
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.utilities.algorithm_utilities.routing_tree import RoutingTree


class TestRoutingTre(unittest.TestCase):

    def setUp(self) -> None:
        unittest_setup()

    def test_call(self) -> None:
        m_vertex_a = SimpleMachineVertex(None, "m_vertex_a")
        m_vertex_b = SimpleMachineVertex(None, "m_vertex_b")
        m_vertex_1 = SimpleMachineVertex(None, "m_vertex_1")
        m_vertex_2 = SimpleMachineVertex(None, "m_vertex_2")
        rt1 = RoutingTree((3, 4))
        self.assertIsNone(rt1.label)
        self.assertEqual(rt1.chip, (3, 4))
        self.assertTrue(rt1.is_leaf)
        self.assertIsNotNone(repr(rt1))
        rt1.append_child((1, m_vertex_a))
        rt1.append_child((2, m_vertex_b))
        self.assertFalse(rt1.is_leaf)
        self.assertListEqual([(1, m_vertex_a), (2, m_vertex_b)],
                             list(rt1.children))
        self.assertListEqual([rt1, m_vertex_a, m_vertex_b],
                             list(iter(rt1)))
        self.assertEqual(len(rt1), len(list(rt1)))

        rt2 = RoutingTree((4, 5), "foo")
        self.assertEqual("foo", rt2.label)
        rt2.append_child((2, m_vertex_1))
        self.assertFalse(rt2.is_leaf)
        rt2.append_child((1, m_vertex_2))
        rt2.append_child((3, rt1))

        self.assertListEqual([(2, m_vertex_1), (1, m_vertex_2), (3, rt1)],
                             list(rt2.children))
        self.assertIsNotNone(str(rt2))
        rt2.remove_child((1, m_vertex_2))
        self.assertListEqual([(2, m_vertex_1), (3, rt1)], list(rt2.children))
        self.assertListEqual([rt2, m_vertex_1, rt1, m_vertex_a, m_vertex_b],
                             list(iter(rt2)))
        self.assertListEqual(
            [(None, (4, 5), {2, 3}), (3, (3, 4), {1, 2})],
            list(rt2.traverse())
        )
        self.assertEqual(len(rt2), len(list(rt2)))


if __name__ == '__main__':
    unittest.main()
