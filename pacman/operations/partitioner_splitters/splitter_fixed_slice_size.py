# Copyright (c) 2020-2021 The University of Manchester
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
from pacman.exceptions import (
    PacmanPartitionException, PacmanConfigurationException)
from pacman.model.constraints.partitioner_constraints import (
    FixedVertexAtomsConstraint, MaxVertexAtomsConstraint)
from pacman.model.graphs.common import Slice
from pacman.model.partitioner_interfaces import AbstractSplitterCommon
from pacman.model.partitioner_interfaces.legacy_partitioner_api import (
    LegacyPartitionerAPI)
from pacman.utilities import utility_calls
from spinn_utilities.overrides import overrides
from pacman.utilities.algorithm_utilities.partition_algorithm_utilities \
    import get_remaining_constraints


class SplitterFixedSliceSized(AbstractSplitterCommon):
    """ Splitter that operates off the max atoms per core constraint and
    fixed atoms per core constraints. Will ensure its feasible to partition at
    that atoms per core.
    """

    __slots__ = []

    NOT_SUITABLE_VERTEX_ERROR = (
        "The vertex {} cannot be supported by the SplitterFixedSliceSized as"
        " the vertex does not support the required API of "
        "LegacyPartitionerAPI. Please inherit from the class in "
        "pacman.model.partitioner_interfaces.legacy_partitioner_api and try "
        "again.")

    def __init__(self):
        AbstractSplitterCommon.__init__(self)

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            raise PacmanConfigurationException(
                self.NOT_SUITABLE_VERTEX_ERROR.format(app_vertex.label))

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):
        atoms_per_core = self._compute_atoms_per_core(resource_tracker)
        if atoms_per_core < 1.0:
            raise PacmanPartitionException(
                "Not enough resources available to create vertex")
        self.__split(atoms_per_core, machine_graph, resource_tracker)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return self._governed_app_vertex.vertex_slices

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return self._governed_app_vertex.vertex_slices

    @overrides(AbstractSplitterCommon.get_pre_vertices)
    def get_pre_vertices(self, edge, outgoing_edge_partition):
        return self._governed_app_vertex.machine_vertices

    @overrides(AbstractSplitterCommon.get_post_vertices)
    def get_post_vertices(self, edge, outgoing_edge_partition,
                          src_machine_vertex):
        return self._governed_app_vertex.machine_vertices

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return self._governed_app_vertex.machine_vertices

    def __split(self, atoms_per_core, machine_graph, resource_tracker):
        """ executes the splitting of the app vertex into machine vertices by
            atoms per core.

        :param int atoms_per_core: how many atoms to split per machine vertex
        :param MachineGraph machine_graph: machine graph
        :param ResourceTracker resource_tracker: resource tracker
        :return:
        """
        # Partition into vertices
        for first in range(
                0, self._governed_app_vertex.n_atoms, atoms_per_core):

            # Determine vertex size
            last = int(min(
                first + atoms_per_core, self._governed_app_vertex.n_atoms) - 1)
            if first < 0 or last < 0:
                raise PacmanPartitionException(
                    "Not enough resources available to create vertex")

            # Create and store new vertex, and increment elements first
            vertex_slice = Slice(first, last)
            resources = self._governed_app_vertex.get_resources_used_by_atoms(
                vertex_slice)

            m_vertex = self._governed_app_vertex.create_machine_vertex(
                vertex_slice, resources,
                "{}:{}:{}".format(
                    self._governed_app_vertex.label, first, last),
                get_remaining_constraints(self._governed_app_vertex))
            machine_graph.add_vertex(m_vertex)

            # update allocated resources
            resource_tracker.allocate_constrained_resources(
                resources, self._governed_app_vertex.constraints)

    def _compute_atoms_per_core(self, resource_tracker):
        """ Work out how many atoms per core are required for the given\
            vertex. Assumes that the first atom of the vertex is fully\
            representative.
        :param ResourceTracker resource_tracker: resource tracker
        :rtype: int
        :raise PacmanPartitionException:
            If something goes wrong with the partitioning
        """
        # Get the usage of the first atom, then assume that this will be the
        # usage of all the atoms.
        requirements = self._governed_app_vertex.get_resources_used_by_atoms(
            Slice(0, 1))

        # Locate the maximum resources available
        limits = resource_tracker.get_maximum_constrained_resources_available(
            requirements, self._governed_app_vertex.constraints)

        # Find the ratio of each of the resources - if 0 is required,
        # assume the ratio is the max available
        atoms_per_sdram = self._get_ratio(
            limits.sdram.get_total_sdram(resource_tracker.plan_n_time_steps),
            requirements.sdram.get_total_sdram(
                resource_tracker.plan_n_time_steps))
        atoms_per_dtcm = self._get_ratio(
            limits.dtcm.get_value(), requirements.dtcm.get_value())
        atoms_per_cpu = self._get_ratio(
            limits.cpu_cycles.get_value(), requirements.cpu_cycles.get_value())

        n_atoms = None
        for fa_constraint in utility_calls.locate_constraints_of_type(
                self._governed_app_vertex.constraints,
                FixedVertexAtomsConstraint):
            if n_atoms is not None and n_atoms != fa_constraint.size:
                raise PacmanPartitionException(
                    "Vertex has multiple contradictory fixed atom constraints"
                    " - cannot be both {} and {}".format(
                        n_atoms, fa_constraint.size))
            n_atoms = fa_constraint.size

        max_atom_values = [atoms_per_sdram, atoms_per_dtcm, atoms_per_cpu]
        for max_atom_constraint in utility_calls.locate_constraints_of_type(
                self._governed_app_vertex.constraints,
                MaxVertexAtomsConstraint):
            max_atom_values.append(float(max_atom_constraint.size))
        max_atoms = min(max_atom_values)

        if n_atoms is not None and max_atoms < n_atoms:
            raise PacmanPartitionException(
                "Max size of {} is incompatible with fixed size of {}".format(
                    max_atoms, n_atoms))
        return int(n_atoms) if n_atoms is not None else int(max_atoms)
