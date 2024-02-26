from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_fixing_operators.abst_solution_fixing import AbstractGaSolutionFixing

from spinn_utilities.overrides import overrides

class GaSolutionFixing1(AbstractGaSolutionFixing):
    @overrides(AbstractGaSolutionFixing.do_solution_fixing)
    def do_solution_fixing(self, solution: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_solution_fix"