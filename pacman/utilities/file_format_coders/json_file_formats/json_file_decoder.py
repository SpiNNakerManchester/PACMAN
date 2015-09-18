"""
JsonFileDecoder for decoder for json files into python objects
"""
from pacman.utilities.file_format_coders.abstract_coders.\
    abstract_format_decoder import AbstractFormatDecoder
from pacman import exceptions

class JsonFileDecoder(AbstractFormatDecoder):
    """
    JsonFileDecoder:  decoder for json files into python objects
    """

    def __init__(self, folder_path):
        AbstractFormatDecoder.__init__(self)
        self._folder_path = folder_path

    def decode_placements(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_partitionable_graph_constraints(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_partitioned_graph(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_tags(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_partitioned_graph_constraints(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_routing_tables(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_machine(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_partitionable_graph(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_routing_paths(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_routing_infos(self):
        raise exceptions.PacmanException("Not implimented yet")

    def decode_algorithm_data_objects(self):
        raise exceptions.PacmanException("Not implimented yet")
