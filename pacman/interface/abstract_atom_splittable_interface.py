# general imports
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractAtomSplittableInterface(object):
    """
    interface for partitioners which need to split a atom down
    """

    def __init__(self):
        pass

    @abstractmethod
    def is_atom_splittable(self):
        """
        helper method for isinstance
        :return:
        """

    @abstractmethod
    def split_atom_due_to_cpu(self, atom_id, max_cpu):
        """
        splits a atom based off its cpu usage
        :param atom_id: the atom to split
        :param max_cpu: the cpu point which it needs to split to.
        :return: resource used which meets the max
        """

    @abstractmethod
    def split_atom_due_to_dtcm(self, atom_id, max_dtcm):
        """
        splits a atom based off its dtcm usage
        :param atom_id: the atom to split
        :param max_dtcm: the dtcm point which it needs to split to.
        :return: resource used which meets the max
        """

    @abstractmethod
    def split_atom_due_to_sdram(self, atom_id, max_sdram):
        """
        splits a atom based off its sdram usage
        :param atom_id: the atom to split
        :param max_sdram: the sdram point which it needs to split to.
        :return: resource used which meets the max
        """
