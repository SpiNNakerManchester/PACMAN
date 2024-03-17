from pacman.operations.partition_algorithms.splitter_partitioner import splitter_partitioner
from pacman.operations.partition_algorithms.random_partitioner import RandomPartitioner
from pacman.operations.partition_algorithms.ga_partitioner import GAPartitioner
from pacman.operations.partition_algorithms.ga.entities.ga_algorithm_configuration import GAAlgorithmConfiguration
from pacman.operations.partition_algorithms.ga.entities.resource_configuration import ResourceConfiguration
from pacman.operations.partition_algorithms.ga.init_population_generators.fixed_slice_pop_generator import GaFixedSlicePopulationPTypeGeneratorOneSliceOneCore
from pacman.operations.partition_algorithms.ga.crossover_operators.slice_crossover import GaSliceCrossoverKPoints
from pacman.operations.partition_algorithms.ga.crossover_individuals_selectors.random_sel_crossover_solution import GaussianWeightInvidualSelection
from pacman.operations.partition_algorithms.ga.variation_operators.slice_variation import GaSliceVariationuUniformGaussian
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_fixing_operators.slice_representation_fixing import GaSliceRepresenationSolutionSimpleFillingFixing
from pacman.operations.partition_algorithms.ga.cost_caculators.resource_utilization_cost import ResourceUtilizationCost
from pacman.operations.partition_algorithms.ga.selection_operators.elite_possibility_selection import GaEliteProbabilisticSelection
from pacman.operations.partition_algorithms.ga.crossover_operators.slice_crossover import GaSliceSliceInfoCombinationUniformCrossover
from pacman.data import PacmanDataView

class PartitionerSelector(object):
    def __init__(self, partitioner_name, resource_constraint_configuration: ResourceConfiguration) -> None:
        self._partitioner_name = partitioner_name
        self._resource_constraint_configuration: ResourceConfiguration = resource_constraint_configuration
        if partitioner_name == "splitter":            
            self._partitioner = None
            self._n_chips = splitter_partitioner()
        if partitioner_name == "random":
            self._partitioner = RandomPartitioner(100, resource_constraint_configuration).partitioning()
            self._n_chips = self._partitioner.get_n_chips()
        if partitioner_name == "ga":
            ga_configuration: GAAlgorithmConfiguration = \
                GAAlgorithmConfiguration(
                    init_solutions_generator=\
                        GaFixedSlicePopulationPTypeGeneratorOneSliceOneCore([50, 100, 200, 300, 400, 500, 600, 700, 800, 900],resource_constraint_configuration),
                    solution_representation_strategy='slice',
                    crossover_individuals_selection_strategy=GaussianWeightInvidualSelection(),
                    crossover_perform_strategy=GaSliceSliceInfoCombinationUniformCrossover(True),
                    variation_strategy=GaSliceVariationuUniformGaussian(True, 0.05, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0), 
                    solution_fixing_strategy=GaSliceRepresenationSolutionSimpleFillingFixing(resource_constraint_configuration, PacmanDataView.get_graph()), 
                    solution_cost_calculation_strategy=ResourceUtilizationCost(),
                    selection_strategy=GaEliteProbabilisticSelection(8, 3),
                    log_processing=True,
                    output_population_all_epoch=True, 
                    output_final_epoch_population=True,
                    epochs = 10, 
                    max_individuals_each_epoch = 20,
                    individual_survivals_each_epoch = 10, 
                    base_path_for_output = "./ga_algorithm_records/",
                    initial_solution_count = 10
            )

            self._partitioner = GAPartitioner(
                resource_contraints_configuration=resource_constraint_configuration,
                max_slice_length=10 ** 9,
                solution_file_path=None,
                serialize_solution_to_file=True,
                ga_algorithm_configuration=ga_configuration).partitioning()

    def get_partitioner_instance(self):
        return self._partitioner
    
    def get_n_chips(self):
        return self._n_chips
