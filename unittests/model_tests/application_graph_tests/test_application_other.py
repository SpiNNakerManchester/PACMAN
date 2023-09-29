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
