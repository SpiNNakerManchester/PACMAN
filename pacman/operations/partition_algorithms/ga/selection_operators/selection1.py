from typing import List
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.selection_operators.abst_selection import AbstractGaSelection

from typing import List
from spinn_utilities.overrides import overrides


class Selection1(AbstractGaSelection):
    @overrides(AbstractGaSelection.select)
    def select(self, costs:List[float], solutions:List[AbstractGASolutionRepresentation]) -> List[AbstractGASolutionRepresentation]:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_sel"