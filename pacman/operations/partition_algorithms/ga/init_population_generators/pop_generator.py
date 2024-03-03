from pacman.operations.partition_algorithms.ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.model.graphs.application import ApplicationGraph
from typing import List
from spinn_utilities.overrides import overrides

class GaFixedSlicePopulationGenerator(AbstractGaInitialPopulationGenerator):
    def __init__(self, population_size, application_graph: ApplicationGraph) -> None:
        super().__init__(population_size)
        self.application_graph = application_graph
    
    @overrides(AbstractGaInitialPopulationGenerator.generate_initial_population)
    def generate_initial_population(self) -> List[CommonGASolutionRepresentation]:
        

    def __str__(self):
        return "abst_init_gen"