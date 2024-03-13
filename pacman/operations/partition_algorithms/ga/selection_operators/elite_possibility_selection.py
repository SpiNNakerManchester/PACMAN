from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.selection_operators.abst_selection import AbstractGaSelection
from typing import List
from spinn_utilities.overrides import overrides
import random

class GaEliteSelection(AbstractGaSelection):
    def __init__(self, count_survival, count_parent_remains:int) -> None:
        super().__init__()
        self._count_survival = count_survival
        self._count_parent_remains = count_parent_remains

    @overrides(AbstractGaSelection._select)
    def _select(self, costs:List[float], solutions:List[AbstractGASolutionRepresentation], parent_count:int, count_survival:int) -> List[AbstractGASolutionRepresentation]:
        def normalize_fitness(costs):
            nor_costs = (costs - min(costs))/(max(costs) - min(costs))
            return nor_costs
        
        if(self._count_parent_remains > len(solutions)):
            raise ValueError
        
        select_indexes = set()
        weights = normalize_fitness(costs)
        indexes = range(0, len(solutions))
        survive_solution_indexes = [solution for _, solution in sorted(zip(costs, range(0, len(solutions))))[:self._count_parent_remains]]
        for solution_index in survive_solution_indexes:
            select_indexes.add(solution_index)

        while len(select_indexes) < count_survival:
            index = random.choices(indexes, weights=weights, k = 1)[0]
            if(index not in select_indexes):
                select_indexes.add(index)
        select_indexes = list(select_indexes)

        return [solutions[sel_index] for sel_index in select_indexes]
    
    def __str__(self):
        return "elite_sel"