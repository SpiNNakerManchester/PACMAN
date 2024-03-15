from pacman.operations.partition_algorithms.splitter_partitioner import splitter_partitioner
from pacman.operations.partition_algorithms.random_partitioner import RandomPartitioner
from pacman.operations.partition_algorithms.ga_partitioner import GAPartitioner
from pacman.operations.partition_algorithms.ga.entities.ga_algorithm_configuration import GAAlgorithmConfiguration
from pacman.operations.partition_algorithms.ga.init_population_generators.fixed_slice_pop_generator import GaFixedSlicePopulationGenerator

class PartitionerSelector(object):
    def __init__(self, partitioner_name, resource_constraints_configuration) -> None:
        self._partitioner_name = partitioner_name
        self._resource_constraints_configuration = resource_constraints_configuration
        if partitioner_name == "splitter":            
            self._partitioner = None
            self._n_chips = splitter_partitioner()
        if partitioner_name == "random":
            self._partitioner = RandomPartitioner(100, resource_constraints_configuration).partitioning()
            self._n_chips = self._partitioner.get_n_chips()
        if partitioner_name == "ga":
            ga_configuration: GAAlgorithmConfiguration = \
                GAAlgorithmConfiguration(init_solutions_common_representation_generator=)
            self._partitioner = GAPartitioner(resource_contraints_configuration=resource_constraints_configuration,\
                max_slice_length=10 ** 9,\
                solution_file_path=None,\
                serialize_solution_to_file=True,\
                ga_algorithm_configuration=ga_configuration).partitioning()

    def get_partitioner_instance(self):
        return self._partitioner
    
    def get_n_chips(self):
        return self._n_chips