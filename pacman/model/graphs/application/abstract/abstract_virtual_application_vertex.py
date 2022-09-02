# Copyright (c) 2022 The University of Manchester
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
from spinn_utilities.abstract_base import abstractmethod


class AbstractVirtualApplicationVertex(ApplicationVertex):
    """ An application vertex which is virtual
    """

    __slots__ = []

    @abstractmethod
    def get_outgoing_link_data(self, machine):
        """ Get the link data for outgoing connections from the machine

        :param Machine machine: The machine to get the link data from
        :rtype: AbstractLinkData
        """
