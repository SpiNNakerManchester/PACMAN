from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from spinn_utilities.overrides import overrides

class ResourceUtilizationCost(AbstractGaCostCalculator):
    @override(AbstractGaCostCalculator._calculate_single)
    def _calculate_single(self, solution: AbstractGASolutionRepresentation) -> List[float]:
        common_solution_representation = solution.to_common_representation()
        gtype_representation: List[int] = common_solution_representation.get_gtype_solution_representation()
        differ_cores = set(gtype_representation)
        return differ_cores


    def __str__(self):
        return "c1_cost"