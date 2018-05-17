from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM


class VariableSDRAM(AbstractSDRAM):
    """ Represents an amount of SDRAM used on a chip in the machine.

    This is where the usage increase as the run time increases
    """

    __slots__ = [
        # The amount of SDRAM in bytes used no matter what
        "_fixed_sdram"
        # The amount of extra SDRAm used for each timestep
        "_per_timestep_sdram"
        # The assumed runtime. Used when no specific runtime is supplied
        "_assumed_timesteps"
    ]

    def __init__(self, fixed_sdram, per_timestep_sdram, assumed_timesteps=None):
        """
        :param sdram: The amount of SDRAM in bytes
        :type sdram: int
        :raise None: No known exceptions are raised
        """
        self._fixed_sdram = fixed_sdram
        self._per_timestep_sdram = per_timestep_sdram
        self._assumed_timesteps = assumed_timesteps

    def get_total_sdram(self):
        return self._fixed_sdram + \
               (self._per_timestep_sdram * self._assumed_timesteps)

    def extend(self, other):
        if isinstance(other, ConstantSDRAM):
            return VariableSDRAM(
                self._fixed_sdram + other.get_total_sdram(),
                self._per_timestep_sdram, self._assumed_timesteps)
        else:
            return VariableSDRAM(
                self._fixed_sdram + other._fixed_sdram,
                self._per_timestep_sdram + other._per_timestep_sdram,
                max(self._assumed_timesteps, other._assumed_timesteps))

    def set_assumed_timesteps(self, assumed_timesteps):
        self._assumed_timesteps = assumed_timesteps
