from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.cost_caculators.abst_cost_calculator import AbstractGaCostCalculator
from spinn_utilities.overrides import overrides
from numpy.typing import NDArray
class ProfilingIsingModelCost(AbstractGaCostCalculator):
    @override(AbstractGaCostCalculator._calculate_single)
    def _calculate_single(self, solution: AbstractGASolutionRepresentation) -> List[float]:
        common_solution_representation = solution.to_common_representation()
        gtype_representation: List[int] = common_solution_representation.get_ptype_solution_representation()


    def __init__(self, H: NDArray, J: NDArray) -> None:
        super().__init__()
        if len(H.shape) or len(J.shape) != 2 or J.shape[0] != J.shape[1] or H.shape[0] != J.shape[1]:
            raise ValueError
        self._H = H
        self._J = J
        

        
    def __str__(self):
        return "c1_cost"