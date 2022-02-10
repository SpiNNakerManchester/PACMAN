# Copyright (c) 2021 The University of Manchester
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
from spinn_utilities.exceptions import (DataLocked, DataNotYetAvialable)
from pacman.config_setup import unittest_setup
from pacman.data import PacmanDataView
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.graphs.machine import (
    MachineGraph, MulticastEdgePartition, SimpleMachineVertex)
from pacman.model.placements import Placements
from pacman.model.routing_info import (
    DictBasedMachinePartitionNKeysMap, RoutingInfo)
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
            PacmanDataView.get_graph()

    def test_mock(self):
        PacmanDataWriter.mock()
        # check there is a value not what it is
        PacmanDataView.get_run_dir_path()

    def test_graphs(self):
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_graph()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_machine_graph()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_runtime_graph()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_runtime_machine_graph()

        writer.create_graphs("bacon")
        writer.get_graph()
        writer.get_machine_graph()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_runtime_graph()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_runtime_machine_graph()

        writer.clone_graphs()
        with self.assertRaises(DataLocked):
            PacmanDataView.get_runtime_graph()
        with self.assertRaises(DataLocked):
            PacmanDataView.get_runtime_machine_graph()
        # the writer still has access to the runtime graphs
        writer.get_runtime_graph()
        writer.get_runtime_machine_graph()

        writer.start_run()
        PacmanDataView.get_runtime_graph()
        PacmanDataView.get_runtime_machine_graph()
        # the writer still has access to the user graphs
        writer.get_graph()
        writer.get_machine_graph()
        # The view does not while in run mode
        with self.assertRaises(DataLocked):
            PacmanDataView.get_graph()
        with self.assertRaises(DataLocked):
            PacmanDataView.get_machine_graph()

        writer.finish_run()
        PacmanDataView.get_graph()
        PacmanDataView.get_machine_graph()
        PacmanDataView.get_runtime_graph()
        PacmanDataView.get_runtime_machine_graph()
        # the writer still has access to the runtime graphs
        writer.get_runtime_graph()
        writer.get_runtime_machine_graph()

        writer.stopping()
        PacmanDataView.get_runtime_graph()
        PacmanDataView.get_runtime_machine_graph()
        # the writer still has access to the user graphs
        writer.get_graph()
        writer.get_machine_graph()
        # The view does not while in stopping mode
        with self.assertRaises(DataLocked):
            PacmanDataView.get_graph()
        with self.assertRaises(DataLocked):
            PacmanDataView.get_machine_graph()

        writer.shut_down()
        PacmanDataView.get_graph()
        PacmanDataView.get_machine_graph()
        with self.assertRaises(DataLocked):
            PacmanDataView.get_runtime_graph()
        with self.assertRaises(DataLocked):
            PacmanDataView.get_runtime_machine_graph()
        # the writer still has access to the runtime graphs
        writer.get_runtime_graph()
        writer.get_runtime_machine_graph()

    def test_graph_support(self):
        writer = PacmanDataWriter.setup()
        writer.create_graphs("test")
        writer.start_run()
        writer.clone_graphs()
        app1 = SimpleTestVertex(12, "app1")
        app2 = SimpleTestVertex(23, "app21")
        app3 = SimpleTestVertex(33, "app3")
        PacmanDataView.get_runtime_graph().add_vertices([app1, app2, app3])
        mach11 = SimpleMachineVertex("mach11",  app_vertex=app1)
        mach12 = SimpleMachineVertex("mach12",  app_vertex=app1)
        mach13 = SimpleMachineVertex("mach13",  app_vertex=app1)
        mach21 = SimpleMachineVertex("mach21",  app_vertex=app2)
        mach22 = SimpleMachineVertex("mach22",  app_vertex=app2)
        mach31 = SimpleMachineVertex("mach31",  app_vertex=app3)
        mg = MachineGraph(
            label="my test",
            application_graph=PacmanDataView.get_runtime_graph())
        m_vertices = set([mach11, mach12, mach13, mach21, mach22, mach31])
        mg.add_vertices(m_vertices)
        writer.set_runtime_machine_graph(mg)
        self.assertEqual(
            6, PacmanDataView.get_runtime_machine_graph().n_vertices)
        self.assertEqual(6, PacmanDataView.get_runtime_n_machine_vertices())
        self.assertEqual(6, PacmanDataView.get_runtime_n_machine_vertices2())
        self.assertSetEqual(
            m_vertices,
            set(PacmanDataView.get_runtime_machine_graph().vertices))
        self.assertSetEqual(
            m_vertices, set(PacmanDataView.get_runtime_machine_vertices()))
        self.assertSetEqual(
            m_vertices, set(PacmanDataView.get_runtime_machine_vertices2()))
        self.assertEqual(PacmanDataView.get_runtime_graph(),
                         PacmanDataView.get_runtime_best_graph())

    def test_graph_mocked(self):
        writer = PacmanDataWriter.mock()
        mg = MachineGraph(label="my test")
        writer.set_runtime_machine_graph(mg)
        self.assertEqual(mg, PacmanDataView.get_runtime_machine_graph())
        self.assertEqual(mg, PacmanDataView.get_runtime_best_graph())

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

    def test_machine_partition_n_keys_map(self):
        pmap = DictBasedMachinePartitionNKeysMap()
        p1 = MulticastEdgePartition(None, "foo")
        p2 = MulticastEdgePartition(None, "bar")
        pmap.set_n_keys_for_partition(p1, 1)
        pmap.set_n_keys_for_partition(p2, 2)
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_machine_partition_n_keys_map()
        writer.set_machine_partition_n_keys_map(pmap)
        self.assertEqual(
            pmap, PacmanDataView.get_machine_partition_n_keys_map())
        with self.assertRaises(TypeError):
            writer.set_machine_partition_n_keys_map("Bacon")

    def test_router_tables(self):
        table = MulticastRoutingTables()
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_uncompressed_router_tables()
        writer.set_uncompressed_router_tables(table)
        self.assertEqual(table, PacmanDataView.get_uncompressed_router_tables())
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_precompressed_router_tables()
        with self.assertRaises(TypeError):
            writer.set_uncompressed_router_tables("Bacon")

    def test_precompressed_router_tables(self):
        table = MulticastRoutingTables()
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_precompressed_router_tables()
        writer.set_precompressed_router_tables(table)
        self.assertEqual(
            table, PacmanDataView.get_precompressed_router_tables())
        with self.assertRaises(DataNotYetAvialable):
            PacmanDataView.get_uncompressed_router_tables()
        with self.assertRaises(TypeError):
            writer.set_precompressed_router_tables()
