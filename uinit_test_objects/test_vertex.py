
"""
test vertex used in many unit tests
"""

# pacman imports
from pacman.model.abstract_classes.abstract_partitionable_vertex import \
    AbstractPartitionableVertex


class TestVertex(AbstractPartitionableVertex):
    """
    test vertex
    """

    def __init__(self, n_atoms, label, max_atoms_per_core=123):
        AbstractPartitionableVertex.__init__(
            self, n_atoms=n_atoms, max_atoms_per_core=max_atoms_per_core,
            label=label)

    def get_resources_used_by_atoms(self, vertex_slice, vertex_in_edges):
        """
        standard method call to get the sdram, cpu and dtcm usage of a
        collection of atoms
        :param vertex_slice: the collection of atoms
        :param vertex_in_edges: the edges coming into this partitionable vertex
        :return:
        """
        return None

    def model_name(self):
        """
        the model name of this test vertex
        :return:
        """
        return "test model"

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice: the atoms being considered
        :param graph: the partitionable graph
        :return: the amount of cpu (in cycles this model will use)
        """
        return 1 * vertex_slice.n_atoms

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice: the atoms being considered
        :param graph: the partitionable graph
        :return: the amount of dtcm (in bytes this model will use)
        """
        return 1 * vertex_slice.n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        :param vertex_slice: the atoms being considered
        :param graph: the partitionable graph
        :return: the amount of sdram (in bytes this model will use)
        """
        return 1 * vertex_slice.n_atoms
