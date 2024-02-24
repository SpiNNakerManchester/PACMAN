
from typing import Optional
from .abstract_partitioner import AbstractPartitioner
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationGraph

class RandomPartitioner(AbstractPartitioner):
  
    def __init__(self, application_graph: ApplicationGraph = None):
        super().__init__(application_graph)

    def application_graph(self):
        return self._application_graph
    
    @overrides(AbstractPartitioner._partitioning)
    def _partitioning(self):
        for vertex in (self.graph.vertices):
            vertex.splitter.create_machine_vertices(self.chip_counter)

