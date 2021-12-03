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

import os
import unittest
from spinn_utilities.config_holder import set_config
from spinn_utilities.data.data_status import Data_Status
# hack do not copy
from spinn_utilities.data.utils_data_writer import _UtilsDataModel
from spinn_utilities.exceptions import (
    DataNotYetAvialable, NotSetupException)
from pacman.config_setup import unittest_setup
from pacman.exceptions import PacmanConfigurationException
from pacman.data import PacmanDataView
from pacman.data.pacman_data_writer import PacmanDataWriter


class TestSimulatorData(unittest.TestCase):

    def setUp(cls):
        unittest_setup()

    def test_setup(self):
        view = PacmanDataView()
        writer = PacmanDataWriter()
        # What happens before setup depends on the previous test
        # Use manual_check to verify this without dependency
        writer.setup()
        with self.assertRaises(DataNotYetAvialable):
            view.graph

    def test_mock(self):
        view = PacmanDataView()
        writer = PacmanDataWriter()
        writer.mock()
        # check there is a value not what it is

    def test_graphs(self):
        view = PacmanDataView()
        writer = PacmanDataWriter()
        writer.setup()
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
        with self.assertRaises(DataNotYetAvialable):
            writer.runtime_graph
        with self.assertRaises(DataNotYetAvialable):
            writer.runtime_machine_graph()

        writer.start_run()
        writer.runtime_graph
        writer.runtime_machine_graph
        # the writer still has access to the user graphs
        writer.get_graph()
        writer.get_machine_graph()
        # The view does not while in run mode
        with self.assertRaises(DataNotYetAvialable):
            view.graph
        with self.assertRaises(DataNotYetAvialable):
            view.machine_graph

        writer.finish_run()
        writer.graph
        writer.machine_graph
        with self.assertRaises(DataNotYetAvialable):
            writer.runtime_graph
        with self.assertRaises(DataNotYetAvialable):
            writer.runtime_machine_graph()
