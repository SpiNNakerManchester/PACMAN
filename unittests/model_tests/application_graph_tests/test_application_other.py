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
from pacman.model.graphs.application import (
    ApplicationFPGAVertex, ApplicationSpiNNakerLinkVertex)


class TestApplicationOther(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def setUp(self):
        unittest_setup()

    def test_spinnaker_link(self):
        slv = ApplicationSpiNNakerLinkVertex(100, 2, "127.4.5.6")
        self.assertEqual(2, slv.spinnaker_link_id)
        self.assertEqual("127.4.5.6", slv.board_address)

    def test_fpga_no_connection(self):
        fpga = ApplicationFPGAVertex(100)
        self.assertEqual(0, len(list(fpga.incoming_fpga_connections)))
        self.assertIsNone(fpga.outgoing_fpga_connection)
