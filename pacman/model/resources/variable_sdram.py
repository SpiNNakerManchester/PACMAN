from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM
from pacman.exceptions import PacmanConfigurationException


class VariableSDRAM(AbstractSDRAM):
    """ Represents an amount of SDRAM used on a chip in the machine.

    This is where the usage increase as the run time increases
    """

    __slots__ = [
        # The amount of SDRAM in bytes used no matter what
        "_fixed_sdram"
        # The amount of extra SDRAm used for each timestep
        "_per_timestep_sdram"
    ]

    def __init__(
            self, fixed_sdram, per_timestep_sdram):
        """
        :param sdram: The amount of SDRAM in bytes
        :type sdram: int
        :raise None: No known exceptions are raised
        """
        self._fixed_sdram = fixed_sdram
        self._per_timestep_sdram = per_timestep_sdram

    def get_total_sdram(self, n_timesteps):
        if n_timesteps:
            return self._fixed_sdram + \
                   (self._per_timestep_sdram * n_timesteps)
        else:
            if n_timesteps == 0:
                # Should never happen but is technically valid.
                return self._fixed_sdram
            if self._per_timestep_sdram == 0:
                return self._fixed_sdram
            else:
                raise PacmanConfigurationException(
                    "Unable to run forever with a variable SDRAM cost")

    @property
    def fixed(self):
        return self._fixed_sdram

    @property
    def per_timestep(self):
        return self._per_timestep_sdram

    def __add__(self, other):
        if isinstance(other, ConstantSDRAM):
            return VariableSDRAM(
                self._fixed_sdram + other.fixed,
                self._per_timestep_sdram)
        else:
            return VariableSDRAM(
                self._fixed_sdram + other._fixed_sdram,
                self._per_timestep_sdram + other._per_timestep_sdram)

    def __sub__(self, other):
        if isinstance(other, ConstantSDRAM):
            return VariableSDRAM(
                self._fixed_sdram - other.fixed,
                self._per_timestep_sdram)
        else:
            return VariableSDRAM(
                self._fixed_sdram - other._fixed_sdram,
                self._per_timestep_sdram - other._per_timestep_sdram)

    def sub_from(self, other):
        if isinstance(other, ConstantSDRAM):
            return VariableSDRAM(
                other.fixed - self._fixed_sdram,
                0 - self._per_timestep_sdram)
        else:
            return VariableSDRAM(
                other._fixed_sdram - self._fixed_sdram,
                other._per_timestep_sdram - self._per_timestep_sdram)
