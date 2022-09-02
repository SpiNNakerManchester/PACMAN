# Copyright (c) 2017-2022 The University of Manchester
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

from spinn_utilities.overrides import overrides
from pacman.model.resources import ConstantSDRAM
from .machine_vertex import MachineVertex
from pacman.model.graphs import AbstractVirtual


class MachineSpiNNakerLinkVertex(MachineVertex, AbstractVirtual):
    """ A virtual vertex on a SpiNNaker Link.
    """

    __slots__ = [
        "_spinnaker_link_id",
        "_board_address",
        "_linked_chip_coordinates",
        "_virtual_chip_x",
        "_virtual_chip_y",
        "_outgoing_keys_and_masks",
        "_incoming",
        "_outgoing"]

    def __init__(
            self, spinnaker_link_id, board_address=None,
            linked_chip_coordinates=None, label=None, constraints=None,
            app_vertex=None, vertex_slice=None, outgoing_keys_and_masks=None,
            incoming=True, outgoing=False):
        super().__init__(
            label=label, constraints=constraints, app_vertex=app_vertex,
            vertex_slice=vertex_slice)
        self._spinnaker_link_id = spinnaker_link_id
        self._board_address = board_address
        self._linked_chip_coordinates = linked_chip_coordinates
        self._outgoing_keys_and_masks = outgoing_keys_and_masks
        self._incoming = incoming
        self._outgoing = outgoing

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self):
        return ConstantSDRAM(0)

    @property
    def spinnaker_link_id(self):
        return self._spinnaker_link_id

    @property
    @overrides(AbstractVirtual.board_address)
    def board_address(self):
        return self._board_address

    @property
    @overrides(AbstractVirtual.linked_chip_coordinates)
    def linked_chip_coordinates(self):
        return self._linked_chip_coordinates

    @overrides(AbstractVirtual.outgoing_keys_and_masks)
    def outgoing_keys_and_masks(self):
        return self._outgoing_keys_and_masks

    @property
    @overrides(AbstractVirtual.incoming)
    def incoming(self):
        return self._incoming

    @property
    @overrides(AbstractVirtual.outgoing)
    def outgoing(self):
        return self._outgoing
