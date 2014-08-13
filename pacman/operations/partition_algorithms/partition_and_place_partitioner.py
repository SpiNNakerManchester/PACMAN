import logging
from pacman.model.constraints.abstract_partitioner_constraint import \
    AbstractPartitionerConstraint
from pacman.model.constraints.abstract_placer_constraint import \
    AbstractPlacerConstraint

from pacman.model.constraints.partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.constraints.placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from pacman.model.graph_mapper.graph_mapper import \
    GraphMapper
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman.operations.partition_algorithms.abstract_partition_algorithm\
    import AbstractPartitionAlgorithm
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.constraints.partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.operations.placer_algorithms.abstract_placer_algorithm import \
    AbstractPlacerAlgorithm
from pacman.utilities.progress_bar import ProgressBar
from pacman import exceptions
from pacman.utilities import utility_calls
from pacman.exceptions import PacmanPlaceException

logger = logging.getLogger(__name__)


class PartitionAndPlacePartitioner(AbstractPartitionAlgorithm):
    """ An basic algorithm that can partition a partitionable_graph based on atoms
    """

    def __init__(self, machine_time_step, runtime_in_machine_time_steps):
        """constructor to build a
pacman.operations.partition_algorithms.partition_and_place_partitioner.PartitionAndPlacePartitioner
        :param machine_time_step: the length of time in ms for a timer tic
        :param runtime_in_machine_time_steps: the number of timer tics expected \
               to occur due to the runtime
        :type machine_time_step: int
        :type runtime_in_machine_time_steps: long
        :return: a new
pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :rtype:
pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :raises None: does not raise any known exception
        """
        AbstractPartitionAlgorithm.__init__(self, machine_time_step,
                                            runtime_in_machine_time_steps)
        #add supported constraints
        self._supported_constraints.append(PartitionerMaximumSizeConstraint)
        self._supported_constraints.append(PartitionerSameSizeAsVertexConstraint)

        self._placer_algorithm = None
        self._placement_to_subvert_mapper = dict()
        self._complete_placements = Placements()

    def set_placer_algorithm(self, placer_algorithm, machine,
                             partitionable_graph):
        """ setter method for setting the placer algorithm

        :param placer_algorithm: the new placer algorithm
        :type placer_algorithm: implementation of \
pacman.operations.placer_algorithms.abstract_placer_algorithm.AbstractPlacerAlgorithm
        :param machine: the machine object
        :param partitionable_graph: the partitionable graph object
        :type machine: spinnmachine.machine.Machine object
        :type partitionable_graph: pacman.model.parit

        :return: None
        :rtype: None
        :raise PacmanConfigurationException: if the placer_algorithm is not a\
        implementation of \
pacman.operations.placer_algorithms.abstract_placer_algorithm.AbstractPlacerAlgorithm

        """
        if issubclass(placer_algorithm, AbstractPlacerAlgorithm):
            self._placer_algorithm = placer_algorithm(machine, partitionable_graph)
        else:
            raise exceptions.PacmanConfigurationException(
                "The placer algorithm submitted is not a recognised placer "
                "algorithm")

    #inherited from AbstractPartitionAlgorithm
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
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=graph.vertices,
            abstract_constraint_type=AbstractPartitionerConstraint,
            supported_constraints=self._supported_constraints)
        logger.info("* Running Partitioner and Placer as one *")

        # Load the machine and vertices objects from the dao
        vertices = graph.vertices
        subgraph = PartitionedGraph()
        graph_to_sub_graph_mapper = GraphMapper()

        #sort out vertex's by constraints
        vertices = utility_calls.sort_objects_by_constraint_authority(vertices)

        n_atoms = 0
        for vertex in vertices:
            n_atoms += vertex.n_atoms

        progress_bar = ProgressBar(n_atoms,
                                   "to partitioning the partitionable_graph's"
                                   " vertices")

        # Partition one vertex at a time
        for vertex in vertices:
            #check that the vertex hasnt already been partitioned
            subverts_from_vertex = \
                graph_to_sub_graph_mapper.get_subvertices_from_vertex(vertex)
            #if not, partition
            if subverts_from_vertex is None:
                self._partition_vertex(
                    vertex, subgraph, graph_to_sub_graph_mapper, machine, graph)
            progress_bar.update(vertex.n_atoms)
        progress_bar.end()

        #update constraints for subverts
        for subvert in subgraph.subvertices:
            if subvert in self._placement_to_subvert_mapper.keys():
                subvert.add_constraint(
                    self._placement_to_subvert_mapper[subvert])

        self._generate_sub_edges(subgraph, graph_to_sub_graph_mapper, graph)

        return subgraph, graph_to_sub_graph_mapper

    @property
    def complete_placements(self):
        """ property which returns the complete placements made by the
        parittioner

        :return: placements object
        :rtype: pacman.model.placements.placements.Placements
        :raise None: this method does not raise any known exceptions
        """
        return self._complete_placements

    def _partition_vertex(self, vertex, subgraph, graph_to_subgraph_mapper,
                          machine, graph):
        """private method (do not call from front ends) to partition a single \
        vertex. SHOULD NOT BE CALLED FROM OUTSIDE THIS CLASS

        :param vertex: the vertex to partition
        :param subgraph: the partitioned_graph to add subverts to
        :param graph_to_subgraph_mapper: the mappings object from partitionable_graph to \
        partitioned_graph which needs to be update with new subverts
        :param machine: the machien object
        :param graph: the partitionable_graph object
        :type graph: pacman.model.graph.partitionable_graph.PartitionableGraph
        :type machine: spinnmachine.machine.Machine object
        :type vertex: py:class:`pacman.model.partitionable_graph.vertex.AbstractConstrainedVertex`
        :type subgraph: py:class:`pacman.model.partitioned_graph.partitioned_graph.Subgraph`
        :type graph_to_subgraph_mapper:
        py:class:'pacman.modelgraph_subgraph_mapper.graph_mapper.GraphMapper'
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanPartitionException: if the extra vertex\
         for partitioning identically has a different number of atoms than its
         \counterpart.
        """

        partiton_together_vertices = \
            self._locate_vertices_to_partition_now(vertex)

        # Prepare for partitioning, getting information
        #todo not needed till we get to random distrubtions
        partition_data_objects = None

        #locate max atoms per core
        possible_max_atoms = list()
        for vertex in partiton_together_vertices:
            max_atom_constraints =\
                utility_calls.locate_constraints_of_type(
                    vertex.constraints, PartitionerMaximumSizeConstraint)
            for constraint in max_atom_constraints:
                possible_max_atoms.append(constraint.size)
        max_atoms_per_core = min(possible_max_atoms)

        #partition by atoms
        self._partition_by_atoms(partiton_together_vertices, vertex.n_atoms,
                                 max_atoms_per_core, partition_data_objects,
                                 subgraph, graph, graph_to_subgraph_mapper,
                                 machine)

    def _partition_by_atoms(self, vertices, n_atoms, max_atoms_per_core,
                            partition_data_objects, subgraph, graph,
                            graph_to_subgraph_mapper, machine):
        """(private method, do not call from outside partitioner) \
        tries to partition subvertices on how many atoms it can fit on\
        each subvert SHOULD NOT BE CALLED FROM OUTSIDE THIS CLASS
        
        :param vertices: the vertexes that need to be partitoned at the same \
        time
        :param n_atoms: the atoms of the first vertex
        :param max_atoms_per_core: the min max atoms from all the vertexes \
        considered that have max_atom constraints
        :param partition_data_objects: the parittion objects for memory \
        estiamtes
        :param subgraph: the partitioned_graph of the propblem space to put subverts in
        :param graph_to_subgraph_mapper: the mapper from partitionable_graph to partitioned_graph
        :param machine: the machien object
        :param graph: the partitionable_graph object
        :type graph: pacman.model.graph.partitionable_graph.PartitionableGraph
        :type machine: spinnmachine.machine.Machine object
        :type vertices: iterable list of pacman.model.partitionable_graph.vertex.AbstractConstrainedVertex
        :type n_atoms: int
        :type max_atoms_per_core: int
        :type partition_data_objects: iterable lsit of partitionable obejcts
        :type subgraph: pacman.model.subgraph.subgraph.Subgraph
        :type graph_to_subgraph_mapper:
py:class:'pacman.modelgraph_subgraph_mapper.graph_mapper.GraphMapper'
        """
        n_atoms_placed = 0
        while n_atoms_placed < n_atoms:

            #logger.debug("Maximum available resources for "
            #             "partitioning: {}".format(resources))

            lo_atom = n_atoms_placed
            hi_atom = lo_atom + max_atoms_per_core - 1
            if hi_atom >= n_atoms:
                hi_atom = n_atoms - 1

            # Scale down the number of atoms to fit the available resources
            used_placements, hi_atom = self._scale_down_resources(
                lo_atom, hi_atom, vertices, machine, partition_data_objects,
                max_atoms_per_core, graph)

            # Update where we are
            n_atoms_placed = hi_atom + 1

            # Create the subvertices and placements
            for (vertex, _, x, y, p, used_resources, _) in used_placements:
                subvertex = PartitionedVertex(lo_atom, hi_atom,
                                              "subvertex with low atoms {} and "
                                              "hi atoms {} for vertex {}"
                                              .format(lo_atom, hi_atom, 
                                                      vertex.label))
                self._placement_to_subvert_mapper[subvertex] = \
                    PlacerChipAndCoreConstraint(x, y, p)
                #update objects
                subgraph.add_subvertex(subvertex)
                graph_to_subgraph_mapper.add_subvertex(subvertex, vertex)
                self._update_sdram_allocator(vertex, used_resources, machine)
                self._complete_placements.add_placement(
                    Placement(x=x, y=y, p=p, subvertex=subvertex))

    #todo need to fix for random distributions
    # noinspection PyUnusedLocal
    def _scale_down_resources(self, lo_atom, hi_atom, vertices, machine,
                              partition_data_objects, max_atoms_per_core,
                              graph):
        """reduces the number of atoms on a core so that it fits within the
        resources available   SHOULD NOT BE CALLED FROM OUTSIDE THIS CLASS

        :param lo_atom: the number of atoms already partitioned
        :param hi_atom: the total number of atoms to place for this vertex
        :param vertices: the vertexes that need to be partitioned at the same \
        time
        :param partition_data_objects: the partition objects for memory \
        estimates
        :param max_atoms_per_core: the min max atoms from all the vertexes \
        considered that have max_atom constraints
        :param graph: the partitionable_graph object
        :param machine: the machine object
        :type graph: pacman.model.graph.partitionable_graph.PartitionableGraph
        :type machine: spinnmachine.machine.Machine object
        :type lo_atom: int
        :type hi_atom: int
        :type vertices: iterable list of pacman.model.partitionable_graph.vertex.AbstractConstrainedVertex
        :type partition_data_objects: iterable list of partitionable objects
        :type max_atoms_per_core: int
        :return: the list of placements made by this method and the new amount \
        of atoms partitioned
        :rtype: iterable of tuples and a int
        :raise PacmanPartitionException: when the vertex cannot be partitioned
        """
        used_placements = list()
        # Find the number of atoms that will fit in each vertex given the
        # resources available
        min_hi_atom = hi_atom
        for i in range(len(vertices)):
            vertex = vertices[i]
            # TODO -> Needs to be updated for random distributions
            partition_data_object = None
            #get max resources available on machine
            resources = self._get_maximum_resources_per_processor(
                vertex_constraints=vertex.constraints, machine=machine)
            #get resources for vertexes
            used_resources = vertex.get_resources_used_by_atoms(
                lo_atom, hi_atom, graph.incoming_edges_to_vertex(vertex))
            
            #figure max ratio
            ratio = self._find_max_ratio(used_resources, resources)

            while ratio > 1.0 and hi_atom >= lo_atom:

                # Scale the resources by the ratio
                old_n_atoms = (hi_atom - lo_atom) + 1
                new_n_atoms = int(float(old_n_atoms) / ratio)

                # Avoid looping
                if old_n_atoms == new_n_atoms:
                    new_n_atoms -= 1
                else:
                    # Subtract a tenth of the difference between the old
                    # and new
                    new_n_atoms -= int((old_n_atoms - new_n_atoms) / 10.0)

                # Find the new resource usage
                hi_atom = lo_atom + new_n_atoms - 1
                used_resources = \
                    vertex.get_resources_used_by_atoms(
                        lo_atom, hi_atom,
                        graph.incoming_edges_to_vertex(vertex))
                ratio = self._find_max_ratio(used_resources, resources)

            # If we couldn't partition, raise and exception
            if hi_atom < lo_atom:
                raise exceptions.PacmanPartitionException(
                    "AbstractConstrainedVertex {} could not be partitioned".format(vertex.label))

            # Try to scale up until just below the resource usage
            used_resources, hi_atom = self._scale_up_resource_usage(
                used_resources, hi_atom, lo_atom, max_atoms_per_core, vertex,
                partition_data_object, resources, ratio)

            # If this hi_atom is smaller than the current, minimum update the
            # other placements to use (hopefully) less resources
            if hi_atom < min_hi_atom:
                min_hi_atom = hi_atom
                #TODO needs to be tied in (old code resulted in no loops, so new code has omitted the code for future look ats

            # Place the vertex
            placement_constraints = \
                utility_calls.locate_constraints_of_type(
                    vertex.constraints, AbstractPlacerConstraint)

            if self._placer_algorithm is not None:
                # noinspection PyProtectedMember
                x, y, p = \
                    self._placer_algorithm._try_to_place(placement_constraints,
                                                         resources, "",
                                                         self._complete_placements)
                used_placements.append((vertex, partition_data_object, x, y, p,
                                        used_resources, resources))
            else:
                raise PacmanPlaceException("No placer algorithm selected")

        return used_placements, min_hi_atom

    def _scale_up_resource_usage(
            self, used_resources, hi_atom, lo_atom, max_atoms_per_core, vertex,
            partition_data_object, resources, ratio):
        """tries to push the number of atoms into a subvertex as it can
         with the estimates SHOULD NOT BE CALLED FROM OUTSIDE THIS CLASS

        :param lo_atom: the number of atoms already partitioned
        :param hi_atom: the total number of atoms to place for this vertex
        :param vertex: the vertexes to scale up the num atoms per core for
        :param partition_data_object: the partition object for memory \
        estimates
        :param max_atoms_per_core: the min max atoms from all the vertexes \
        considered that have max_atom constraints
        :param used_resources: the resources used by the machine so far
        :param resources: the resource estimate for the vertex for a given\
        number of atoms
        :param ratio: the ratio between max atoms and availalbe resources
        :type lo_atom: int
        :type hi_atom: int
        :type vertex: pacman.model.graph.vertex.AbstractConstrainedVertex
        :type partition_data_object: partitionable object
        :type max_atoms_per_core: int
        :type used_resources: pacman.model.resources.resource.Resource
        :type resources: pacman.model.resources.resource.Resource
        :type ratio: int
        :return: the list of placements made by this method and the new amount \
        of atoms partitioned
        :rtype: iterable of tuples and a int
        :raise PacmanPartitionException: when the vertex cannot be partitioned
        """

        previous_used_resources = used_resources
        previous_hi_atom = hi_atom
        while ((ratio < 1.0) and ((hi_atom + 1) < vertex.n_atoms)
                and ((hi_atom - lo_atom + 2) < max_atoms_per_core)):

            #logger.debug("Scaling up - Current subvertex from"
            #    " %d to %d of %d, ratio = %f, resources = %s" % (lo_atom,
            #             hi_atom, no_atoms, ratio, used_resources))

            previous_hi_atom = hi_atom
            hi_atom += 1

            # Find the new resource usage
            previous_used_resources = used_resources
            used_resources = \
                vertex.get_resources_for_atoms(
                    lo_atom, hi_atom, self._runtime_in_machine_time_steps,
                    self._machine_time_step, partition_data_object)
            ratio = self._find_max_ratio(used_resources, resources)
        return previous_used_resources, previous_hi_atom

    @staticmethod
    def _get_max_atoms_per_core(vertices):
        """ helper method for finding the max atoms per core for a collection \
        of vertices SHOULD NOT BE CALLED FROM OUTSIDE THIS CLASS

        :param vertices: a iterable list of vertex
        :type vertices: iterable of pacman.model.partitionable_graph.vertex.AbstractConstrainedVertex
        :return: the minimum level of max atoms from all constraints
        :rtype: int
        :raise None: this method does not raise any known exceptions
        """
        max_atoms_per_core = 0
        for v in vertices:
            max_for_vertex = v.get_maximum_atoms_per_core()

            # If there is no maximum, the maximum is the number of atoms
            if max_for_vertex is None:
                max_for_vertex = v.atoms

            # Override the maximum with any custom maximum
            if v.custom_max_atoms_per_core is not None:
                max_for_vertex = v.custom_max_atoms_per_core

            max_atoms_per_core = max(max_atoms_per_core, max_for_vertex)
        return max_atoms_per_core

    @staticmethod
    def _find_max_ratio(resources, max_resources):
        """ helper method for finding the max ratio for a resources \
        SHOULD NOT BE CALLED FROM OUTSIDE THIS CLASS

        :param resources: the resources used by the vertex
        :param max_resources: the max resources available from the machine
        :type max_resources: pacman.model.resources.resource.Resource
        :type resources:pacman.model.resources.resource.Resource
        :return: the best available ratio of resources
        :rtype: int
        :raise None: this method does not raise any known exceptions

        """
        if resources.cpu.get_value() == 0 or max_resources.cpu.get_value() == 0:
            cpu_ratio = 0
        else:
            cpu_ratio = \
                (float(resources.cpu.get_value()) /
                 float(max_resources.cpu.get_value()))
        if (resources.dtcm.get_value() == 0
           or max_resources.dtcm.get_value() == 0):
            dtcm_ratio = 0
        else:
            dtcm_ratio = (float(resources.dtcm.get_value()) /
                          float(max_resources.dtcm.get_value()))
        if (resources.sdram.get_value() == 0
           or max_resources.sdram.get_value() == 0):
            sdram_ratio = 0
        else:
            sdram_ratio = (float(resources.sdram.get_value()) /
                           float(max_resources.sdram.get_value()))
        return max((cpu_ratio, dtcm_ratio, sdram_ratio))

    @staticmethod
    def _locate_vertices_to_partition_now(vertex):
        """ Locates any other vertices that need to be partitioned in the same\
         way SHOULD NOT BE CALLED FROM OUTSIDE THIS CLASS

        :param vertex: the vertex that is currently being partitioned
        :type vertex: pacman.model.graph.vertex.AbstractConstrainedVertex
        :return: iterable of vertexes that need to be partitioned in the same \
        way
        :rtype: iterable of pacman.model.partitionable_graph.vertex.AbstractConstrainedVertex
        :raise PacmanPartitionException: if the vertices that need to be \
        partitioned in the same way have different numbers of atoms
        """
        partiton_together_vertices = list()
        partiton_together_vertices.append(vertex)
        same_size_vertex_constraints = \
            utility_calls.locate_constraints_of_type(
                vertex.constraints, PartitionerSameSizeAsVertexConstraint)
        for constraint in same_size_vertex_constraints:
            if constraint.vertex.n_atoms != vertex.n_atoms:
                raise exceptions.PacmanPartitionException(
                    "A vertex and its partition-dependent vertices must "
                    "have the same number of atoms")
            else:
                partiton_together_vertices.append(constraint.vertex)
        return partiton_together_vertices