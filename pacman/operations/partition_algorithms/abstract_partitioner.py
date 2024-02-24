
from typing import Optional
from .solution_adapter import SolutionAdapter
from .solution_checker import SolutionChecker
from spinn_utilities.overrides import overrides

class AbstractPartitioner(SolutionAdapter, object):
    __slots__ = (
        # an application graph
        "application_graph"
        )

    def __init__(self, application_graph: Optional[str] = None):
        self._application_graph = application_graph
        self.checker = SolutionChecker()

    def application_graph(self):
        return self._application_graph

    def _partitioning(self):
        raise NotImplementedError
    
    def partitioning(self):
        self._partitioning()
        return self._adapted_output()

    @overrides(SolutionAdapter.adapted_output)
    def _adapted_output(self):
        pass

    
    def adapted_output(self):
        self._adapted_output()

