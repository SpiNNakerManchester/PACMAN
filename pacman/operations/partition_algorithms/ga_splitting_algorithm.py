from .ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from .ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from .ga.crossover_individuals_selectors.abst_crossover_individuals_selector import AbstractGaCrossoverIndividualSelector
from .ga.crossover_operators.abst_crossover import AbstractGaCrossover
from .ga.variation_operators.abst_variation import AbstractGaVariation
from .ga.solution_fixing_operators.abst_solution_fixing import AbstractGaSolutionFixing
from .ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from .ga.selection_operators.abst_selection import AbstractGaSelection
import numpy as np
class GaLogger(object):
    def log(self, message):
        print(message)

class GaAlgorithm(object):
    def __init__(self, 
                 init_solutions_common_representation_generator : AbstractGaInitialPopulationGenerator,
                 solution_representation_strategy: AbstractGASolutionRepresentation,
                 crossover_individuals_selection_strategy: AbstractGaCrossoverIndividualSelector, 
                 crossover_perform_strategy: AbstractGaCrossover,
                 variation_strategy: AbstractGaVariation, 
                 solution_fixing_strategy: AbstractGaSolutionFixing, 
                 solution_cost_calculation_strategy: AbstractGaCostCalculator,
                 selection_strategy: AbstractGaSelection,
                 log_processing=False,
                 output_population_all_epoch=False, 
                 output_final_epoch_population=False,
                 epochs = 10, max_individuals_each_epoch = 20, remains_individuals = 10, base_path_for_output = "./") -> None:
        self.init_solutions_common_representation_generator = init_solutions_common_representation_generator
        self.solution_representation_strategy = solution_representation_strategy
        self.crossover_individuals_selection_strategy = crossover_individuals_selection_strategy
        self.crossover_perform_strategy = crossover_perform_strategy
        self.variation_strategy = variation_strategy
        self.solution_fixing_strategy = solution_fixing_strategy
        self.solution_cost_calculation_strategy = solution_cost_calculation_strategy
        self.selection_strategy = selection_strategy
        self.log_processing=log_processing
        self.output_populaton_all_epoch=output_population_all_epoch
        self.output_final_epoch_population=output_final_epoch_population
        self.epochs = epochs
        self.max_individuals_each_epoch = max_individuals_each_epoch
        self.remains_individuals = remains_individuals
        self.base_path_for_output = base_path_for_output
        if self.log_processing:
            self.GaLogger = GaLogger()


    def _log(self, message):
        if self.log_processing:
            self.GaLogger.log(message)

    def _out_solutions(self, epoch, solutions):
        filename = "[%s][%s][%s][%s][%s][%s][%s][%s]epoch-%d.npy" % \
            (self.init_solutions_common_representation_generator,
             self.solution_representation_strategy,
             self.crossover_individuals_selection_strategy,
             self.crossover_perform_strategy,
             self.variation_strategy,
             self.solution_fixing_strategy,
             self.solution_cost_calculation_strategy,
             self.selection_strategy,
             epoch)
        
        data = np.array([solution.get_npy_data() for solution in solutions])
        np.save("%s/%s" % (self.base_path_for_output, filename), data)
    
    def do_GA_algorithm(self) -> AbstractGASolutionRepresentation:
        init_solution = self.init_solutions_common_representation_generator.generate_initial_population()
        solutions = self.solution_representation_strategy.convert_from_common_representation(init_solution)
        for epoch in range(0, self.epochs):
            self._log("begin epoch %d..." % epoch)

            avaliable_parents_count = len(solutions)
            while len(solutions) < self.max_individuals_each_epoch:
                individual1, individual2 = self.crossover_individuals_selection_strategy.do_select_individuals(solutions[:avaliable_parents_count], self.solution_cost_calculation_strategy)
                new_individual = self.crossover_perform_strategy.do_crossover(individual1, individual2)
                new_individual = self.variation_strategy.do_variation(new_individual)
                new_individual = self.solution_fixing_strategy.do_solution_fixing(new_individual)
                solutions.append(new_individual)
                self._log("[In Epoch %d] Finish solution %d/%d" % (len(solutions), self.max_individuals_each_epoch))
            
            self._log("[In Epoch %d] Finish. Begin calculating cost of each individual." % epoch)
            costs = self.solution_cost_calculation_strategy.calculate(solutions)
            self._log("[In Epoch %d] Finish. Costs = %s" % str(costs))
            solutions = self.selection_strategy.select(costs, solutions)
            if self.output_populaton_all_epoch:
                self._out_solutions(epoch, solutions)
        costs = self.solution_cost_calculation_strategy.calculate(solutions)
        self._log("Finish Ga. Costs = %s" % str(costs))

        return [solution for _, solution in sorted(zip(costs, solutions))][0]