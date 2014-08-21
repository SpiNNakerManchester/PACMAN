from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.partitionable_graph.abstract_constrained_vertex import \
    AbstractConstrainedVertex


class PartitionedVertex(AbstractConstrainedVertex):
    """ Represents a sub-set of atoms from a AbstractConstrainedVertex
    """
    def __init__(self, lo_atom, hi_atom, resources_required, label=None,
                 constraints=None):
        """

        :param lo_atom: The id of the first atom in the subvertex with\
                        reference to the atoms in the vertex
        :type lo_atom: int
        :param hi_atom: The id of the last atom in the subvertex with\
                        reference to the atoms in the vertex
        :type hi_atom: int
        :param resources_required: The approximate resources needed for
                                   the vertex
        :type resources_required:
        :py:class:`pacman.models.resources.resource_container.ResourceContainer`
        :param label: The name of the subvertex, or None if no name
        :type label: str
        :param constraints: The constraints of the subvertex
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
                    * If lo_atom is less than 0
                    * If hi_atom is less than lo_atom
        """
        AbstractConstrainedVertex.__init__(self, label=label,
                                           n_atoms=hi_atom - lo_atom + 1)
        if lo_atom < 0:
            raise PacmanInvalidParameterException(
                "lo_atom", str(lo_atom), "Cannot be less than 0")
        if hi_atom < lo_atom:
            raise PacmanInvalidParameterException(
                "hi_atom", str(hi_atom), "Cannot be less than lo_atom")
        
        self._label = label
        self._lo_atom = lo_atom
        self._hi_atom = hi_atom
        self._resources_required = resources_required
        self._constraints = list()
        self.add_constraints(constraints)
    
    @property
    def lo_atom(self):
        """ The id of the first atom in the subvertex

        :return: The id of the first atom
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._lo_atom

    @property
    def hi_atom(self):
        """ The id of the last atom in the subvertex

        :return: The id of the last atom
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._hi_atom

    @property
    def resources_required(self):
        """The resources that vertex requires

        :return: The resources required by the vertex
        :rtype:
        :py:class:`pacman.models.resources.resource_container.ResourceContainer`
        :raise None: Raises no known exceptions
        """
        return self._resources_required