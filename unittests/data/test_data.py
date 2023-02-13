# Copyright (c) 2021-2023 The University of Manchester
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
from spinn_utilities.exceptions import (
    DataNotYetAvialable, SimulatorRunningException, SimulatorShutdownException)
from pacman.config_setup import unittest_setup
from pacman.data import PacmanDataView
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.exceptions import (
    PacmanConfigurationException, PacmanNotPlacedError)
from pacman.model.graphs.common import Slice
from pacman.model.graphs.application import ApplicationEdge
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placement, Placements
from pacman.model.routing_info import RoutingInfo
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition)
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.model.tags import Tags
from pacman_test_objects import SimpleTestVertex


class SimpleTestVertex2(SimpleTestVertex):
    pass


class TestSimulatorData(unittest.TestCase):

    def setUp(cls):
        unittest_setup()

    def test_setup(self):
        # What happens before setup depends on the previous test
        # Use manual_check to verify this without dependency
        PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_n_placements()

    def test_mock(self):
        PacmanDataWriter.mock()
        # check there is a value not what it is
        PacmanDataView.get_run_dir_path()

    def test_graph_functions(self):
        writer = PacmanDataWriter.setup()
        app1 = SimpleTestVertex(12, "app1")
        m11 = app1.create_machine_vertex(Slice(0, 6), None)
        app1.remember_machine_vertex(m11)
        m12 = app1.create_machine_vertex(Slice(7, 12), None)
        app1.remember_machine_vertex(m12)
        app2 = SimpleTestVertex2(23, "app21")
        m21 = app2.create_machine_vertex(Slice(0, 23), None)
        app2.remember_machine_vertex(m21)
        app3 = SimpleTestVertex2(33, "app3")
        m31 = app3.create_machine_vertex(Slice(0, 11), None)
        app3.remember_machine_vertex(m31)
        m32 = app3.create_machine_vertex(Slice(11, 22), None)
        app3.remember_machine_vertex(m32)
        m33 = app3.create_machine_vertex(Slice(22, 33), None)
        app3.remember_machine_vertex(m33)
        edge12 = ApplicationEdge(app1, app2)
        edge32 = ApplicationEdge(app3, app2)
        edge13 = ApplicationEdge(app1, app3)
        edge11 = ApplicationEdge(app1, app1)

        self.assertFalse(PacmanDataView.get_n_vertices() == 1)
        PacmanDataView.add_vertex(app1)
        PacmanDataView.add_vertex(app2)
        PacmanDataView.add_vertex(app3)
        PacmanDataView.add_edge(edge12, "foo")
        PacmanDataView.add_edge(edge13, "foo")
        PacmanDataView.add_edge(edge11, "foo")
        PacmanDataView.add_edge(edge32, "bar")

        self.assertTrue(PacmanDataView.get_n_vertices() > 0)
        self.assertSetEqual(
            set([app1, app2, app3]),
            set(PacmanDataView.iterate_vertices()))
        self.assertEqual(
            [app2, app3],
            list(PacmanDataView.get_vertices_by_type(SimpleTestVertex2)))
        self.assertEqual(3, PacmanDataView.get_n_vertices())
        partitions = set(PacmanDataView.iterate_partitions())
        self.assertEqual(2, len(partitions))
        self.assertEqual(2, PacmanDataView.get_n_partitions())
        ps = PacmanDataView.get_outgoing_edge_partitions_starting_at_vertex(
            app1)
        self.assertEqual(1, len(ps))
        self.assertEqual([edge12, edge13, edge11, edge32],
                         PacmanDataView.get_edges())
        self.assertEqual(6, PacmanDataView.get_n_machine_vertices())
        self.assertEqual([m11, m12, m21, m31, m32, m33],
                         list(PacmanDataView.iterate_machine_vertices()))

        writer.shut_down()
        # Graph info calls still work
        list(PacmanDataView.iterate_vertices())
        list(PacmanDataView.get_vertices_by_type(SimpleTestVertex2))
        PacmanDataView.get_n_vertices()
        set(PacmanDataView.iterate_partitions())
        PacmanDataView.get_n_partitions()
        PacmanDataView.get_outgoing_edge_partitions_starting_at_vertex(app1)
        PacmanDataView.get_edges()
        PacmanDataView.get_n_machine_vertices()
        PacmanDataView.iterate_machine_vertices()

        # Adding will no longer work
        with self.assertRaises(SimulatorShutdownException):
            PacmanDataView.add_vertex(SimpleTestVertex(12, "new"))
        with self.assertRaises(SimulatorShutdownException):
            PacmanDataView.add_edge(ApplicationEdge(app1, app2), "new")

    def test_graph_safety_code(self):
        writer = PacmanDataWriter.setup()
        # there is always a graph so to hit safety code you need a hack
        writer._PacmanDataWriter__pacman_data._graph = None
        with self.assertRaises(DataNotYetAvialable):
            writer.add_vertex(None)
        with self.assertRaises(DataNotYetAvialable):
            writer.add_edge(None, None)
        with self.assertRaises(DataNotYetAvialable):
            writer.iterate_vertices()
        with self.assertRaises(DataNotYetAvialable):
            list(writer.get_vertices_by_type(None))
        with self.assertRaises(DataNotYetAvialable):
            writer.get_n_vertices()
        with self.assertRaises(DataNotYetAvialable):
            writer.iterate_partitions()
        with self.assertRaises(DataNotYetAvialable):
            writer.get_n_partitions()
        with self.assertRaises(DataNotYetAvialable):
            writer.get_outgoing_edge_partitions_starting_at_vertex(None)
        with self.assertRaises(DataNotYetAvialable):
            writer.get_edges()
        with self.assertRaises(DataNotYetAvialable):
            writer.get_n_machine_vertices()
        with self.assertRaises(DataNotYetAvialable):
            list(writer.iterate_machine_vertices())

    def test_graph_never_changes(self):
        writer = PacmanDataWriter.setup()
        # graph is hidden so need a hack to get it.
        graph1 = writer._PacmanDataWriter__pacman_data._graph
        writer.start_run()
        graph2 = writer._PacmanDataWriter__pacman_data._graph
        self.assertEqual(id(graph1), id(graph2))
        writer.finish_run()
        graph2 = writer._PacmanDataWriter__pacman_data._graph
        self.assertEqual(id(graph1), id(graph2))
        writer.soft_reset()
        graph2 = writer._PacmanDataWriter__pacman_data._graph
        self.assertEqual(id(graph1), id(graph2))
        writer.hard_reset()
        graph2 = writer._PacmanDataWriter__pacman_data._graph
        self.assertEqual(id(graph1), id(graph2))
        writer.start_run()
        graph2 = writer._PacmanDataWriter__pacman_data._graph
        self.assertEqual(id(graph1), id(graph2))
        writer.finish_run()
        graph2 = writer._PacmanDataWriter__pacman_data._graph
        self.assertEqual(id(graph1), id(graph2))

    def test_placements_safety_code(self):
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            writer.iterate_placemements()
        with self.assertRaises(DataNotYetAvialable):
            writer.iterate_placements_by_vertex_type(None)
        with self.assertRaises(DataNotYetAvialable):
            writer.iterate_placements_on_core(None, None)
        with self.assertRaises(DataNotYetAvialable):
            writer.iterate_placements_by_xy_and_type(None, None, None)
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_n_placements()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_placement_of_vertex(None)
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_placement_on_processor(None, None, None)

    def test_placements(self):
        writer = PacmanDataWriter.setup()
        info = Placements([])
        p1 = Placement(SimpleMachineVertex(None), 1, 2, 3)
        info.add_placement(p1)
        v2 = SimpleMachineVertex(None)
        p2 = Placement(v2, 1, 2, 5)
        info.add_placement(p2)
        info.add_placement(Placement(SimpleMachineVertex(None), 2, 2, 3))
        writer.set_placements(info)
        self.assertEqual(3, PacmanDataView.get_n_placements())
        on12 = list(PacmanDataView.iterate_placements_on_core(1, 2))
        self.assertEqual(on12, [p1, p2])
        vertex = PacmanDataView.get_placement_on_processor(1, 2, 5).vertex
        self.assertEqual(v2, vertex)
        with self.assertRaises(PacmanNotPlacedError):
            PacmanDataView.get_placement_of_vertex(SimpleMachineVertex(None))

        with self.assertRaises(TypeError):
            writer.set_placements("Bacon")

    def test_routing_infos(self):
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_routing_infos()
        info = RoutingInfo()
        writer.set_routing_infos(info)
        self.assertEqual(info, PacmanDataView.get_routing_infos())
        with self.assertRaises(TypeError):
            writer.set_routing_infos("Bacon")

    def test_tags(self):
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_tags()
        tags = Tags()
        writer.set_tags(tags)
        self.assertEqual(tags, PacmanDataView.get_tags())
        with self.assertRaises(TypeError):
            writer.set_tags("Bacon")

    def test_router_tables(self):
        table = MulticastRoutingTables()
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_uncompressed()
        writer.set_uncompressed(table)
        self.assertEqual(table, PacmanDataView.get_uncompressed())
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_precompressed()
        with self.assertRaises(TypeError):
            writer.set_uncompressed("Bacon")

    def test_precompressed_router_tables(self):
        table = MulticastRoutingTables()
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_precompressed()
        writer.set_precompressed(table)
        self.assertEqual(
            table, PacmanDataView.get_precompressed())
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_uncompressed()
        with self.assertRaises(TypeError):
            writer.set_precompressed(None)

    def test_plan_n_timesteps(self):
        writer = PacmanDataWriter.setup()
        writer.set_plan_n_timesteps(1234)
        self.assertEqual(1234, PacmanDataView.get_plan_n_timestep())
        with self.assertRaises(TypeError):
            writer.set_plan_n_timesteps("Bacon")
        with self.assertRaises(PacmanConfigurationException):
            writer.set_plan_n_timesteps(-1)

    def test_routing_table_by_partition(self):
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_routing_table_by_partition()
        table = MulticastRoutingTableByPartition()
        writer.set_routing_table_by_partition(table)
        self.assertEqual(
            table, PacmanDataView.get_routing_table_by_partition())
        with self.assertRaises(TypeError):
            writer.set_routing_table_by_partition("Bacon")

    def test_add_requires_mapping(self):
        writer = PacmanDataWriter.setup()
        # before first run
        self.assertTrue(PacmanDataView.get_requires_mapping())
        writer.start_run()
        writer.finish_run()
        # after a run false
        self.assertFalse(PacmanDataView.get_requires_mapping())

        # Check add vertex requires mapping
        v1 = SimpleTestVertex(1)
        PacmanDataView.add_vertex(v1)
        self.assertTrue(PacmanDataView.get_requires_mapping())
        v2 = SimpleTestVertex(2)
        PacmanDataView.add_vertex(v2)

        # after a run false
        writer.start_run()
        writer.finish_run()
        self.assertFalse(PacmanDataView.get_requires_mapping())

        # Check add edge requires mapping
        e12 = ApplicationEdge(v1, v2)
        PacmanDataView.add_edge(e12, "foo")
        self.assertTrue(PacmanDataView.get_requires_mapping())

        # after a run false
        writer.start_run()
        writer.finish_run()
        self.assertFalse(PacmanDataView.get_requires_mapping())

        # check can not add if requires mapping false
        v3 = SimpleTestVertex(1)
        e13 = ApplicationEdge(v1, v2)
        writer.start_run()
        with self.assertRaises(SimulatorRunningException):
            PacmanDataView.add_vertex(v3)
        with self.assertRaises(SimulatorRunningException):
            PacmanDataView.add_edge(e13, "foo")
        with self.assertRaises(PacmanConfigurationException):
            writer.add_vertex(v3)
        with self.assertRaises(PacmanConfigurationException):
            writer.add_edge(e13, "foo")
        writer.finish_run()
        self.assertFalse(PacmanDataView.get_requires_mapping())

        # check writer can add if requires mapping True
        PacmanDataView.add_vertex(v3)
        v4 = SimpleTestVertex(1)
        e13 = ApplicationEdge(v1, v2)
        self.assertTrue(PacmanDataView.get_requires_mapping())
        writer.start_run()
        with self.assertRaises(SimulatorRunningException):
            PacmanDataView.add_vertex(v4)
        with self.assertRaises(SimulatorRunningException):
            PacmanDataView.add_edge(e13, "foo")
        writer.add_vertex(v4)
        writer.add_edge(e13, "foo")
        writer.finish_run()
        self.assertFalse(PacmanDataView.get_requires_mapping())

        # Check resets
        v5 = SimpleTestVertex(1)
        PacmanDataView.add_vertex(v5)
        self.assertTrue(PacmanDataView.get_requires_mapping())
        writer.soft_reset()
        self.assertTrue(PacmanDataView.get_requires_mapping())
        writer.hard_reset()
        self.assertTrue(PacmanDataView.get_requires_mapping())
