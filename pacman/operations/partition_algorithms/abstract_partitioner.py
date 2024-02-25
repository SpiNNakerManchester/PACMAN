
from typing import Optional
from .solution_adapter import SolutionAdapter
from .solution_checker import SolutionChecker
from spinn_utilities.overrides import overrides
from pacman.data import PacmanDataView
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.utility_objs.chip_counter import ChipCounter

class AbstractPartitioner(SolutionAdapter, object):
  
    def __init__(self, application_graph: Optional[str] = None):
        self._application_graph = application_graph
        self.checker = SolutionChecker()
        self.chip_counter = ChipCounter()
        self.graph = PacmanDataView.get_graph()


    def application_graph(self):
        return self._application_graph

    def _partitioning(self):
        raise NotImplementedError
    
    def partitioning(self):
        self._partitioning()
        return self

    @overrides(SolutionAdapter._adapted_output)
    def _adapted_output(self):
        raise NotImplementedError

    def adapted_output(self):
        self._adapted_output()


    def get_chip_counter(self):
        return self.chip_counter

    def get_n_chips(self):
        return self.chip_counter.n_chips

