
"""
test vertex used in many unit tests
"""

# pacman imports
from pacman.model.resources.cpu_cycles_resource import \
    CPUCyclesResource

from pacman.model.graphs.application.abstract_application_vertex import \
    AbstractApplicationVertex
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource


class TestVertex(AbstractApplicationVertex):
    """
    test vertex
    """
    _model_based_max_atoms_per_core = None

    def __init__(self, n_atoms, label, max_atoms_per_core=256):
        AbstractApplicationVertex.__init__(
            self, n_atoms=n_atoms, max_atoms_per_core=max_atoms_per_core,
            label=label)
        self._model_based_max_atoms_per_core = max_atoms_per_core

    def get_resources_used_by_atoms(self, vertex_slice, vertex_in_edges):
        """
        standard method call to get the sdram, cpu and dtcm usage of a
        collection of atoms
        :param vertex_slice: the collection of atoms
        :param vertex_in_edges: the edges coming into this vertex
        :return:
        """
        return ResourceContainer(
            sdram=SDRAMResource(
                self.get_sdram_usage_for_atoms(vertex_slice, None)),
            cpu=CPUCyclesResource(
                self.get_cpu_usage_for_atoms(vertex_slice, None)),
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms(vertex_slice,
                                                            None)))

    def model_name(self):
        """
        the model name of this test vertex
        :return:
        """
        return "test model"

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice: the atoms being considered
        :param graph: the graph
        :return: the amount of cpu (in cycles this model will use)
        """
        return 1 * vertex_slice.n_atoms

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice: the atoms being considered
        :param graph: the graph
        :return: the amount of dtcm (in bytes this model will use)
        """
        return 1 * vertex_slice.n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        :param vertex_slice: the atoms being considered
        :param graph: the graph
        :return: the amount of sdram (in bytes this model will use)
        """
        return 1 * vertex_slice.n_atoms
