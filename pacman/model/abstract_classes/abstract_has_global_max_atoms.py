from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractHasGlobalMaxAtoms(object):

    @abstractmethod
    def get_max_atoms_per_core(self):
        """
        returns the global max atoms per core.
        :return:
        """
        pass