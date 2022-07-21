# Copyright (c) 2017-2019 The University of Manchester
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
import sys
import unittest

from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.routing_tables.multicast_routing_tables import (from_json)
from pacman.exceptions import PacmanElementAllocationException
from pacman.operations.router_compressors import (
    pair_compressor)


class TestUnorderedPairCompressor(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_onordered_pair_big(self):
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        j_router = os.path.join(path, "many_to_one.json.gz")
        original_tables = from_json(j_router)

        PacmanDataWriter.mock().set_precompressed(original_tables)
        with self.assertRaises(PacmanElementAllocationException):
            pair_compressor(
                ordered=False, accept_overflow=False,  verify=True)
