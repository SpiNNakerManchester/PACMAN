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

from typing import Any, Optional, TextIO
from spinn_utilities.overrides import overrides
from .abstract_sdram import AbstractSDRAM


class ConstantSDRAM(AbstractSDRAM):
    """
    Represents an amount of SDRAM used  on a chip in the machine.

    This is used when the amount of SDRAM needed is not effected by runtime
    """

    __slots__ = (
        # The amount of SDRAM in bytes
        "_sdram", )

    def __init__(self, sdram: int):
        """
        :param sdram: The amount of SDRAM in bytes
        """
        self._sdram = int(sdram)

    @overrides(AbstractSDRAM.get_total_sdram)
    def get_total_sdram(self, n_timesteps: Optional[int]) -> int:
        return self._sdram

    @property
    @overrides(AbstractSDRAM.fixed)
    def fixed(self) -> int:
        return self._sdram

    @property
    @overrides(AbstractSDRAM.per_timestep)
    def per_timestep(self) -> float:
        return 0

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ConstantSDRAM):
            return False
        return other.fixed == self.fixed

    def __add__(self, other: AbstractSDRAM) -> AbstractSDRAM:
        if isinstance(other, ConstantSDRAM):
            return ConstantSDRAM(
                self._sdram + other.fixed)
        else:
            # The other is more complex so delegate to it
            return other.__add__(self)

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps: Optional[int], indent: str = "",
               preamble: str = "", target: Optional[TextIO] = None) -> None:
        print(indent, preamble, f"Constant {self._sdram} bytes", file=target)

    @property
    @overrides(AbstractSDRAM.short_str)
    def short_str(self) -> str:
        return f"fixed: {self._sdram}"
