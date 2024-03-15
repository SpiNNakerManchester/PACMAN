
from typing import Optional
from .solution_adapter import SolutionAdapter
from spinn_utilities.overrides import overrides
from pacman.data import PacmanDataView
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.utility_objs.chip_counter import ChipCounter
from pacman.operations.partition_algorithms.solution_checker import SolutionChecker

class AbstractPartitioner(SolutionAdapter, object):
  
    def __init__(self, resource_constraints_configuration = None):
        self._application_graph = application_graph
        self._checker = SolutionChecker(resource_constraints_configuration)
        self._chip_counter = ChipCounter() # chip_counter instance is used
                                            # to record the amount of allocated chips and 
        self._graph = PacmanDataView.get_graph() # get the application graph
        self._resource_constraints_configuration = resource_constraints_configuration

    def application_graph(self):
        return self._application_graph
    
    def partitioning(self):
        self._partitioning()
        return self

    def _partitioning(self):
        raise NotImplementedError
    
    def adapted_output(self):
        return self._adapted_output()

    def get_chip_counter(self):
        return self._chip_counter

    def get_n_chips(self):
        return self._chip_counter.n_chips

    @overrides(SolutionAdapter._adapted_output)
    def _adapted_output(self):
        raise NotImplementedError


