from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from spinn_utilities.overrides import overrides

class C1Cost(AbstractGaCostCalculator):
    @override(AbstractGaCostCalculator.calculate)
    def calculate(self, solutions: List[AbstractGASolutionRepresentation]) -> List[float]:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_cost"