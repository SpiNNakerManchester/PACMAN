from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.model.graphs.application import ApplicationGraph

from typing import List
class AbstractGaInitialPopulationGenerator(object):
    def __init__(self) -> None:
        pass

    def generate_initial_population(self, population_size: int, application_graph: ApplicationGraph) -> List[CommonGASolutionRepresentation]:
        raise NotImplementedError
    
    def __str__(self):
        return "abst_init_gen"