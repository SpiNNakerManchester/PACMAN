# Copyright (c) 2017 The University of Manchester
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

import os
import sys
import unittest

from spinn_utilities.config_holder import set_config
from spinn_machine import virtual_machine
from spinn_machine.version.version_strings import VersionStrings
from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.routing_tables.multicast_routing_tables import (from_json)
from pacman.exceptions import PacmanElementAllocationException
from pacman.operations.router_compressors import (
    pair_compressor)


class TestUnorderedPairCompressor(unittest.TestCase):

    def setUp(self):
        unittest_setup()
        set_config("Machine", "versions", VersionStrings.WRAPPABLE.value)

    def test_onordered_pair_big(self):

        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        j_router = os.path.join(path, "many_to_one.json.gz")
        original_tables = from_json(j_router)

        writer = PacmanDataWriter.mock()
        writer.set_precompressed(original_tables)
        # This tests requires a full wrap machine
        # The input includes Chips like 3, 8
        writer.set_machine(virtual_machine(24, 24))
        with self.assertRaises(PacmanElementAllocationException):
            pair_compressor(
                ordered=False, accept_overflow=False,  verify=True)
