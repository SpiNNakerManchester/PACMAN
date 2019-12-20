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

from .machine_timestep_vertex import MachineTimestepVertex
from .machine_vertex import MachineVertex
from spinn_utilities.overrides import overrides


class SimpleMachineTimestepVertex(MachineTimestepVertex):
    """ A MachineVertex with timestep that stores its own resources.
    """

    def __init__(self, timestep, resources, label=None, constraints=None):
        super(SimpleMachineTimestepVertex, self).__init__(
            timestep_in_us=timestep, label=label, constraints=constraints)
        self._resources = resources

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self._resources
