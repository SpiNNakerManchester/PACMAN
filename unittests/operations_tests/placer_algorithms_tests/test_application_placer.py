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

from typing import Iterable, List, Optional, Sequence, Tuple

from spinn_utilities.config_holder import set_config
from spinn_utilities.overrides import overrides

from spinn_machine.virtual_machine import virtual_machine_by_cores
from spinn_machine.version.version_strings import VersionStrings

from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.exceptions import (PacmanPlaceException, PacmanTooBigToPlace)
from pacman.model.partitioner_splitters import (
    SplitterFixedLegacy, AbstractSplitterCommon)
from pacman.operations.placer_algorithms.application_placer import (
    place_application_graph, ApplicationPlacer)
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import MachineVertex, SimpleMachineVertex
from pacman.model.resources import ConstantSDRAM, AbstractSDRAM
from pacman.model.graphs.application import ApplicationVertex
from pacman.config_setup import unittest_setup
from pacman.model.placements.placements import Placements
from pacman.utilities.utility_objs.chip_counter import ChipCounter
from pacman_test_objects import SimpleTestVertex


class MockSplitter(AbstractSplitterCommon):

    def __init__(self, n_groups: int, n_machine_vertices: int, sdram: int = 0):
        super().__init__()
        self.__n_groups = n_groups
        self.__n_machine_vertices = n_machine_vertices
        self.__same_chip_groups: List[
            Tuple[Sequence[MachineVertex], AbstractSDRAM]] = list()
        self.__sdram = sdram

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(
            self, chip_counter: Optional[ChipCounter]) -> None:
        for _ in range(self.__n_groups):
            m_vertices = [
                SimpleMachineVertex(
                    ConstantSDRAM(0),
                    app_vertex=self.governed_app_vertex,
                    label=f"{self.governed_app_vertex.label}_{i}")
                for i in range(self.__n_machine_vertices)]
            for m_vertex in m_vertices:
                self.governed_app_vertex.remember_machine_vertex(m_vertex)
            self.__same_chip_groups.append(
                (m_vertices, ConstantSDRAM(self.__sdram)))

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        raise NotImplementedError

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return self.governed_app_vertex.machine_vertices

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        return self.governed_app_vertex.machine_vertices

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> Iterable[MachineVertex]:
        return []

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass

    @overrides(AbstractSplitterCommon.get_same_chip_groups)
    def get_same_chip_groups(self) -> Sequence[
            Tuple[Sequence[MachineVertex], AbstractSDRAM]]:
        return self.__same_chip_groups


class MockAppVertex(ApplicationVertex):
    def __init__(self, n_atoms: int, label: str):
        super().__init__(label)
        self.__n_atoms = n_atoms

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self) -> int:
        return self.__n_atoms


def _make_vertices(
        writer: PacmanDataWriter, n_atoms: int, n_groups: int,
        n_machine_vertices: int, label: str, sdram: int = 0) -> MockAppVertex:
    vertex = MockAppVertex(n_atoms, label)
    vertex.splitter = MockSplitter(n_groups, n_machine_vertices, sdram)
    writer.add_vertex(vertex)
    vertex.splitter.create_machine_vertices(None)
    return vertex


def test_application_placer() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    # fixed early works as this vertex is looked at first
    fixed = SimpleTestVertex(10, "FIXED", max_atoms_per_core=1)
    fixed.splitter = SplitterFixedLegacy()
    fixed.set_fixed_location(0, 0)
    writer.add_vertex(fixed)
    fixed.splitter.create_machine_vertices(ChipCounter())
    for i in range(61):
        _make_vertices(writer, 1000, 14, 5, f"app_vertex_{i}")
    # Fudge factor needed as not filling chips well
    writer.set_machine(virtual_machine_by_cores(
        n_cores=int(writer.get_n_machine_vertices() * 1.2)))
    place_application_graph(Placements())


def test_application_placer_large_groups() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    version = writer.get_machine_version()
    # fixed early works as this vertex is looked at first
    fixed = SimpleTestVertex(10, "FIXED", max_atoms_per_core=1)
    fixed.splitter = SplitterFixedLegacy()
    fixed.set_fixed_location(0, 0)
    writer.add_vertex(fixed)
    fixed.splitter.create_machine_vertices(ChipCounter())
    # make groups to fill chips
    n_machine_vertices = version.max_cores_per_chip - 2
    for i in range(17):
        _make_vertices(
            writer, 1000, 14, n_machine_vertices, f"app_vertex_{i}")
    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    place_application_graph(Placements())


def test_application_placer_too_few_boards() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    # fixed early works as this vertex is looked at first
    fixed = SimpleTestVertex(10, "FIXED", max_atoms_per_core=1)
    fixed.splitter = SplitterFixedLegacy()
    fixed.set_fixed_location(0, 0)
    writer.add_vertex(fixed)
    version = writer.get_machine_version()
    n_machine_vertices = version.max_cores_per_chip - 2
    fixed.splitter.create_machine_vertices(ChipCounter())
    for i in range(56):
        _make_vertices(writer, 1000, 14, n_machine_vertices, f"app_vertex_{i}")
    # intentionally too small
    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices() // 2))
    try:
        place_application_graph(Placements())
        raise AssertionError("Error not raise")
    except PacmanPlaceException as ex:
        assert ("No more chips to start" in str(ex))


