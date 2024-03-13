
from typing import Optional
from .abstract_partitioner import AbstractPartitioner
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationGraph
from .solution_adopter import SolutionAdopter
import numpy as np
import random
from pacman.utilities.utility_objs.chip_counter import ChipCounter
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga_splitting_algorithm import GaAlgorithm
from pacman.operations.partition_algorithms.ga.entities.resource_configuration import ResourceConfiguration
from pacman.operations.partition_algorithms.ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from pacman.operations.partition_algorithms.ga.init_population_generators.fixed_slice_pop_generator import GaFixedSlicePopulationGenerator

from typing import List

class GAPartitioner(AbstractPartitioner):
    def __init__(self, application_graph: ApplicationGraph = None, max_slice_length = 100, max_chips = -1, max_cores_per_chip = 18):
        super().__init__(application_graph)
        SDRAM_SIZE =  128 * 1024 * 1024
        self._max_slice_length = max_slice_length
        self._neuron_count = int(sum(map(lambda x: len(x), application_graph.vertices)))
        self._resource_configuration = ResourceConfiguration(self._neuron_count, max_chips if max_chips > 0 else \
                                                             self._neuron_count, max_cores_per_chip, SDRAM_SIZE)
    
    @overrides(AbstractPartitioner._adapted_output)
    def _adapted_output(self) -> bytearray:
        return self._global_solution.to_common_representation().get_gtype_solution_representation()

    def _generate_init_solutions(self, generator: AbstractGaInitialPopulationGenerator, population_size: int)->List[AbstractGASolutionRepresentation]:
        return generator.generate_initial_population(population_size)

    def _get_max_slice_length(self):
        return self._max_slice_length

    def initialization_generator_selection(self)->AbstractGaInitialPopulationGenerator:
        return GaFixedSlicePopulationGenerator(application_graph=self.application_graph(), \
                                               fixed_slice_size=100, \
                                               max_cores_per_chip=self._resource_configuration.get_max_cores_per_chip())

    # important :: entry
    @overrides(AbstractPartitioner._partitioning)
    def _partitioning(self):
        # Begin coding for partitioning here

        initilization_solutions_generator:AbstractGaInitialPopulationGenerator = self.initialization_generator_selection() 
        init_solutions_common_representation = \
            self._generate_init_solutions(initilization_solutions_generator) # None -> List<CommonRepresentation>[]
        
        self._global_solution : AbstractGASolutionRepresentation = \
            GaAlgorithm().do_GA_algorithm(init_solutions_common_representation)
        
        # Convert the solution to a gtype common solution representation, no matther what kind of solution
        # representation the GA algorithm generated.
        adapter_output = self._adapted_output()

        # Deploy the network by utilizing the solution GA generated.
        SolutionAdopter.AdoptSolution(adapter_output, self.graph, self.chip_counter)