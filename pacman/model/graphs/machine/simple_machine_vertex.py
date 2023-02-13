# Copyright (c) 2016-2023 The University of Manchester
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

from .machine_vertex import MachineVertex
from spinn_utilities.overrides import overrides


class SimpleMachineVertex(MachineVertex):
    """ A MachineVertex that stores its own resources.

    This class is mainly intended for json and testing as it support the
        mininal API. If a more complex Vertex is required consider the
        MockMachineVertex.
    """
    __slots__ = ["_iptags", "_reverse_iptags", "_sdram"]

    def __init__(self, sdram, label=None,
                 app_vertex=None, vertex_slice=None, iptags=None,
                 reverse_iptags=None):
        super().__init__(
            label=label, app_vertex=app_vertex, vertex_slice=vertex_slice)
        self._sdram = sdram
        self._iptags = []
        if iptags:
            self._iptags = iptags
        self._reverse_iptags = []
        if reverse_iptags:
            self._reverse_iptags = reverse_iptags

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self):
        return self._sdram

    @property
    @overrides(MachineVertex.iptags)
    def iptags(self):
        return self._iptags

    @property
    @overrides(MachineVertex.reverse_iptags)
    def reverse_iptags(self):
        return self._reverse_iptags
