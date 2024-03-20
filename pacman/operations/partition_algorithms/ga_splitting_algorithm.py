from .ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from .ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from .ga.crossover_individuals_selectors.abst_crossover_individuals_selector import AbstractGaCrossoverIndividualSelector
from .ga.crossover_operators.abst_crossover import AbstractGaCrossover
from .ga.variation_operators.abst_variation import AbstractGaVariation
from .ga.solution_fixing_operators.abst_solution_fixing import AbstractGaSolutionFixing
from .ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from .ga.selection_operators.abst_selection import AbstractGaSelection
from .ga.entities.ga_algorithm_configuration import GAAlgorithmConfiguration
from pacman.model.graphs.application import ApplicationGraph
import numpy as np
import os

class GaLogger(object):
    def log(self, message):
        print(message)

class GaAlgorithm(object):
    def __init__(self, ga_configuration: GAAlgorithmConfiguration) -> None:
        self.init_solutions_generator = ga_configuration.init_solutions_generator
        self.solution_representation_strategy = ga_configuration.solution_representation_strategy
        self.crossover_individuals_selection_strategy = ga_configuration.crossover_individuals_selection_strategy
        self.crossover_perform_strategy = ga_configuration.crossover_perform_strategy
        self.variation_strategy = ga_configuration.variation_strategy
        self.solution_fixing_strategy = ga_configuration.solution_fixing_strategy
        self.solution_cost_calculation_strategy = ga_configuration.solution_cost_calculation_strategy
        self.selection_strategy = ga_configuration.selection_strategy
        self.log_processing = ga_configuration.log_processing
        self.output_populaton_all_epoch = ga_configuration.output_population_all_epoch
        self.output_final_epoch_population = ga_configuration.output_final_epoch_population
        self.epochs = ga_configuration.epochs
        self.max_individuals_each_epoch = ga_configuration.max_individuals_each_epoch
        self.individual_survivals_each_epoch = ga_configuration.individual_survivals_each_epoch
        self.k_value_top_k_survival = ga_configuration.k_value_top_k_survival
        self.base_path_for_output = ga_configuration.base_path_for_output
        self.initial_solution_count = ga_configuration.initial_solution_count
        if self.log_processing:
            self.GaLogger = GaLogger()


    def _log(self, message):
        if self.log_processing:
            self.GaLogger.log(message)

    def _out_solutions_of_a_epoch_before_selection(self, epoch, solutions):
        filename = "[%s][%s][%s][%s][%s][%s][%s][%s]epoch-%d.npy" % \
            (self.init_solutions_generator,
             self.solution_representation_strategy,
             self.crossover_individuals_selection_strategy,
             self.crossover_perform_strategy,
             self.variation_strategy,
             self.solution_fixing_strategy,
             self.solution_cost_calculation_strategy,
             self.selection_strategy,
             epoch)

        def get_output_folder_of_file(output_file_path: str):
            pos = len(output_file_path) - 1
            while(pos >= 0 and output_file_path[pos] != '/' and output_file_path[pos] != '\\'):
                pos -= 1
            if pos < 0:
                return output_file_path
            return output_file_path[:pos + 1]
        file_path = "%s/%s" % (self.base_path_for_output, filename)
        output_file_folder = get_output_folder_of_file(file_path)
        if not os.path.exists(output_file_folder):
            os.makedirs(output_file_folder)
        data = [solution.get_serialized_data() for solution in solutions]
        while file_path.count("//") > 0:
            file_path = file_path.replace("//", "/")
        while file_path.count("\\\\") > 0:
            file_path = file_path.replace("\\\\", "\\")
        np.save(file_path, np.array(data, dtype=object), allow_pickle=True)
    
    def do_GA_algorithm(self, application_graph: ApplicationGraph) -> AbstractGASolutionRepresentation:
        init_solution = self.init_solutions_generator.generate_initial_population(self.initial_solution_count, application_graph)
        solutions = init_solution # self.solution_representation_strategy.from_common_representation(init_solution)
        for epoch in range(0, self.epochs):
            self._log("begin epoch %d..." % epoch)
            avaliable_parents_count = len(solutions)
            costs = self.solution_cost_calculation_strategy.calculate(solutions)
            while len(solutions) < self.max_individuals_each_epoch:
                individual1, individual2 = self.crossover_individuals_selection_strategy.do_select_individuals(solutions[:avaliable_parents_count], costs)
                new_individual1, new_individual2 = self.crossover_perform_strategy.do_crossover(individual1, individual2)
                new_individual1, new_individual2 = self.variation_strategy.do_variation(new_individual1), self.variation_strategy.do_variation(new_individual2)
                new_individual1, new_individual2 = self.solution_fixing_strategy.do_solution_fixing(new_individual1), self.solution_fixing_strategy.do_solution_fixing(new_individual2)
                solutions.append(new_individual1)
                solutions.append(new_individual2)
                self._log("[In Epoch %d] Finish solution %d/%d" % (epoch, len(solutions), self.max_individuals_each_epoch))
            self._log("[In Epoch %d] Finish. Begin calculating cost of each individual." % epoch)
            costs += (self.solution_cost_calculation_strategy.calculate(solutions[avaliable_parents_count:]))
            self._log("[In Epoch %d] Finish. Costs = %s" % (epoch, str(costs)))
            if self.output_populaton_all_epoch:
                self._log("[In Epoch %d] Output solution of current epoch..." % epoch)
                self._out_solutions_of_a_epoch_before_selection(epoch, solutions)
            self._log("[In Epoch %d] Selection Begin..." % epoch)
            solutions = self.selection_strategy.select(costs, solutions, self.k_value_top_k_survival, self.individual_survivals_each_epoch)
            self._log("[In Epoch %d] Cost after selection: %s" % (epoch, str(costs)))

        costs = self.solution_cost_calculation_strategy.calculate(solutions)
        self._log("Finish GA. Costs = %s" % str(costs))

        return [solution for _, solution in sorted(zip(costs, solutions))][0]