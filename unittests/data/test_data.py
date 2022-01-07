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
from pacman.model.graphs.machine import (MachineGraph, SimpleMachineVertex)
from pacman.model.placements import Placements
from pacman.model.routing_info import RoutingInfo
from pacman_test_objects import SimpleTestVertex


class TestSimulatorData(unittest.TestCase):

    def setUp(cls):
        unittest_setup()

    def test_setup(self):
        view = PacmanDataView()
        # What happens before setup depends on the previous test
        # Use manual_check to verify this without dependency
        PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            view.graph

    def test_mock(self):
        PacmanDataWriter.mock()
        # check there is a value not what it is
        PacmanDataView.get_run_dir_path()

    def test_graphs(self):
        view = PacmanDataView()
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            writer.graph
        with self.assertRaises(DataNotYetAvialable):
            writer.machine_graph
        with self.assertRaises(DataNotYetAvialable):
            writer.runtime_graph
        with self.assertRaises(DataNotYetAvialable):
            writer.runtime_machine_graph()

        writer.create_graphs("bacon")
        writer.graph
        writer.machine_graph
        with self.assertRaises(DataNotYetAvialable):
            writer.runtime_graph
        with self.assertRaises(DataNotYetAvialable):
            writer.runtime_machine_graph()

        writer.clone_graphs()
        with self.assertRaises(DataLocked):
            writer.runtime_graph
        with self.assertRaises(DataLocked):
            writer.runtime_machine_graph()
        # the writer still has access to the runtime graphs
        writer.get_runtime_graph()
        writer.get_runtime_machine_graph()

        writer.start_run()
        writer.runtime_graph
        writer.runtime_machine_graph
        # the writer still has access to the user graphs
        writer.get_graph()
        writer.get_machine_graph()
        # The view does not while in run mode
        with self.assertRaises(DataLocked):
            view.graph
        with self.assertRaises(DataLocked):
            view.machine_graph

        writer.finish_run()
        writer.graph
        writer.machine_graph
        writer.runtime_graph
        writer.runtime_machine_graph
        # the writer still has access to the runtime graphs
        writer.get_runtime_graph()
        writer.get_runtime_machine_graph()

        writer.stopping()
        writer.runtime_graph
        writer.runtime_machine_graph
        # the writer still has access to the user graphs
        writer.get_graph()
        writer.get_machine_graph()
        # The view does not while in stopping mode
        with self.assertRaises(DataLocked):
            view.graph
        with self.assertRaises(DataLocked):
            view.machine_graph

        writer.shut_down()
        writer.graph
        writer.machine_graph
        with self.assertRaises(DataLocked):
            writer.runtime_graph
        with self.assertRaises(DataLocked):
            writer.runtime_machine_graph()
        # the writer still has access to the runtime graphs
        writer.get_runtime_graph()
        writer.get_runtime_machine_graph()

    def test_graph_support(self):
        view = PacmanDataView()
        writer = PacmanDataWriter.setup()
        writer.create_graphs("test")
        writer.start_run()
        writer.clone_graphs()
        app1 = SimpleTestVertex(12, "app1")
        app2 = SimpleTestVertex(23, "app21")
        app3 = SimpleTestVertex(33, "app3")
        writer.runtime_graph.add_vertices([app1, app2, app3])
        mach11 = SimpleMachineVertex("mach11",  app_vertex=app1)
        mach12 = SimpleMachineVertex("mach12",  app_vertex=app1)
        mach13 = SimpleMachineVertex("mach13",  app_vertex=app1)
        mach21 = SimpleMachineVertex("mach21",  app_vertex=app2)
        mach22 = SimpleMachineVertex("mach22",  app_vertex=app2)
        mach31 = SimpleMachineVertex("mach31",  app_vertex=app3)
        mg = MachineGraph(
            label="my test", application_graph=writer.runtime_graph)
        m_vertices = set([mach11, mach12, mach13, mach21, mach22, mach31])
        mg.add_vertices(m_vertices)
        writer.set_runtime_machine_graph(mg)
        self.assertEqual(6, view.runtime_machine_graph.n_vertices)
        self.assertEqual(6, view.runtime_n_machine_vertices)
        self.assertEqual(6, view.runtime_n_machine_vertices2)
        self.assertSetEqual(
            m_vertices, set(view.runtime_machine_graph.vertices))
        self.assertSetEqual(
            m_vertices, set(view.runtime_machine_vertices))
        self.assertSetEqual(
            m_vertices, set(view.runtime_machine_vertices2))

    def test_placements(self):
        view = PacmanDataView()
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            view.placements
        info = Placements([])
        writer.set_placements(info)
        self.assertEqual(info, view.placements)
        with self.assertRaises(TypeError):
            writer.set_placements("Bacon")

    def test_routing_infos(self):
        view = PacmanDataView()
        writer = PacmanDataWriter.setup()
        with self.assertRaises(DataNotYetAvialable):
            view.routing_infos
        info = RoutingInfo()
        writer.set_routing_infos(info)
        self.assertEqual(info, view.routing_infos)
        with self.assertRaises(TypeError):
            writer.set_routing_infos("Bacon")
