# Copyright (c) 2021 The University of Manchester
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

from pacman.data import PacmanDataView
from pacman.model.resources.abstract_sdram import AbstractSDRAM


class ChipCounter(object):
    """
    A counter of how many chips are needed to hold machine vertices.
    This does not look at the fixed_locations of the vertices at all.
    The value produced will be a (hopefully) worst-case estimate and should
    not be used to decide failure in terms of space!
    """

    __slots__ = (
        # How many cores there are to be used on a chip
        "__n_cores_per_chip",

        # How much SDRAM there is to be used on a chip
        "__sdram_per_chip",

        # The number of cores free on the "current" chip
        "__cores_free",

        # The SDRAM free on the "current" chip
        "__sdram_free",

        # The number of chips used, including the current one
        "__n_chips")

    def __init__(self) -> None:
        version = PacmanDataView.get_machine_version()
        self.__n_cores_per_chip = (
                version.max_cores_per_chip - version.n_scamp_cores -
                PacmanDataView.get_all_monitor_cores())
        self.__sdram_per_chip = (
                version.max_sdram_per_chip -
                PacmanDataView.get_all_monitor_sdram().get_total_sdram(
                    PacmanDataView().get_plan_n_timestep()))
        self.__cores_free = 0
        self.__sdram_free = 0
        self.__n_chips = 0

    def add_core(self, resources: AbstractSDRAM, n_cores: int = 1) -> None:
        """
        Adds a core (or if needed a Chip) to the count

        :param resources:
        """
        sdram = resources.get_total_sdram(
            PacmanDataView.get_plan_n_timestep())
        if self.__cores_free < n_cores or self.__sdram_free < sdram:
            self.__n_chips += 1
            self.__cores_free = self.__n_cores_per_chip
            self.__sdram_free = self.__sdram_per_chip
        self.__cores_free -= n_cores
        self.__sdram_free -= sdram

    @property
    def n_chips(self) -> int:
        """
        The number of chips used, including the current one
        """
        return self.__n_chips
