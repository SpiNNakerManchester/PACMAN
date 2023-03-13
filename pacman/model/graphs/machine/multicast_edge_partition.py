# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from pacman.model.graphs import AbstractSingleSourcePartition
from pacman.model.graphs.machine.machine_edge import MachineEdge


class MulticastEdgePartition(AbstractSingleSourcePartition):
    """
    A simple implementation of a machine edge partition that will
    communicate with SpiNNaker multicast packets. They have a common set
    of sources with the same semantics and so can share a single key.
    """

    __slots__ = ()

    def __init__(self, pre_vertex, identifier):
        """
        :param pre_vertex: the pre vertex of this partition.
        :param str identifier: The identifier of the partition
        """
        super().__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=MachineEdge)

    def __repr__(self):
        return (f"MulticastEdgePartition(pre_vertex={self.pre_vertex},"
                f" identifier={self.identifier})")
