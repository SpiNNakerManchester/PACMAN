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

from spinn_utilities.overrides import overrides
from .abstract_sdram import AbstractSDRAM


class ConstantSDRAM(AbstractSDRAM):
    """ Represents an amount of SDRAM used  on a chip in the machine.

    This is used when the amount of SDRAM needed is not effected by runtime
    """

    __slots__ = [
        # The amount of SDRAM in bytes
        "_sdram"
    ]

    def __init__(self, sdram):
        """
        :param sdram: The amount of SDRAM in bytes
        :type sdram: int or ~numpy.int64
        """
        self._sdram = int(sdram)

    @overrides(AbstractSDRAM.get_total_sdram)
    def get_total_sdram(self, n_timesteps):  # @UnusedVariable
        return self._sdram

    @property
    @overrides(AbstractSDRAM.fixed)
    def fixed(self):
        return self._sdram

    @property
    @overrides(AbstractSDRAM.per_timestep)
    def per_timestep(self):
        return 0

    def __add__(self, other):
        if isinstance(other, ConstantSDRAM):
            return ConstantSDRAM(
                self._sdram + other.fixed)
        else:
            # The other is more complex so delegate to it
            return other.__add__(self)

    def __sub__(self, other):
        if isinstance(other, ConstantSDRAM):
            return ConstantSDRAM(
                self._sdram - other.fixed)
        else:
            # The other is more complex so delegate to it
            return other.sub_from(self)

    @overrides(AbstractSDRAM.sub_from)
    def sub_from(self, other):
        if isinstance(other, ConstantSDRAM):
            return ConstantSDRAM(
                other.fixed - self._sdram)
        else:
            # The other is more complex so delegate to it
            return other - self

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps, indent="", preamble="", target=None):
        print(indent, preamble, "Constant {} bytes".format(self._sdram),
              file=target)
