# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from pacman.model.graphs import AbstractVirtual
from pacman.model.resources import ConstantSDRAM
from .machine_vertex import MachineVertex


class MachineFPGAVertex(MachineVertex, AbstractVirtual):
    """ A virtual vertex on an FPGA link.
    """

    __slots__ = [
        "_fpga_id",
        "_fpga_link_id",
        "_board_address",
        "_linked_chip_coordinates",
        "_outgoing_keys_and_masks",
        "_incoming",
        "_outgoing"]

    def __init__(
            self, fpga_id, fpga_link_id, board_address=None,
            linked_chip_coordinates=None, label=None,
            app_vertex=None, vertex_slice=None, outgoing_keys_and_masks=None,
            incoming=True, outgoing=False):
        super().__init__(
            label=label, app_vertex=app_vertex, vertex_slice=vertex_slice)

        self._fpga_id = fpga_id
        self._fpga_link_id = fpga_link_id
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
    def fpga_id(self):
        return self._fpga_id

    @property
    def fpga_link_id(self):
        return self._fpga_link_id

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

    @overrides(AbstractVirtual.get_link_data)
    def get_link_data(self, machine):
        return machine.get_fpga_link_with_id(
            self._fpga_id, self._fpga_link_id, self._board_address,
            self._linked_chip_coordinates)
