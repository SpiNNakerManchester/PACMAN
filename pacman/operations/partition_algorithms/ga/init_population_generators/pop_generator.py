from pacman.operations.partition_algorithms.ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation

from typing import List
from spinn_utilities.overrides import overrides

class GaInitialPopulationGenerator1(AbstractGaInitialPopulationGenerator):
    @overrides(AbstractGaInitialPopulationGenerator.generate_initial_population)
    def generate_initial_population(self) -> List[CommonGASolutionRepresentation]:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_init_gen"