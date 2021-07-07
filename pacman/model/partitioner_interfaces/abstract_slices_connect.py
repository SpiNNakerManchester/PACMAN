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
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.application import ApplicationEdge


@require_subclass(ApplicationEdge)
class AbstractSlicesConnect(object, metaclass=AbstractBase):
    """ An object that can check if a pre-slice and a post-slice could\
        connect.

    Typically used to determine if a Machine Edge should be created by
    checking that at least one of the indexes in the source slice could
    connect to at least one of the indexes in the destination slice.
    """

    __slots__ = ()

    @abstractmethod
    def could_connect(self, src_machine_vertex, dest_machine_vertex):
        """ Determine if there is a chance that one of the indexes in the\
            pre-slice could connect to at least one of the indexes in the\
            post-slice.

        .. note::
            This method should never return a false negative,
            but may return a false positives

        :param ~pacman.model.graphs.machine.MachineVertex src_machine_vertexx:
        :param ~pacman.model.graphs.machine.MachineVertex dest_machine_vertex:
        :return: True if a connection could be possible
        :rtype: bool
        """
