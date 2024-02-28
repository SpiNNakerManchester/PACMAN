from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.variation_operators.abst_variation import AbstractGaVariation

from spinn_utilities.overrides import overrides

class GaVariation1(AbstractGaVariation):
    @overrides(AbstractGaVariation)
    def do_variation(self, solution: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_variation"

