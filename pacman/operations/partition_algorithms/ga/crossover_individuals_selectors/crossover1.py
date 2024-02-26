from pacman.operations.partition_algorithms.ga.crossover_individuals_selectors.abst_crossover_individuals_selector import AbstractGaCrossoverIndividualSelector
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from typing import List
from spinn_utilities.overrides import overrides

class CrossoverInd1(AbstractGaCrossoverIndividualSelector):
    @overrides(AbstractGaCrossoverIndividualSelector.do_select_individuals)
    def do_select_individuals(solutions: List[AbstractGASolutionRepresentation], solution_cost_calculation_strategy: AbstractGaCostCalculator) -> List[AbstractGASolutionRepresentation]:
        raise NotImplementedError

    def __str__(self):
        return "abst_co_ind_sel"