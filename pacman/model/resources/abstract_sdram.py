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
from __future__ import annotations
from typing import Any, Optional, TextIO
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractSDRAM(object, metaclass=AbstractBase):
    """
    Represents an amount of SDRAM used on a chip in the machine.
    """
    __slots__ = ()

    @abstractmethod
    def get_total_sdram(self, n_timesteps: Optional[int]) -> int:
        """
        The total SDRAM.

        :param n_timesteps: number of timesteps to cost for
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def __add__(self, other: AbstractSDRAM) -> AbstractSDRAM:
        """
        Combines this SDRAM resource with the other one and creates a new one.

        :param other: another SDRAM resource
        :return: a New AbstractSDRAM
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def fixed(self) -> int:
        """
        The fixed SDRAM cost.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def per_timestep(self) -> float:
        """
        The extra SDRAM cost for each additional timestep.

        .. warning::
            May well be zero.
        """
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    def report(self, timesteps: Optional[int], indent: str = "",
               preamble: str = "", target: Optional[TextIO] = None) -> None:
        """
        Writes a description of this SDRAM to the target.

        :param timesteps: Number of timesteps to do total cost for
        :param indent: Text at the start of this and all children
        :param preamble:
            Additional text at the start but not in children
        :param target: Where to write the output.
            ``None`` is standard print
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def short_str(self) -> str:
        """
        A short string representation of this SDRAM.

        To be used within main str methods
        """
        raise NotImplementedError

    def __str__(self) -> str:
        return f"SDRAM:{self.short_str}"
