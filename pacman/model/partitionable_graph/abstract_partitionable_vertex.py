from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.partitionable_graph.abstract_constrained_vertex \
    import AbstractConstrainedVertex
from pacman.model.constraints.partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.model.resources.resource_container import ResourceContainer

import sys
import logging

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPartitionableVertex(AbstractConstrainedVertex):
    """the abstract partitionable vertex is a type of vertex that is recongised
    by the pacman partitioners. Due to this, it is recommended that front end
    developers inhirrit from this class when creating new neural models.

    this class enforces methods for supporting the partitioning of a vertex
    based on cost metrics.
    """

    def __init__(self, n_atoms, label, max_atoms_per_core, constraints=None):
        """constructor for the abstract partitionable vertex.
        :param n_atoms: the number of atoms for the vertex
        :param label: the label of the vertex
        :param max_atoms_per_core: the max atoms that cna be supported by a\
         core. Note that this is trnaslated into a partitioner max size
         constraint
         :param constraints: any extra constranits to be added to this vertex.
         :type n_atoms: int
         :type label: str
         :type max_atoms_per_core: int
         :type constraints: iterable list

         :return: a new \
         pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex\
         object

         :rtype:
         pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex

         :raise None: this method does not raise any exceptions


        """
        AbstractConstrainedVertex.__init__(self, label, constraints)
        if n_atoms < 1:
            raise PacmanInvalidParameterException(
                "n_atoms", str(n_atoms),
                "Must be at least one atom in the vertex")

        self._n_atoms = n_atoms
        #add the max atom per core constraint
        max_atom_per_core_constraint = \
            PartitionerMaximumSizeConstraint(max_atoms_per_core)
        self.add_constraint(max_atom_per_core_constraint)

    @abstractmethod
    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        """method for calculating sdram usage of a collection of atoms

        :param lo_atom: the low atom value to calcualte sdram usage from
        :param hi_atom: the high atom value to calculate sdram usage from
        :param vertex_in_edges: the incomign edges of this vertex for
        calcualting sdram usage
        :type lo_atom: int
        :type hi_atom: int
        :type vertex_in_edges: iterable of edges
        :return a int value for sdram usage
        :rtype: int
        :raise None: this emthod raises no known exception
        """

    @abstractmethod
    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        """method for caulculating dtcm usage for a coltection of atoms

        :param lo_atom: the low atom value to calcualte sdram usage from
        :param hi_atom: the high atom value to calculate sdram usage from
        :type lo_atom: int
        :type hi_atom: int
        :return a int value for sdram usage
        :rtype: int
        :raise None: this emthod raises no known exception
        """

    @abstractmethod
    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        """Gets the CPU requirements for a range of atoms

        :param lo_atom: the low atom value to calcualte sdram usage from
        :param hi_atom: the high atom value to calculate sdram usage from
        :type lo_atom: int
        :type hi_atom: int
        :return a int value for sdram usage
        :rtype: int
        :raise None: this emthod raises no known exception
        """

    @abstractmethod
    def model_name(self):
        """method to be impliemnted by inhirrted objects. This lists the type of
        model is being used in a human friednly form

        :return: a string rep of the model
        :rtype: str
        :raise None: does not raise any knwon exception
        """

    def get_resources_used_by_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        """returns the separate resource requirements for a range of atoms
        in a resource object with a assumption object that tracks any
        assumptions made by the model when estimating resource requirement

        :param lo_atom: the low value of atoms to calculate resources from
        :param hi_atom: the high value of atoms to calculate resources from.
        :param vertex_in_edges: the edges going into this vertex.
        :type lo_atom: int
        :type hi_atom: int
        :type vertex_in_edges: list of edges
        :return: a Resource container that contains a CPUCyclesPerTickResource,
        DTCMResource and SDRAMResource
        :rtype: ResourceContainer
        :raise None: this method does not raise any known exception
        """
        cpu_cycles = self.get_cpu_usage_for_atoms(lo_atom, hi_atom)
        dtcm_requirement = self.get_dtcm_usage_for_atoms(lo_atom, hi_atom)
        sdram_requirement = \
            self.get_sdram_usage_for_atoms(lo_atom, hi_atom, vertex_in_edges)
        # noinspection PyTypeChecker
        resources = ResourceContainer(cpu=CPUCyclesPerTickResource(cpu_cycles),
                                      dtcm=DTCMResource(dtcm_requirement),
                                      sdram=SDRAMResource(sdram_requirement))
        return resources

    def get_max_atoms_per_core(self):
        """returns the max atom per core possible given the constraints set on
        this vertex

        :return: the minimum value of a the collection of max_atom constraints \
        currently instilled on this vertex. It is expected that every vertex
        has at least one value here, as a default should always have been
        entered during construction
        :rtype: int
        :raise None: this method does not raise any known exception
        """
        current_found_max_atoms_per_core = sys.maxint
        for constraint in self.constraints:
            if (isinstance(constraint, PartitionerMaximumSizeConstraint) and
                    constraint.size <= current_found_max_atoms_per_core):
                current_found_max_atoms_per_core = constraint.size
        return current_found_max_atoms_per_core

    def create_subvertex(self, resources_required, label=None,
                         additional_constraints=list()):
        """ Creates a subvertex of this vertex.  Can be overridden in vertex\
            subclasses to create an subvertex instance that contains detailed\
            information

        :param label: The label to give the subvertex.  If not given, and the\
                    vertex has no label, no label will be given to the\
                    subvertex.  If not given and the vertex has a label, a\
                    default label will be given to the subvertex
        :type label: str
        :param additional_constraints: An iterable of constraints from the\
                    subvertex over-and-above those of the vertex
        :type additional_constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If lo_atom or hi_atom are out of range
                    * If one of the constraints is invalid
        """
        # Combine the AbstractConstrainedVertex and PartitionedVertex constraints
        additional_constraints.extend(self.constraints)

        return PartitionedVertex(label=label,
                                 resources_required=resources_required,
                                 constraints=additional_constraints)

    @property
    def n_atoms(self):
        """ The number of atoms in the vertex

        :return: The number of atoms
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._n_atoms