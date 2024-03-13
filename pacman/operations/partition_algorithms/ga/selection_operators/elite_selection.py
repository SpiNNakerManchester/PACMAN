from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.selection_operators.abst_selection import AbstractGaSelection

from typing import List
from spinn_utilities.overrides import overrides


class GaEliteSelection(AbstractGaSelection):
    def __init__(self, count_survival) -> None:
        super().__init__()
        self._count_survival = count_survival

    @overrides(AbstractGaSelection._select)
    def _select(self, costs:List[float], solutions:List[AbstractGASolutionRepresentation], parent_count:int, count_survival:int) -> List[AbstractGASolutionRepresentation]:
        return [solution for (_, solution) in sorted(zip(costs, solutions))[:self._count_survival]]
    
    def __str__(self):
        return "elite_sel"