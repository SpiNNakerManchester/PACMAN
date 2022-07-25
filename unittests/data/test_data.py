# Copyright (c) 2021-2022 The University of Manchester
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
from spinn_utilities.exceptions import (
    DataNotYetAvialable, SimulatorRunningException)
from pacman.config_setup import unittest_setup
from pacman.data import PacmanDataView
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.application import ApplicationEdge
from pacman.model.placements import Placements
from pacman.model.routing_info import RoutingInfo
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition)
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.model.tags import Tags
from pacman_test_objects import SimpleTestVertex


class TestSimulatorData(unittest.TestCase):

    def setUp(cls):
        unittest_setup()

    def test_setup(self):
        # What happens before setup depends on the previous test
        # Use manual_check to verify this without dependency
        PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_n_vertices()

    def test_mock(self):
        PacmanDataWriter.mock()
        # check there is a value not what it is
        PacmanDataView.get_run_dir_path()

    def test_graphs(self):
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_n_vertices()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_runtime_graph()

        writer.create_graphs("bacon")
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_runtime_graph()

        writer.start_run()
        writer.clone_graphs()
        PacmanDataView.get_runtime_graph()

        writer.finish_run()
        PacmanDataView.get_n_vertices()
        PacmanDataView.get_runtime_graph()
        # the writer still has access to the runtime graphs
        writer.get_runtime_graph()

        writer.stopping()
        PacmanDataView.get_runtime_graph()

    def test_graph_functions(self):
        writer = PacmanDataWriter.setup()
        app1 = SimpleTestVertex(12, "app1")
        app2 = SimpleTestVertex(23, "app21")
        app3 = SimpleTestVertex(33, "app3")
        edge12 = ApplicationEdge(app1, app2)
        edge32 = ApplicationEdge(app3, app2)
        edge13 = ApplicationEdge(app1, app3)
        edge11 = ApplicationEdge(app1, app1)
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_n_vertices()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_edges_ending_at_vertex(app1)
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.add_vertex(app1)
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.add_edge(edge12, "foo")
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.iterate_vertices()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_n_vertices()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.iterate_partitions()

        writer.create_graphs("test")
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
            set([edge12, edge32]),
            set(PacmanDataView.get_edges_ending_at_vertex(app2)))
        self.assertSetEqual(
            set([app1, app2, app3]),
            set(PacmanDataView.iterate_vertices()))
        self.assertEqual(3, PacmanDataView.get_n_vertices())
        partitions = set(PacmanDataView.iterate_partitions())
        self.assertEqual(2, len(partitions))
        self.assertEqual(2, PacmanDataView.get_n_partitions())

        writer.start_run()
        # the add methods go boom
        with self.assertRaises(SimulatorRunningException):
            PacmanDataView.add_vertex(app1)
        with self.assertRaises(SimulatorRunningException):
            PacmanDataView.add_edge(edge12, "foo")
        # The info methods do still work
        self.assertTrue(PacmanDataView.get_n_vertices() > 0)
        self.assertSetEqual(
            set([app1, app2, app3]),
            set(PacmanDataView.iterate_vertices()))
        self.assertEqual(3, PacmanDataView.get_n_vertices())

        writer.finish_run()
        app4 = SimpleTestVertex(44, "app4")
        edge14 = ApplicationEdge(app1, app4)
        PacmanDataView.add_vertex(app4)
        self.assertSetEqual(
            set([app1, app2, app3, app4]),
            set(PacmanDataView.iterate_vertices()))
        self.assertEqual(4, PacmanDataView.get_n_vertices())
        PacmanDataView.add_edge(edge14, "other")

    def test_placements(self):
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_placements()
        info = Placements([])
        writer.set_placements(info)
        self.assertEqual(info, PacmanDataView.get_placements())
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
            writer.set_precompressed()

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
