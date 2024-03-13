from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from typing import List
class AbstractGaInitialPopulationGenerator(object):
    def __init__(self) -> None:
        pass

    def generate_initial_population(self, population: int) -> List[CommonGASolutionRepresentation]:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_init_gen"