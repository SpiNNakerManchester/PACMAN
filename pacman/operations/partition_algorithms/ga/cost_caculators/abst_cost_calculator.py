from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
class AbstractGaCostCalculator(object):
    def calculate(self, solutions: List[AbstractGASolutionRepresentation]) -> List[float]:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_cost"