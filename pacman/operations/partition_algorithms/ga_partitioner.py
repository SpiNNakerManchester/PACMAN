
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
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from pacman.operations.partition_algorithms.ga_splitting_algorithm import GaAlgorithm
from pacman.operations.partition_algorithms.ga.entities.resource_configuration import ResourceConfiguration
from pacman.operations.partition_algorithms.ga.init_population_generators.abst_init_pop_generator import AbstractGaInitialPopulationGenerator
from pacman.operations.partition_algorithms.ga.init_population_generators.fixed_slice_pop_generator import GaFixedSlicePopulationGenerator
from pacman.operations.partition_algorithms.ga.entities.ga_algorithm_configuration import GAAlgorithmConfiguration
from typing import List
import numpy as np

class GaAlgorithmSolutionReader(object):
    @classmethod
    def read_solution_from_file(solution_file_path) -> AbstractGASolutionRepresentation:
        solution = np.load(solution_file_path, allow_pickle=True)
        solution_type = solution[0]
        solution_use_ptype = True if solution[1] == 1 else 0
        solution_max_chips = solution[2]
        solution_max_cores_per_chip = solution[3]
        if solution_type == CommonGASolutionRepresentation.class_str():
            return CommonGASolutionRepresentation(solution[4], solution_max_cores_per_chip, solution_max_chips, solution_use_ptype)
        elif solution_type == GASliceSolutionRepresentation.class_str():
            if solution_use_ptype:
                return GASliceSolutionRepresentation(solution[4], solution[5], solution[6], solution_max_cores_per_chip, solution_max_chips, True)
            else:
                return GASliceSolutionRepresentation(solution[4], None, None, solution_max_cores_per_chip, solution_max_chips, False)
    
class GAPartitioner(AbstractPartitioner):
    def __init__(self, resource_contraints_configuration, max_slice_length = 100, solution_file_path=None, read_solution_from_file=False, serialize_solution_to_file=False, ga_algorithm_configuration: GAAlgorithmConfiguration=None):
        super().__init__(resource_contraints_configuration)
        SDRAM_SIZE = self.get_resource_constraints_configuration().get_max_sdram()
        self._max_slice_length = max_slice_length
        self._neuron_count = self.get_resource_constraints_configuration().get_neruon_count()
        max_chips = self.get_resource_constraints_configuration().get_max_chips()
        max_cores_per_chip = self.get_resource_constraints_configuration().get_max_cores_per_chip()
        self._resource_configuration = ResourceConfiguration(self._neuron_count, max_chips if max_chips > 0 else \
                                                             self._neuron_count, max_cores_per_chip, SDRAM_SIZE)
        self._solution_file_path = solution_file_path
        self._read_solution_from_file = read_solution_from_file
        self._ga_algorithm_configuration: GAAlgorithmConfiguration = ga_algorithm_configuration
    
    @overrides(AbstractPartitioner._adapted_output)
    def _adapted_output(self) -> bytearray:
        return self._global_solution.to_common_representation().get_gtype_solution_representation()

    def _generate_init_solutions(self, generator: AbstractGaInitialPopulationGenerator, population_size: int)->List[AbstractGASolutionRepresentation]:
        return generator.generate_initial_population(population_size, self._graph)

    def _get_max_slice_length(self):
        return self._max_slice_length

    # important :: entry
    @overrides(AbstractPartitioner._partitioning)
    def _partitioning(self):
        # Begin coding for partitioning here

        initilization_solutions_generator:AbstractGaInitialPopulationGenerator = self._ga_algorithm_configuration.init_solutions_common_representation_generator 
        init_solutions_common_representation = \
            self._generate_init_solutions(generator=initilization_solutions_generator, population_size=15) # None -> List<CommonRepresentation>[]
        
        if not self._read_solution_from_file:
            self._global_solution : AbstractGASolutionRepresentation = \
               GaAlgorithm(self._ga_algorithm_configuration).do_GA_algorithm(init_solutions_common_representation)
        else:
            self._global_solution : AbstractGASolutionRepresentation = \
                GaAlgorithmSolutionReader().read_solution_from_file(self._solution_file_path)
        
        # Convert the solution to a gtype common solution representation, no matther what kind of solution
            # representation the GA algorithm generated.
        adapter_output = self._adapted_output()

        # Deploy the network by utilizing the solution GA generated.
        SolutionAdopter.AdoptSolution(adapter_output, self._graph, self._chip_counter, self._resource_configuration)