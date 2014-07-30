from pacman.model.graph_subgraph_mapper.graph_subgraph_mapper import \
    GraphSubgraphMapper
from pacman.operations.partition_algorithms.abstract_partition_algorithm\
    import AbstractPartitionAlgorithm
from pacman.model.subgraph.subgraph import Subgraph
from pacman.model.subgraph.subvertex import Subvertex
from pacman.model.constraints.partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.progress_bar import ProgressBar
from spinn_machine.sdram import SDRAM
import logging

logger = logging.getLogger(__name__)


class PartitionAndPlacePartitioner(AbstractPartitionAlgorithm):
    """ An basic algorithm that can partition a graph based on atoms
    """

    def __init__(self, machine_time_step, runtime_in_machine_time_steps):
        """constructor to build a
        pacman.operations.partition_algorithms.partition_and_place_partitioner.PartitionAndPlacePartitioner
        :param machine_time_step: the length of tiem in ms for a timer tic
        :param runtime_in_machine_time_steps: the number of timer tics expected \
               to occur due to the runtime
        :type machine_time_step: int
        :type runtime_in_machine_time_steps: long
        :return: a new pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :rtype: pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :raises None: does not raise any known expection
        """
        AbstractPartitionAlgorithm.__init__(self, machine_time_step,
                                            runtime_in_machine_time_steps)
        self._placer_algorithum = None

    def set_placer_algorithum(self, placer_algorithum):
        self._placer_algorithum = placer_algorithum

    #inherited from AbstractPartitionAlgorithm
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
        self._check_can_support_partitioner_constraints(graph)
        logger.info("* Running Partitioner and Placer as one *")

        # Load the machine and vertices objects from the dao
        vertices = graph.vertices
        subgraph = Subgraph()
        graph_to_sub_graph_mapper = GraphSubgraphMapper()

        #sort out vertex's by constraints
        sort = lambda each_vertex: each_vertex.constraints.placement_cardinality
        vertices = sorted(vertices, key=sort, reverse=True)

        n_atoms = 0
        for vertex in vertices:
            n_atoms += vertex.atoms

        progress_bar = ProgressBar(n_atoms,
                                   "to partitioning the graph's vertices")

        # Partition one vertex at a time
        for vertex in vertices:
            self.partition_vertex(vertex, subgraph, graph_to_sub_graph_mapper)
            progress_bar.update()
        progress_bar.end()

        self.generate_sub_edges(subgraph, graph_to_sub_graph_mapper, graph)

        return subgraph, graph_to_sub_graph_mapper

    def partition_vertex(self, vertex, subgraph, graph_to_subgraph_mapper):

        vertices = list()
        vertices.append(vertex)
        extra_vertices = vertex.get_partition_dependent_vertices()
        if extra_vertices is not None:
            for v in extra_vertices:
                if v.atoms != vertex.atoms:
                    raise Exception("A vertex and its partition-dependent"
                            + " vertices must have the same number of atoms")
                vertices.append(v)


        # Prepare for partitioning, getting information
        partition_data_objects = [v.get_partition_data_object()
                for v in vertices]
        max_atoms_per_core = self.get_max_atoms_per_core(vertices)

        self.partition_by_atoms(vertices, placer, vertex.atoms,
                max_atoms_per_core, no_machine_time_steps, machine_time_step_us,
                partition_data_objects, subvertices, placements)

    def partition_by_atoms(self, vertices, placer, n_atoms,
            max_atoms_per_core, no_machine_time_steps, machine_time_step_us,
            partition_data_objects, subvertices, placements):
        '''
        tries to partition subvertexes on how many atoms it can fit on
        each subvert
        '''
        n_atoms_placed = 0
        while n_atoms_placed < n_atoms:

            #logger.debug("Maximum available resources for "
            #             "partitioning: {}".format(resources))

            lo_atom = n_atoms_placed
            hi_atom = lo_atom + max_atoms_per_core - 1
            if hi_atom >= n_atoms:
                hi_atom = n_atoms - 1

            # Scale down the number of atoms to fit the available resources
            used_placements, hi_atom = self.scale_down_resources(
                    lo_atom, hi_atom, vertices,
                    no_machine_time_steps, machine_time_step_us,
                    partition_data_objects, placer,
                    max_atoms_per_core)

            # Update where we are
            n_atoms_placed = hi_atom + 1

            # Create the subvertices and placements
            for (vertex, _, x, y, p, used_resources, _) in used_placements:

                subvertex = graph.Subvertex(vertex, lo_atom, hi_atom,
                        used_resources)
                processor = self.dao.machine.get_processor(x, y, p)
                placement = lib_map.Placement(subvertex, processor)

                subvertices.append(subvertex)
                placements.append(placement)

            no_atoms_this_placement = (hi_atom - lo_atom) + 1
            self.progress.update(no_atoms_this_placement)

    def scale_down_resources(self, lo_atom, hi_atom, vertices,
            no_machine_time_steps, machine_time_step_us,
            partition_data_objects, placer, max_atoms_per_core):
        '''
        reduces the number of atoms on a core so that it fits within the
        resoruces avilable
        '''

        # Find the number of atoms that will fit in each vertex given the
        # resources available
        used_placements = list()
        min_hi_atom = hi_atom
        for i in range(len(vertices)):
            vertex = vertices[i]
            partition_data_object = partition_data_objects[i]

            resources = placer.get_maximum_resources(vertex.constraints)
            used_resources = vertex.get_resources_for_atoms(lo_atom, hi_atom,
                no_machine_time_steps, machine_time_step_us,
                partition_data_object)
            ratio = self.find_max_ratio(used_resources, resources)

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
                    vertex.get_resources_for_atoms(lo_atom, hi_atom,
                                                   no_machine_time_steps,
                                                   machine_time_step_us,
                                                   partition_data_object)
                ratio = self.find_max_ratio(used_resources, resources)

            # If we couldn't partition, raise and exception
            if hi_atom < lo_atom:
                raise Exception("Vertex {} could not be partitioned".format(
                        vertex.label))

            # Try to scale up until just below the resource usage
            used_resources, hi_atom = self.scale_up_resource_usage(
                    used_resources, hi_atom, lo_atom,
                    max_atoms_per_core, vertex, no_machine_time_steps,
                    machine_time_step_us, partition_data_object, resources,
                    ratio)

            # If this hi_atom is smaller than the current, minimum update the
            # other placements to use (hopefully) less resources
            if hi_atom < min_hi_atom:
                min_hi_atom = hi_atom
                new_used_placements = list()
                for (v, part_obj, x, y, p, v_resources, resources) in used_placements:
                    placer.unplace_subvertex(x, y, p, v_resources)
                    new_resources = v.get_resources_for_atoms(lo_atom,
                            min_hi_atom, no_machine_time_steps,
                            machine_time_step_us, part_obj)
                    (new_x, new_y, new_p) = placer.place_subvertex(
                            new_resources, v.constraints)
                    new_used_placements.append(v, part_obj, new_x, new_y, new_p,
                            new_resources, resources)
                used_placements = new_used_placements

            # Place the vertex
            x, y, p = placer.place_subvertex(used_resources,
                    vertex.constraints)
            used_placements.append((vertex, partition_data_object, x, y, p,
                    used_resources, resources))

        return used_placements, min_hi_atom


    def scale_up_resource_usage(self, used_resources, hi_atom, lo_atom,
                        max_atoms_per_core, vertex, no_machine_time_steps,
                        machine_time_step_us, partition_data_object, resources,
                        ratio):
        '''
        tries to psuh the number of atoms into a subvertex as it can
         with the estimates
        '''

        previous_used_resources = used_resources
        previous_hi_atom = hi_atom
        while ((ratio < 1.0) and ((hi_atom + 1) < vertex.atoms)
                and ((hi_atom - lo_atom + 2) < max_atoms_per_core)):

            #logger.debug("Scaling up - Current subvertex from"
            #    " %d to %d of %d, ratio = %f, resources = %s" % (lo_atom,
            #             hi_atom, no_atoms, ratio, used_resources))

            previous_hi_atom = hi_atom
            hi_atom += 1

            # Find the new resource usage
            previous_used_resources = used_resources
            used_resources = \
                vertex.get_resources_for_atoms(lo_atom, hi_atom,
                                               no_machine_time_steps,
                                               machine_time_step_us,
                                               partition_data_object)
            ratio = self.find_max_ratio(used_resources, resources)
        return previous_used_resources, previous_hi_atom

    def get_max_atoms_per_core(self, vertices):

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

    def find_max_ratio(self, resources, max_resources):
        '''
        helper method for finding the max ratio for a resoruces
        '''
        cpu_ratio = (float(resources.clock_ticks)
                / float(max_resources.clock_ticks))
        dtcm_ratio = (float(resources.dtcm) / float(max_resources.dtcm))
        sdram_ratio = (float(resources.sdram) / float(max_resources.sdram))
        return max((cpu_ratio, dtcm_ratio, sdram_ratio))



