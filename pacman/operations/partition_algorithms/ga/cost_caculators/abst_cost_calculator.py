from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
class AbstractGaCostCalculator(object):
    def calculate(self, solutions: List[AbstractGASolutionRepresentation] | AbstractGASolutionRepresentation) -> List[float]:
        costs = []
        if type(solutions) is list:
            for solution in solutions:
                cost = self._calculate_single(solution)
                costs.append(cost)
        elif isinstance(solutions, AbstractGASolutionRepresentation):
            costs.append(self._calculate_single(solution))
        else:
            raise TypeError
        return costs
    
    def _calculate_single(self, solution: AbstractGASolutionRepresentation):
        raise NotImplementedError
    
    def __str__(self):
        return "abst_cost"