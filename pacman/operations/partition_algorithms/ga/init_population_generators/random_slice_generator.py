from pacman.operations.partition_algorithms.ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from pacman.model.graphs.application import ApplicationGraph
from typing import List
from spinn_utilities.overrides import overrides
import numpy as np
import random
from .fixed_slice_pop_generator import GaFixedSlicePopulationGenerator

class GaRandomSlicePopulationGenerator(AbstractGaInitialPopulationGenerator):
    def __init__(self, application_graph: ApplicationGraph, max_cores_per_chip = 18, max_slice_size = -1) -> None:
        super().__init__()
        if(max_cores_per_chip < 0):
            raise ValueError
        self._application_graph = application_graph
        self._max_cores_per_chip = max_cores_per_chip
        self._max_slice_size = max_slice_size if max_slice_size >= 1 else (int)(np.sum([v.n_atoms() for v in application_graph.vertices]))

    @overrides(AbstractGaInitialPopulationGenerator.generate_initial_population)
    def generate_initial_population(self, population_size: int) -> List[CommonGASolutionRepresentation]:
        fixed_slice_sizes = random.choices(range(0, self._max_slice_size), k = population_size)
        self._fix_slice_init_population_generator = GaFixedSlicePopulationGenerator(self._application_graph, fixed_slice_sizes, self._max_cores_per_chip)
        return self._fix_slice_init_population_generator.generate_initial_population(population_size, fixed_slice_sizes)
    def __str__(self):
        return "random_slice_init_gen"