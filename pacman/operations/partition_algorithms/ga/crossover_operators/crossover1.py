from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.crossover_operators.abst_crossover import AbstractGaCrossover

from spinn_utilities.overrides import overrides

class Crossover1(AbstractGaCrossover):
    @overrides(AbstractGaCrossover.do_crossover)
    def do_crossover(self, individual1: AbstractGASolutionRepresentation, individual2: AbstractGASolutionRepresentation):
        raise NotImplementedError
    
    def __str__(self):
        return "abst_co"