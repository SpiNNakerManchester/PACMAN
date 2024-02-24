from pacman.operations.partition_algorithms.splitter_partitioner import splitter_partitioner
from pacman.operations.partition_algorithms.random_partitioner import RandomPartitioner

class PartitionerSelector(object):
    
    def __init__(self, partitioner_name) -> None:
        self._partitioner_name = partitioner_name
        if partitioner_name == "splitter":            
            self._partitioner = None
            self._n_chips = splitter_partitioner()
        if partitioner_name == "random":
            self._partitioner = RandomPartitioner().partitioning()
            self._n_chips = self._partitioner.get_n_chips()
    
    def get_partitioner_instance(self):
        return self._partitioner
    
    def get_n_chips(self):
        return self._n_chips