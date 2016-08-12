from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractHasGlobalMaxAtoms(object):
    """ A interface to support models which have a global max atoms per core
    per application vertex

    """

    __slots__ = []

    @abstractmethod
    def get_max_atoms_per_core(self):
        """
        returns the global max atoms per core.
        :return:
        """
        pass