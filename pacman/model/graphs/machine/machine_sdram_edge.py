# Copyright (c) 2019-2020 The University of Manchester
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
from pacman.exceptions import SDRAMEdgeSizeException
from pacman.model.graphs.abstract_supports_sdram_edges import \
    AbstractSupportsSDRAMEdges
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import MachineEdge


class SDRAMMachineEdge(MachineEdge):

    __slots__ = [
        "_sdram_size",
        "_sdram_base_address"

    ]

    NO_SUPPORT_MESSAGE = (
        "The {}vertex {} does not implement the AbstractSupportsSDRAMEdges"
        " API that can be found at \' "
        "pacman.model.graphs.abstract_supports_sdram_edges \'. Please fix and"
        " try again so that sdram edge {} can know its required size.")

    DISAGREEMENT_MESSAGE = (
        "The pre vertex sdram size {} does not agree with the post vertex "
        "sdram size {}. The SDRAM machine edge does not yet know how to "
        "handle this case. Please fix and try again.")

    def __init__(self, pre_vertex, post_vertex, label):
        MachineEdge.__init__(
            self, pre_vertex, post_vertex, traffic_type=EdgeTrafficType.SDRAM,
            label=label, traffic_weight=1)

        (pre_vertex_sdram, post_vertex_sdram) = self.__get_vertex_sdrams()
        self._sdram_size = self.__check_vertex_sdram_sizes(
            pre_vertex_sdram, post_vertex_sdram)
        self._sdram_base_address = None

    def __check_vertex_sdram_sizes(self, pre_vertex_sdram, post_vertex_sdram):
        """ checks that the sdram request is consistent between the vertices.

        :param int pre_vertex_sdram: pre vertex sdram requirement
        :param int post_vertex_sdram: post vertex sdram requirement
        :return: the sdram requirement.
        :rtype: int
        :raises SDRAMEdgeSizeException: if the values disagree
        """
        if pre_vertex_sdram == post_vertex_sdram:
            return pre_vertex_sdram
        else:
            raise SDRAMEdgeSizeException(self.DISAGREEMENT_MESSAGE.format(
                pre_vertex_sdram, post_vertex_sdram))

    def __get_vertex_sdrams(self):
        """ query the vertices to find the sdram requirements.

        :return: tuple of pre and post sdram costs.
        :rtype: tuple(int, int)
        :rtype SDRAMEdgeSizeException: if either vertex does not support \
            SDRAM edges
        """

        if isinstance(self.pre_vertex, AbstractSupportsSDRAMEdges):
            pre_vertex_sdram_size = self.pre_vertex.sdram_requirement(self)
        else:
            raise SDRAMEdgeSizeException(
                self.NO_SUPPORT_MESSAGE.format("pre", self.pre_vertex, self))

        if isinstance(self.post_vertex, AbstractSupportsSDRAMEdges):
            post_vertex_sdram_size = self.post_vertex.sdram_requirement(self)
        else:
            raise SDRAMEdgeSizeException(self.NO_SUPPORT_MESSAGE.format(
                "post", self.post_vertex, self))
        return pre_vertex_sdram_size, post_vertex_sdram_size

    @property
    def sdram_size(self):
        return self._sdram_size

    @property
    def sdram_base_address(self):
        return self._sdram_base_address

    @sdram_base_address.setter
    def sdram_base_address(self, new_value):
        self._sdram_base_address = new_value

    def __repr__(self):
        return self._label

    def __str__(self):
        return self.__repr__()
