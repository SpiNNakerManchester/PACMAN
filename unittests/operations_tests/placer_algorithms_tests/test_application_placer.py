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

from spinn_machine import Machine
from spinn_machine.virtual_machine import virtual_machine
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.exceptions import (
    PacmanConfigurationException, PacmanTooBigToPlace)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.model.partitioner_splitters import SplitterFixedLegacy
from pacman.operations.placer_algorithms.application_placer import (
    place_application_graph, _check_could_fit)
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import ConstantSDRAM
from pacman.model.graphs.application import ApplicationVertex
from pacman.config_setup import unittest_setup
from pacman.model.placements.placements import Placements
from pacman.utilities.utility_objs.chip_counter import ChipCounter
from pacman_test_objects import SimpleTestVertex


class TestSplitter(AbstractSplitterCommon):

    def __init__(self, n_groups, n_machine_vertices, sdram=0):
        super().__init__()
        self.__n_groups = n_groups
        self.__n_machine_vertices = n_machine_vertices
        self.__same_chip_groups = list()
        self.__sdram = sdram

    def create_machine_vertices(self, chip_counter):
        for _ in range(self.__n_groups):
            m_vertices = [
                SimpleMachineVertex(
                    ConstantSDRAM(0),
                    app_vertex=self._governed_app_vertex,
                    label=f"{self._governed_app_vertex.label}_{i}")
                for i in range(self.__n_machine_vertices)]
            for m_vertex in m_vertices:
                self._governed_app_vertex.remember_machine_vertex(m_vertex)
            self.__same_chip_groups.append(
                (m_vertices, ConstantSDRAM(self.__sdram)))

    def get_out_going_slices(self):
        return None

    def get_in_coming_slices(self):
        return None

    def get_out_going_vertices(self, partition_id):
        return self._governed_app_vertex.machine_vertices

    def get_in_coming_vertices(self, partition_id):
        return self._governed_app_vertex.machine_vertices

    def machine_vertices_for_recording(self, variable_to_record):
        return []

    def reset_called(self):
        pass

    def get_same_chip_groups(self):
        return self.__same_chip_groups


class TestAppVertex(ApplicationVertex):
    def __init__(self, n_atoms, label):
        super(TestAppVertex, self).__init__(label)
        self.__n_atoms = n_atoms

    @property
    def n_atoms(self):
        return self.__n_atoms


def _make_vertices(
        writer, n_atoms, n_groups, n_machine_vertices, label, sdram=0):
    vertex = TestAppVertex(n_atoms, label)
    vertex.splitter = TestSplitter(n_groups, n_machine_vertices, sdram)
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(None)
    return vertex


def test_application_placer():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    # fixed early works as this vertex is looked at first
    fixed = SimpleTestVertex(10, "FIXED", max_atoms_per_core=1)
    fixed.splitter = SplitterFixedLegacy()
    fixed.set_fixed_location(0, 0)
    writer.add_vertex(fixed)
    fixed.splitter.create_machine_vertices(ChipCounter())
    for i in range(56):
        _make_vertices(writer, 1000, 14, 5, f"app_vertex_{i}")
    writer.set_machine(virtual_machine(24, 12))
    place_application_graph(Placements())


def test_application_placer_late_fixed():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    for i in range(56):
        _make_vertices(writer, 1000, 14, 5, f"app_vertex_{i}")
    # fixed later should work too
    fixed = SimpleTestVertex(10, "FIXED", max_atoms_per_core=1)
    fixed.splitter = SplitterFixedLegacy()
    fixed.set_fixed_location(0, 0)
    writer.add_vertex(fixed)
    fixed.splitter.create_machine_vertices(ChipCounter())

    writer.set_machine(virtual_machine(24, 12))
    try:
        place_application_graph(Placements())
    except PacmanConfigurationException:
        raise unittest.SkipTest(
            "https://github.com/SpiNNakerManchester/PACMAN/issues/444")


def test_sdram_bigger_than_chip():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    _make_vertices(writer, 1, 1, 5, "big_app_vertex",
                   sdram=Machine.DEFAULT_SDRAM_BYTES + 24)
    try:
        place_application_graph(Placements())
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("a Chip only has" in str(ex))


def test_sdram_bigger_monitors():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    monitor = SimpleMachineVertex(
                    ConstantSDRAM(Machine.DEFAULT_SDRAM_BYTES // 2))
    # This is purely an info call so test check directly
    writer.add_monitor_all_chips(monitor)
    try:
        _check_could_fit("app_test", ["m_vertex]"],
                         sdram=Machine.DEFAULT_SDRAM_BYTES // 2 + 5)
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("after monitors only" in str(ex))


def test_more_cores_than_chip():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    _make_vertices(writer, 1, 1, 19, "big_app_vertex")
    try:
        place_application_graph(Placements())
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("number of cores on a chip" in str(ex))


def test_more_cores_than_user():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    _make_vertices(writer, 1, 1, 18, "big_app_vertex")
    try:
        place_application_graph(Placements())
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("the user cores" in str(ex))


def test_more_cores_with_monitor():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    monitor = SimpleMachineVertex(ConstantSDRAM(4000))
    # This is purely an info call so test check directly
    writer.add_monitor_all_chips(monitor)
    m_vertexs = [f"m_v_{i}" for i in range(17)]
    try:
        _check_could_fit("app_test", m_vertexs, 500000)
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("reserved for monitors" in str(ex))


def test_could_fit():
    unittest_setup()
    writer = PacmanDataWriter.mock()
    monitor = SimpleMachineVertex(ConstantSDRAM(0))
    writer.add_monitor_all_chips(monitor)
    m_vertexs = [f"m_v_{i}" for i in range(16)]
    _check_could_fit("app_test", m_vertexs, 500000)
