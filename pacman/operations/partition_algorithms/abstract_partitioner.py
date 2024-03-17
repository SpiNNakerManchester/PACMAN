
from typing import Optional
from .solution_adapter import SolutionAdapter
from spinn_utilities.overrides import overrides
from pacman.data import PacmanDataView
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.utility_objs.chip_counter import ChipCounter
from pacman.operations.partition_algorithms.solution_checker import SolutionChecker
from pacman.operations.partition_algorithms.ga.entities.resource_configuration import ResourceConfiguration

import numpy as np

class AbstractPartitioner(SolutionAdapter, object):
    def __init__(self, resource_constraint_configuration:ResourceConfiguration = None):
        self._checker = SolutionChecker(resource_constraint_configuration)
        self._chip_counter = ChipCounter() # chip_counter instance is used
                                           # to record the amount of allocated chips and 
        self._graph = PacmanDataView.get_graph() # get the application graph
        resource_constraint_configuration.set_neuron_count((int)(np.sum([vertex.n_atoms for vertex in self._graph.vertices])))
        self._resource_constraint_configuration = resource_constraint_configuration

    def application_graph(self):
        return self._graph
    
    def partitioning(self):
        # call the partiting implementation.
        self._partitioning()
        return self

    def _partitioning(self):
        # the partitioning implementation should be implemented by the subclass.
        raise NotImplementedError
    
    def adapted_output(self):
        return self._adapted_output()

    def get_chip_counter(self):
        return self._chip_counter

    def get_n_chips(self):
        return self._chip_counter.n_chips

    def get_resource_constraint_configuration(self) -> ResourceConfiguration:
        return self._resource_constraint_configuration
    
    @overrides(SolutionAdapter._adapted_output)
    def _adapted_output(self):
        raise NotImplementedError


