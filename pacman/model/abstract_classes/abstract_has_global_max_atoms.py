from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractHasGlobalMaxAtoms(object):
    """ Indicates an application vertex which has a global max atoms per core
    """

    __slots__ = []

    @abstractmethod
    def get_max_atoms_per_core(self):
        """ The global maximum atoms per core
        """
