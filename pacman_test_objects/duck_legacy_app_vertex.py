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
from pacman.model.graphs.application import ApplicationVertex


class DuckLegacyApplicationVertex(ApplicationVertex):
    """
    A mock vertex that is a LegacyPartitionerAPI by ducktyping the methods
    """
    def __init__(self, label="test"):
        super().__init__(label=label)

    def n_atoms(self):
        pass

    def get_sdram_used_by_atoms(self, vertex_slice):
        pass

    def create_machine_vertex(self, vertex_slice, sdram, label=None):
        pass
