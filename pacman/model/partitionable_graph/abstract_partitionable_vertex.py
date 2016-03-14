from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.abstract_classes.abstract_constrained_vertex \
    import AbstractConstrainedVertex
from pacman.model.constraints.partitioner_constraints\
    .partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.model.resources.resource_container import ResourceContainer


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
        :param max_atoms_per_core: the max atoms that cna be supported by a \
                    core. Note that this is translated into a partitioner max \
                    size constraint
        :type max_atoms_per_core: int
        :param constraints: any extra constraints to be added to this vertex.
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_contraints.abstract_constraint.AbstractConstraint`
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
    def get_static_sdram_usage_for_atoms(self, vertex_slice, graph):
        """ Get the SDRAM usage of a collection of atoms

        :param vertex_slice: the vertex vertex_slice which determines\
                    which atoms are being represented by this vertex
        :param graph: A reference to the graph containing this vertex
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return a int value for sdram usage
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
        :return a int value for sdram usage
        :rtype: int
        :raise None: this emthod raises no known exception
        """

    @abstractmethod
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """ Get the CPU cycles per timestep for a range of atoms

        :param vertex_slice: the vertex vertex_slice which determines\
                    which atoms are being represented by this vertex
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return a int value for sdram usage
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

    def get_resources_used_by_atoms(
            self, vertex_slice, graph):
        """ Get the separate resource requirements for a range of atoms

        :param vertex_slice: the low value of atoms to calculate resources from
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return: a Resource container that contains a \
                    CPUCyclesPerTickResource, DTCMResource and SDRAMResource
        :rtype: ResourceContainer
        :raise None: this method does not raise any known exception
        """

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
