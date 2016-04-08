from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.abstract_classes.abstract_constrained_vertex \
    import AbstractConstrainedVertex
from pacman.model.constraints.partitioner_constraints\
    .partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.fixed_route_packets_per_tic import \
    FixedRoutePacketsPerTic
from pacman.model.resources.multi_cast_no_payload_packets_per_tic import \
    MultiCastNoPayloadPacketsPerTic
from pacman.model.resources.multi_cast_payload_packets_per_tic import \
    MultiCastPayloadPacketsPerTic
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource


from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
import logging

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPartitionableVertex(AbstractConstrainedVertex):
    """ The abstract partitionable vertex is a type of vertex that is
        recognised by the pacman partitioners. Due to this, it is recommended
        that front end developers inherit from this class when creating new
        neural models.

        This class enforces methods for supporting the partitioning of a vertex
        based on cost metrics.
    """

    def __init__(self, n_atoms, label, max_atoms_per_core, constraints=None):
        """

        :param n_atoms: the number of atoms for the vertex
        :type n_atoms: int
        :param label: the label of the vertex
        :type label: str
        :param max_atoms_per_core: the max atoms that can be supported by a \
                    core. Note that this is translated into a partitioner max \
                    size constraint
        :type max_atoms_per_core: int
        :param constraints: any extra constraints to be added to this vertex.
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraints.abstract_constraint.AbstractConstraint`
        """
        AbstractConstrainedVertex.__init__(self, label, constraints)
        if n_atoms < 1:
            raise PacmanInvalidParameterException(
                "n_atoms", str(n_atoms),
                "Must be at least one atom in the vertex")

        self._n_atoms = n_atoms

        # add the max atom per core constraint
        max_atom_per_core_constraint = \
            PartitionerMaximumSizeConstraint(max_atoms_per_core)
        self.add_constraint(max_atom_per_core_constraint)

    @abstractmethod
    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """ Get the SDRAM usage of a collection of atoms

        :param vertex_slice: the vertex vertex_slice which determines\
                    which atoms are being represented by this vertex
        :param graph: A reference to the graph containing this vertex
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return a int value for SDRAM usage
        :rtype: int
        :raise None: this method raises no known exception
        """

    @abstractmethod
    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """ Get the DTCM usage for a collection of atoms

        :param vertex_slice: the vertex vertex_slice which determines\
                    which atoms are being represented by this vertex
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return a int value for SDRAM usage
        :rtype: int
        :raise None: this method raises no known exception
        """

    @abstractmethod
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """ Get the CPU cycles per timestep for a range of atoms

        :param vertex_slice: the vertex vertex_slice which determines\
                    which atoms are being represented by this vertex
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return a int value for SDRAM usage
        :rtype: int
        :raise None: this method raises no known exception
        """

    @abstractmethod
    def get_multi_cast_payload_packets_per_tick_requirement(
            self, vertex_slice, graph):
        """ Get the number of multicast packets with payloads per timestep
        for a range of atoms

        :param vertex_slice: the vertex vertex_slice which determines\
                    which atoms are being represented by this vertex
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return a int value for SDRAM usage
        :rtype: int
        :raise None: this method raises no known exception
        """

    @abstractmethod
    def get_multi_cast_no_payload_packets_per_tick_requirement(
            self, vertex_slice, graph):
        """ Get the number of multicast packets without payloads per timestep
        for a range of atoms

        :param vertex_slice: the vertex vertex_slice which determines\
                    which atoms are being represented by this vertex
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return a int value for SDRAM usage
        :rtype: int
        :raise None: this method raises no known exception
        """

    @abstractmethod
    def get_fixed_route_packets_per_tick_requirement(self, vertex_slice, graph):
        """ Get the number of fixed route packets per timestep for a range of
         atoms

        :param vertex_slice: the vertex vertex_slice which determines\
                    which atoms are being represented by this vertex
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return a int value for SDRAM usage
        :rtype: int
        :raise None: this method raises no known exception
        """

    @abstractmethod
    def model_name(self):
        """ Get the type of model is being used in a human readable form

        :return: the name of the model
        :rtype: str
        :raise None: does not raise any known exception
        """

    def get_resources_used_by_atoms(self, vertex_slice, graph):
        """ Get the separate resource requirements for a range of atoms

        :param vertex_slice: the low value of atoms to calculate resources from
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return: a Resource container that contains a \
                    CPUCyclesPerTickResource, DTCMResource and SDRAMResource
        :rtype: ResourceContainer
        :raise None: this method does not raise any known exception
        """
        cpu_cycles = self.get_cpu_usage_for_atoms(vertex_slice, graph)
        dtcm_requirement = self.get_dtcm_usage_for_atoms(vertex_slice, graph)
        sdram_requirement = self.get_sdram_usage_for_atoms(vertex_slice, graph)
        multi_cast_payload_packets_per_tick_requirement = \
            self.get_multi_cast_payload_packets_per_tick_requirement(
                vertex_slice, graph)
        multi_cast_no_payload_packets_per_tick_requirement = \
            self.get_multi_cast_no_payload_packets_per_tick_requirement(
                vertex_slice, graph)
        fixed_route_packets_per_tick_requirement = \
            self.get_fixed_route_packets_per_tick_requirement(
                vertex_slice, graph)

        # noinspection PyTypeChecker
        resources = ResourceContainer(
            cpu=CPUCyclesPerTickResource(cpu_cycles),
            dtcm=DTCMResource(dtcm_requirement),
            sdram=SDRAMResource(sdram_requirement),
            multicast_no_payload_packets_per_tic=
            MultiCastNoPayloadPacketsPerTic(
                multi_cast_no_payload_packets_per_tick_requirement),
            multicast_payload_packets_per_tic=
            MultiCastPayloadPacketsPerTic(
                multi_cast_payload_packets_per_tick_requirement),
            fixed_route_packets_per_tic=FixedRoutePacketsPerTic(
                fixed_route_packets_per_tick_requirement))
        return resources

    def get_max_atoms_per_core(self):
        """ Get the maximum number of atoms that can be run on a single core \
            given the constraints set on this vertex

        :return: The maximum number of atoms that can be run on a core
        :rtype: int
        :raise None: this method does not raise any known exception
        """
        current_found_max_atoms_per_core = self._n_atoms
        for constraint in self.constraints:
            if (isinstance(constraint, PartitionerMaximumSizeConstraint) and
                    constraint.size <= current_found_max_atoms_per_core):
                current_found_max_atoms_per_core = constraint.size
        return current_found_max_atoms_per_core

    def create_subvertex(self, vertex_slice, resources_required, label=None,
                         constraints=None):
        """ Create a subvertex of this vertex.  Can be overridden in vertex\
            subclasses to create an subvertex instance that contains detailed\
            information

        :param label: The label to give the subvertex.  If not given, and the\
                    vertex has no label, no label will be given to the\
                    subvertex.  If not given and the vertex has a label, a\
                    default label will be given to the subvertex
        :type label: str
        :param resources_required: the SDRAM, DTCM, and ITCM used by this\
                    partitioned vertex
        :type resources_required:\
                    :py:class:`pacman.model.resources_resource_container.ResourceContainer`
        :param vertex_slice: the slice of the partitionable vertex that this\
                    partitioned vertex will cover
        :type vertex_slice: pacman.model.graph_mapper.vertex_slice.VertexSlice
        :param constraints: An iterable of constraints for the subvertex.\
                    These are generated by the partitioner from the vertex\
                    constraints.
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If lo_atom or hi_atom are out of range
                    * If one of the constraints is invalid
        """
        return PartitionedVertex(label=label,
                                 resources_required=resources_required,
                                 constraints=constraints)

    @property
    def n_atoms(self):
        """ The number of atoms in the vertex

        :return: The number of atoms
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._n_atoms
