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
An Machine vertex with a not None timestep
"""

from pacman.model.graphs.machine.machine_vertex import MachineVertex


class MachineTimestepVertex(MachineVertex):

    __slots__ = ["_timestep_in_us"]

    def __init__(self, timestep_in_us, label=None, constraints=None,
                 app_vertex=None, vertex_slice=None):
        """
        :param timestep_in_us: The timestep of this vertex in us
        :type timestep_in_us: int
        :param label: The optional name of the vertex
        :type label: str
        :param constraints: The optional initial constraints of the vertex
        :type constraints: \
            iterable(~pacman.model.constraints.AbstractConstraint)
        :param app_vertex:
            The application vertex that caused this machine vertex to be
            created. If None, there is no such application vertex.
        :type app_vertex: ApplicationVertex or None
        :param vertex_slice:
            The slice of the application vertex that this machine vertex
            implements.
        :type vertex_slice: Slice or None
        :raise pacman.exceptions.PacmanInvalidParameterException:
            If one of the constraints is not valid
        :raises PacmanValueError: If the slice of the machine_vertex is too big
        :raise AttributeError:
            If a not None app_vertex is not an ApplicationVertex
        """
        super(MachineTimestepVertex, self).__init__(
            label, constraints, app_vertex, vertex_slice)
        assert 0 < timestep_in_us
        self._timestep_in_us = timestep_in_us

    @property
    def timestep_in_us(self):
        return self._timestep_in_us

    def simtime_in_us_to_timesteps(self, simtime_in_us):
        """
        Helper function to convert simtime in us to whole timestep

        This function verfies that the simtime is a multile of the timestep.

        :param simtime_in_us: a simulation time in us
        :type simtime_in_us: int
        :return: the exact number of timeteps covered by this simtime
        :rtype: int
        :raises ValueError: If the simtime is not a mutlple of the timestep
        """
        n_timesteps = simtime_in_us // self.timestep_in_us
        check = n_timesteps * self.timestep_in_us
        if check != simtime_in_us:
            raise ValueError(
                "The requested time {} is not a multiple of the timestep {}"
                "".format(simtime_in_us, self.timestep_in_us))
        return n_timesteps
