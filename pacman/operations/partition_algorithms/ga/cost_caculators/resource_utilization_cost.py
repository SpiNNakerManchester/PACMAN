from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from spinn_utilities.overrides import overrides

class ResourceUtilizationCost(AbstractGaCostCalculator):
    @overrides(AbstractGaCostCalculator._calculate_cost_for_single_individual)
    def _calculate_cost_for_single_individual(self, solution: AbstractGASolutionRepresentation) -> List[float]:
        common_solution_representation = solution.to_common_representation()
        ptype_representation: List[int] = common_solution_representation.get_ptype_solution_representation()
        different_core_ids = set(ptype_representation)
        return len(different_core_ids)

    def __str__(self):
        return "res_util_cost"