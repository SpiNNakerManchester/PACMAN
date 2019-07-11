from six import add_metaclass
from spinn_utilities.abstract_base import abstractmethod, AbstractBase


@add_metaclass(AbstractBase)
class AbstractSDRAMPartition(object):
    def __init__(self):
        pass

    @abstractmethod
    def total_sdram_requirements(self):
        """

        :return: 
        """