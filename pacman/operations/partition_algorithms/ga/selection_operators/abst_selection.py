from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
class AbstractGaSelection(object):
    def select(self, costs:List[float], solutions:List[AbstractGASolutionRepresentation], parent_count:int, count_survival:int) -> List[AbstractGASolutionRepresentation]:
        if(count_survival > len(solutions)):
            raise ValueError
        self._select(costs, solutions)

    def _select(self, costs:List[float], solutions:List[AbstractGASolutionRepresentation], parent_count:int, count_survival:int) -> List[AbstractGASolutionRepresentation]:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_sel"