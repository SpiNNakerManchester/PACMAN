
from typing import Optional
from .abstract_partitioner import AbstractPartitioner
from spinn_utilities.overrides import overrides


class RandomPartitioner(AbstractPartitioner):
    __slots__ = (
        # an application graph
        "application_graph"
        )

    def __init__(self, application_graph: Optional[str] = None):
        super(application_graph)

    def application_graph(self):
        return self._application_graph
    
    @overrides(AbstractPartitioner._partitioning)
    def _partitioning(self):
        raise NotImplementedError
