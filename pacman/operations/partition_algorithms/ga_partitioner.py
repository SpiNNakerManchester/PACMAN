
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
from pacman.operations.partition_algorithms.ga_splitting_algorithm import GaAlgorithm
class GAPartitioner(AbstractPartitioner):
  
    def __init__(self, application_graph: ApplicationGraph = None, max_slice_length = 100):
        super().__init__(application_graph)
        self.max_slice_length = max_slice_length

    def application_graph(self):
        return self._application_graph
    
    @overrides(AbstractPartitioner._adapted_output)
    def _adapted_output(self):
        return self.global_solution

    @overrides(AbstractPartitioner._partitioning)
    def _partitioning(self):
        # Begin coding for partitioning here
        N_Ai = [vertex.n_atoms for vertex in self.graph.vertices]
        N = int(np.sum(N_Ai))
        max_cores_per_chip = 18
        max_chips = N

        init_solutions_common_representation = self._generate_init_solutions(N_Ai, N, max_cores_per_chip, max_chips) # None -> List<CommonRepresentation>[]

        self.solution = GaAlgorithm().do_GA_algorithm(init_solutions_common_representation)
        adapter_output = self._adapted_output()
        SolutionAdopter.AdoptSolution(adapter_output, self.graph, self.chip_counter)