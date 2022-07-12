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

"""
runs all pacman unittest scripts
"""
import unittest

testmodules = [
    'model_tests.graph_mapper_tests.test_graph_mapping',
    'model_tests.graph_mapper_tests.test_slice',
    'model_tests.application_graph_tests.test_application_edge',
    'model_tests.application_graph_tests.test_application_graph',
    'model_tests.application_graph_tests.test_application_vertex',
    'model_tests.placement_tests.test_placement_object',
    'model_tests.placement_tests.test_placements_model',
    'model_tests.resources_tests.test_resources_model',
    'model_tests.routing_table_tests.test_multi_cast_routing_entry',
    'model_tests.routing_table_tests.test_routing_tables_model',
    'model_tests.tag_tests.test_tag_infos_model',
    'utilities_tests.test_progress_bar',
    'operations_tests.partition_algorithms_tests.test_basic_partitioner',
    'operations_tests.partition_algorithms_tests.'
    'test_partition_and_place_partitioner',
    'operations_tests.placer_algorithms_tests.test_basic_placer',
    'operations_tests.placer_algorithms_tests.test_radial_placer',
    'operations_tests.router_algorithms_tests.test_basic_dijkstra_routing',
    'operations_tests.router_algorithms_tests.test_generic_router',
    'operations_tests.routing_info_algorithms_tests.'
    'test_malloc_routing_info_allocator']

suite = unittest.TestSuite()

for t in testmodules:
    try:
        # If the module defines a suite() function, call it to get the suite.
        mod = __import__(t, globals(), locals(), ['suite'])
        suitefn = getattr(mod, 'suite')
        suite.addTest(suitefn())
    except (ImportError, AttributeError):
        # else, just load all the test cases from the module.
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

unittest.TextTestRunner().run(suite)
