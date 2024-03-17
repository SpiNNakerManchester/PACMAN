from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from pacman.operations.partition_algorithms.ga.crossover_individuals_selectors.abst_crossover_individuals_selector import AbstractGaCrossoverIndividualSelector
from pacman.operations.partition_algorithms.ga.crossover_operators.abst_crossover import AbstractGaCrossover
from pacman.operations.partition_algorithms.ga.variation_operators.abst_variation import AbstractGaVariation
from pacman.operations.partition_algorithms.ga.solution_fixing_operators.abst_solution_fixing import AbstractGaSolutionFixing
from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from pacman.operations.partition_algorithms.ga.selection_operators.abst_selection import AbstractGaSelection

class GAAlgorithmConfiguration(object):
    def __init__(self, init_solutions_generator: AbstractGaInitialPopulationGenerator,
            solution_representation_strategy: str,
            crossover_individuals_selection_strategy: AbstractGaCrossoverIndividualSelector, 
            crossover_perform_strategy: AbstractGaCrossover,
            variation_strategy: AbstractGaVariation, 
            solution_fixing_strategy: AbstractGaSolutionFixing, 
            solution_cost_calculation_strategy: AbstractGaCostCalculator,
            selection_strategy: AbstractGaSelection,
            log_processing = False,
            output_population_all_epoch = False, 
            output_final_epoch_population = False,
            epochs = 10, 
            max_individuals_each_epoch = 20,
            individual_survivals_each_epoch = 10, # 
            k_value_top_k_survival = 3,
            base_path_for_output = "./ga_algorithm_records/",
            initial_solution_count = 10
            ) -> None:
        self.init_solutions_generator = init_solutions_generator
        self.solution_representation_strategy = solution_representation_strategy
        self.crossover_individuals_selection_strategy = crossover_individuals_selection_strategy
        self.crossover_perform_strategy = crossover_perform_strategy
        self.variation_strategy = variation_strategy
        self.solution_fixing_strategy = solution_fixing_strategy
        self.solution_cost_calculation_strategy = solution_cost_calculation_strategy
        self.selection_strategy = selection_strategy
        self.log_processing = log_processing
        self.output_population_all_epoch = output_population_all_epoch
        self.output_final_epoch_population = output_final_epoch_population
        self.epochs = epochs
        self.max_individuals_each_epoch = max_individuals_each_epoch
        self.individual_survivals_each_epoch = individual_survivals_each_epoch
        self.k_value_top_k_survival = k_value_top_k_survival
        self.base_path_for_output = base_path_for_output
        self.initial_solution_count = initial_solution_count