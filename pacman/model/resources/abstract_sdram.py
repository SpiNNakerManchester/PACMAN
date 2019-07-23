from six import add_metaclass

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


@add_metaclass(AbstractBase)
class AbstractSDRAM(object):
    """ Represents an amount of SDRAM used on a chip in the\
        machine.
    """

    @abstractmethod
    def get_total_sdram(self, n_timesteps):
        """
        The total sdram.

        :param n_timesteps: number of timesteps to cost for
        :type n_timesteps: int
        :return:
        """

    @abstractmethod
    def __add__(self, other):
        """ Combines this SDRAM resource with the other one and creates a new one

        :param other: another  SDRAM resource
        :type other: AbstractSDRAM
        :return: a New AbstractSDRAM
        :rtype AbstractSDRAM
        """

    @abstractmethod
    def __sub__(self, other):
        """ Creates a new SDRAM which is this one less the other

        :param other: another  SDRAM resource
        :type other: AbstractSDRAM
        :return: a New AbstractSDRAM
        :rtype AbstractSDRAM
        """

    @abstractmethod
    def sub_from(self, other):
        """ Creates a new SDRAM which is the other less this one

        :param other: another  SDRAM resource
        :type other: AbstractSDRAM
        :return: a New AbstractSDRAM
        :rtype AbstractSDRAM
        """

    @abstractproperty
    def fixed(self):
        """ Returns the fixed sdram cost
        """

    @abstractproperty
    def per_timestep(self):
        """ Returns extra sdram cost for each additional timestep

        Warning may well be zero
        """
