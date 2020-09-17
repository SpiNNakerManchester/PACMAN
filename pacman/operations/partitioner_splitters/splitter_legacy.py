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

from pacman.exceptions import PacmanConfigurationException
from pacman.model.partitioner_interfaces.abstract_splitter_common import (
    AbstractSplitterCommon)
from pacman.model.partitioner_interfaces.legacy_partitioner_api import (
    LegacyPartitionerAPI)
from pacman.model.partitioner_interfaces.abstract_splitter_slice import (
    AbstractSplitterSlice)
from spinn_utilities.overrides import overrides


class SplitterLegacy(AbstractSplitterSlice):
    """ contains the checks for legacy api and the printing of error messages

    """

    __slots__ = [
        "__splitter_name"
    ]

    NOT_SUITABLE_VERTEX_ERROR = (
        "The vertex {} cannot be supported by the {} as"
        " the vertex does not support the required API of "
        "LegacyPartitionerAPI. Please inherit from the class in "
        "pacman.model.partitioner_interfaces.legacy_partitioner_api and try "
        "again.")

    SPLITTER_NAME = "SplitterLegacy"

    STR_MESSAGE = "{}} governing app vertex {}"

    def __init__(self, splitter_name=None):
        AbstractSplitterCommon.__init__(self)
        if splitter_name is None:
            self.__splitter_name = self.SPLITTER_NAME
        else:
            self.__splitter_name = splitter_name

    def __str__(self):
        return self.STR_MESSAGE.format(
            self.__splitter_name, self._governed_app_vertex)

    def __repr__(self):
        return self.__str__()

    @overrides(AbstractSplitterSlice.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            raise PacmanConfigurationException(
                self.NOT_SUITABLE_VERTEX_ERROR.format(
                    self.__splitter_name, app_vertex.label))
