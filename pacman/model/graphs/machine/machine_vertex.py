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

from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from spinn_utilities.overrides import overrides
from pacman.model.graphs import AbstractVertex


@add_metaclass(AbstractBase)
class MachineVertex(AbstractVertex):
    """ A machine graph vertex.
    """

    __slots__ = ["_timestep_in_us"]

    def __init__(self, timestep_in_us, label=None, constraints=None):
        """
        :param timestep_in_us: The timestep of this vertex in us
        :type timestep_in_us: int
        :param label: The optional name of the vertex
        :type label: str
        :param constraints: The optional initial constraints of the vertex
        :type constraints: \
            iterable(~pacman.model.constraints.AbstractConstraint)
        :raise pacman.exceptions.PacmanInvalidParameterException:
            If one of the constraints is not valid
        """
        if label is None:
            label = str(type(self))
        super(MachineVertex, self).__init__(label, constraints)
        self._timestep_in_us = timestep_in_us
        self._added_to_graph = False

    def __str__(self):
        _l = self.label
        return self.__repr__() if _l is None else _l

    def __repr__(self):
        if self.constraints:
            return "MachineVertex(label={}, constraints={})".format(
                self.label, self.constraints)
        return "MachineVertex(label={})".format(self.label)

    @abstractproperty
    def resources_required(self):
        """ The resources required by the vertex

        :rtype: ~pacman.model.resources.ResourceContainer
        """
    @property
    @overrides(AbstractVertex.timestep_in_us)
    def timestep_in_us(self):
        return self._timestep_in_us
