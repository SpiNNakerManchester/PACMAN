from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractHasGlobalMaxAtoms(object):
    """ Indicates an application vertex which has a global max atoms per core
    """

    __slots__ = []

    @staticmethod
    @abstractmethod
    def get_max_atoms_per_core():
        """ The global maximum atoms per core
        """
