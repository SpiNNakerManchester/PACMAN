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

from __future__ import division
from six import print_
from spinn_utilities.helpful_functions import lcm
from spinn_utilities.overrides import overrides
from .abstract_sdram import AbstractSDRAM
from pacman.exceptions import PacmanConfigurationException


class VariableSDRAM(AbstractSDRAM):
    """ Represents an amount of SDRAM used on a chip in the machine.

    This is where the usage increase as the run time increases

    This version is based on a cost per timestep and will check and raise\
    exceptions if none timestep multuples are used.
    """

    __slots__ = [
        # The amount of SDRAM in bytes used no matter what
        "_fixed_sdram",
        # The amount of extra SDRAm used for each timestep
        "_per_timestep_sdram",
        # Timestep in us
        "_timestep_in_us"
    ]

    def __init__(
            self, fixed_sdram, per_timestep_sdram, timestep_in_us):
        """

        :param int fixed_sdram:
            The amount of SDRAM (in bytes) that represents static overhead
        :param int per_timestep_sdram:
            The amount of SDRAM (in bytes) required per timestep.
            Often represents the space to record a timestep.
        :param int timestep_in_us: the timestep used by the cost provider
        """
        self._fixed_sdram = fixed_sdram
        self._per_timestep_sdram = per_timestep_sdram
        self._timestep_in_us = timestep_in_us

    @overrides(AbstractSDRAM.get_sdram_for_simtime)
    def get_sdram_for_simtime(self, time_in_us):
        if time_in_us is None:
            if self._per_timestep_sdram != 0:
                raise PacmanConfigurationException(
                    "Unable to run forever with a variable SDRAM cost")
        n_timesteps = time_in_us // self._timestep_in_us
        check = n_timesteps * self._timestep_in_us
        if check != time_in_us:
            raise ValueError(
                "The requested time {} is not a multiple of the timestep {}"
                "".format(time_in_us, self._timestep_in_us))
        return self._fixed_sdram + (self._per_timestep_sdram * n_timesteps)

    @property
    @overrides(AbstractSDRAM.fixed)
    def fixed(self):
        return self._fixed_sdram

    @property
    @overrides(AbstractSDRAM.per_simtime_us)
    def per_simtime_us(self):
        return self._per_timestep_sdram / self._timestep_in_us

    def __new_costs(self, other):
        """
        Calculates the new costs when combining the two sdram Costs

        The timestep is the lowest common multiple of the two timesteps.

        The individual per timesteps costs have to be increase by the same\
        multiple as their "timestep" increases.

        If other does not have a timestep its per_simetime cost\
        (which could be zero) is converted to a per timestep one.

        :param other: Another sdram cost to combine with
        :return: The new timestep and the two per_timesteps to combine
        """
        if isinstance(other, VariableSDRAM):
            if self._timestep_in_us == other._timestep_in_us:
                return (self._timestep_in_us, self._per_timestep_sdram,
                        other._per_timestep_sdram)
            new_timestep = lcm(self._timestep_in_us, other._timestep_in_us)
            return (
                new_timestep,
                self._per_timestep_sdram * new_timestep / self._timestep_in_us,
                other._per_timestep_sdram * new_timestep /
                other._timestep_in_us)
        else:
            return (
                self._timestep_in_us, self._per_timestep_sdram,
                other.per_simtime_us * self._timestep_in_us)

    def __add__(self, other):
        timestep, per_self, per_other = self.__new_costs(other)
        return VariableSDRAM(
            self.fixed + other.fixed,
            per_self + per_other,
            timestep)

    def __sub__(self, other):
        timestep, per_self, per_other = self.__new_costs(other)
        return VariableSDRAM(
            self.fixed - other.fixed,
            per_self - per_other,
            timestep)

    @overrides(AbstractSDRAM.sub_from)
    def sub_from(self, other):
        timestep, per_self, per_other = self.__new_costs(other)
        return VariableSDRAM(
            other.fixed - self.fixed,
            per_other - per_self,
            timestep)

    @overrides(AbstractSDRAM.report)
    def report(self, time_in_us, indent="", preamble="", target=None):
        print_(indent, preamble,
               "Fixed {} bytes Per_timestep {} bytes for a total of {}".format(
                   self._fixed_sdram, self._per_timestep_sdram,
                   self.get_sdram_for_simtime(time_in_us)), file=target)