def test_application_placer_restart_needed() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    for (x, y) in [(1, 0), (1, 1), (0, 1)]:
        fixed = SimpleTestVertex(15, f"FIXED {x}:{y}", max_atoms_per_core=1)
        fixed.splitter = SplitterFixedLegacy()
        fixed.set_fixed_location(x, y)
        writer.add_vertex(fixed)
        fixed.splitter.create_machine_vertices(ChipCounter())
    for i in range(56):
        _make_vertices(writer, 1000, 14, 5, f"app_vertex_{i}")
    # Don't use a full wrap machine
    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    place_application_graph(Placements())


def test_application_placer_late_fixed() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    for i in range(56):
        _make_vertices(writer, 1000, 14, 5, f"app_vertex_{i}")
    # fixed later should work too
    fixed = SimpleTestVertex(10, "FIXED", max_atoms_per_core=1)
    fixed.splitter = SplitterFixedLegacy()
    fixed.set_fixed_location(0, 0)
    writer.add_vertex(fixed)
    fixed.splitter.create_machine_vertices(ChipCounter())

    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    place_application_graph(Placements())


def test_application_placer_fill_chips() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.BIG.text)
    writer = PacmanDataWriter.mock()
    # fixed early works as this vertex is looked at first
    fixed = SimpleTestVertex(10, "FIXED", max_atoms_per_core=1)
    fixed.splitter = SplitterFixedLegacy()
    fixed.set_fixed_location(0, 0)
    writer.add_vertex(fixed)
    fixed.splitter.create_machine_vertices(ChipCounter())
    version = writer.get_machine_version()
    half = version.max_cores_per_chip // 2
    for i in range(17):
        _make_vertices(writer, 1000, 14, half, f"app_vertex_{i}")
    for i in range(17):
        _make_vertices(writer, 1000, 14, half - 1, f"app_vertex_{i}")
    writer.set_machine(virtual_machine_by_cores(
        n_cores=writer.get_n_machine_vertices()))
    place_application_graph(Placements())


def test_sdram_bigger_than_chip() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.ANY.text)
    writer = PacmanDataWriter.mock()
    max_sdram = writer.get_machine_version().max_sdram_per_chip
    _make_vertices(writer, 1, 1, 5, "big_app_vertex",
                   sdram=max_sdram + 24)
    try:
        place_application_graph(Placements())
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("a Chip only has" in str(ex))


def test_sdram_bigger_monitors() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.ANY.text)
    writer = PacmanDataWriter.mock()
    max_sdram = writer.get_machine_version().max_sdram_per_chip
    monitor = SimpleMachineVertex(ConstantSDRAM(max_sdram // 2))
    # This is purely an info call so test check directly
    writer.add_sample_monitor_vertex(monitor, True)
    try:
        placer = ApplicationPlacer(Placements())
        sdram = ConstantSDRAM(max_sdram // 2 + 5)
        placer._check_could_fit(1, sdram=sdram)
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("after monitors only" in str(ex))


def test_more_cores_than_chip() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.ANY.text)
    writer = PacmanDataWriter.mock()
    many = writer.get_machine_version().max_cores_per_chip + 1
    _make_vertices(writer, 1, 1, many, "big_app_vertex")
    try:
        place_application_graph(Placements())
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("number of cores on a chip" in str(ex))


def test_more_cores_than_user() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.ANY.text)
    writer = PacmanDataWriter.mock()
    many = writer.get_machine_version().max_cores_per_chip
    _make_vertices(writer, 1, 1, many, "big_app_vertex")
    try:
        place_application_graph(Placements())
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("the user cores" in str(ex))


def test_more_cores_with_monitor() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.ANY.text)
    writer = PacmanDataWriter.mock()
    monitor = SimpleMachineVertex(ConstantSDRAM(4000))
    # This is purely an info call so test check directly
    writer.add_sample_monitor_vertex(monitor, True)
    many = writer.get_machine_version().max_cores_per_chip - 1
    try:
        placer = ApplicationPlacer(Placements())
        placer._check_could_fit(many, ConstantSDRAM(500000))
        raise AssertionError("Error not raise")
    except PacmanTooBigToPlace as ex:
        assert ("reserved for monitors" in str(ex))


def test_could_fit() -> None:
    unittest_setup()
    set_config("Machine", "versions", VersionStrings.ANY.text)
    writer = PacmanDataWriter.mock()
    monitor = SimpleMachineVertex(ConstantSDRAM(0))
    writer.add_sample_monitor_vertex(monitor, True)
    placer = ApplicationPlacer(Placements())
    many = writer.get_machine_version().max_cores_per_chip - 2
    placer._check_could_fit(many, ConstantSDRAM(500000))
