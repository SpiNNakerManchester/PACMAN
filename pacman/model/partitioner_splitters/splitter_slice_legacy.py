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
import logging
from pacman.exceptions import PacmanConfigurationException
from pacman.model.constraints.partitioner_constraints import \
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint, \
    AbstractPartitionerConstraint, SameAtomsAsVertexConstraint
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterSlice)
from pacman.utilities import utility_calls
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter

logger = FormatAdapter(logging.getLogger(__name__))


class SplitterSliceLegacy(AbstractSplitterSlice):

    __slots__ = [
        "__splitter_name",
    ]

    NOT_API_WARNING = (
        "Your vertex is deprecated. Please add a Splitter or "
        "inherit from the class in "
        "pacman.model.partitioner_interfaces.legacy_partitioner_api")

    NOT_SUITABLE_VERTEX_ERROR = (
        "The vertex {} cannot be supported by the {} as"
        " the vertex does not support the required method {} of "
        "LegacyPartitionerAPI. Please inherit from the class in "
        "pacman.model.partitioner_interfaces.legacy_partitioner_api and try "
        "again.")

    SPLITTER_NAME = "SplitterLegacy"

    def __init__(self, splitter_name=None, adapt_to_resources=True):
        """

        :param splitter_name: Label of the Splitter
        :type splitter_name: str or None
        :param adapt_to_resources:
            Flag to say if the splitter may adapt to the resources available
            Only affects splitters that can adapt
        :type adapt_to_resources:
            bool or None
        """
        if splitter_name is None:
            splitter_name = self.SPLITTER_NAME
        AbstractSplitterSlice.__init__(self, splitter_name, adapt_to_resources)

    @overrides(AbstractSplitterSlice.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterSlice.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            for abstractmethod in LegacyPartitionerAPI.abstractmethods():
                check = getattr(app_vertex, abstractmethod, None)
                if not check:
                    raise PacmanConfigurationException(
                        self.NOT_SUITABLE_VERTEX_ERROR.format(
                            self._splitter_name, app_vertex.label,
                            abstractmethod))
                logger.warning(self.NOT_API_WARNING)

    @overrides(AbstractSplitterSlice.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources, label, remaining_constraints):
        return self._governed_app_vertex.create_machine_vertex(
            vertex_slice, resources, label, remaining_constraints)

    def get_resources_used_by_atoms(self, vertex_slice):
        return self._governed_app_vertex.get_resources_used_by_atoms(
            vertex_slice)

    @overrides(AbstractSplitterSlice.check_supported_constraints)
    def check_supported_constraints(self):
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=[self._governed_app_vertex],
            supported_constraints=[
                MaxVertexAtomsConstraint, FixedVertexAtomsConstraint,
                SameAtomsAsVertexConstraint],
            abstract_constraint_type=AbstractPartitionerConstraint)
