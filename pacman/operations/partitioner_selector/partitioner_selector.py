from pacman.operations.partition_algorithms.splitter_partitioner import splitter_partitioner
from pacman.operations.partition_algorithms.random_partitioner import RandomPartitioner

class PartitionerSelector(object):
    
    def __init__(self, partitioner_name) -> None:
        self._partitioner_name = partitioner_name
        if partitioner_name == "splitter":
            return splitter_partitioner()
        if partitioner_name == "random":
            return RandomPartitioner()