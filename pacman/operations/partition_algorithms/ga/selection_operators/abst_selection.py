from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
class AbstractGaSelection(object):
    def select(self, costs:List[float], solutions:List[AbstractGASolutionRepresentation], k_value_top_k_survival:int, count_survivals:int) -> List[AbstractGASolutionRepresentation]:
        if(count_survivals > len(solutions)):
            raise ValueError
        return self._select(costs, solutions, k_value_top_k_survival, count_survivals)

    def _select(self, costs:List[float], solutions:List[AbstractGASolutionRepresentation], k_value_top_k_survival:int, count_survivals:int) -> List[AbstractGASolutionRepresentation]:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_sel"