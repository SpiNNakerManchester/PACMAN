from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
from pacman.model.constraints.abstract_partitioner_constraint import \
    AbstractPartitionerConstraint
from pacman.model.constraints.partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint
from pacman.model.constraints.placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from pacman.model.resources.sdram_tracker import SDRAMTracker
from pacman import exceptions
from pacman import constants as pacman_constants


@add_metaclass(ABCMeta)
class AbstractPartitionAlgorithm(object):
    """ An abstract algorithm that can partition a graph
    """

    def __init__(self, machine_time_step, runtime_in_machine_time_steps):
        """constructor to build a
        pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :param machine_time_step: the length of tiem in ms for a timer tic
        :param runtime_in_machine_time_steps: the number of timer tics expected \
               to occur due to the runtime
        :type machine_time_step: int
        :type runtime_in_machine_time_steps: long
        :return: a new pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :rtype: pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :raises None: does not raise any known expection
        """
        self._machine_time_step = machine_time_step
        self._runtime_in_machine_time_steps = runtime_in_machine_time_steps
        self._supported_constrants = list()
        self._sdram_tracker = SDRAMTracker()
    
    @abstractmethod
    def partition(self, graph, machine):
        """ Partition a graph so that each subvertex will fit on a processor\
            within the machine
            
        :param graph: The graph to partition
        :type graph: :py:class:`pacman.model.graph.graph.Graph`
        :param machine: The machine with respect to which to partition the graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A subgraph of partitioned vertices and edges from the graph
        :rtype: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """

    def _check_can_support_partitioner_constraints(self, graph):
        """checks that the constraints on the vertices in the graph are all
        supported by the given implimentation of the partitioner.

        :param graph: The graph to partition
        :type graph: :py:class:`pacman.model.graph.graph.Graph`
        :raise pacman.exceptions.PacmanPartitionException: if theres a
        constraint in the vertices in the graph to which this implemntation
        of the partitioner cannot handle
        """
        for vertex in graph.vertices:
            for constraint in vertex.constraints:
                if isinstance(constraint, AbstractPartitionerConstraint):
                    located = False
                    for supported_constraint in self._supported_constrants:
                        if isinstance(constraint, supported_constraint):
                            located = True
                    if not located:
                        raise exceptions.PacmanPartitionException(
                            "the partitioning algorithum selected cannot support "
                            "the partitioning constraint '{}', which has been "
                            "placed on vertex labelled {}"
                            .format(constraint, vertex.label))

    @staticmethod
    def _locate_max_atom_constrants(constraints):
        """locates all max_atom constraints in a given collection of constraints

        :param constraints: a iterable of
         pacman.model.constraints.AbstractConstraint.AbstractConstraint
        :type constraints: a iterable object
        :return: a list containing only
        pacman.model.constraints.partitioner_maximum_size_constraint constraints
        or a empty list if none exist
        :rtype: iterable object
        :raises None: no known exceptions
        """
        max_atom_constraints = list()
        for constrant in constraints:
            if isinstance(constrant, PartitionerMaximumSizeConstraint):
                max_atom_constraints.append(constrant)
        return max_atom_constraints

    def _get_maximum_resources_per_processor(self, vertex_constriants, machine):
        """locates the maximum rsources avilable given the subverts already
        produced

        :param vertex_constriants: the constraints of a given vertex
        :param machine: the imutable machine object
        :type vertex_constriants: list of pacman.model.constraints.abstract_constraint
        :type machine: a spinnmachine.machine.machine object
        :return: the max sdram usage avilable given sdram allocations
        :rtype: int
        """
        #locate any instances of PlacerChipAndCoreConstraint
        for constraint in vertex_constriants:
            if isinstance(constraint, PlacerChipAndCoreConstraint):
                sdram_avilable = self._sdram_tracker.get_usage(constraint.x,
                                                               constraint.y)
                return sdram_avilable

        # no PlacerChipAndCoreConstraint was found, search till max value
        # returned
        maximum_sdram = 0
        for chip in machine.chips:
            sdram_avilable = self._sdram_tracker.get_usage(chip.x, chip.y)
            if sdram_avilable >= maximum_sdram:
                maximum_sdram = sdram_avilable
            #if a chip has been returned with sdram usage as the hard coded
            # max supported, then stop searching and return max.
            if sdram_avilable == pacman_constants.SDRAM_AVILABLE_BYTES:
                return maximum_sdram