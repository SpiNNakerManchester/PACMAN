from abc import ABCMeta
from abc import abstractmethod

from six import add_metaclass

from pacman.model.constraints.abstract_partitioner_constraint import \
    AbstractPartitionerConstraint
from pacman.model.constraints.partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint
from pacman.model.constraints.placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.utilities.sdram_tracker import SDRAMTracker
from pacman import exceptions
from pacman.utilities.progress_bar import ProgressBar
from spinn_machine.processor import Processor
from spinn_machine.sdram import SDRAM

import logging

logger = logging.getLogger(__name__)

@add_metaclass(ABCMeta)
class AbstractPartitionAlgorithm(object):
    """ An abstract algorithm that can partition a partitionable_graph
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
        self._supported_constraints = list()
        self._sdram_tracker = SDRAMTracker()
    
    @abstractmethod
    def partition(self, graph, machine):
        """ Partition a partitionable_graph so that each subvertex will fit on a processor\
            within the machine
            
        :param graph: The partitionable_graph to partition
        :type graph: :py:class:`pacman.model.graph.partitionable_graph.PartitionableGraph`
        :param machine: The machine with respect to which to partition the partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A partitioned_graph of partitioned vertices and edges from the partitionable_graph
        :rtype: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """

    def _get_maximum_resources_per_processor(self, vertex_constraints, machine):
        """locates the maximum rsources avilable given the subverts already
        produced

        :param vertex_constraints: the constraints of a given vertex
        :param machine: the imutable machine object
        :type vertex_constraints: list of pacman.model.constraints.abstract_constraint
        :type machine: a spinnmachine.machine.machine object
        :return: the max sdram usage avilable given sdram allocations
        :rtype: pacman.model.resources.resource_container.ResourceContainer
        """
        #locate any instances of PlacerChipAndCoreConstraint
        for constraint in vertex_constraints:
            if isinstance(constraint, PlacerChipAndCoreConstraint):
                sdram_available = self._sdram_tracker.get_usage(constraint.x,
                                                                constraint.y)
                return ResourceContainer(
                    cpu=CPUCyclesPerTickResource(Processor.CPU_AVAILABLE),
                    dtcm=DTCMResource(Processor.DTCM_AVAILABLE),
                    sdram=SDRAMResource(sdram_available))

        # no PlacerChipAndCoreConstraint was found, search till max value
        # returned or highest avilable
        maximum_sdram = 0
        for chip in machine.chips:
            sdram_used = self._sdram_tracker.get_usage(chip.x, chip.y)
            sdram_available = chip.sdram.size - sdram_used
            if sdram_available >= maximum_sdram:
                maximum_sdram = sdram_available
            #if a chip has been returned with sdram usage as the hard coded
            # max supported, then stop searching and return max.
            if sdram_available == SDRAM.DEFAULT_SDRAM_BYTES:
                return ResourceContainer(
                    cpu=CPUCyclesPerTickResource(Processor.CPU_AVAILABLE),
                    dtcm=DTCMResource(Processor.DTCM_AVAILABLE),
                    sdram=SDRAMResource(maximum_sdram))

        return ResourceContainer(
            cpu=CPUCyclesPerTickResource(Processor.CPU_AVAILABLE),
            dtcm=DTCMResource(Processor.DTCM_AVAILABLE),
            sdram=SDRAMResource(maximum_sdram))

    @staticmethod
    def _generate_sub_edges(subgraph, graph_to_subgraph_mapper, graph):
        '''generates the sub edges for the subvertices in the partitioned_graph.

        :param subgraph: the partitioned_graph to work with
        :param graph_to_subgraph_mapper: the mapper between partitionable_graph and partitioned_graph
        :param graph: the partitionable_graph to work with
        :type subgraph: pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph
        :type graph_to_subgraph_mapper:
        pacman.model.graph_mapper.GraphMapper
        :type graph: pacman.model.graph.partitionable_graph.PartitionableGraph
        :return: None
        :rtype: None
        :raise None: this method does not raise any known exceptions

        '''
         #start progress bar
        progress_bar = ProgressBar(len(subgraph.subvertices),
                                   "on partitioning the partitionable_graph's edges")

        # Partition edges according to vertex partitioning
        for src_sv in subgraph.subvertices:
            # For each out edge of the parent vertex...
            vertex = graph_to_subgraph_mapper.get_vertex_from_subvertex(src_sv)
            out_edges = graph.outgoing_edges_from_vertex(vertex)
            for edge in out_edges:
                # ... and create and store a new subedge for each postsubvertex
                post_vertex = edge.post_vertex
                post_subverts = \
                    graph_to_subgraph_mapper\
                    .get_subvertices_from_vertex(post_vertex)
                for dst_sv in post_subverts:
                    subedge = edge.create_subedge(src_sv, dst_sv)
                    subgraph.add_subedge(subedge)
                    graph_to_subgraph_mapper.add_subedge(subedge, edge)
            progress_bar.update()
        progress_bar.end()

    def _update_sdram_allocator(self, subvertex, sub_vertex_requirement,
                                machine):
        """private method for partitioners. Not to be called by front ends. \
        Updates the interal sdram tracker to account for a node being
        partitioned and "placed"

        :param subvertex: the subvertex thats been generated and placed
        :param sub_vertex_requirement: the sdram usage of the subvertex
        :param machine: the machine object
        :type subvertex: pacman.model.subgraph.subvertex.PartitionedVertex
        :type sub_vertex_requirement:
         pacman.model.resources.resource_container.ResoruceContainer
        :type machine: spinnMachine.machine.Machine
        :return None
        :rtype: None
        :raise PacmanPartitionException: when theres no space to put the \
        subvertex on the machine via the sdram tracker.
        """
        allocated = False
        for constraint in subvertex.constraints:
            if isinstance(constraint, PlacerChipAndCoreConstraint):
                usage = self._sdram_tracker.get_usage(constraint.x,
                                                      constraint.y)
                self._sdram_tracker.add_usage(
                    constraint.x, constraint.y,
                    usage + sub_vertex_requirement.sdram.get_value())
                allocated = True

        chip_index = 0
        chips = list(machine.chips)
        while not allocated and chip_index < len(chips):
            chip = chips[chip_index]
            key = (chip.x, chip.y)
            if not key in self._sdram_tracker.keys:
                self._sdram_tracker.add_usage(chip.x, chip.y,
                                              sub_vertex_requirement.
                                              sdram.get_value())
                allocated = True
            else:
                usage = self._sdram_tracker.get_usage(chip.x, chip.y)
                if (SDRAM.DEFAULT_SDRAM_BYTES - usage) >= \
                        sub_vertex_requirement.sdram.get_value():
                    sub_vert_usage = sub_vertex_requirement.sdram.get_value()
                    self._sdram_tracker.add_usage(chip.x, chip.y,
                                                  sub_vert_usage)
                    allocated = True
            chip_index += 1

        if not allocated:
            raise exceptions.PacmanPartitionException(
                "no space to put subvertex {}".format(subvertex.label))


    @staticmethod
    def _add_vertex_constraints_to_subvertex(subvert, vertex):
        """private method for partitioners, not to be used by front end
        updates subvertices with their assocaited vertex's constraints that are
        not partitioner based. As future algorithms only use the partitioned_graph,
        and partitionable constraints should not be needed from now on.
        """
        subclasses = AbstractPartitionerConstraint.__subclasses__()
        for constraint in vertex.constraints:
            if not type(constraint) in subclasses:
                subvert.add_constraint(constraint)