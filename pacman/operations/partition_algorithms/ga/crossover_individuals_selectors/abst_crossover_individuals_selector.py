from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator

from typing import List
class AbstractGaCrossoverIndividualSelector(object):
    def do_select_individuals(self, solutions: List[AbstractGASolutionRepresentation], costs: List[int]) -> List[AbstractGASolutionRepresentation]:
        self._do_select_individuals(costs)

    def _do_select_individuals(self, solutions: List[AbstractGASolutionRepresentation], costs: List[int]) -> List[AbstractGASolutionRepresentation]:
        raise NotImplementedError
 
    def __str__(self):
        return "abst_co_ind_sel"