from typing import List, Union
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation

class AbstractGaCostCalculator(object):
    def calculate(self, solutions: Union[List[AbstractGASolutionRepresentation], AbstractGASolutionRepresentation]) -> List[float]:
        costs = []
        if type(solutions) is list:
            for solution in solutions:
                cost = self._calculate_cost_for_single_individual(solution)
                costs.append(cost)
        elif isinstance(solutions, AbstractGASolutionRepresentation):
            costs.append(self._calculate_cost_for_single_individual(solution))
        else:
            raise TypeError
        return costs
    
    def _calculate_cost_for_single_individual(self, solution: AbstractGASolutionRepresentation):
        raise NotImplementedError
    
    def __str__(self):
        return "abst_cost"